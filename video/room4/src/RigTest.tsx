import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Character, HeldLantern, HeldPhone } from './rig/Character';

export const RigTest: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: '#3a4250' }}>
      <Character id="rahul" x={180} y={900} height={760} expr="curious" mouth={0.5} />
      <Character id="karan" x={540} y={900} height={760} expr="scared" headTurn={-0.4} sweat />
      <Character id="vikram" x={900} y={900} height={760} expr="warm" armR={[20, 70]} holdR={<HeldLantern />} mouth={0.3} />
      <Character id="vikram" x={180} y={1850} height={760} view="side" walk={f / 5 + 1} holdR={<HeldLantern />} armR={[25, 60]} />
      <Character id="rahul" x={540} y={1850} height={760} view="side" walk={f / 5 + 2} armR={[70, 20]} holdR={<HeldPhone />} expr="worried" />
      <Character id="karan" x={900} y={1850} height={760} view="back" walk={f / 5} />
    </AbsoluteFill>
  );
};
export const FaceTest: React.FC = () => (
  <AbsoluteFill style={{ background: '#20242c' }}>
    <Character id="vikram" x={300} y={2900} height={2900} expr="sinister" light={{ dir: -1, hard: 0.9 }} />
    <Character id="karan" x={820} y={2900} height={2900} expr="terrified" sweat />
  </AbsoluteFill>
);
