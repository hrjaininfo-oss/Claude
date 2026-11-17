import React from 'react';
import { Composition } from 'remotion';
import { Room4 } from './Room4';
import { DURATION_SECONDS, FPS, HEIGHT, WIDTH, sec } from './timeline';
import { RigTest, FaceTest } from './RigTest';
import './fonts';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Room4" component={Room4} durationInFrames={sec(DURATION_SECONDS)} fps={FPS} width={WIDTH} height={HEIGHT} />
    {/* Character rig previews */}
    <Composition id="RigTest" component={RigTest} durationInFrames={60} fps={30} width={1080} height={1920} />
    <Composition id="FaceTest" component={FaceTest} durationInFrames={60} fps={30} width={1080} height={1920} />
  </>
);
