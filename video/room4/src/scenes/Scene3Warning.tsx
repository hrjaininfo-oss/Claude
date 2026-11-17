import React from 'react';
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from 'remotion';
import { localFrame, sec } from '../timeline';
import { Camera, Dust, Glow, flicker } from '../components/fx';
import { Corridor, Lantern, Person, WoodenDoor } from '../components/props';

const CORRIDOR_SECONDS = 4.4;

/** Shot A — Vikram leads them down the long corridor. */
const CorridorWalk: React.FC = () => {
  const frame = useCurrentFrame();
  const dur = sec(CORRIDOR_SECONDS);
  const push = interpolate(frame, [0, dur], [1, 1.55]);
  const lamp = flicker(frame, 'cw-lamp', 0.35);
  const phase = frame / 5;
  return (
    <>
      <Camera scale={push} origin="540px 935px" y={Math.sin(phase) * 3}>
        <Corridor lightLevel={0.75} />
      </Camera>
      <Glow x={600} y={1120} r={620} intensity={0.6 * lamp} />
      <Person x={560} y={1420} height={430} variant="vikram" walk={phase + 1} rim={0.6 * lamp} />
      <Lantern x={630} y={1170} size={44} seed="cw" />
      <Person x={370} y={1800} height={760} variant="rahul" walk={phase} rim={0.5 * lamp} />
      <Person x={740} y={1860} height={800} variant="karan" walk={phase + Math.PI} rim={0.5 * lamp} />
      <AbsoluteFill style={{ background: 'rgba(0,0,0,0.25)' }} />
    </>
  );
};

/** Shot B — he stops at Room 4 and gives the warning, then walks away. */
const DoorWarning: React.FC = () => {
  const frame = useCurrentFrame();
  const offset = sec(CORRIDOR_SECONDS);
  const dur = sec(12 - CORRIDOR_SECONDS);
  const leave = localFrame('warning', 30.1) - offset;
  const walkAway = interpolate(frame, [leave, leave + 45], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const push = interpolate(frame, [0, dur], [1.0, 1.12]);
  const lamp = flicker(frame, 'dw-lamp', 0.35) * (1 - walkAway * 0.85);
  const vx = 860 + walkAway * 520;
  const turn = interpolate(frame, [localFrame('warning', 24.4) - offset, localFrame('warning', 24.9) - offset], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <>
      <Camera scale={push} origin="50% 52%">
        <AbsoluteFill style={{ background: 'linear-gradient(180deg,#14100c 0%,#231b14 62%,#0d0907 62%,#1a120c 100%)' }} />
        {/* peeling plaster blotches */}
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(ellipse 160px 90px at 150px 420px, rgba(0,0,0,0.35), transparent), radial-gradient(ellipse 120px 200px at 960px 700px, rgba(0,0,0,0.4), transparent)',
          }}
        />
        <WoodenDoor x={300} y={420} width={480} numberOpacity={0.8} />
        <Dust count={30} seed="dw-dust" area={{ x: 200, y: 300, w: 800, h: 1200 }} fall={0.2} opacity={0.4} />
      </Camera>
      <Glow x={vx - 120} y={1080} r={760} intensity={0.75 * lamp} />
      {/* Vikram, close to camera at the right; turns his head slightly toward them */}
      <Person
        x={vx}
        y={1980}
        height={1180}
        variant="vikram"
        lean={-2 * turn}
        rim={0.9 * lamp}
        walk={walkAway > 0 ? frame / 5 : undefined}
        opacity={1 - walkAway * 0.3}
      />
      <Lantern x={vx - 230} y={1150} size={70} seed="dw" on={1 - walkAway * 0.2} />
      {/* Rahul (left foreground) */}
      <Person x={150} y={2100} height={1050} variant="rahul" rim={0.4 * lamp} />
      <AbsoluteFill style={{ background: `rgba(0,0,0,${0.2 + walkAway * 0.55})` }} />
    </>
  );
};

/** 0:20–0:32 — The Warning. */
export const Scene3Warning: React.FC = () => (
  <AbsoluteFill style={{ background: 'black' }}>
    <Sequence durationInFrames={sec(CORRIDOR_SECONDS)} name="Corridor walk">
      <CorridorWalk />
    </Sequence>
    <Sequence from={sec(CORRIDOR_SECONDS)} name="Door 4 warning">
      <DoorWarning />
    </Sequence>
  </AbsoluteFill>
);
