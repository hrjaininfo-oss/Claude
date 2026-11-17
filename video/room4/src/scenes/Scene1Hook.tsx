import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { BEATS, localFrame } from '../timeline';
import { Camera, Dust, Glow, flicker, joltAt } from '../components/fx';
import { WoodenDoor } from '../components/props';

/** 0:00–0:08 — Close-up of the dusty door with a faded "4". A slow knock from inside. */
export const Scene1Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const knocks = BEATS.hookKnocks.map((s) => localFrame('hook', s));
  const jolt = joltAt(frame, knocks, 9);
  const push = interpolate(frame, [0, durationInFrames], [1.18, 1.38]);
  const drift = interpolate(frame, [0, durationInFrames], [20, -30]);
  const light = flicker(frame, 'hook-lamp', 0.4);
  const fadeIn = interpolate(frame, [0, 24], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: '#050302', opacity: fadeIn }}>
      <Camera scale={push} x={drift} shake={jolt * 6} origin="50% 38%">
        {/* plaster wall around the door */}
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(ellipse at 30% 40%, #2c241c 0%, #15100c 55%, #070504 100%)',
          }}
        />
        <WoodenDoor x={190} y={300} width={700} jolt={jolt} numberOpacity={0.7} />
        {/* dust shaken loose from the lintel on each knock */}
        <AbsoluteFill style={{ opacity: 0.3 + jolt * 0.9 }}>
          <Dust count={70} seed="hook-dust" area={{ x: 180, y: 220, w: 720, h: 1500 }} fall={1.2 + jolt * 3} />
        </AbsoluteFill>
      </Camera>
      {/* lantern off-screen left, flickering */}
      <Glow x={-80} y={760} r={900} intensity={0.5 * light} />
      <AbsoluteFill
        style={{ background: `rgba(0,0,0,${0.35 - light * 0.2 + jolt * 0.15})`, pointerEvents: 'none' }}
      />
    </AbsoluteFill>
  );
};
