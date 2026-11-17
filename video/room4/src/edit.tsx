import React from 'react';
import { AbsoluteFill, interpolate, random } from 'remotion';
import { FPS } from './timeline';

export type ShotCtx = { t: number; abs: number; d: number; p: number; frame: number };
export type Transition = 'cut' | 'dip' | 'flash' | 'whip' | 'zoom';
export type Shot = { name: string; from: number; to: number; in?: Transition; out?: 'dip' | 'cut'; render: (c: ShotCtx) => React.ReactNode };

/** Renders the active shot with its incoming transition. */
export const ShotPlayer: React.FC<{ shots: Shot[]; abs: number }> = ({ shots, abs }) => {
  const active = shots.find((s) => abs >= s.from && abs < s.to);
  if (!active) return null;
  const t = abs - active.from;
  const d = active.to - active.from;
  const frame = Math.round(t * FPS);
  const ctx: ShotCtx = { t, abs, d, p: t / d, frame };
  const tr = active.in ?? 'cut';
  let style: React.CSSProperties = {};
  let overlay: React.ReactNode = null;
  if (tr === 'dip') {
    const o = interpolate(t, [0, 0.35], [1, 0], { extrapolateRight: 'clamp' });
    overlay = <AbsoluteFill style={{ background: 'black', opacity: o }} />;
  } else if (tr === 'flash') {
    const o = interpolate(t, [0, 0.22], [0.85, 0], { extrapolateRight: 'clamp' });
    overlay = <AbsoluteFill style={{ background: '#fff8ee', opacity: o, mixBlendMode: 'screen' }} />;
  } else if (tr === 'whip') {
    const k = interpolate(t, [0, 0.22], [1, 0], { extrapolateRight: 'clamp' });
    style = { transform: `translateX(${k * k * 700}px)`, filter: k > 0.02 ? `blur(${k * 26}px)` : undefined };
  } else if (tr === 'zoom') {
    const k = interpolate(t, [0, 0.25], [1, 0], { extrapolateRight: 'clamp' });
    style = { transform: `scale(${1 + k * k * 0.35})`, filter: k > 0.02 ? `blur(${k * 14}px)` : undefined };
  }
  const outO = active.out === 'dip' ? interpolate(t, [d - 0.3, d], [0, 1], { extrapolateLeft: 'clamp' }) : 0;
  return (
    <AbsoluteFill style={{ background: 'black' }}>
      <AbsoluteFill style={style}>{active.render(ctx)}</AbsoluteFill>
      {overlay}
      {outO > 0 && <AbsoluteFill style={{ background: 'black', opacity: outO }} />}
    </AbsoluteFill>
  );
};

/** Subtle handheld drift, used on top of every shot. */
export const handheld = (abs: number, amount = 1) => {
  const n = (k: string, f: number) => Math.sin(abs * f + random(k) * 10) + 0.5 * Math.sin(abs * f * 2.3 + random(k + 'b') * 10);
  return { x: n('hx', 0.9) * 4 * amount, y: n('hy', 0.7) * 4 * amount, r: n('hr', 0.5) * 0.25 * amount };
};

export const ease = (x: number) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2);
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const ramp = (t: number, a: number, b: number) => clamp01((t - a) / (b - a));
