/**
 * ROOM NO. 4 — timing.
 * Dialogue, titles, story beats and walk timings live in story.json (shared with audio/build_audio.py).
 * Shot boundaries live in shots/index.ts. Everything is in absolute seconds on the 90 s timeline.
 */
import story from './story.json';

export const FPS = story.fps;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const DURATION_SECONDS = story.duration;
export const BEATS = story.beats;
export const TITLES = story.titles;
export const sec = (s: number) => Math.round(s * FPS);

/** Audio stems produced by audio/build_audio.py (set a src to null to mute that stem). */
export const AUDIO = {
  dialogue: { src: 'audio/dialogue.mp3' as string | null, volume: 1 },
  sfx: { src: 'audio/sfx.mp3' as string | null, volume: 0.8 },
  music: { src: 'audio/music.mp3' as string | null, volume: 0.6 },
};

/** Walk phase (radians) for a walk that started at `from` with `step` seconds per footstep. */
export const walkPhase = (t: number, from: number, step: number) => ((t - from) / step) * Math.PI;
