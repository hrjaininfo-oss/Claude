import React, { useId } from 'react';
import { random } from 'remotion';
import { CharId, LOOKS, Look } from './looks';
import { mouthAt, useAbsFrame } from '../time';

/**
 * 2D character rig.
 * - views: front (with head turn), side (profile, faces right; use flip for left), back
 * - expressions, auto-blink, gaze, lip-sync from the real voice track, breathing
 * - walk cycle (side: proper hip/knee/arm swing; front/back: alternating lift)
 * - posable arms with props held in the hand
 * - directional lighting baked into gradients (soft or hard "half-lit" terminator)
 *
 * Units: the rig is drawn in a 400 × 1000 box, feet at y = 1000. `height` scales it.
 */

export type Expr =
  | 'neutral'
  | 'smile'
  | 'warm'
  | 'worried'
  | 'scared'
  | 'terrified'
  | 'serious'
  | 'curious'
  | 'sinister'
  | 'sleep'
  | 'whisper';

type Arm = [number, number]; // [shoulder°, elbow°]

export type CharacterProps = {
  id: CharId;
  x: number;
  y: number;
  height: number;
  view?: 'front' | 'side' | 'back';
  flip?: boolean;
  expr?: Expr;
  mouth?: number;
  lipSync?: boolean;
  blink?: number;
  gaze?: [number, number];
  headTurn?: number; // -1..1 (front view)
  headTilt?: number; // degrees
  walk?: number; // phase in radians
  armL?: Arm;
  armR?: Arm;
  holdL?: React.ReactNode;
  holdR?: React.ReactNode;
  light?: { dir?: number; hard?: number; amount?: number };
  filter?: string;
  lean?: number;
  breathe?: boolean;
  opacity?: number;
  sweat?: boolean;
};

type ExprDef = {
  eyeOpen: number;
  pupil: number;
  browIn: number; // +down / -up
  browOut: number;
  browAsym?: number; // raise left brow extra
  smile: number;
  smileAsym?: number;
  mouthBase: number;
  lidTop?: number; // heavy upper lid 0..1
};

const EXPR: Record<Expr, ExprDef> = {
  neutral: { eyeOpen: 1, pupil: 1, browIn: 0, browOut: 0, smile: 0.05, mouthBase: 0 },
  smile: { eyeOpen: 0.85, pupil: 1, browIn: -2, browOut: 0, smile: 0.75, mouthBase: 0 },
  warm: { eyeOpen: 0.8, pupil: 1.05, browIn: -3, browOut: 1, smile: 0.9, mouthBase: 0.05, lidTop: 0.15 },
  worried: { eyeOpen: 1.1, pupil: 0.95, browIn: -9, browOut: 3, smile: -0.35, mouthBase: 0 },
  scared: { eyeOpen: 1.35, pupil: 0.7, browIn: -12, browOut: -4, smile: -0.4, mouthBase: 0.18 },
  terrified: { eyeOpen: 1.5, pupil: 0.55, browIn: -15, browOut: -6, smile: -0.6, mouthBase: 0.45 },
  serious: { eyeOpen: 0.85, pupil: 1, browIn: 6, browOut: -2, smile: -0.12, mouthBase: 0, lidTop: 0.25 },
  curious: { eyeOpen: 1.1, pupil: 1.05, browIn: -4, browOut: -6, browAsym: -6, smile: 0.05, mouthBase: 0 },
  sinister: { eyeOpen: 0.7, pupil: 0.9, browIn: 7, browOut: -5, smile: 0.55, smileAsym: 0.5, mouthBase: 0, lidTop: 0.35 },
  sleep: { eyeOpen: 0, pupil: 1, browIn: 0, browOut: 1, smile: 0, mouthBase: 0.05 },
  whisper: { eyeOpen: 1.05, pupil: 0.9, browIn: -6, browOut: 2, smile: -0.1, mouthBase: 0 },
};

const UA = 175; // upper arm
const FA = 160; // forearm
const TH = 230; // thigh
const SH = 225; // shin

/* ---------------------------------------------------------------- helpers */

const Grad: React.FC<{ id: string; light: string; mid: string; dark: string; dir: number; hard: number }> = ({
  id,
  light,
  mid,
  dark,
  dir,
  hard,
}) => {
  const a = 0.5 - 0.45 * (1 - hard);
  const b = 0.5 + 0.45 * (1 - hard);
  const lit = dir >= 0;
  return (
    <linearGradient id={id} x1={lit ? '1' : '0'} y1="0" x2={lit ? '0' : '1'} y2="0.15">
      <stop offset="0" stopColor={light} />
      <stop offset={a} stopColor={mid} />
      <stop offset={b} stopColor={mid} stopOpacity={1} />
      <stop offset={Math.min(1, b + 0.02 + 0.25 * (1 - hard))} stopColor={dark} />
      <stop offset="1" stopColor={dark} />
    </linearGradient>
  );
};

/* ---------------------------------------------------------------- hair */

const HairFront: React.FC<{ look: Look; fill: string; turn: number }> = ({ look, fill, turn }) => {
  const s = turn * 10;
  if (look.hairStyle === 'curly') {
    const curls = [];
    for (let i = 0; i < 15; i++) {
      const a = Math.PI * (1.05 + (i / 14) * 0.9);
      const r = 66 + (i % 2) * 5;
      curls.push(<circle key={i} cx={Math.cos(a) * r + s} cy={86 + Math.sin(a) * 82} r={21 + (i % 3) * 3} fill={fill} />);
    }
    return (
      <g>
        <path d={`M-70 92 C-80 10 80 10 70 92 C60 55 30 40 0 40 C-30 40 -60 55 -70 92 Z`} fill={fill} />
        {curls}
        <circle cx={-30 + s} cy={30} r={22} fill={fill} />
        <circle cx={18 + s} cy={24} r={24} fill={fill} />
        <circle cx={48 + s} cy={40} r={18} fill={fill} />
      </g>
    );
  }
  if (look.hairStyle === 'oiled') {
    return (
      <g>
        <path
          d={`M-70 102 C-80 20 -30 -4 4 -2 C50 0 82 26 72 102 C70 70 62 52 46 44 C20 36 -8 40 ${-26 + s} 30 C-50 46 -62 66 -70 102 Z`}
          fill={fill}
        />
        <path d={`M${-28 + s} 30 C-10 14 30 10 56 30`} stroke="rgba(255,255,255,0.22)" strokeWidth={4} fill="none" />
        <path d={`M-58 60 C-48 34 -30 22 -10 16`} stroke="rgba(255,255,255,0.12)" strokeWidth={3} fill="none" />
      </g>
    );
  }
  // side-swept (Rahul)
  return (
    <g>
      <path
        d={`M-71 104 C-84 24 -36 -14 10 -10 C58 -8 86 26 73 104 C68 76 60 58 46 48 C${18 + s} 36 ${-14 + s} 52 ${-44 + s} 34 C-58 52 -66 76 -71 104 Z`}
        fill={fill}
      />
      <path d={`M${-44 + s} 34 C-20 4 30 -2 62 26`} stroke="rgba(255,255,255,0.1)" strokeWidth={5} fill="none" />
      <path d={`M${-20 + s} 20 C0 6 20 4 40 12`} stroke="rgba(0,0,0,0.35)" strokeWidth={3} fill="none" />
    </g>
  );
};

/* ---------------------------------------------------------------- face (front) */

const FaceFront: React.FC<{
  look: Look;
  uid: string;
  e: ExprDef;
  mouth: number;
  blink: number;
  gaze: [number, number];
  turn: number;
  sweat?: boolean;
}> = ({ look, uid, e, mouth, blink, gaze, turn, sweat }) => {
  const s = turn * 14;
  const open = Math.max(0, e.eyeOpen * (1 - blink));
  const eyeH = 9.5 * open;
  const eye = (side: -1 | 1) => {
    const cx = side * 27 + s;
    const cy = 96;
    const far = (side === 1 && turn < 0) || (side === -1 && turn > 0);
    const w = 17 * (far ? 1 - Math.abs(turn) * 0.35 : 1);
    const gx = gaze[0] * 6;
    const gy = gaze[1] * 3;
    const lid = (e.lidTop ?? 0) * eyeH;
    return (
      <g key={side}>
        {/* socket shadow */}
        <ellipse cx={cx} cy={cy - 2} rx={w + 5} ry={13} fill={look.skinShadow} opacity={0.35} />
        {open > 0.05 ? (
          <>
            <clipPath id={`${uid}-eye${side}`}>
              <path d={`M${cx - w} ${cy} Q${cx} ${cy - eyeH * 1.5} ${cx + w} ${cy} Q${cx} ${cy + eyeH * 1.2} ${cx - w} ${cy} Z`} />
            </clipPath>
            <path
              d={`M${cx - w} ${cy} Q${cx} ${cy - eyeH * 1.5} ${cx + w} ${cy} Q${cx} ${cy + eyeH * 1.2} ${cx - w} ${cy} Z`}
              fill="#f2ece4"
            />
            <g clipPath={`url(#${uid}-eye${side})`}>
              <circle cx={cx + gx} cy={cy + gy} r={8.5} fill={look.iris} />
              <circle cx={cx + gx} cy={cy + gy} r={8.5} fill="none" stroke="#000" strokeOpacity={0.5} strokeWidth={1.5} />
              <circle cx={cx + gx} cy={cy + gy} r={4.2 * e.pupil} fill="#050303" />
              <circle cx={cx + gx + 2.5} cy={cy + gy - 3} r={2} fill="#fff" opacity={0.9} />
              {/* upper lid shadow on the eyeball */}
              <rect x={cx - w} y={cy - eyeH * 1.6} width={w * 2} height={eyeH * 0.55 + lid} fill={look.skinShadow} opacity={0.55} />
            </g>
            <path
              d={`M${cx - w - 1} ${cy + 1} Q${cx} ${cy - eyeH * 1.55 + lid} ${cx + w + 1} ${cy}`}
              stroke="#140c08"
              strokeWidth={3.2}
              fill="none"
              strokeLinecap="round"
            />
            <path d={`M${cx - w + 3} ${cy + 2} Q${cx} ${cy + eyeH * 1.15} ${cx + w - 2} ${cy + 1}`} stroke={look.skinShadow} strokeWidth={1.5} fill="none" opacity={0.8} />
          </>
        ) : (
          <path d={`M${cx - w} ${cy + 1} Q${cx} ${cy + 6} ${cx + w} ${cy + 1}`} stroke="#140c08" strokeWidth={3} fill="none" strokeLinecap="round" />
        )}
      </g>
    );
  };
  const brow = (side: -1 | 1) => {
    const cx = side * 27 + s;
    const asym = side === -1 ? (e.browAsym ?? 0) : 0;
    const yi = 76 + e.browIn + asym * 0.5;
    const yo = 76 + e.browOut + asym;
    const xi = cx - side * 15;
    const xo = cx + side * 18;
    return (
      <path
        key={`b${side}`}
        d={`M${xi} ${yi + 2} Q${(xi + xo) / 2} ${Math.min(yi, yo) - 6} ${xo} ${yo + 3} L${xo} ${yo + 7} Q${(xi + xo) / 2} ${Math.min(yi, yo) + 1} ${xi} ${yi + 8} Z`}
        fill={look.brow}
      />
    );
  };

  // mouth
  const m = Math.min(1, Math.max(0, mouth + e.mouthBase));
  const mx = s * 0.9;
  const my = 148;
  const w = 17 + e.smile * 4 + m * 2;
  const cornerL = my - e.smile * 7 - (e.smileAsym ?? 0) * 6;
  const cornerR = my - e.smile * 7 + (e.smileAsym ?? 0) * 4;
  const h = 2 + m * 20;
  const mouthEl =
    m > 0.06 ? (
      <g>
        <path
          d={`M${mx - w} ${cornerL} Q${mx} ${my - 4} ${mx + w} ${cornerR} Q${mx} ${my + h * 1.6} ${mx - w} ${cornerL} Z`}
          fill="#2a0c0a"
        />
        <clipPath id={`${uid}-mouth`}>
          <path d={`M${mx - w} ${cornerL} Q${mx} ${my - 4} ${mx + w} ${cornerR} Q${mx} ${my + h * 1.6} ${mx - w} ${cornerL} Z`} />
        </clipPath>
        <g clipPath={`url(#${uid}-mouth)`}>
          <rect x={mx - w} y={my - 8} width={w * 2} height={8 + Math.min(5, h * 0.25)} fill="#efe9de" />
          <ellipse cx={mx} cy={my + h * 1.1} rx={w * 0.6} ry={h * 0.45} fill="#9a3a36" />
        </g>
        <path d={`M${mx - w} ${cornerL} Q${mx} ${my - 4} ${mx + w} ${cornerR}`} stroke={look.lip} strokeWidth={3.2} fill="none" strokeLinecap="round" />
        <path d={`M${mx - w * 0.7} ${my + h * 1.05} Q${mx} ${my + h * 1.45} ${mx + w * 0.7} ${my + h * 1.05}`} stroke={look.lip} strokeWidth={4} fill="none" strokeLinecap="round" opacity={0.85} />
      </g>
    ) : (
      <g>
        <path d={`M${mx - w} ${cornerL} Q${mx} ${my + 3 + e.smile * 4} ${mx + w} ${cornerR}`} stroke="#3a1712" strokeWidth={3.2} fill="none" strokeLinecap="round" />
        <path d={`M${mx - w * 0.6} ${my + 8} Q${mx} ${my + 13} ${mx + w * 0.6} ${my + 8}`} stroke={look.lip} strokeWidth={4} fill="none" strokeLinecap="round" opacity={0.6} />
      </g>
    );

  return (
    <g>
      {eye(-1)}
      {eye(1)}
      {brow(-1)}
      {brow(1)}
      {/* nose */}
      <path d={`M${-2 + s} 98 Q${-6 + s * 1.2} 118 ${-12 + s * 1.2} 126`} stroke={look.skinShadow} strokeWidth={3} fill="none" opacity={0.7} strokeLinecap="round" />
      <path d={`M${-13 + s * 1.2} 126 Q${s * 1.2} 135 ${13 + s * 1.2} 126`} stroke={look.skinShadow} strokeWidth={3} fill="none" strokeLinecap="round" />
      <ellipse cx={-7 + s * 1.2} cy={128} rx={3.5} ry={2} fill="#2a140c" opacity={0.6} />
      <ellipse cx={7 + s * 1.2} cy={128} rx={3.5} ry={2} fill="#2a140c" opacity={0.6} />
      <ellipse cx={2 + s * 1.2} cy={116} rx={4} ry={9} fill={look.skinLight} opacity={0.35} />
      {look.mustache && (
        <path
          d={`M${mx - 30} ${my - 2} Q${mx - 18} ${my - 17} ${mx} ${my - 11} Q${mx + 18} ${my - 17} ${mx + 30} ${my - 2} Q${mx + 16} ${my - 8} ${mx} ${my - 5} Q${mx - 16} ${my - 8} ${mx - 30} ${my - 2} Z`}
          fill={look.hair}
        />
      )}
      {mouthEl}
      {look.glasses && (
        <g fill="rgba(200,220,255,0.08)" stroke="#161210" strokeWidth={3.5}>
          <circle cx={-27 + s} cy={96} r={20} />
          <circle cx={27 + s} cy={96} r={20} />
          <path d={`M${-7 + s} 94 Q${s} 89 ${7 + s} 94`} fill="none" />
          <line x1={-47 + s} y1={93} x2={-66} y2={88} />
          <line x1={47 + s} y1={93} x2={66} y2={88} />
          <path d={`M${-36 + s} 84 L${-28 + s} 80`} stroke="rgba(255,255,255,0.5)" strokeWidth={2} />
        </g>
      )}
      {sweat && (
        <g fill="rgba(220,235,255,0.75)">
          <path d={`M${50 + s} 58 Q${46 + s} 70 ${50 + s} 74 Q${54 + s} 70 ${50 + s} 58 Z`} />
          <path d={`M${-56 + s} 112 Q${-60 + s} 124 ${-56 + s} 128 Q${-52 + s} 124 ${-56 + s} 112 Z`} />
        </g>
      )}
    </g>
  );
};

/* ---------------------------------------------------------------- side face */

const FaceSide: React.FC<{ look: Look; e: ExprDef; mouth: number; blink: number }> = ({ look, e, mouth, blink }) => {
  const m = Math.min(1, mouth + e.mouthBase);
  const open = Math.max(0, e.eyeOpen * (1 - blink));
  return (
    <g>
      {/* eye */}
      {open > 0.05 ? (
        <g>
          <path d={`M30 96 Q40 ${96 - 9 * open} 50 95 Q42 ${100 + 4 * open} 30 96 Z`} fill="#f2ece4" />
          <circle cx={44} cy={96} r={5.5} fill={look.iris} />
          <circle cx={45} cy={96} r={2.6} fill="#000" />
          <path d={`M29 96 Q40 ${95 - 10 * open} 51 94`} stroke="#140c08" strokeWidth={3} fill="none" strokeLinecap="round" />
        </g>
      ) : (
        <path d="M30 97 Q40 101 50 96" stroke="#140c08" strokeWidth={3} fill="none" />
      )}
      <path d={`M26 ${78 + e.browIn * 0.5} Q40 ${72 + Math.min(e.browIn, e.browOut) * 0.6} 54 ${80 + e.browIn}`} stroke={look.brow} strokeWidth={6} fill="none" strokeLinecap="round" />
      {/* nostril + cheek line */}
      <path d="M62 124 Q58 128 62 130" stroke="#2a140c" strokeWidth={2.5} fill="none" />
      {look.mustache && <path d="M48 134 Q62 128 74 136 Q64 140 50 140 Z" fill={look.hair} />}
      {/* mouth: lips part with speech */}
      <path d={`M54 ${142} L72 ${141 - e.smile * 3}`} stroke="#3a1712" strokeWidth={3} strokeLinecap="round" />
      {m > 0.06 && <path d={`M56 141 L71 140 L68 ${142 + m * 12} Q60 ${144 + m * 10} 56 141 Z`} fill="#2a0c0a" />}
      {look.glasses && (
        <g stroke="#161210" strokeWidth={3.5} fill="rgba(200,220,255,0.08)">
          <ellipse cx={46} cy={96} rx={10} ry={18} />
          <line x1={36} y1={93} x2={-6} y2={92} />
        </g>
      )}
    </g>
  );
};

/* ---------------------------------------------------------------- main */

export const Character: React.FC<CharacterProps> = (p) => {
  const frame = useAbsFrame();
  const uid = useId().replace(/[^a-zA-Z0-9]/g, '');
  const look = LOOKS[p.id];
  const view = p.view ?? 'front';
  const e = EXPR[p.expr ?? 'neutral'];
  const dir = p.light?.dir ?? 0.6;
  const hard = p.light?.hard ?? 0;
  const t = frame / 30;

  // automatic blink: ~every 3–5 s, 5 frames long, unique rhythm per character
  const seed = p.id.length * 7.3;
  const period = 3.4 + random(`blink-${p.id}`) * 1.8;
  const ph = ((t + seed) % period) / period;
  const autoBlink = ph > 0.965 ? Math.sin(((ph - 0.965) / 0.035) * Math.PI) : 0;
  const blink = Math.max(p.blink ?? 0, (p.expr === 'sleep' ? 0 : autoBlink));

  const lip = p.lipSync === false ? 0 : mouthAt(p.id, frame);
  const mouth = Math.max(p.mouth ?? 0, lip);
  const talkNod = lip * 1.6 * Math.sin(frame / 3);

  const breathe = p.breathe === false ? 0 : Math.sin((t * 2 * Math.PI) / 3.6 + seed);
  const walking = p.walk !== undefined;
  const wp = p.walk ?? 0;
  const bob = walking ? -Math.abs(Math.sin(wp)) * 10 : breathe * -1.5;

  const s = p.height / 1000;
  const flipX = p.flip ? -1 : 1;

  const skinF = `url(#${uid}-skin)`;
  const topF = `url(#${uid}-top)`;
  const pantsF = `url(#${uid}-pants)`;
  const hairF = `url(#${uid}-hair)`;
  const shawlF = `url(#${uid}-shawl)`;

  const defs = (
    <defs>
      <Grad id={`${uid}-skin`} light={look.skinLight} mid={look.skin} dark={look.skinShadow} dir={dir} hard={hard} />
      <Grad id={`${uid}-top`} light={look.top} mid={look.top} dark={look.topShadow} dir={dir} hard={hard} />
      <Grad id={`${uid}-pants`} light={look.pants} mid={look.pants} dark={look.pantsShadow} dir={dir} hard={hard} />
      <Grad id={`${uid}-hair`} light="#3a2c28" mid={look.hair} dark={look.hair} dir={dir} hard={hard} />
      {look.shawl && <Grad id={`${uid}-shawl`} light="#8a5a3a" mid={look.shawl} dark="#2c180c" dir={dir} hard={hard} />}
      {look.check && (
        <pattern id={`${uid}-check`} width="26" height="26" patternUnits="userSpaceOnUse">
          <rect width="26" height="26" fill={look.top} />
          <rect width="26" height="8" fill={look.topDetail} opacity={0.55} />
          <rect width="8" height="26" fill={look.topDetail} opacity={0.55} />
          <rect x="15" width="2" height="26" fill="#e3c9a0" opacity={0.25} />
        </pattern>
      )}
      {/* overall shading overlay for the dark side when the light is hard */}
      <linearGradient id={`${uid}-shade`} x1={dir >= 0 ? '1' : '0'} y1="0" x2={dir >= 0 ? '0' : '1'} y2="0">
        <stop offset="0" stopColor="#000" stopOpacity={0} />
        <stop offset={0.5 - 0.3 * (1 - hard)} stopColor="#000" stopOpacity={0} />
        <stop offset={0.52 + 0.3 * (1 - hard)} stopColor="#000" stopOpacity={0.35 + 0.6 * hard} />
        <stop offset="1" stopColor="#000" stopOpacity={0.45 + 0.5 * hard} />
      </linearGradient>
    </defs>
  );

  const hand = (fill: string) => (
    <g>
      <ellipse cx={0} cy={18} rx={17} ry={24} fill={fill} />
      <ellipse cx={-10} cy={6} rx={6} ry={12} fill={fill} transform="rotate(25 -10 6)" />
    </g>
  );

  /* ---------- FRONT / BACK ---------- */
  const front = () => {
    const back = view === 'back';
    const turn = back ? 0 : p.headTurn ?? 0;
    const liftL = walking ? Math.max(0, Math.sin(wp)) : 0;
    const liftR = walking ? Math.max(0, -Math.sin(wp)) : 0;
    const swing = walking ? Math.sin(wp) : 0;
    const armL: Arm = p.armL ?? [6 + (walking ? swing * 6 : 0), walking ? 12 + liftR * 18 : 8];
    const armR: Arm = p.armR ?? [6 - (walking ? swing * 6 : 0), walking ? 12 + liftL * 18 : 8];
    const kurta = !!look.kurta;

    const leg = (side: -1 | 1, lift: number) => (
      <g transform={`translate(${side * 40} 515)`}>
        <g transform={`scale(1 ${1 - lift * 0.16})`}>
          <path d={`M-38 0 L38 0 L34 ${TH} L-32 ${TH} Z`} fill={pantsF} />
        </g>
        <g transform={`translate(0 ${TH * (1 - lift * 0.16)})`}>
          <path d={`M-32 0 L34 0 L28 ${SH - lift * 40} L-28 ${SH - lift * 40} Z`} fill={pantsF} />
          <path d={`M-36 ${SH - 10 - lift * 40} Q0 ${SH - 30 - lift * 40} 40 ${SH - 6 - lift * 40} L44 ${SH + 20 - lift * 40} L-40 ${SH + 20 - lift * 40} Z`} fill={look.shoes} />
          <rect x={-40} y={SH + 14 - lift * 40} width={84} height={8} fill="rgba(0,0,0,0.35)" />
        </g>
      </g>
    );

    const arm = (side: -1 | 1, a: Arm, held?: React.ReactNode) => {
      const sh = side === -1 ? a[0] : -a[0];
      const el = side === -1 ? -a[1] : a[1];
      return (
        <g transform={`translate(${side * 98} 236) rotate(${sh})`}>
          <path d={`M-24 -6 L24 -6 L20 ${UA} L-20 ${UA} Z`} fill={kurta ? topF : topF} />
          <g transform={`translate(0 ${UA}) rotate(${el})`}>
            <path d={`M-20 -4 L20 -4 L16 ${FA} L-16 ${FA} Z`} fill={topF} />
            {look.hoodie && <rect x={-18} y={FA - 18} width={36} height={18} rx={4} fill={look.topShadow} />}
            <g transform={`translate(0 ${FA - 4})`}>
              {hand(skinF)}
              {held && <g transform={`translate(0 30) rotate(${-(sh + el)})`}>{held}</g>}
            </g>
          </g>
        </g>
      );
    };

    const torso = (
      <g transform={`scale(1 ${1 + breathe * 0.006})`} style={{ transformOrigin: '0 520px' }}>
        {kurta ? (
          <path d="M-100 222 Q0 200 100 222 L104 520 L130 770 L-130 770 L-104 520 Z" fill={topF} />
        ) : (
          <path d="M-100 222 Q0 202 100 222 L90 380 L82 530 L-82 530 L-90 380 Z" fill={look.check ? `url(#${uid}-check)` : topF} />
        )}
        {!back && look.check && (
          <>
            <path d="M-22 214 L22 214 L18 530 L-18 530 Z" fill={look.under} />
            <path d="M-26 208 L-4 250 L-30 300 Z" fill={look.topShadow} />
            <path d="M26 208 L4 250 L30 300 Z" fill={look.topShadow} />
          </>
        )}
        {!back && look.hoodie && (
          <>
            <path d="M-56 214 Q0 262 56 214 Q30 236 0 238 Q-30 236 -56 214 Z" fill={look.topShadow} />
            <line x1={-14} y1={236} x2={-16} y2={330} stroke={look.topDetail} strokeWidth={4} />
            <line x1={14} y1={236} x2={16} y2={322} stroke={look.topDetail} strokeWidth={4} />
            <path d="M-62 420 L62 420 L72 500 L-72 500 Z" fill={look.topShadow} opacity={0.7} />
            <rect x={-84} y={506} width={168} height={24} fill={look.topShadow} />
          </>
        )}
        {back && look.hoodie && <path d="M-60 212 Q0 300 60 212 Q0 236 -60 212 Z" fill={look.topShadow} />}
        {!back && kurta && (
          <>
            <line x1={0} y1={220} x2={0} y2={380} stroke={look.topDetail} strokeWidth={3} />
            {[250, 290, 330].map((y) => (
              <circle key={y} cx={0} cy={y} r={4} fill="#8a7a5a" />
            ))}
          </>
        )}
        {look.shawl && (
          <>
            <path d="M-108 216 Q0 190 108 216 L118 300 Q0 270 -118 300 Z" fill={shawlF} />
            {!back && (
              <>
                <path d="M-112 236 L-70 236 L-58 640 L-104 650 Z" fill={shawlF} />
                <path d="M112 236 L70 236 L58 640 L104 650 Z" fill={shawlF} />
                <path d="M-104 640 L-58 632 M104 640 L58 632" stroke="#c9a26a" strokeWidth={5} />
              </>
            )}
            {back && <path d="M-118 220 Q0 200 118 220 L110 640 Q0 660 -110 640 Z" fill={shawlF} />}
          </>
        )}
        {/* lighting overlay on torso */}
        <path d={kurta ? 'M-100 222 Q0 200 100 222 L104 520 L130 770 L-130 770 L-104 520 Z' : 'M-100 222 Q0 202 100 222 L90 380 L82 530 L-82 530 L-90 380 Z'} fill={`url(#${uid}-shade)`} />
      </g>
    );

    const head = (
      <g transform={`rotate(${(p.headTilt ?? 0) + talkNod} 0 200)`}>
        {/* neck */}
        <path d="M-22 160 L22 160 L24 222 L-24 222 Z" fill={skinF} />
        <path d="M-22 175 Q0 196 22 175 L22 190 Q0 206 -22 190 Z" fill="#000" opacity={0.25} />
        {/* ears */}
        {!back && (
          <>
            <ellipse cx={-68 + turn * 6} cy={104} rx={11} ry={20} fill={skinF} opacity={turn > 0.6 ? 0 : 1} />
            <ellipse cx={68 + turn * 6} cy={104} rx={11} ry={20} fill={skinF} opacity={turn < -0.6 ? 0 : 1} />
          </>
        )}
        {/* face */}
        <path
          d={`M-68 84 C-70 18 70 18 68 84 C68 ${128 + look.jaw * 8} ${36 + look.jaw * 8} 182 ${turn * 8} 184 C${-36 - look.jaw * 8} 182 -68 ${128 + look.jaw * 8} -68 84 Z`}
          fill={skinF}
        />
        {!back && (
          <>
            {/* cheek warmth + jaw shadow */}
            <ellipse cx={-38 + turn * 14} cy={132} rx={16} ry={10} fill="#c0504a" opacity={0.12} />
            <ellipse cx={38 + turn * 14} cy={132} rx={16} ry={10} fill="#c0504a" opacity={0.12} />
            {look.stubble && (
              <path
                d={`M-60 120 C-56 160 -30 182 ${turn * 8} 184 C30 182 56 160 60 120 C40 150 20 160 ${turn * 8} 160 C-20 160 -40 150 -60 120 Z`}
                fill="#1d1a22"
                opacity={0.22}
              />
            )}
            <FaceFront look={look} uid={uid} e={e} mouth={mouth} blink={blink} gaze={p.gaze ?? [0, 0]} turn={turn} sweat={p.sweat} />
          </>
        )}
        <path
          d={`M-68 84 C-70 18 70 18 68 84 C68 ${128 + look.jaw * 8} ${36 + look.jaw * 8} 182 ${turn * 8} 184 C${-36 - look.jaw * 8} 182 -68 ${128 + look.jaw * 8} -68 84 Z`}
          fill={`url(#${uid}-shade)`}
        />
        {back ? (
          <g fill={hairF}>
            <ellipse cx={0} cy={92} rx={72} ry={94} />
            {look.hairStyle === 'curly' &&
              [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((i) => (
                <circle key={i} cx={Math.cos((i / 12) * Math.PI * 2) * 58} cy={86 + Math.sin((i / 12) * Math.PI * 2) * 70} r={24} />
              ))}
            <ellipse cx={-70} cy={108} rx={10} ry={18} fill={skinF} />
            <ellipse cx={70} cy={108} rx={10} ry={18} fill={skinF} />
          </g>
        ) : (
          <HairFront look={look} fill={hairF} turn={turn} />
        )}
      </g>
    );

    return (
      <g>
        {leg(-1, liftL)}
        {leg(1, liftR)}
        {back ? null : null}
        {torso}
        {arm(-1, armL, p.holdL)}
        {arm(1, armR, p.holdR)}
        {head}
      </g>
    );
  };

  /* ---------- SIDE (faces right) ---------- */
  const side = () => {
    const amp = walking ? 1 : 0;
    const legPose = (phase: number) => {
      const thigh = 21 * Math.sin(phase) * amp;
      const knee = (4 + 34 * Math.pow(Math.max(0, Math.cos(phase)), 1.6)) * amp;
      return { thigh, knee };
    };
    const lA = legPose(wp);
    const lB = legPose(wp + Math.PI);
    const armSwingA = walking ? -22 * Math.sin(wp) : 0;
    const armA: Arm = p.armR ?? [armSwingA + 4, walking ? 14 + 10 * Math.max(0, -Math.sin(wp)) : 10];
    const armB: Arm = p.armL ?? [-armSwingA + 4, walking ? 14 + 10 * Math.max(0, Math.sin(wp)) : 10];
    const kurta = !!look.kurta;

    const leg = (pose: { thigh: number; knee: number }, far: boolean) => (
      <g transform={`translate(${far ? -6 : 6} 512) rotate(${-pose.thigh})`} opacity={1}>
        <path d={`M-34 0 L34 0 L28 ${TH} L-24 ${TH} Z`} fill={far ? look.pantsShadow : pantsF} />
        <g transform={`translate(2 ${TH}) rotate(${pose.knee})`}>
          <path d={`M-26 0 L28 0 L22 ${SH} L-22 ${SH} Z`} fill={far ? look.pantsShadow : pantsF} />
          <path d={`M-26 ${SH - 6} L44 ${SH - 2} Q62 ${SH + 6} 58 ${SH + 20} L-28 ${SH + 20} Z`} fill={far ? '#111' : look.shoes} opacity={far ? 0.85 : 1} />
        </g>
      </g>
    );
    const arm = (a: Arm, far: boolean, held?: React.ReactNode) => (
      <g transform={`translate(4 236) rotate(${-a[0]})`}>
        <path d={`M-24 -8 L24 -8 L19 ${UA} L-19 ${UA} Z`} fill={far ? look.topShadow : topF} />
        <g transform={`translate(0 ${UA}) rotate(${-a[1]})`}>
          <path d={`M-19 -4 L19 -4 L15 ${FA} L-15 ${FA} Z`} fill={far ? look.topShadow : topF} />
          <g transform={`translate(0 ${FA - 4})`}>
            {hand(far ? look.skinShadow : skinF)}
            {held && <g transform={`translate(0 30) rotate(${a[0] + a[1]})`}>{held}</g>}
          </g>
        </g>
      </g>
    );
    const torsoPath = kurta
      ? 'M-52 222 Q20 206 66 226 L70 520 L96 770 L-84 770 L-62 520 Z'
      : 'M-52 222 Q20 206 66 226 L72 360 L62 530 L-58 530 L-62 380 Z';
    return (
      <g>
        {arm(armB, true)}
        {leg(lB, true)}
        {leg(lA, false)}
        <g transform={`scale(1 ${1 + breathe * 0.006})`}>
          <path d={torsoPath} fill={look.check ? `url(#${uid}-check)` : topF} />
          {look.hoodie && <path d="M-60 214 Q-30 260 0 226 Q-30 210 -60 214 Z" fill={look.topShadow} />}
          {look.shawl && (
            <>
              <path d="M-62 214 Q10 196 70 222 L74 300 Q0 276 -66 300 Z" fill={shawlF} />
              <path d="M30 236 L70 236 L76 640 L36 650 Z" fill={shawlF} />
            </>
          )}
          <path d={torsoPath} fill={`url(#${uid}-shade)`} />
        </g>
        {/* head (profile) */}
        <g transform={`rotate(${(p.headTilt ?? 0) + talkNod} 0 200)`}>
          <path d="M-18 160 L22 160 L26 222 L-24 222 Z" fill={skinF} />
          <path
            d="M-62 84 C-66 22 0 8 42 30 C56 40 58 62 58 78 L64 104 L74 118 L62 126 L64 136 L60 146 L62 152 L52 172 C40 186 10 186 -6 178 C-30 170 -56 150 -62 84 Z"
            fill={skinF}
          />
          <ellipse cx={-6} cy={106} rx={12} ry={20} fill={skinF} />
          <path d="M-8 98 Q-2 106 -8 116" stroke={look.skinShadow} strokeWidth={3} fill="none" />
          {look.stubble && <path d="M-4 150 C10 176 40 182 52 170 L58 150 C40 160 20 160 -4 150 Z" fill="#1d1a22" opacity={0.22} />}
          <FaceSide look={look} e={e} mouth={mouth} blink={blink} />
          <path
            d="M-62 84 C-66 22 0 8 42 30 C56 40 58 62 58 78 L64 104 L74 118 L62 126 L64 136 L60 146 L62 152 L52 172 C40 186 10 186 -6 178 C-30 170 -56 150 -62 84 Z"
            fill={`url(#${uid}-shade)`}
          />
          {/* hair (profile) */}
          {look.hairStyle === 'curly' ? (
            <g fill={hairF}>
              <path d="M-66 104 C-74 20 10 0 50 36 C40 30 20 40 6 52 C-20 56 -40 70 -40 104 Z" />
              {[-56, -36, -14, 8, 30].map((cx, i) => (
                <circle key={cx} cx={cx} cy={i === 4 ? 30 : 22 + Math.abs(cx + 20) * 0.25} r={20} />
              ))}
              <circle cx={-62} cy={70} r={18} />
            </g>
          ) : (
            <path
              d={
                look.hairStyle === 'oiled'
                  ? 'M-66 110 C-76 20 10 -6 52 36 C40 34 24 38 10 46 C-14 48 -36 64 -38 108 Z'
                  : 'M-68 112 C-80 18 14 -14 58 40 C44 36 26 40 12 50 C-12 46 -34 66 -38 110 Z'
              }
              fill={hairF}
            />
          )}
        </g>
        {arm(armA, false, p.holdR ?? p.holdL)}
      </g>
    );
  };

  return (
    <svg
      width={400 * s}
      height={1060 * s}
      viewBox="-200 -40 400 1060"
      style={{
        position: 'absolute',
        left: p.x - 200 * s,
        top: p.y - 1000 * s - 20 * s,
        overflow: 'visible',
        transform: `scaleX(${flipX}) rotate(${p.lean ?? 0}deg) translateY(${bob * s}px)`,
        transformOrigin: '50% 95%',
        filter: p.filter,
        opacity: p.opacity ?? 1,
      }}
    >
      {defs}
      {view === 'side' ? side() : front()}
    </svg>
  );
};

/* ---------------------------------------------------------------- props */

export const HeldLantern: React.FC<{ glow?: number }> = ({ glow = 1 }) => (
  <g transform="translate(0 6)">
    <path d="M0 -20 L0 6" stroke="#1a1208" strokeWidth={4} />
    <circle cx={0} cy={60} r={160} fill="url(#lanternHalo)" opacity={0.55 * glow} />
    <defs>
      <radialGradient id="lanternHalo">
        <stop offset="0" stopColor="#ffd27a" stopOpacity={0.9} />
        <stop offset="0.4" stopColor="#ff9a3a" stopOpacity={0.25} />
        <stop offset="1" stopColor="#ff9a3a" stopOpacity={0} />
      </radialGradient>
    </defs>
    <path d="M-26 8 L26 8 L22 18 L-22 18 Z" fill="#2a1c0c" />
    <path d="M-22 18 L22 18 L26 92 L-26 92 Z" fill={`rgba(255,${180 + 40 * glow},${90 + 40 * glow},${0.75 * glow + 0.15})`} stroke="#2a1c0c" strokeWidth={5} />
    <ellipse cx={0} cy={60} rx={8} ry={16} fill="#fff6d0" opacity={glow} />
    <path d="M-30 92 L30 92 L24 104 L-24 104 Z" fill="#2a1c0c" />
  </g>
);

export const HeldPhone: React.FC<{ on?: boolean }> = ({ on = true }) => (
  <g transform="rotate(-90) translate(-8 -14)">
    <rect x={-14} y={-10} width={28} height={56} rx={5} fill="#111" stroke="#333" strokeWidth={2} />
    {on && <circle cx={0} cy={-2} r={4} fill="#fffbe8" />}
  </g>
);
