/**
 * ROOM NO. 4 — single source of truth for timing.
 *
 * Every scene boundary, subtitle and on-screen text is defined here in SECONDS.
 * Change a number here and the scene, its subtitles and the total length all follow.
 */

export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

export type SceneId = 'hook' | 'arrival' | 'warning' | 'night' | 'door' | 'reveal' | 'twist';

export const SCENES: { id: SceneId; title: string; start: number; end: number }[] = [
  { id: 'hook', title: 'Scene 1 — Hook', start: 0, end: 8 },
  { id: 'arrival', title: 'Scene 2 — Arrival', start: 8, end: 20 },
  { id: 'warning', title: 'Scene 3 — The Warning', start: 20, end: 32 },
  { id: 'night', title: 'Scene 4 — The Night', start: 32, end: 48 },
  { id: 'door', title: 'Scene 5 — The Door', start: 48, end: 65 },
  { id: 'reveal', title: 'Scene 6 — The Reveal', start: 65, end: 80 },
  { id: 'twist', title: 'Scene 7 — The Twist', start: 80, end: 90 },
];

export const DURATION_SECONDS = SCENES[SCENES.length - 1].end;

export type SubtitleStyle = 'dialogue' | 'whisper' | 'sfx' | 'glitch';

export type Subtitle = {
  start: number; // absolute seconds
  end: number;
  speaker?: string;
  text: string;
  style?: SubtitleStyle;
};

/** Burned-in Hinglish subtitles (absolute time on the 90 s timeline). */
export const SUBTITLES: Subtitle[] = [
  // Scene 2 — Arrival
  { start: 13.6, end: 16.4, speaker: 'Vikram', text: 'Aa gaye tum dono? Bahut saal ho gaye.' },
  { start: 16.7, end: 19.8, speaker: 'Karan', text: 'Bahut saal? We met him last month…', style: 'whisper' },

  // Scene 3 — The Warning
  { start: 24.6, end: 28.0, speaker: 'Vikram', text: 'Ghar mein kahin bhi jao. Bas yeh kamra… kabhi mat kholna.' },
  { start: 28.2, end: 29.9, speaker: 'Rahul', text: "Kyun? What's inside?" },
  { start: 30.1, end: 31.9, speaker: 'Vikram', text: 'Khana lag gaya hai.' },

  // Scene 4 — The Night
  { start: 36.0, end: 39.6, text: '[ knock… knock… knock ]', style: 'sfx' },
  { start: 40.2, end: 43.6, text: 'Rahul… Karan…', style: 'whisper' },
  { start: 44.6, end: 47.8, speaker: 'Karan', text: 'Tune suna?' },

  // Scene 5 — The Door
  { start: 56.5, end: 58.8, text: '[ door handle rattles ]', style: 'sfx' },
  { start: 59.0, end: 61.4, speaker: 'Karan', text: 'Mat khol, Rahul!' },
  { start: 62.6, end: 64.8, text: '[ creeeak ]', style: 'sfx' },

  // Scene 6 — The Reveal
  { start: 76.2, end: 79.8, speaker: 'Rahul', text: 'Yeh… hum hain?' },

  // Scene 7 — The Twist (glitch effect)
  { start: 83.4, end: 86.6, speaker: 'Vikram', text: 'Tum log wapas aa gaye.', style: 'glitch' },
];

/** Big on-screen title text (not subtitles). */
export const ON_SCREEN_TEXT = [
  { start: 3.2, end: 8.0, text: 'Never open room number 4.' },
  { start: 88.0, end: 90.0, text: 'Part 2?' },
];

/** Key story beats used by scene components (absolute seconds). */
export const BEATS = {
  hookKnocks: [1.4, 2.1, 2.8], // knocks from inside the door
  nightKnocks: [36.2, 37.4, 38.6],
  karanSitsUp: 44.2,
  handleShakeStart: 56.0,
  doorPushOpen: 62.4,
  photoFound: 70.5,
  photoCloseUp1987: 74.0,
  vikramAppears: 81.0,
  torchFlickerStart: 87.0,
  blackOut: 87.9,
};

/**
 * Audio tracks — intentionally EMPTY.
 * Drop files into /public/audio and set the file names here, e.g.
 *   music: 'audio/bg-music.mp3', voiceover: 'audio/voiceover.wav'
 * Optional `startAt` is in seconds on the 90 s timeline.
 */
export const AUDIO: {
  music: { src: string | null; volume: number };
  voiceover: { src: string | null; volume: number };
  sfx: { src: string; startAt: number; volume?: number }[];
} = {
  music: { src: null, volume: 0.6 },
  voiceover: { src: null, volume: 1 },
  sfx: [],
};

export const sec = (s: number) => Math.round(s * FPS);
export const sceneById = (id: SceneId) => SCENES.find((s) => s.id === id)!;
/** Convert an absolute-seconds beat into a frame local to its scene. */
export const localFrame = (id: SceneId, absSeconds: number) => sec(absSeconds - sceneById(id).start);
