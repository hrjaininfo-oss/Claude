import React from 'react';
import { AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame } from 'remotion';
import { BEATS, localFrame, sec } from '../timeline';
import { C } from '../theme';
import { Camera, Dust, TorchDarkness, flicker } from '../components/fx';
import { Corridor, WoodenDoor } from '../components/props';

const WALK_SECONDS = 7;

/** Shot A — POV: phone torch down the black corridor. */
const TorchWalk: React.FC = () => {
  const frame = useCurrentFrame();
  const dur = sec(WALK_SECONDS);
  const push = interpolate(frame, [0, dur], [1, 2.1], { easing: Easing.inOut(Easing.quad) });
  // turn toward door 4 on the right wall near the end
  const turnX = interpolate(frame, [dur * 0.6, dur], [0, -260], { extrapolateLeft: 'clamp' });
  const step = frame / 7;
  const bx = 540 + Math.sin(step * 0.5) * 70 + interpolate(frame, [dur * 0.55, dur], [0, 170], { extrapolateLeft: 'clamp' });
  const by = 1180 + Math.sin(step) * 40;
  const power = flicker(frame, 'torch-walk', 0.12);
  return (
    <>
      <Camera scale={push} x={turnX} y={Math.abs(Math.sin(step)) * 10} origin="540px 935px">
        <AbsoluteFill style={{ filter: 'brightness(2.1) sepia(0.25)' }}>
          <Corridor lightLevel={1} />
        </AbsoluteFill>
      </Camera>
      <TorchDarkness x={bx} y={by} r={430} power={power} ambient={0.06} />
    </>
  );
};

/** Shot B — Door 4. The handle rattles. Karan begs. Rahul pushes it open. */
const DoorPush: React.FC = () => {
  const frame = useCurrentFrame();
  const offset = sec(WALK_SECONDS);
  const lf = (abs: number) => localFrame('door', abs) - offset;
  const shakeStart = lf(BEATS.handleShakeStart);
  const silence = lf(BEATS.doorPushOpen) - 18; // everything goes still before the push
  const shake =
    frame < shakeStart || frame > silence
      ? 0
      : interpolate(frame, [shakeStart, shakeStart + 20, silence - 10, silence], [0.3, 0.7, 1, 1]);
  const open = interpolate(frame, [lf(BEATS.doorPushOpen), lf(BEATS.doorPushOpen) + 50], [0, 0.78], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const arm = interpolate(frame, [lf(BEATS.doorPushOpen) - 14, lf(BEATS.doorPushOpen) + 6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // torch: first the number, then down to the rattling handle, then into the void
  const bx = interpolate(frame, [0, shakeStart + 10, lf(BEATS.doorPushOpen), lf(BEATS.doorPushOpen) + 40], [540, 720, 700, 560], {
    extrapolateRight: 'clamp',
  });
  const by = interpolate(frame, [0, shakeStart + 10, lf(BEATS.doorPushOpen), lf(BEATS.doorPushOpen) + 40], [620, 980, 960, 900], {
    extrapolateRight: 'clamp',
  });
  const tremble = Math.sin(frame * 1.7) * 6 * (0.4 + shake);
  const power = flicker(frame, 'torch-door', 0.12);
  const push = interpolate(frame, [0, sec(17 - WALK_SECONDS)], [1.0, 1.18]);

  return (
    <>
      <Camera scale={push} origin="50% 50%" shake={shake * 3}>
        <AbsoluteFill style={{ background: 'linear-gradient(180deg,#1b1611,#29211a 70%,#0f0b08 70%,#17110c)' }} />
        <WoodenDoor x={240} y={360} width={600} handleShake={shake} open={open} numberOpacity={0.8} />
        <Dust count={40} seed="door-dust" area={{ x: 240, y: 300, w: 600, h: 1300 }} fall={0.3} opacity={0.5} />
      </Camera>
      {/* Rahul's arm reaching in from the bottom-right */}
      <div
        style={{
          position: 'absolute',
          left: interpolate(arm, [0, 1], [1100, 760]),
          top: interpolate(arm, [0, 1], [1950, 1050]),
          width: 130,
          height: 900,
          background: C.silhouette,
          borderRadius: 60,
          transform: 'rotate(-28deg)',
          transformOrigin: '50% 0%',
          opacity: arm > 0 ? 1 : 0,
        }}
      />
      <TorchDarkness x={bx + tremble} y={by + tremble * 0.6} r={340} power={power} ambient={0.05} />
    </>
  );
};

/** 0:48–1:05 — The Door. */
export const Scene5Door: React.FC = () => (
  <AbsoluteFill style={{ background: 'black' }}>
    <Sequence durationInFrames={sec(WALK_SECONDS)} name="Torch walk">
      <TorchWalk />
    </Sequence>
    <Sequence from={sec(WALK_SECONDS)} name="Door push">
      <DoorPush />
    </Sequence>
  </AbsoluteFill>
);
