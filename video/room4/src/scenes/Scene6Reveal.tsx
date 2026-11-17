import React from 'react';
import { AbsoluteFill, Easing, interpolate, random, useCurrentFrame } from 'remotion';
import { BEATS, localFrame } from '../timeline';
import { FONT_HAND } from '../fonts';
import { Camera, Dust, TorchDarkness, flicker } from '../components/fx';

// Photo frame placement on the wall (screen space, before zoom)
const PHOTO = { x: 250, y: 640, w: 580, h: 470 };
const YEAR = { x: PHOTO.x + PHOTO.w - 120, y: PHOTO.y + PHOTO.h - 40 }; // where "1987" sits

/** Sepia figure: head and shoulders in an old studio photograph. */
const SepiaMan: React.FC<{ cx: number; base: number; h: number; tone: string; hair?: number }> = ({ cx, base, h, tone, hair = 0 }) => (
  <g>
    <path
      d={`M${cx - h * 0.42} ${base} Q${cx - h * 0.4} ${base - h * 0.55} ${cx} ${base - h * 0.6} Q${cx + h * 0.4} ${base - h * 0.55} ${cx + h * 0.42} ${base} Z`}
      fill={tone}
    />
    <rect x={cx - h * 0.07} y={base - h * 0.72} width={h * 0.14} height={h * 0.16} fill={tone} />
    <ellipse cx={cx} cy={base - h * 0.84} rx={h * 0.15} ry={h * 0.18} fill={tone} />
    <path
      d={`M${cx - h * 0.16} ${base - h * 0.86} Q${cx - h * (0.1 - hair * 0.05)} ${base - h * 1.06} ${cx + h * 0.16} ${base - h * 0.88} Q${cx + h * 0.05} ${base - h * 0.98} ${cx - h * 0.16} ${base - h * 0.86} Z`}
      fill="#2a1a0c"
      opacity={0.85}
    />
  </g>
);

const OldPhoto: React.FC = () => {
  const { x, y, w, h } = PHOTO;
  const ix = 26;
  const iy = 26;
  const iw = w - 52;
  const ih = h - 110;
  return (
    <div style={{ position: 'absolute', left: x - 30, top: y - 30, width: w + 60, height: h + 60 }}>
      {/* carved wooden frame */}
      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(135deg,#3a2615,#160d06 60%,#2a1a0d)', boxShadow: '0 20px 40px rgba(0,0,0,0.9)' }} />
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ position: 'absolute', left: 30, top: 30 }}>
        <defs>
          <radialGradient id="sepiaBg" cx="50%" cy="45%" r="70%">
            <stop offset="0" stopColor="#c9a874" />
            <stop offset="0.7" stopColor="#8a6a40" />
            <stop offset="1" stopColor="#3c2a16" />
          </radialGradient>
        </defs>
        {/* aged paper border */}
        <rect width={w} height={h} fill="#d8c7a3" />
        <rect width={w} height={h} fill="#6b4a22" opacity={0.25} />
        {/* the print */}
        <rect x={ix} y={iy} width={iw} height={ih} fill="url(#sepiaBg)" />
        {/* haveli arch behind them */}
        <path
          d={`M${ix + iw * 0.2} ${iy + ih} L${ix + iw * 0.2} ${iy + ih * 0.35} Q${ix + iw * 0.5} ${iy - ih * 0.05} ${ix + iw * 0.8} ${iy + ih * 0.35} L${ix + iw * 0.8} ${iy + ih} Z`}
          fill="#5a3f22"
          opacity={0.55}
        />
        {/* Rahul, Vikram (centre, taller), Karan */}
        <SepiaMan cx={ix + iw * 0.24} base={iy + ih} h={ih * 0.78} tone="#3b2814" />
        <SepiaMan cx={ix + iw * 0.5} base={iy + ih} h={ih * 0.88} tone="#2e1f0f" hair={1} />
        <SepiaMan cx={ix + iw * 0.76} base={iy + ih} h={ih * 0.8} tone="#3b2814" />
        {/* scratches, stains, cracks */}
        {new Array(18).fill(0).map((_, i) => (
          <line
            key={i}
            x1={random(`sc-x-${i}`) * w}
            y1={random(`sc-y-${i}`) * h}
            x2={random(`sc-x-${i}`) * w + (random(`sc-d-${i}`) - 0.5) * 60}
            y2={random(`sc-y-${i}`) * h + 40 + random(`sc-l-${i}`) * 120}
            stroke="#f1e2c0"
            strokeOpacity={0.35}
            strokeWidth={1 + random(`sc-w-${i}`)}
          />
        ))}
        <circle cx={w * 0.15} cy={h * 0.2} r={50} fill="#4a2e10" opacity={0.25} />
        <path d={`M${w * 0.9} 0 L${w * 0.82} ${h * 0.3} L${w * 0.86} ${h * 0.55}`} stroke="#1a1006" strokeWidth={2} fill="none" opacity={0.5} />
        <rect width={w} height={h} fill="none" stroke="#000" strokeOpacity={0.4} strokeWidth={6} />
      </svg>
      {/* handwritten year on the bottom border */}
      <div
        style={{
          position: 'absolute',
          left: YEAR.x - x + 30 - 70,
          top: YEAR.y - y + 30 - 46,
          fontFamily: FONT_HAND,
          fontWeight: 700,
          fontSize: 64,
          color: '#2b1a0c',
          transform: 'rotate(-6deg)',
          opacity: 0.9,
        }}
      >
        1987
      </div>
    </div>
  );
};

/** Cobweb in a corner. */
const Cobweb: React.FC<{ x: number; y: number; size: number; flip?: boolean }> = ({ x, y, size, flip }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 100 100"
    style={{ position: 'absolute', left: x, top: y, transform: flip ? 'scaleX(-1)' : undefined, opacity: 0.35 }}
  >
    <g stroke="#cfc8b8" strokeWidth={0.5} fill="none">
      {[0, 15, 30, 45, 60, 75, 90].map((a) => (
        <line key={a} x1={0} y1={0} x2={100 * Math.cos((a * Math.PI) / 180)} y2={100 * Math.sin((a * Math.PI) / 180)} />
      ))}
      {[20, 38, 56, 74].map((r) => (
        <path key={r} d={`M${r} 0 Q${r * 0.75} ${r * 0.75} 0 ${r}`} />
      ))}
    </g>
  </svg>
);

/** 1:05–1:20 — The Reveal. Empty dusty room; the torch finds a 1987 photo. */
export const Scene6Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const found = localFrame('reveal', BEATS.photoFound);
  const yearShot = localFrame('reveal', BEATS.photoCloseUp1987);
  const rahulLine = localFrame('reveal', 76.2);

  // torch sweep → settle on the photo
  const pcx = PHOTO.x + PHOTO.w / 2;
  const pcy = PHOTO.y + PHOTO.h / 2;
  const bx = interpolate(frame, [0, found * 0.35, found * 0.7, found], [160, 880, 300, pcx], {
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.sin),
  });
  const by = interpolate(frame, [0, found * 0.35, found * 0.7, found], [1400, 1250, 520, pcy], {
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.sin),
  });

  // camera: hold → push into the photo → crash-in on "1987"
  const zoom1 = interpolate(frame, [found, yearShot], [1, 1.65], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.quad),
  });
  const zoom2 = interpolate(frame, [yearShot, yearShot + 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.exp),
  });
  const scale = zoom1 + zoom2 * 2.4;
  const focusX = interpolate(zoom2, [0, 1], [pcx, YEAR.x]);
  const focusY = interpolate(zoom2, [0, 1], [pcy, YEAR.y]);
  const tx = (540 - focusX) * Math.min(1, (scale - 1) / 0.65);
  const ty = (960 - focusY) * Math.min(1, (scale - 1) / 0.65);
  const pullBack = interpolate(frame, [rahulLine, rahulLine + 60], [1, 0.82], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const shaking = frame > rahulLine ? 5 : frame > found ? 1.5 : 0;

  const power = flicker(frame, 'torch-reveal', 0.1);
  const beamR = frame < found ? 300 : 300 + (scale - 1) * 260;
  const beamX = frame < found ? bx : 540;
  const beamY = frame < found ? by : 960;

  return (
    <AbsoluteFill style={{ background: 'black' }}>
      <Camera scale={scale * pullBack} x={tx} y={ty} origin={`${focusX}px ${focusY}px`} shake={shaking}>
        {/* stained, peeling plaster wall */}
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(ellipse 300px 220px at 200px 300px, rgba(0,0,0,0.35), transparent), radial-gradient(ellipse 260px 420px at 900px 1300px, rgba(0,0,0,0.4), transparent), linear-gradient(180deg,#3a332b 0%,#2c2620 70%,#120f0c 70%,#1d1712 100%)',
          }}
        />
        {new Array(14).fill(0).map((_, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: random(`pp-x-${i}`) * 1000,
              top: random(`pp-y-${i}`) * 1250,
              width: 40 + random(`pp-w-${i}`) * 160,
              height: 20 + random(`pp-h-${i}`) * 90,
              background: '#1d1813',
              borderRadius: '40% 60% 30% 70%',
              opacity: 0.55,
            }}
          />
        ))}
        <Cobweb x={0} y={0} size={320} />
        <Cobweb x={760} y={0} size={320} flip />
        <OldPhoto />
        <Dust count={110} seed="reveal-dust" fall={0.25} opacity={0.75} />
      </Camera>
      <TorchDarkness x={beamX} y={beamY} r={beamR} power={power} ambient={0.03} />
    </AbsoluteFill>
  );
};
