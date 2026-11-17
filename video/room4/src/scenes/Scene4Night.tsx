import React from 'react';
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from 'remotion';
import { BEATS, localFrame, sec } from '../timeline';
import { FONT_SUB } from '../fonts';
import { C } from '../theme';
import { Camera, Glow, joltAt } from '../components/fx';

const CLOCK_SECONDS = 3.5;

const LedClock: React.FC<{ x: number; y: number; size: number; blink: boolean }> = ({ x, y, size, blink }) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      padding: `${size * 0.18}px ${size * 0.35}px`,
      background: 'linear-gradient(180deg,#151515,#050505)',
      borderRadius: size * 0.16,
      boxShadow: `0 0 ${size * 0.6}px rgba(255,30,30,0.25), inset 0 0 ${size * 0.2}px #000`,
      fontFamily: FONT_SUB,
      fontWeight: 800,
      fontSize: size,
      letterSpacing: size * 0.04,
      color: '#ff2b2b',
      textShadow: `0 0 ${size * 0.15}px #ff2b2b, 0 0 ${size * 0.45}px rgba(255,0,0,0.7)`,
      whiteSpace: 'nowrap',
    }}
  >
    2<span style={{ opacity: blink ? 1 : 0.15 }}>:</span>13
    <span style={{ fontSize: size * 0.32, marginLeft: size * 0.12, verticalAlign: 'top' }}>AM</span>
  </div>
);

/** Shot A — insert: the clock reads 2:13 AM. */
const ClockInsert: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, sec(CLOCK_SECONDS)], [1, 1.12]);
  return (
    <Camera scale={zoom}>
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 55%, #1a0606 0%, #050202 60%, #000 100%)' }} />
      <LedClock x={170} y={760} size={240} blink={frame % 30 < 18} />
      <AbsoluteFill style={{ top: 1180, background: 'linear-gradient(180deg,#0e0705,#000)' }} />
    </Camera>
  );
};

/** A sleeper under a blanket; `sit` 0 = lying down, 1 = bolt upright. */
const Sleeper: React.FC<{ x: number; y: number; scale: number; sit?: number; flip?: boolean }> = ({ x, y, scale, sit = 0, flip }) => {
  const torsoAngle = interpolate(sit, [0, 1], [-84, -8]);
  return (
    <svg
      width={700 * scale}
      height={420 * scale}
      viewBox="0 0 700 420"
      style={{ position: 'absolute', left: x, top: y, overflow: 'visible', transform: flip ? 'scaleX(-1)' : undefined }}
    >
      {/* mattress */}
      <rect x={20} y={300} width={660} height={90} rx={24} fill="#2a3449" />
      <rect x={20} y={300} width={660} height={22} rx={10} fill="#3a4766" />
      {/* pillow */}
      <ellipse cx={110} cy={300} rx={80} ry={26} fill="#3d4a6a" />
      {/* legs under blanket */}
      <path d="M260 300 Q420 230 660 286 L660 312 L260 312 Z" fill="#222b40" />
      {/* torso + head pivoting at the hip (260,300) */}
      <g transform={`rotate(${torsoAngle} 260 300)`}>
        <path d="M230 300 L230 130 Q260 110 290 130 L290 300 Z" fill={C.silhouette} />
        <ellipse cx={260} cy={86} rx={40} ry={46} fill={C.silhouette} />
      </g>
      {/* blanket edge over the waist */}
      <path d="M220 290 Q300 250 380 280 L380 316 L220 316 Z" fill="#26304a" />
    </svg>
  );
};

/** Shot B — the dark room. Knocks, then a whisper from the corridor. */
const RoomShot: React.FC = () => {
  const frame = useCurrentFrame();
  const offset = sec(CLOCK_SECONDS);
  const lf = (abs: number) => localFrame('night', abs) - offset;
  const knocks = BEATS.nightKnocks.map(lf);
  const jolt = joltAt(frame, knocks, 10);
  const sit = interpolate(frame, [lf(BEATS.karanSitsUp), lf(BEATS.karanSitsUp) + 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const whisper = interpolate(frame, [lf(40.0), lf(40.6), lf(43.4), lf(44.0)], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  // feet shadow sliding across the light gap under the door during the whisper
  const feetX = interpolate(frame, [lf(39.6), lf(44.2)], [-120, 260], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const push = interpolate(frame, [0, sec(16 - CLOCK_SECONDS)], [1.0, 1.16]);
  const gap = 0.75 + 0.25 * Math.sin(frame / 9);

  return (
    <Camera scale={push} shake={jolt * 9} origin="62% 45%">
      {/* back wall + floor */}
      <AbsoluteFill style={{ background: 'linear-gradient(180deg,#0a0f1a 0%,#0f1522 58%,#06080d 58%,#0b0e15 100%)' }} />
      {/* barred window with moonlight */}
      <div style={{ position: 'absolute', left: 90, top: 330, width: 260, height: 340, background: 'linear-gradient(180deg,#5d7398,#26344d)', borderRadius: '130px 130px 6px 6px', boxShadow: '0 0 120px rgba(120,150,200,0.35)' }}>
        {[1, 2, 3].map((i) => (
          <div key={i} style={{ position: 'absolute', left: i * 65 - 6, top: 0, width: 12, height: '100%', background: '#05070b' }} />
        ))}
      </div>
      {/* moonlight patch on floor */}
      <div
        style={{
          position: 'absolute',
          left: 140,
          top: 1180,
          width: 520,
          height: 360,
          background: 'linear-gradient(160deg, rgba(130,160,210,0.22), rgba(130,160,210,0.03))',
          transform: 'skewX(-28deg)',
          filter: 'blur(6px)',
        }}
      />
      {/* the room's own door, back wall right */}
      <div
        style={{
          position: 'absolute',
          left: 640,
          top: 420,
          width: 300,
          height: 690,
          background: 'linear-gradient(90deg,#120c08,#1c130c,#120c08)',
          border: '10px solid #080605',
          transform: `translateX(${jolt * 6}px)`,
        }}
      />
      {/* light gap under that door */}
      <div style={{ position: 'absolute', left: 650, top: 1108, width: 300, height: 8, overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, background: '#ffb347', opacity: 0.8 * gap, boxShadow: '0 0 20px #ffb347' }} />
        <div style={{ position: 'absolute', left: feetX, top: 0, width: 40, height: 8, background: '#000' }} />
        <div style={{ position: 'absolute', left: feetX + 70, top: 0, width: 40, height: 8, background: '#000' }} />
      </div>
      <Glow x={800} y={1140} r={220} intensity={0.35 * gap} />
      {/* wall clock silhouette */}
      <div style={{ position: 'absolute', left: 470, top: 300, width: 110, height: 110, borderRadius: '50%', border: '6px solid #1d2230', background: '#0c1018' }}>
        <div style={{ position: 'absolute', left: 50, top: 18, width: 4, height: 38, background: '#596480', transformOrigin: '50% 100%', transform: 'rotate(65deg)' }} />
        <div style={{ position: 'absolute', left: 50, top: 8, width: 3, height: 48, background: '#596480', transformOrigin: '50% 100%', transform: 'rotate(78deg)' }} />
      </div>
      {/* the two friends on mattresses */}
      <Sleeper x={60} y={1150} scale={1.0} />
      <Sleeper x={240} y={1430} scale={1.15} sit={sit} />
      <LedClock x={820} y={1500} size={56} blink={frame % 30 < 18} />
      {/* whisper: the dark itself breathes */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at 80% 60%, rgba(0,0,0,0) 0%, rgba(0,0,0,${0.35 + whisper * 0.35}) 70%)`,
        }}
      />
      <AbsoluteFill style={{ background: `rgba(255,255,255,${jolt * 0.04})` }} />
    </Camera>
  );
};

/** 0:32–0:48 — The Night. */
export const Scene4Night: React.FC = () => (
  <AbsoluteFill style={{ background: 'black' }}>
    <Sequence durationInFrames={sec(CLOCK_SECONDS)} name="Clock 2:13 AM">
      <ClockInsert />
    </Sequence>
    <Sequence from={sec(CLOCK_SECONDS)} name="Room">
      <RoomShot />
    </Sequence>
  </AbsoluteFill>
);
