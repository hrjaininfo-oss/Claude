import React from 'react';
import { AbsoluteFill, Easing, interpolate, random, useCurrentFrame } from 'remotion';
import { BEATS, localFrame } from '../timeline';
import { C } from '../theme';
import { Camera, GlitchLayer, TorchDarkness, flicker } from '../components/fx';
import { Person } from '../components/props';

/** Vikram's face half lit by the torch, half in shadow. Faint smile on the lit side. */
const HalfLitFace: React.FC<{ x: number; y: number; size: number; reveal: number; smile: number }> = ({ x, y, size, reveal, smile }) => (
  <svg width={size} height={size * 1.25} viewBox="0 0 200 250" style={{ position: 'absolute', left: x - size / 2, top: y - size * 0.6, overflow: 'visible' }}>
    <defs>
      <linearGradient id="halfLit" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stopColor="#b98b62" stopOpacity={0.85 * reveal} />
        <stop offset="0.46" stopColor="#7a5436" stopOpacity={0.6 * reveal} />
        <stop offset="0.52" stopColor="#000" stopOpacity={1} />
        <stop offset="1" stopColor="#000" stopOpacity={1} />
      </linearGradient>
    </defs>
    <ellipse cx={100} cy={120} rx={78} ry={100} fill={C.silhouette} />
    <ellipse cx={100} cy={120} rx={78} ry={100} fill="url(#halfLit)" />
    {/* shawl over head */}
    <path d="M14 120 Q20 0 100 4 Q180 0 186 120 L196 250 L160 250 Q170 120 100 40 Q30 120 40 250 L4 250 Z" fill="#050403" />
    {/* lit eye with a cold glint; the shadow eye is just a faint glint */}
    <ellipse cx={68} cy={108} rx={13} ry={6} fill="#120a05" opacity={reveal} />
    <circle cx={70} cy={107} r={3} fill="#fff" opacity={0.9 * reveal} />
    <circle cx={132} cy={107} r={2.2} fill="#cfd8ff" opacity={0.55 * reveal} />
    {/* thin smile on the lit side */}
    <path d={`M58 168 Q80 ${170 + 14 * smile} ${102} ${166 - 2 * smile}`} stroke="#2a150a" strokeWidth={3.5} fill="none" opacity={reveal} strokeLinecap="round" />
  </svg>
);

/** 1:20–1:30 — The Twist. Vikram in the doorway. Torch flickers. Black. */
export const Scene7Twist: React.FC = () => {
  const frame = useCurrentFrame();
  const appear = localFrame('twist', BEATS.vikramAppears);
  const lineStart = localFrame('twist', 83.4);
  const lineEnd = localFrame('twist', 86.6);
  const flickerStart = localFrame('twist', BEATS.torchFlickerStart);
  const blackOut = localFrame('twist', BEATS.blackOut);

  // the friends spin round; the torch swings from the photo to the doorway
  const swing = interpolate(frame, [0, appear], [0, 1], { extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
  const reveal = interpolate(frame, [appear, appear + 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const push = interpolate(frame, [appear, blackOut], [1.0, 1.45], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const smile = interpolate(frame, [lineStart - 10, lineStart + 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // torch flicker → dead
  let power = flicker(frame, 'torch-twist', 0.1);
  if (frame >= flickerStart && frame < blackOut) power *= random(`dead-${frame}`) > 0.5 ? 1 : 0.05;
  if (frame >= blackOut) power = 0;

  const glitch = frame >= lineStart && frame <= lineEnd ? (random(`tw-g-${Math.floor(frame / 3)}`) > 0.55 ? 0.9 : 0) : 0;
  const bx = interpolate(swing, [0, 1], [1400, 540]);

  const scene = (
    <Camera scale={push} origin="50% 42%">
      {/* inside the room, looking back at the doorway */}
      <AbsoluteFill style={{ background: 'linear-gradient(180deg,#2c261f 0%,#221d18 72%,#0f0c09 72%,#17120d 100%)' }} />
      {/* doorway: dim corridor beyond */}
      <div
        style={{
          position: 'absolute',
          left: 300,
          top: 420,
          width: 480,
          height: 960,
          background: 'radial-gradient(ellipse at 50% 70%, #1a140e, #060504 75%)',
          borderRadius: '240px 240px 0 0',
          boxShadow: '0 0 0 34px #160f09, inset 0 0 120px #000',
        }}
      />
      {/* the open door slab, swung inward on the left */}
      <div
        style={{
          position: 'absolute',
          left: 160,
          top: 420,
          width: 150,
          height: 960,
          background: 'linear-gradient(90deg,#120b06,#2a1a0e)',
          transform: 'skewY(6deg)',
        }}
      />
      {/* Vikram standing in the doorway */}
      <AbsoluteFill style={{ opacity: reveal }}>
        <Person x={540} y={1395} height={900} variant="vikram" rim={0.5 * reveal} rimColor="#d9c3a0" />
        <HalfLitFace x={540} y={600} size={140} reveal={reveal} smile={smile} />
      </AbsoluteFill>
    </Camera>
  );

  return (
    <AbsoluteFill style={{ background: 'black' }}>
      <GlitchLayer amount={glitch} seed="twist">
        {scene}
      </GlitchLayer>
      <TorchDarkness x={bx} y={760} r={460} power={power} ambient={0.02} />
      {/* Rahul & Karan, backs to us, foreground (outside the beam) */}
      <AbsoluteFill style={{ opacity: frame >= blackOut ? 0 : 1 }}>
        <Person x={170} y={2250} height={1200} variant="rahul" rim={0.25 * power} rimColor="#fff1d6" />
        <Person x={930} y={2280} height={1230} variant="karan" rim={0.25 * power} rimColor="#fff1d6" />
      </AbsoluteFill>
      {frame >= blackOut && <AbsoluteFill style={{ background: 'black' }} />}
    </AbsoluteFill>
  );
};
