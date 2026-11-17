import React from 'react';
import { AbsoluteFill, Easing, interpolate, random } from 'remotion';
import { Shot, handheld } from '../edit';
import { BEATS } from '../timeline';
import { Camera, Dust, GlitchLayer, TorchDarkness, flicker } from '../components/fx';
import { Character } from '../rig/Character';
import { DustyWall, LightPool, OldPhoto, PHOTO, YEAR_POS } from '../sets/sets';
import { feetFor } from './act1';

const Cobweb: React.FC<{ x: number; y: number; size: number; flip?: boolean }> = ({ x, y, size, flip }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" style={{ position: 'absolute', left: x, top: y, transform: flip ? 'scaleX(-1)' : undefined, opacity: 0.4 }}>
    <g stroke="#d8d0c0" strokeWidth={0.5} fill="none">
      {[0, 15, 30, 45, 60, 75, 90].map((a) => (
        <line key={a} x1={0} y1={0} x2={100 * Math.cos((a * Math.PI) / 180)} y2={100 * Math.sin((a * Math.PI) / 180)} />
      ))}
      {[20, 38, 56, 74].map((r) => (
        <path key={r} d={`M${r} 0 Q${r * 0.75} ${r * 0.75} 0 ${r}`} />
      ))}
    </g>
  </svg>
);

const Room: React.FC = () => (
  <>
    <DustyWall />
    <Cobweb x={0} y={0} size={340} />
    <Cobweb x={740} y={0} size={340} flip />
    <OldPhoto />
    <Dust count={110} seed="reveal-dust" fall={0.25} opacity={0.75} />
  </>
);

const pcx = PHOTO.x + PHOTO.w / 2;
const pcy = PHOTO.y + PHOTO.h / 2;

/* ===================================================== SCENE 6 — THE REVEAL (1:05–1:20) */
const sweep: Shot = {
  name: 'Empty room — torch sweep',
  from: 65,
  to: BEATS.photoFound,
  in: 'dip',
  render: ({ t, d, abs }) => {
    const bx = interpolate(t, [0, d * 0.35, d * 0.72, d], [160, 880, 300, pcx], { easing: Easing.inOut(Easing.sin) });
    const by = interpolate(t, [0, d * 0.35, d * 0.72, d], [1400, 1250, 480, pcy], { easing: Easing.inOut(Easing.sin) });
    const h = handheld(abs, 1);
    return (
      <AbsoluteFill>
        <Camera x={h.x} y={h.y} scale={1.02}>
          <Room />
        </Camera>
        <TorchDarkness x={bx} y={by} r={330} power={flicker(Math.round(abs * 30), 'sw', 0.1)} ambient={0.03} />
      </AbsoluteFill>
    );
  },
};

const photoPush: Shot = {
  name: 'Photo — push in',
  from: BEATS.photoFound,
  to: BEATS.yearHit,
  in: 'flash',
  render: ({ t, d, abs }) => {
    const s = interpolate(t, [0, d], [1.15, 1.9], { easing: Easing.inOut(Easing.quad) });
    const h = handheld(abs, 0.7);
    return (
      <AbsoluteFill>
        <Camera scale={s} x={(540 - pcx) + h.x} y={(960 - pcy) + h.y} origin={`${pcx}px ${pcy}px`}>
          <Room />
        </Camera>
        <TorchDarkness x={540} y={960} r={330 + s * 260} power={flicker(Math.round(abs * 30), 'pp', 0.08)} ambient={0.03} />
      </AbsoluteFill>
    );
  },
};

const yearHit: Shot = {
  name: '"1987" — crash zoom',
  from: BEATS.yearHit,
  to: 76.4,
  in: 'zoom',
  render: ({ t, abs }) => (
    <AbsoluteFill>
      <Camera scale={interpolate(t, [0, 2.4], [4.4, 4.7])} x={540 - YEAR_POS.x} y={960 - YEAR_POS.y} origin={`${YEAR_POS.x}px ${YEAR_POS.y}px`} shake={t < 0.4 ? 8 : 1.5}>
        <Room />
      </Camera>
      <TorchDarkness x={540} y={960} r={900} power={flicker(Math.round(abs * 30), 'yh', 0.08)} ambient={0.05} />
    </AbsoluteFill>
  ),
};

const FriendsUnderTorch: React.FC<{ abs: number; turn?: number; flickerPower?: number; push?: number }> = ({ abs, turn = -0.45, flickerPower = 1, push = 1 }) => {
  const H = 2500;
  const h = handheld(abs, 1.3);
  const lookUp = turn < 0;
  return (
    <Camera x={h.x} y={h.y} scale={push}>
      <AbsoluteFill style={{ filter: 'blur(9px) brightness(0.45)' }}>
        <Room />
      </AbsoluteFill>
      <Character id="rahul" x={310} y={feetFor(760, H)} height={H} expr="terrified" headTurn={turn} gaze={[turn * 1.4, lookUp ? -0.6 : 0]} light={{ dir: 1, hard: 0.35 }} />
      <Character id="karan" x={810} y={feetFor(790, H)} height={H} expr="scared" sweat headTurn={turn} gaze={[turn * 1.4, lookUp ? -0.6 : 0]} light={{ dir: -1, hard: 0.35 }} />
      <LightPool x={540} y={1650} r={1250 * flickerPower + 1} dark={0.72 + (1 - flickerPower) * 0.28} color="255,240,210" warm={0.18 * flickerPower} />
    </Camera>
  );
};

const horror: Shot = {
  name: 'Rahul & Karan — "Yeh… hum hain?" (L9)',
  from: 76.4,
  to: 80,
  in: 'cut',
  render: ({ t, abs }) => <FriendsUnderTorch abs={abs} push={interpolate(t, [0, 3.6], [1.0, 1.07])} />,
};

/* ===================================================== SCENE 7 — THE TWIST (1:20–1:30) */
const turnAround: Shot = {
  name: 'They hear something behind them',
  from: 80,
  to: BEATS.vikramAppears,
  in: 'cut',
  render: ({ abs }) => {
    const turn = interpolate(abs, [BEATS.turnAround + 0.15, BEATS.turnAround + 0.45], [-0.45, 0.65], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return <FriendsUnderTorch abs={abs} turn={turn} push={1.08} />;
  },
};

const Doorway: React.FC<{ abs: number; push: number; power: number }> = ({ abs, push, power }) => {
  const H = 1000;
  return (
    <AbsoluteFill>
      <Camera scale={push} origin="50% 40%">
        <AbsoluteFill style={{ background: 'linear-gradient(180deg,#3a3229 0%,#2c251f 72%,#120e0a 72%,#1c1610 100%)' }} />
        <div style={{ position: 'absolute', left: 290, top: 400, width: 500, height: 990, background: 'radial-gradient(ellipse at 50% 70%, #1f1810, #060504 75%)', borderRadius: '250px 250px 0 0', boxShadow: '0 0 0 36px #1c130b, inset 0 0 140px #000' }} />
        <div style={{ position: 'absolute', left: 150, top: 400, width: 150, height: 990, background: 'linear-gradient(90deg,#140c06,#2c1c0f)', transform: 'skewY(6deg)' }} />
        <Character id="vikram" x={540} y={1395} height={H} expr="sinister" light={{ dir: -1, hard: 1 }} gaze={[0, 0]} lipSync={false} />
      </Camera>
      <TorchDarkness x={500} y={720} r={520} power={power} ambient={0.02} />
    </AbsoluteFill>
  );
};

const vikramReveal: Shot = {
  name: 'Vikram in the doorway',
  from: BEATS.vikramAppears,
  to: 83.5,
  in: 'flash',
  render: ({ t, abs }) => <Doorway abs={abs} push={interpolate(t, [0, 2.3], [1.0, 1.25])} power={flicker(Math.round(abs * 30), 'vr', 0.1)} />,
};

const VikramECU: React.FC<{ abs: number; scale?: number; glitch?: number; power?: number }> = ({ abs, scale = 1, glitch = 0, power = 1 }) => {
  const H = 4300;
  const face = (
    <AbsoluteFill style={{ background: '#020101' }}>
      <Camera scale={scale} origin="50% 38%">
        <Character id="vikram" x={560} y={feetFor(760, H)} height={H} expr="sinister" light={{ dir: -1, hard: 1 }} gaze={[0, 0.05]} />
      </Camera>
      <AbsoluteFill style={{ background: `rgba(0,0,0,${1 - power})` }} />
    </AbsoluteFill>
  );
  return glitch > 0 ? <GlitchLayer amount={glitch} seed={`vk${Math.floor(abs * 10)}`}>{face}</GlitchLayer> : face;
};

const vikramLine: Shot = {
  name: 'Vikram ECU — "Tum log wapas aa gaye." (L10)',
  from: 83.5,
  to: BEATS.torchFlickerStart,
  in: 'cut',
  render: ({ t, abs }) => {
    const g = random(`gl-${Math.floor(abs * 10)}`) > 0.6 ? 0.9 : 0;
    const red = random(`red-${Math.floor(abs * 7)}`) > 0.85;
    return (
      <AbsoluteFill>
        <VikramECU abs={abs} scale={interpolate(t, [0, 3.3], [1.0, 1.12])} glitch={g} />
        {red && <AbsoluteFill style={{ background: 'rgba(160,0,10,0.25)', mixBlendMode: 'multiply' }} />}
      </AbsoluteFill>
    );
  },
};

const flickerOut: Shot = {
  name: 'Torch flickers — black-out',
  from: BEATS.torchFlickerStart,
  to: 90,
  in: 'cut',
  render: ({ t, abs, frame }) => {
    if (abs >= BEATS.blackOut) return <AbsoluteFill style={{ background: 'black' }} />;
    const on = random(`fo-${Math.floor(frame / 2)}`) > 0.45;
    const cut = Math.floor(t / 0.18) % 2 === 0;
    const power = on ? 1 : 0.06;
    return cut ? (
      <FriendsUnderTorch abs={abs} turn={0.65} flickerPower={power} push={1.15} />
    ) : (
      <VikramECU abs={abs} scale={1.15 + t * 0.4} power={power} glitch={0.6} />
    );
  },
};

export const ACT3: Shot[] = [sweep, photoPush, yearHit, horror, turnAround, vikramReveal, vikramLine, flickerOut];
