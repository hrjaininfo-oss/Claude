import React from 'react';
import { AbsoluteFill, random } from 'remotion';
import { FONT_HAND, FONT_TITLE } from '../fonts';
import { DeadTree } from '../components/haveli';
import { flicker } from '../components/fx';
import { Character } from '../rig/Character';

/* ------------------------------------------------------------------ lighting */

/** Darkness with a soft pool of light; everything outside the pool falls off to `dark`. */
export const LightPool: React.FC<{ x: number; y: number; r: number; dark?: number; color?: string; warm?: number }> = ({
  x,
  y,
  r,
  dark = 0.85,
  color = '255,170,80',
  warm = 0.18,
}) => (
  <>
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at ${x}px ${y}px, rgba(0,0,0,0) 0px, rgba(0,0,0,${dark * 0.35}) ${r * 0.55}px, rgba(0,0,0,${dark}) ${r}px, rgba(0,0,0,${Math.min(1, dark + 0.08)}) ${r * 1.8}px)`,
        pointerEvents: 'none',
      }}
    />
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at ${x}px ${y}px, rgba(${color},${warm}) 0px, rgba(${color},${warm * 0.4}) ${r * 0.4}px, transparent ${r * 0.9}px)`,
        mixBlendMode: 'screen',
        pointerEvents: 'none',
      }}
    />
  </>
);

/** Colour grade: cool moonlight in the shadows. */
export const MoonGrade: React.FC<{ amount?: number }> = ({ amount = 0.35 }) => (
  <AbsoluteFill style={{ background: `rgba(30,60,110,${amount})`, mixBlendMode: 'soft-light', pointerEvents: 'none' }} />
);

/* ------------------------------------------------------------------ sky & road */

export const Sky: React.FC<{ t: number; moonX?: number; moonY?: number; horizon?: number }> = ({ t, moonX = 820, moonY = 330, horizon = 1100 }) => (
  <AbsoluteFill style={{ background: `linear-gradient(180deg,#050a18 0%,#0d1a33 ${horizon * 0.06}%,#1c2c4a ${(horizon / 1920) * 100}%)` }}>
    {new Array(90).fill(0).map((_, i) => (
      <div
        key={i}
        style={{
          position: 'absolute',
          left: random(`sx${i}`) * 1080,
          top: random(`sy${i}`) * horizon * 0.8,
          width: 2 + random(`ss${i}`) * 2.5,
          height: 2 + random(`ss${i}`) * 2.5,
          borderRadius: '50%',
          background: '#e6eeff',
          opacity: 0.25 + 0.55 * Math.abs(Math.sin(t * (0.6 + random(`st${i}`)) + i)),
        }}
      />
    ))}
    <div
      style={{
        position: 'absolute',
        left: moonX - 85,
        top: moonY - 85,
        width: 170,
        height: 170,
        borderRadius: '50%',
        background: 'radial-gradient(circle at 38% 38%, #fbfbf2, #c9d0d4 62%, #9aa4ad)',
        boxShadow: '0 0 160px 60px rgba(150,180,230,0.28)',
      }}
    />
    {[0, 1, 2].map((k) => (
      <div
        key={k}
        style={{
          position: 'absolute',
          left: ((-500 + t * (14 + k * 6) + k * 420) % 1700) - 300,
          top: moonY - 60 + k * 70,
          width: 700 + k * 120,
          height: 70 + k * 20,
          borderRadius: 120,
          background: 'rgba(18,26,44,0.82)',
          filter: 'blur(22px)',
        }}
      />
    ))}
  </AbsoluteFill>
);

export const Car: React.FC<{ x: number; y: number; scale?: number; t: number; lights?: number; moving?: boolean }> = ({
  x,
  y,
  scale = 1,
  t,
  lights = 1,
  moving = true,
}) => {
  const wheelRot = moving ? (t * 720) % 360 : 0;
  const bounce = moving ? Math.sin(t * 17) * 2 + (random(`cb${Math.floor(t * 6)}`) - 0.5) * 3 : 0;
  const wheel = (cx: number) => (
    <g transform={`translate(${cx} 200) rotate(${-wheelRot})`}>
      <circle r={46} fill="#0b0b0c" />
      <circle r={28} fill="#3a3d44" />
      {[0, 72, 144, 216, 288].map((a) => (
        <rect key={a} x={-4} y={-26} width={8} height={22} fill="#1b1c20" transform={`rotate(${a})`} />
      ))}
      <circle r={7} fill="#777" />
    </g>
  );
  return (
    <svg width={620 * scale} height={300 * scale} viewBox="0 0 620 300" style={{ position: 'absolute', left: x, top: y, overflow: 'visible' }}>
      <defs>
        <linearGradient id="carBody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#5a6b80" />
          <stop offset="0.45" stopColor="#2b3646" />
          <stop offset="1" stopColor="#11161e" />
        </linearGradient>
        <linearGradient id="beam" x1="1" y1="0" x2="0" y2="0">
          <stop offset="0" stopColor="#fff4d6" stopOpacity={0} />
          <stop offset="1" stopColor="#fff4d6" stopOpacity={0.55} />
        </linearGradient>
      </defs>
      {/* headlight beam (car faces left) */}
      <polygon points="40,150 -700,60 -700,320 40,190" fill="url(#beam)" opacity={lights} style={{ filter: 'blur(10px)' }} />
      <g transform={`translate(0 ${bounce})`}>
        <path d="M20 190 L30 130 Q40 112 70 108 L150 100 L210 40 Q226 26 260 24 L470 22 Q510 22 530 50 L585 120 Q604 128 604 150 L604 190 Z" fill="url(#carBody)" />
        <path d="M222 48 L262 36 L360 34 L360 104 L170 108 Z" fill="#0d1a2a" />
        <path d="M374 34 L462 34 Q492 36 508 60 L536 104 L374 104 Z" fill="#0d1a2a" />
        <path d="M232 46 L300 38" stroke="rgba(200,220,255,0.35)" strokeWidth={4} />
        {/* passengers' heads silhouettes */}
        <circle cx={300} cy={78} r={22} fill="#05070b" />
        <circle cx={450} cy={78} r={22} fill="#05070b" />
        <rect x={360} y={34} width={14} height={154} fill="#1a2230" />
        <path d="M30 150 L604 150" stroke="#0a0d12" strokeWidth={3} />
        <rect x={380} y={126} width={28} height={6} rx={3} fill="#8a96a8" />
        <rect x={232} y={126} width={28} height={6} rx={3} fill="#8a96a8" />
        {/* headlight & tail light */}
        <ellipse cx={34} cy={150} rx={12} ry={16} fill={lights > 0.1 ? '#fffbe6' : '#555'} />
        <ellipse cx={34} cy={150} rx={40} ry={30} fill="#fff1c8" opacity={0.35 * lights} />
        <rect x={592} y={128} width={12} height={28} rx={4} fill="#ff2a2a" opacity={0.6 + 0.4 * lights} />
        <ellipse cx={604} cy={142} rx={30} ry={22} fill="#ff2a2a" opacity={0.25 * lights} />
      </g>
      {wheel(130)}
      {wheel(500)}
      {/* dust kicked up */}
      {moving &&
        new Array(14).fill(0).map((_, i) => {
          const k = ((t * 1.6 + i / 14) % 1);
          return (
            <circle key={i} cx={560 + k * 260} cy={225 - k * 60 + random(`d${i}`) * 30} r={10 + k * 40} fill="#6b5c4a" opacity={(1 - k) * 0.18} />
          );
        })}
    </svg>
  );
};

/** Side-view night road with parallax layers. `travel` = how far the camera has moved (px). */
export const RoadParallax: React.FC<{ t: number; travel: number }> = ({ t, travel }) => {
  const layer = (speed: number, children: (off: number) => React.ReactNode) => children(-(travel * speed) % 2160);
  return (
    <AbsoluteFill>
      <Sky t={t} moonX={300} moonY={420} horizon={1150} />
      {/* far hills */}
      {layer(0.08, (o) => (
        <svg width={3240} height={1920} style={{ position: 'absolute', left: o, top: 0 }}>
          <path d="M0 1150 Q270 1040 540 1110 T1080 1090 T1620 1120 T2160 1100 T2700 1090 T3240 1150 L3240 1920 L0 1920 Z" fill="#0d1526" />
        </svg>
      ))}
      {/* mid trees */}
      {layer(0.35, (o) => (
        <div style={{ position: 'absolute', left: o, top: 0, width: 3240, height: 1920 }}>
          {[150, 520, 900, 1250, 1700, 2060, 2310, 2700, 3050].map((x, i) => (
            <DeadTree key={i} x={x} y={1250} h={380 + (i % 3) * 90} flip={i % 2 === 1} />
          ))}
        </div>
      ))}
      {/* ground */}
      <AbsoluteFill style={{ top: 1230, background: 'linear-gradient(180deg,#141310,#2a2219 40%,#3a2e20 60%,#17120c)' }} />
      {/* road ruts streaming */}
      {layer(1.0, (o) => (
        <svg width={3240} height={1920} style={{ position: 'absolute', left: o, top: 0 }}>
          {new Array(60).fill(0).map((_, i) => (
            <ellipse key={i} cx={(i * 54) % 3240} cy={1450 + (i % 5) * 28} rx={12 + (i % 4) * 6} ry={4} fill="#120d08" opacity={0.6} />
          ))}
        </svg>
      ))}
      {/* foreground grass, fast */}
      {layer(1.8, (o) => (
        <svg width={3240} height={1920} style={{ position: 'absolute', left: o, top: 0 }}>
          {new Array(120).fill(0).map((_, i) => {
            const x = i * 27;
            const h = 60 + random(`g${i}`) * 120;
            return <path key={i} d={`M${x} 1920 Q${x + 6} ${1920 - h * 0.6} ${x + 14} ${1920 - h} Q${x + 10} ${1920 - h * 0.5} ${x + 20} 1920 Z`} fill="#050605" />;
          })}
        </svg>
      ))}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ haveli */

export const HaveliFacade: React.FC<{ x: number; y: number; scale?: number; lampOn?: number; t: number }> = ({ x, y, scale = 1, lampOn = 1, t }) => {
  const W = 1600;
  const f = flicker(Math.round(t * 30), 'facade', 0.35) * lampOn;
  return (
    <svg width={W * scale} height={1000 * scale} viewBox={`0 0 ${W} 1000`} style={{ position: 'absolute', left: x, top: y, overflow: 'visible' }}>
      <defs>
        <linearGradient id="stone" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#3b4560" />
          <stop offset="1" stopColor="#1b2133" />
        </linearGradient>
        <radialGradient id="lampWash" cx="0.45" cy="0.75" r="0.35">
          <stop offset="0" stopColor="#ffb05a" stopOpacity={0.55 * f} />
          <stop offset="1" stopColor="#ffb05a" stopOpacity={0} />
        </radialGradient>
      </defs>
      <g fill="url(#stone)">
        {[220, 800, 1380].map((cx, i) => (
          <g key={cx}>
            <path d={`M${cx - 74} 250 Q${cx} ${i === 1 ? 110 : 150} ${cx + 74} 250 Z`} />
            <rect x={cx - 4} y={i === 1 ? 80 : 120} width={8} height={40} fill="#5a6278" />
            <rect x={cx - 84} y={250} width={168} height={18} />
            <rect x={cx - 74} y={268} width={14} height={60} />
            <rect x={cx + 60} y={268} width={14} height={60} />
          </g>
        ))}
        <rect x={60} y={320} width={1480} height={260} />
        {new Array(37).fill(0).map((_, i) => (
          <rect key={i} x={60 + i * 40} y={300} width={22} height={24} />
        ))}
        <rect x={0} y={580} width={W} height={420} />
      </g>
      <rect x={-20} y={570} width={W + 40} height={18} fill="#4a5470" />
      {/* plaster damage */}
      {new Array(20).fill(0).map((_, i) => (
        <ellipse key={i} cx={random(`hp${i}`) * W} cy={340 + random(`hq${i}`) * 640} rx={30 + random(`hr${i}`) * 70} ry={12 + random(`hs${i}`) * 30} fill="#141826" opacity={0.5} />
      ))}
      {[0, 1, 2, 3, 4, 5, 6].map((i) => (
        <g key={`w${i}`}>
          <path d={`M${150 + i * 210} 540 L${150 + i * 210} 430 Q${200 + i * 210} 370 ${250 + i * 210} 430 L${250 + i * 210} 540 Z`} fill="#06080f" stroke="#59627c" strokeWidth={5} />
          <rect x={140 + i * 210} y={540} width={120} height={12} fill="#59627c" />
        </g>
      ))}
      {[0, 1, 2, 4, 5, 6].map((i) => (
        <path key={`a${i}`} d={`M${130 + i * 210} 1000 L${130 + i * 210} 760 Q${200 + i * 210} 660 ${270 + i * 210} 760 L${270 + i * 210} 1000 Z`} fill="#05070c" stroke="#3d4660" strokeWidth={6} />
      ))}
      <path d="M680 1000 L680 712 Q800 570 920 712 L920 1000 Z" fill="#0a0806" stroke="#6a5a40" strokeWidth={12} />
      <path d="M690 1000 L690 716 Q745 650 798 630 L798 1000 Z" fill="#2a1a0e" />
      <path d="M802 1000 L802 630 Q855 650 910 716 L910 1000 Z" fill="#24160c" />
      <rect x={0} y={0} width={W} height={1000} fill="url(#lampWash)" />
    </svg>
  );
};

/* ------------------------------------------------------------------ corridor (side view) */

export const CorridorSide: React.FC<{ scroll: number; lampX?: number; lampY?: number; lamp?: number; dark?: number }> = ({
  scroll,
  lampX = 540,
  lampY = 1000,
  lamp = 1,
  dark = 0.8,
}) => {
  const bay = 520;
  const off = -(scroll % bay);
  const first = Math.floor(scroll / bay);
  return (
    <AbsoluteFill style={{ background: '#16120f' }}>
      {/* back wall */}
      <AbsoluteFill style={{ background: 'linear-gradient(180deg,#1c1712 0%,#3a3026 30%,#4a3d30 62%,#2b231b 74%)' }} />
      {/* arched niches + doors on the back wall */}
      {new Array(4).fill(0).map((_, k) => {
        const i = first + k;
        const x = off + k * bay;
        const isDoor = i % 2 === 1;
        return (
          <div key={i} style={{ position: 'absolute', left: x + 120, top: 640, width: 280, height: 780 }}>
            <div
              style={{
                position: 'absolute',
                inset: 0,
                borderRadius: '140px 140px 0 0',
                background: isDoor ? 'linear-gradient(90deg,#2a190e,#3e2716,#2a190e)' : 'linear-gradient(180deg,#120e0a,#1f1812)',
                boxShadow: 'inset 0 0 50px rgba(0,0,0,0.8), 0 0 0 16px #5a4a38',
              }}
            />
            {isDoor && (
              <div style={{ position: 'absolute', top: 120, width: '100%', textAlign: 'center', fontFamily: FONT_TITLE, fontSize: 110, color: '#c9b894', opacity: 0.55 }}>
                {i + 1}
              </div>
            )}
          </div>
        );
      })}
      {/* floor */}
      <AbsoluteFill style={{ top: 1420, background: 'linear-gradient(180deg,#3c2e22,#22190f)' }} />
      {new Array(12).fill(0).map((_, k) => (
        <div key={k} style={{ position: 'absolute', left: ((off * 1.0 + k * 180) % 2160) - 180, top: 1420, width: 4, height: 500, background: 'rgba(0,0,0,0.35)', transform: 'skewX(-30deg)' }} />
      ))}
      <LightPool x={lampX} y={lampY} r={760} dark={dark} warm={0.22 * lamp} />
    </AbsoluteFill>
  );
};

/** Foreground pillars that slide past faster than the wall (parallax). */
export const ForegroundPillars: React.FC<{ scroll: number }> = ({ scroll }) => {
  const bay = 900;
  const off = -((scroll * 1.6) % bay);
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {[0, 1, 2].map((k) => (
        <div
          key={k}
          style={{
            position: 'absolute',
            left: off + k * bay - 100,
            top: 0,
            width: 170,
            height: 1920,
            background: 'linear-gradient(90deg,#030202,#120d09 50%,#030202)',
            filter: 'blur(6px)',
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ bedroom */

export const Mattress: React.FC<{ x: number; y: number; w: number; h: number; color?: string }> = ({ x, y, w, h, color = '#3b4a6a' }) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      width: w,
      height: h,
      borderRadius: 26,
      background: `linear-gradient(180deg, ${color}, #1d2538)`,
      boxShadow: '0 18px 30px rgba(0,0,0,0.6)',
    }}
  >
    <div style={{ position: 'absolute', left: 0, right: 0, top: 14, height: 6, background: 'rgba(255,255,255,0.08)' }} />
  </div>
);

export const Blanket: React.FC<{ x: number; y: number; w: number; h: number; color: string; breathe: number }> = ({ x, y, w, h, color, breathe }) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y - breathe * 4,
      width: w,
      height: h + breathe * 4,
      borderRadius: '40px 60px 30px 30px',
      background: `linear-gradient(180deg, ${color}, rgba(0,0,0,0.6))`,
      boxShadow: 'inset 0 10px 20px rgba(255,255,255,0.06)',
    }}
  >
    {[0.2, 0.45, 0.7].map((k) => (
      <div key={k} style={{ position: 'absolute', left: `${k * 100}%`, top: 10, width: 3, height: '80%', background: 'rgba(0,0,0,0.25)', transform: 'rotate(8deg)' }} />
    ))}
  </div>
);

/* ------------------------------------------------------------------ the 1987 photograph */

export const PHOTO = { x: 250, y: 600, w: 580, h: 480 };
export const YEAR_POS = { x: PHOTO.x + PHOTO.w - 120, y: PHOTO.y + PHOTO.h - 42 };

export const OldPhoto: React.FC = () => {
  const { x, y, w, h } = PHOTO;
  const iw = w - 52;
  const ih = h - 112;
  return (
    <div style={{ position: 'absolute', left: x - 30, top: y - 30, width: w + 60, height: h + 60 }}>
      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg,#4a2e18,#1a0f06 60%,#3a2412)', boxShadow: '0 24px 40px rgba(0,0,0,0.9)' }} />
      <div style={{ position: 'absolute', left: 30, top: 30, width: w, height: h, background: '#ddcca8' }}>
        <div
          style={{
            position: 'absolute',
            left: 26,
            top: 26,
            width: iw,
            height: ih,
            overflow: 'hidden',
            background: 'radial-gradient(ellipse at 50% 40%, #cdb085, #8a6a42 70%, #3c2a16)',
            filter: 'sepia(1) contrast(1.05) brightness(0.95)',
          }}
        >
          {/* haveli arch behind them */}
          <div style={{ position: 'absolute', left: iw * 0.2, top: ih * 0.1, width: iw * 0.6, height: ih, borderRadius: `${iw * 0.3}px ${iw * 0.3}px 0 0`, background: '#5a3f22', opacity: 0.6 }} />
          {/* the same three young men — 1987 */}
          <Character id="rahul" x={iw * 0.2} y={ih * 1.9} height={ih * 1.7} expr="smile" lipSync={false} breathe={false} filter="grayscale(1)" />
          <Character id="karan" x={iw * 0.8} y={ih * 1.9} height={ih * 1.66} expr="smile" lipSync={false} breathe={false} filter="grayscale(1)" />
          <Character id="vikram" x={iw * 0.5} y={ih * 1.92} height={ih * 1.82} expr="smile" lipSync={false} breathe={false} filter="grayscale(1)" />
          {/* age: vignette, scratches, stain */}
          <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(40,22,6,0.75))' }} />
          {new Array(16).fill(0).map((_, i) => (
            <div key={i} style={{ position: 'absolute', left: random(`ps${i}`) * iw, top: random(`pt${i}`) * ih, width: 1.5, height: 40 + random(`pl${i}`) * 140, background: 'rgba(250,235,200,0.4)', transform: `rotate(${(random(`pr${i}`) - 0.5) * 30}deg)` }} />
          ))}
          <div style={{ position: 'absolute', left: iw * 0.05, top: ih * 0.08, width: 120, height: 90, borderRadius: '50%', background: 'rgba(70,40,10,0.3)', filter: 'blur(6px)' }} />
        </div>
        <div
          style={{
            position: 'absolute',
            left: YEAR_POS.x - x - 72,
            top: YEAR_POS.y - y - 50,
            fontFamily: FONT_HAND,
            fontWeight: 700,
            fontSize: 66,
            color: '#2b1a0c',
            transform: 'rotate(-6deg)',
          }}
        >
          1987
        </div>
      </div>
    </div>
  );
};

export const DustyWall: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'radial-gradient(ellipse 300px 220px at 200px 300px, rgba(0,0,0,0.35), transparent), radial-gradient(ellipse 260px 420px at 900px 1300px, rgba(0,0,0,0.4), transparent), linear-gradient(180deg,#4a4035 0%,#3a3128 70%,#17120d 70%,#241c15 100%)',
    }}
  >
    {new Array(16).fill(0).map((_, i) => (
      <div
        key={i}
        style={{
          position: 'absolute',
          left: random(`pp-x-${i}`) * 1000,
          top: random(`pp-y-${i}`) * 1250,
          width: 40 + random(`pp-w-${i}`) * 160,
          height: 20 + random(`pp-h-${i}`) * 90,
          background: '#231d17',
          borderRadius: '40% 60% 30% 70%',
          opacity: 0.6,
        }}
      />
    ))}
  </AbsoluteFill>
);
