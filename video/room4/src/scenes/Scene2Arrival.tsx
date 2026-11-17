import React from 'react';
import { AbsoluteFill, Sequence, interpolate, random, useCurrentFrame } from 'remotion';
import { localFrame, sec } from '../timeline';
import { Camera, Glow, NightSky, flicker } from '../components/fx';
import { DeadTree, Haveli } from '../components/haveli';
import { Lantern, Person } from '../components/props';

const ROAD_SECONDS = 4.5;

/** Shot A — headlights on a dirt road (POV from behind the car). */
const RoadShot: React.FC = () => {
  const frame = useCurrentFrame();
  const bob = Math.sin(frame / 4) * 4 + (random(`bump-${Math.floor(frame / 9)}`) - 0.5) * 6;
  const beam = 0.85 + flicker(frame, 'beam', 0.15) * 0.15;
  return (
    <Camera y={bob} scale={1.04}>
      <NightSky moonX={260} moonY={360} />
      {/* fields */}
      <AbsoluteFill style={{ top: 820, background: 'linear-gradient(180deg,#05070a,#0b0a08)' }} />
      {/* road */}
      <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="road" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stopColor="#3a2d20" />
            <stop offset="1" stopColor="#0d0a07" />
          </linearGradient>
          <linearGradient id="beamG" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stopColor="#fff6dc" stopOpacity={0.3} />
            <stop offset="0.7" stopColor="#ffeab8" stopOpacity={0.06} />
            <stop offset="1" stopColor="#ffeab8" stopOpacity={0} />
          </linearGradient>
        </defs>
        <polygon points="40,1920 1040,1920 590,820 490,820" fill="url(#road)" />
        {/* tyre ruts / stones streaming toward camera */}
        {new Array(40).fill(0).map((_, i) => {
          const t = ((random(`st-${i}`) + frame * 0.012) % 1) ** 2.2;
          const side = random(`ss-${i}`) - 0.5;
          const y = 820 + (1920 - 820) * t;
          const half = 50 + (500 - 50) * t;
          const x = 540 + side * half * 1.8;
          return <ellipse key={i} cx={x} cy={y} rx={2 + 10 * t} ry={1 + 4 * t} fill="#000" opacity={0.55} />;
        })}
        <polygon points="40,1920 560,1920 540,880 470,880" fill="url(#beamG)" opacity={beam} style={{ filter: 'blur(28px)' }} />
        <polygon points="520,1920 1040,1920 610,880 540,880" fill="url(#beamG)" opacity={beam} style={{ filter: 'blur(28px)' }} />
      </svg>
      {/* passing trees */}
      {[0, 1, 2].map((i) => {
        const t = (frame / 70 + i / 3) % 1;
        const h = 200 + t * t * 1900;
        const x = 520 - t * t * 1200;
        return <DeadTree key={`l${i}`} x={x - h * 0.35} y={820 + t * t * 900} h={h} />;
      })}
      {[0, 1, 2].map((i) => {
        const t = (frame / 70 + i / 3 + 0.17) % 1;
        const h = 200 + t * t * 1900;
        const x = 560 + t * t * 1200;
        return <DeadTree key={`r${i}`} x={x - h * 0.35} y={820 + t * t * 900} h={h} flip />;
      })}
      <Glow x={540} y={1100} r={500} color="#fff1cc" intensity={0.18} />
    </Camera>
  );
};

/** Shot B — the haveli with a single lantern; Vikram waiting at the gate. */
const HaveliShot: React.FC = () => {
  const frame = useCurrentFrame();
  const dur = sec(12 - ROAD_SECONDS);
  const scale = interpolate(frame, [0, dur], [1.0, 1.28]);
  const panX = interpolate(frame, [0, dur], [70, 0]);
  const headlights = interpolate(frame, [0, 40, 80], [0.55, 0.35, 0], { extrapolateRight: 'clamp' });
  const offset = sec(ROAD_SECONDS);
  const vikramIn = interpolate(frame, [localFrame('arrival', 12.4) - offset, localFrame('arrival', 13.4) - offset], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const friendsIn = interpolate(frame, [localFrame('arrival', 16.2) - offset, localFrame('arrival', 16.8) - offset], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const whisperLean = interpolate(frame, [localFrame('arrival', 16.6) - offset, localFrame('arrival', 17.2) - offset], [0, -7], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const lamp = flicker(frame, 'gate-lamp', 0.35);

  return (
    <>
      <Camera scale={scale} x={panX} origin="50% 78%">
        <NightSky moonX={860} moonY={420} />
        <Haveli x={-260} y={700} />
        {/* dirt courtyard */}
        <AbsoluteFill style={{ top: 1700, background: 'linear-gradient(180deg,#120d09,#1d150e)' }} />
        {/* the one burning lantern by the gate */}
        <Lantern x={460} y={1330} size={60} seed="gate" />
        <Glow x={470} y={1450} r={420} intensity={0.55 * lamp} />
        <Person x={610} y={1702} height={330} variant="vikram" rim={0.9 * lamp} opacity={vikramIn} />
        {/* car headlights fading as the engine stops */}
        <Glow x={540} y={1950} r={900} color="#fff4d8" intensity={headlights} />
      </Camera>
      {/* Rahul & Karan from behind, foreground */}
      <AbsoluteFill style={{ opacity: friendsIn }}>
        <Person x={330} y={2200} height={1100} variant="rahul" rim={0.4} />
        <Person x={760} y={2220} height={1120} variant="karan" lean={whisperLean} rim={0.4} />
      </AbsoluteFill>
    </>
  );
};

/** 0:08–0:20 — Arrival. */
export const Scene2Arrival: React.FC = () => (
  <AbsoluteFill style={{ background: 'black' }}>
    <Sequence durationInFrames={sec(ROAD_SECONDS)} name="Road">
      <RoadShot />
    </Sequence>
    <Sequence from={sec(ROAD_SECONDS)} name="Haveli">
      <HaveliShot />
    </Sequence>
  </AbsoluteFill>
);
