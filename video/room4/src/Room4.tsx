import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import './fonts';
import { FPS } from './timeline';
import { AbsFrameContext } from './time';
import { ShotPlayer } from './edit';
import { SHOTS } from './shots';
import { Grain, Vignette } from './components/fx';
import { AudioTracks, OnScreenText, Subtitles } from './components/text';

/** Full 90-second short. Layers: edit (shots + transitions) → grade → grain/vignette → titles → subtitles → audio. */
export const Room4: React.FC = () => {
  const frame = useCurrentFrame();
  const abs = frame / FPS;
  return (
    <AbsFrameContext.Provider value={frame}>
      <AbsoluteFill style={{ backgroundColor: 'black' }}>
        <AbsoluteFill style={{ filter: 'contrast(1.08) saturate(0.92)' }}>
          <ShotPlayer shots={SHOTS} abs={abs} />
        </AbsoluteFill>
        <Vignette strength={0.8} />
        <Grain opacity={0.14} />
        <OnScreenText />
        <Subtitles />
        <AudioTracks />
      </AbsoluteFill>
    </AbsFrameContext.Provider>
  );
};
