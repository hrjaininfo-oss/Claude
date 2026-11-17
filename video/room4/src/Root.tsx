import React from 'react';
import { Composition } from 'remotion';
import { Room4 } from './Room4';
import { DURATION_SECONDS, FPS, HEIGHT, SCENES, WIDTH, sec } from './timeline';
import { Scene1Hook } from './scenes/Scene1Hook';
import { Scene2Arrival } from './scenes/Scene2Arrival';
import { Scene3Warning } from './scenes/Scene3Warning';
import { Scene4Night } from './scenes/Scene4Night';
import { Scene5Door } from './scenes/Scene5Door';
import { Scene6Reveal } from './scenes/Scene6Reveal';
import { Scene7Twist } from './scenes/Scene7Twist';
import './fonts';

const scenes = [Scene1Hook, Scene2Arrival, Scene3Warning, Scene4Night, Scene5Door, Scene6Reveal, Scene7Twist];

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Room4" component={Room4} durationInFrames={sec(DURATION_SECONDS)} fps={FPS} width={WIDTH} height={HEIGHT} />
    {/* Each scene on its own for quick previewing in Remotion Studio (no subtitles). */}
    {SCENES.map((s, i) => (
      <Composition
        key={s.id}
        id={`Scene${i + 1}-${s.id}`}
        component={scenes[i]}
        durationInFrames={sec(s.end - s.start)}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
    ))}
  </>
);
