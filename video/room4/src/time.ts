import { createContext, useContext } from 'react';
import { useCurrentFrame } from 'remotion';
import story from './story.json';
import lipsync from './generated/lipsync.json';

export const FPS = story.fps;
/** Absolute frame on the full 90 s timeline (shots are rendered without nested Sequences). */
export const AbsFrameContext = createContext<number | null>(null);
export const useAbsFrame = () => {
  const ctx = useContext(AbsFrameContext);
  const f = useCurrentFrame();
  return ctx ?? f;
};
export const useAbsTime = () => useAbsFrame() / FPS;

type Lip = { id: string; speaker: string; start: number; end: number; env: number[] };
const LIPS = lipsync.lines as Lip[];

/** Mouth opening (0..1) for a speaker at an absolute frame, from the real voice track. */
export const mouthAt = (speaker: string, absFrame: number) => {
  const t = absFrame / FPS;
  for (const l of LIPS) {
    if (l.speaker !== speaker || t < l.start || t > l.end) continue;
    const i = Math.floor((t - l.start) * FPS);
    const v = l.env[Math.min(l.env.length - 1, i)] ?? 0;
    const v2 = l.env[Math.min(l.env.length - 1, i + 1)] ?? v;
    const frac = (t - l.start) * FPS - i;
    return v + (v2 - v) * frac;
  }
  return 0;
};

export const isSpeaking = (speaker: string, absFrame: number) => {
  const t = absFrame / FPS;
  return LIPS.some((l) => l.speaker === speaker && t >= l.start && t <= l.end);
};

export const LINES = LIPS;
