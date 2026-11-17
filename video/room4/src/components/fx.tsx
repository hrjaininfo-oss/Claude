import React from 'react';
import { AbsoluteFill, interpolate, random, useCurrentFrame, useVideoConfig } from 'remotion';
import { C } from '../theme';

/** Deterministic 0..1 flicker value for lantern / torch light. */
export const flicker = (frame: number, seed: string, amount = 0.25) => {
  const slow = Math.sin(frame / 7 + random(seed) * 10) * 0.5 + 0.5;
  const fast = random(`${seed}-${Math.floor(frame / 2)}`);
  return 1 - amount + amount * (slow * 0.6 + fast * 0.4);
};

/** Decaying jolt after each beat frame — used for knocks and rattles. */
export const joltAt = (frame: number, beats: number[], length = 10) => {
  let v = 0;
  for (const b of beats) {
    const d = frame - b;
    if (d >= 0 && d < length) v = Math.max(v, 1 - d / length);
  }
  return v;
};

/** Camera wrapper: slow push / pan / shake in one place. */
export const Camera: React.FC<{
  children: React.ReactNode;
  scale?: number;
  x?: number;
  y?: number;
  rotate?: number;
  shake?: number; // px amplitude
  origin?: string;
}> = ({ children, scale = 1, x = 0, y = 0, rotate = 0, shake = 0, origin = '50% 50%' }) => {
  const frame = useCurrentFrame();
  const sx = shake ? (random(`sx${frame}`) - 0.5) * 2 * shake : 0;
  const sy = shake ? (random(`sy${frame}`) - 0.5) * 2 * shake : 0;
  return (
    <AbsoluteFill
      style={{
        transform: `translate(${x + sx}px, ${y + sy}px) scale(${scale}) rotate(${rotate}deg)`,
        transformOrigin: origin,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

/** Animated film grain. */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.16 }) => {
  const frame = useCurrentFrame();
  const seed = frame % 12;
  return (
    <AbsoluteFill style={{ opacity, mixBlendMode: 'overlay', pointerEvents: 'none' }}>
      <svg width="100%" height="100%">
        <filter id={`grain${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={seed} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.85 }) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(ellipse 75% 60% at 50% 48%, rgba(0,0,0,0) 40%, rgba(0,0,0,${strength}) 100%)`,
      pointerEvents: 'none',
    }}
  />
);

/** Dip-to-black at the start and end of a scene. */
export const SceneFade: React.FC<{ children: React.ReactNode; inFrames?: number; outFrames?: number }> = ({
  children,
  inFrames = 10,
  outFrames = 8,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const opacity = Math.min(
    inFrames ? interpolate(frame, [0, inFrames], [0, 1], { extrapolateRight: 'clamp' }) : 1,
    outFrames
      ? interpolate(frame, [durationInFrames - outFrames, durationInFrames], [1, 0], { extrapolateLeft: 'clamp' })
      : 1,
  );
  return (
    <AbsoluteFill style={{ backgroundColor: 'black' }}>
      <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Warm light pool (lantern) — additive glow. */
export const Glow: React.FC<{
  x: number;
  y: number;
  r: number;
  color?: string;
  intensity?: number;
}> = ({ x, y, r, color = C.lantern, intensity = 1 }) => (
  <div
    style={{
      position: 'absolute',
      left: x - r,
      top: y - r,
      width: r * 2,
      height: r * 2,
      borderRadius: '50%',
      background: `radial-gradient(circle, ${color} 0%, ${color}66 22%, ${color}22 50%, transparent 72%)`,
      opacity: intensity,
      mixBlendMode: 'screen',
      pointerEvents: 'none',
    }}
  />
);

/** Darkness everywhere except a torch beam circle. */
export const TorchDarkness: React.FC<{
  x: number;
  y: number;
  r: number;
  power?: number; // 0 = torch off (full dark), 1 = full beam
  ambient?: number; // how much of the scene is visible outside the beam
}> = ({ x, y, r, power = 1, ambient = 0.04 }) => {
  const dark = 1 - ambient;
  const inner = r * 0.35 * power;
  const outer = Math.max(r * power, 1);
  return (
    <>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${x}px ${y}px, rgba(0,0,0,${1 - power}) 0px, rgba(0,0,0,${
            (1 - power) * 0.9
          }) ${inner}px, rgba(0,0,0,${dark}) ${outer}px, rgba(0,0,0,${Math.min(1, dark + 0.02)}) ${outer * 1.6}px)`,
          pointerEvents: 'none',
        }}
      />
      {/* warm hotspot of the beam */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${x}px ${y}px, rgba(255,240,205,${0.22 * power}) 0px, rgba(255,230,190,${
            0.08 * power
          }) ${inner}px, transparent ${outer}px)`,
          mixBlendMode: 'screen',
          pointerEvents: 'none',
        }}
      />
    </>
  );
};

/** Floating dust motes (optionally only visible inside a light pool). */
export const Dust: React.FC<{
  count?: number;
  seed?: string;
  color?: string;
  area?: { x: number; y: number; w: number; h: number };
  fall?: number;
  opacity?: number;
}> = ({ count = 60, seed = 'dust', color = '#f3e2c0', area = { x: 0, y: 0, w: 1080, h: 1920 }, fall = 0.4, opacity = 0.6 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {new Array(count).fill(0).map((_, i) => {
        const r = (k: string) => random(`${seed}-${i}-${k}`);
        const size = 2 + r('s') * 5;
        const x = area.x + ((r('x') * area.w + Math.sin(frame / (30 + r('w') * 40) + r('p') * 6) * 25) % area.w);
        const y = area.y + ((r('y') * area.h + frame * fall * (0.3 + r('v'))) % area.h);
        const tw = 0.4 + 0.6 * Math.abs(Math.sin(frame / (12 + r('t') * 20) + i));
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: '50%',
              background: color,
              opacity: opacity * tw * (0.3 + r('o') * 0.7),
              filter: size > 5 ? 'blur(1.5px)' : undefined,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** RGB-split / slice glitch over arbitrary content. */
export const GlitchLayer: React.FC<{ children: React.ReactNode; amount: number; seed?: string }> = ({
  children,
  amount,
  seed = 'g',
}) => {
  const frame = useCurrentFrame();
  if (amount <= 0) return <>{children}</>;
  const burst = random(`${seed}-burst-${Math.floor(frame / 3)}`) > 0.45 ? 1 : 0.25;
  const a = amount * burst;
  const off = (k: string) => (random(`${seed}-${k}-${frame}`) - 0.5) * 2 * 22 * a;
  const slices = new Array(5).fill(0).map((_, i) => {
    const top = random(`${seed}-st-${i}-${Math.floor(frame / 2)}`) * 100;
    const h = 2 + random(`${seed}-sh-${i}-${Math.floor(frame / 2)}`) * 9;
    return { top, h, dx: off(`sl${i}`) * 2.2 };
  });
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ transform: `translateX(${off('r')}px)`, mixBlendMode: 'screen', filter: 'url(#onlyRed)' }}>
        {children}
      </AbsoluteFill>
      <AbsoluteFill style={{ transform: `translateX(${off('c')}px)`, mixBlendMode: 'screen', filter: 'url(#onlyCyan)' }}>
        {children}
      </AbsoluteFill>
      {slices.map((s, i) => (
        <AbsoluteFill
          key={i}
          style={{
            clipPath: `inset(${s.top}% 0 ${Math.max(0, 100 - s.top - s.h)}% 0)`,
            transform: `translateX(${s.dx}px)`,
          }}
        >
          {children}
        </AbsoluteFill>
      ))}
      <svg width="0" height="0" style={{ position: 'absolute' }}>
        <filter id="onlyRed">
          <feColorMatrix type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" />
        </filter>
        <filter id="onlyCyan">
          <feColorMatrix type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" />
        </filter>
      </svg>
    </AbsoluteFill>
  );
};

/** Night sky with faint stars and a hazy moon. */
export const NightSky: React.FC<{ moonX?: number; moonY?: number }> = ({ moonX = 800, moonY = 330 }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, #02040a 0%, ${C.nightBlue} 55%, #142033 100%)` }}>
      {new Array(70).fill(0).map((_, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: random(`star-x-${i}`) * 1080,
            top: random(`star-y-${i}`) * 900,
            width: 2 + random(`star-s-${i}`) * 2,
            height: 2 + random(`star-s-${i}`) * 2,
            borderRadius: '50%',
            background: '#dfe8ff',
            opacity: 0.2 + 0.5 * Math.abs(Math.sin(frame / (20 + i) + i)),
          }}
        />
      ))}
      <div
        style={{
          position: 'absolute',
          left: moonX - 70,
          top: moonY - 70,
          width: 140,
          height: 140,
          borderRadius: '50%',
          background: 'radial-gradient(circle at 40% 40%, #f2f4ea, #b9c2c9 70%)',
          boxShadow: '0 0 120px 40px rgba(170,190,220,0.25)',
          opacity: 0.85,
        }}
      />
      {/* drifting cloud band over the moon */}
      <div
        style={{
          position: 'absolute',
          left: -400 + frame * 0.6,
          top: moonY - 40,
          width: 900,
          height: 90,
          borderRadius: 90,
          background: 'rgba(8,12,20,0.75)',
          filter: 'blur(18px)',
        }}
      />
    </AbsoluteFill>
  );
};
