import React from 'react';
import { AbsoluteFill, Sequence } from 'remotion';
import './fonts';
import { SCENES, SceneId, sec } from './timeline';
import { Grain, SceneFade, Vignette } from './components/fx';
import { AudioTracks, OnScreenText, Subtitles } from './components/text';
import { Scene1Hook } from './scenes/Scene1Hook';
import { Scene2Arrival } from './scenes/Scene2Arrival';
import { Scene3Warning } from './scenes/Scene3Warning';
import { Scene4Night } from './scenes/Scene4Night';
import { Scene5Door } from './scenes/Scene5Door';
import { Scene6Reveal } from './scenes/Scene6Reveal';
import { Scene7Twist } from './scenes/Scene7Twist';

const SCENE_COMPONENTS: Record<SceneId, React.FC> = {
  hook: Scene1Hook,
  arrival: Scene2Arrival,
  warning: Scene3Warning,
  night: Scene4Night,
  door: Scene5Door,
  reveal: Scene6Reveal,
  twist: Scene7Twist,
};

/** Full 90-second short. Layers: scenes → film grain/vignette → titles → subtitles → audio. */
export const Room4: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: 'black' }}>
    {SCENES.map((s, i) => {
      const Comp = SCENE_COMPONENTS[s.id];
      return (
        <Sequence key={s.id} from={sec(s.start)} durationInFrames={sec(s.end - s.start)} name={s.title}>
          <SceneFade inFrames={i === 0 ? 0 : 8} outFrames={i === SCENES.length - 1 ? 0 : 6}>
            <Comp />
          </SceneFade>
        </Sequence>
      );
    })}
    <Vignette />
    <Grain />
    <OnScreenText />
    <Subtitles />
    <AudioTracks />
  </AbsoluteFill>
);
