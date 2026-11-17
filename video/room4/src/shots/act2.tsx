import React from 'react';
import { AbsoluteFill, Easing, interpolate, random } from 'remotion';
import { Shot, handheld } from '../edit';
import { BEATS, walkPhase } from '../timeline';
import { FONT_SUB } from '../fonts';
import { Camera, Dust, TorchDarkness, flicker, joltAt } from '../components/fx';
import { Corridor, WoodenDoor } from '../components/props';
import { Character, HeldPhone } from '../rig/Character';
import { Blanket, CorridorSide, LightPool, Mattress, MoonGrade } from '../sets/sets';
import { feetFor } from './act1';

const LedClock: React.FC<{ x: number; y: number; size: number; blink: boolean }> = ({ x, y, size, blink }) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      padding: `${size * 0.18}px ${size * 0.35}px`,
      background: 'linear-gradient(180deg,#191919,#050505)',
      borderRadius: size * 0.16,
      boxShadow: `0 0 ${size * 0.8}px rgba(255,30,30,0.3), inset 0 0 ${size * 0.2}px #000`,
      fontFamily: FONT_SUB,
      fontWeight: 800,
      fontSize: size,
      color: '#ff2b2b',
      textShadow: `0 0 ${size * 0.15}px #ff2b2b, 0 0 ${size * 0.45}px rgba(255,0,0,0.7)`,
      whiteSpace: 'nowrap',
    }}
  >
    2<span style={{ opacity: blink ? 1 : 0.15 }}>:</span>13
    <span style={{ fontSize: size * 0.32, marginLeft: size * 0.12, verticalAlign: 'top' }}>AM</span>
  </div>
);

/** Back wall of the guest room with window + door, shared by the night shots. */
const GuestRoom: React.FC<{ jolt?: number; gapLight?: number; feetX?: number }> = ({ jolt = 0, gapLight = 0.8, feetX = -300 }) => (
  <AbsoluteFill>
    <AbsoluteFill style={{ background: 'linear-gradient(180deg,#141c2c 0%,#1c2638 55%,#0b0f17 55%,#121824 100%)' }} />
    <div style={{ position: 'absolute', left: 80, top: 260, width: 280, height: 380, background: 'linear-gradient(180deg,#7088b0,#2c3c58)', borderRadius: '140px 140px 6px 6px', boxShadow: '0 0 160px rgba(120,150,210,0.45)' }}>
      {[1, 2, 3].map((i) => (
        <div key={i} style={{ position: 'absolute', left: i * 70 - 6, top: 0, width: 12, height: '100%', background: '#05070b' }} />
      ))}
    </div>
    <div style={{ position: 'absolute', left: 120, top: 1100, width: 600, height: 420, background: 'linear-gradient(160deg, rgba(140,170,220,0.25), rgba(140,170,220,0.02))', transform: 'skewX(-28deg)', filter: 'blur(8px)' }} />
    <div style={{ position: 'absolute', left: 640, top: 360, width: 320, height: 700, background: 'linear-gradient(90deg,#1a110a,#2a1b10,#1a110a)', border: '12px solid #0b0806', transform: `translateX(${jolt * 7}px)` }}>
      <div style={{ position: 'absolute', right: 30, top: 340, width: 20, height: 20, borderRadius: '50%', background: '#6b5b3d' }} />
    </div>
    <div style={{ position: 'absolute', left: 652, top: 1072, width: 320, height: 9, overflow: 'hidden' }}>
      <div style={{ position: 'absolute', inset: 0, background: '#ffb347', opacity: gapLight, boxShadow: '0 0 20px #ffb347' }} />
      <div style={{ position: 'absolute', left: feetX, width: 44, height: 9, background: '#000' }} />
      <div style={{ position: 'absolute', left: feetX + 80, width: 44, height: 9, background: '#000' }} />
    </div>
  </AbsoluteFill>
);

/* ===================================================== SCENE 4 — THE NIGHT (0:32–0:48) */
const clock: Shot = {
  name: 'Clock 2:13 AM',
  from: 32,
  to: 35.5,
  in: 'dip',
  render: ({ t, frame }) => (
    <Camera scale={interpolate(t, [0, 3.5], [1, 1.15])}>
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 50% 55%, #200707 0%, #070202 60%, #000 100%)' }} />
      <LedClock x={170} y={760} size={240} blink={frame % 30 < 18} />
      <AbsoluteFill style={{ top: 1180, background: 'linear-gradient(180deg,#120806,#000)' }} />
    </Camera>
  ),
};

const sleeping: Shot = {
  name: 'Room — both asleep, knocks',
  from: 35.5,
  to: 40,
  in: 'cut',
  render: ({ t, abs, frame }) => {
    const knocks = BEATS.nightKnocks.map((s) => Math.round((s - 35.5) * 30));
    const jolt = joltAt(frame, knocks, 10);
    const karanAwake = abs >= BEATS.karanEyesOpen;
    const br = Math.sin(abs * 1.7);
    return (
      <Camera scale={interpolate(t, [0, 4.5], [1.0, 1.1])} shake={jolt * 10} origin="50% 60%">
        <GuestRoom jolt={jolt} gapLight={0.75 + 0.25 * Math.sin(abs * 4)} />
        <Mattress x={60} y={1230} w={900} h={170} />
        <Character id="rahul" x={930} y={1265} height={760} lean={-90} expr="sleep" light={{ dir: -1 }} lipSync={false} />
        <Blanket x={380} y={1150} w={580} h={170} color="#36507a" breathe={br} />
        <Mattress x={100} y={1580} w={920} h={180} color="#4a3a5a" />
        <Character
          id="karan"
          x={990}
          y={1625}
          height={780}
          lean={-90}
          expr={karanAwake ? 'scared' : 'sleep'}
          gaze={[-0.8, 0]}
          light={{ dir: -1 }}
          lipSync={false}
        />
        <Blanket x={430} y={1500} w={590} h={180} color="#6a3a3a" breathe={Math.sin(abs * 1.5 + 1)} />
        <LedClock x={760} y={1830} size={50} blink={frame % 30 < 18} />
        <LightPool x={330} y={1100} r={1350} dark={0.55} color="140,170,230" warm={0.15} />
        <AbsoluteFill style={{ background: `rgba(255,255,255,${jolt * 0.05})` }} />
        <MoonGrade amount={0.5} />
      </Camera>
    );
  },
};

const underDoor: Shot = {
  name: 'Under the door — whisper (L6)',
  from: 40,
  to: 44.2,
  in: 'cut',
  render: ({ t, abs }) => {
    const feetX = interpolate(abs, [40.2, 42.2], [-160, 110], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return (
      <Camera scale={interpolate(t, [0, 4.2], [2.6, 3.2])} origin="62% 56%">
        <GuestRoom feetX={feetX} gapLight={0.9} />
        <LightPool x={800} y={1076} r={700} dark={0.75} warm={0.2} />
        <MoonGrade amount={0.45} />
      </Camera>
    );
  },
};

const karanSitsUp: Shot = {
  name: 'Karan bolts upright (L7)',
  from: 44.2,
  to: 48,
  in: 'flash',
  render: ({ t, abs }) => {
    const H = 2600;
    const rise = interpolate(t, [0, 0.3], [900, 0], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
    const turnToRahul = interpolate(abs, [44.75, 45.0], [0.5, -0.6], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const rahulWakes = abs > 46.3;
    const h = handheld(abs, 1.4);
    return (
      <Camera x={h.x} y={h.y} scale={interpolate(t, [0, 3.8], [1, 1.08])}>
        <AbsoluteFill style={{ filter: 'blur(8px) brightness(0.6)' }}>
          <GuestRoom />
        </AbsoluteFill>
        <Character id="karan" x={620} y={feetFor(700, H) + rise} height={H} expr="terrified" sweat headTurn={turnToRahul} gaze={[turnToRahul * 1.2, 0]} light={{ dir: -1, hard: 0.2 }} />
        {/* Rahul lying in the lower foreground, waking */}
        <Character id="rahul" x={1050} y={1700} height={1500} lean={-90} expr={rahulWakes ? 'worried' : 'sleep'} gaze={[0.6, -0.4]} light={{ dir: -1 }} filter="brightness(0.8)" />
        <Blanket x={400} y={1720} w={900} h={260} color="#36507a" breathe={Math.sin(abs * 1.7)} />
        <LightPool x={180} y={700} r={1400} dark={0.6} color="140,170,230" warm={0.15} />
        <MoonGrade amount={0.5} />
      </Camera>
    );
  },
};

/* ===================================================== SCENE 5 — THE DOOR (0:48–1:05) */
const TorchCone: React.FC<{ x: number; y: number; len: number; spread: number; on?: number }> = ({ x, y, len, spread, on = 1 }) => (
  <svg width={1080} height={1920} style={{ position: 'absolute', inset: 0, mixBlendMode: 'screen', pointerEvents: 'none' }}>
    <defs>
      <linearGradient id="cone" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stopColor="#fff6dc" stopOpacity={0.55 * on} />
        <stop offset="1" stopColor="#fff6dc" stopOpacity={0} />
      </linearGradient>
    </defs>
    <polygon points={`${x},${y - 6} ${x + len},${y - spread} ${x + len},${y + spread} ${x},${y + 6}`} fill="url(#cone)" style={{ filter: 'blur(14px)' }} />
  </svg>
);

const darkWalk: Shot = {
  name: 'Dark corridor — Rahul with phone torch',
  from: 48,
  to: 52,
  in: 'dip',
  render: ({ t, abs }) => {
    const H = 1200;
    const power = flicker(Math.round(abs * 30), 'dw-torch', 0.1);
    const scroll = t * 200;
    return (
      <AbsoluteFill>
        <CorridorSide scroll={scroll + 1000} lampX={1000} lampY={1150} lamp={0.4} dark={0.8} />
        <Character id="karan" view="side" x={330} y={1840} height={H} walk={walkPhase(abs, 48.13, 0.62)} armR={[75, 0]} expr="scared" light={{ dir: 1, hard: 0.5 }} filter="brightness(0.9)" />
        <Character id="rahul" view="side" x={600} y={1840} height={H} walk={walkPhase(abs, 48, 0.62)} armR={[72, 12]} holdR={<HeldPhone />} expr="worried" light={{ dir: 1, hard: 0.5 }} />
        <TorchDarkness x={980} y={1150} r={560} power={power} ambient={0.32} />
        <TorchCone x={800} y={1170} len={600} spread={260} on={power} />
      </AbsoluteFill>
    );
  },
};

const povWalk: Shot = {
  name: 'POV torch — whisper stops at 4 (L7b)',
  from: 52,
  to: 56,
  in: 'cut',
  render: ({ t, abs }) => {
    const push = interpolate(t, [0, 4], [1.1, 2.15], { easing: Easing.inOut(Easing.quad) });
    const turnX = interpolate(t, [2.4, 4], [0, -260], { extrapolateLeft: 'clamp' });
    const step = (abs - 52) / 0.66;
    const bx = 540 + Math.sin(step * 0.5 * Math.PI) * 60 + interpolate(t, [2.2, 4], [0, 170], { extrapolateLeft: 'clamp' });
    const by = 1180 + Math.sin(step * Math.PI) * 30;
    const power = flicker(Math.round(abs * 30), 'pov', 0.12);
    return (
      <AbsoluteFill>
        <Camera scale={push} x={turnX} y={Math.abs(Math.sin(step * Math.PI)) * 12} origin="540px 935px">
          <AbsoluteFill style={{ filter: 'brightness(2.6) sepia(0.3)' }}>
            <Corridor lightLevel={1} />
          </AbsoluteFill>
        </Camera>
        <TorchDarkness x={bx} y={by} r={500} power={power} ambient={0.12} />
      </AbsoluteFill>
    );
  },
};

const handle: Shot = {
  name: 'Handle rattles — ECU',
  from: 56,
  to: 59,
  in: 'cut',
  render: ({ t, abs }) => {
    const shake = abs < BEATS.silenceBeforePush ? interpolate(t, [0, 0.4, 3], [0.4, 0.8, 1]) : 0;
    const pulse = 1 + 0.015 * Math.max(0, Math.sin(abs * 9));
    return (
      <AbsoluteFill>
        <Camera scale={3.0 * pulse} origin="740px 1030px" shake={shake * 4}>
          <AbsoluteFill style={{ background: '#1b1611' }} />
          <WoodenDoor x={240} y={360} width={600} handleShake={shake} />
        </Camera>
        <TorchDarkness x={560 + Math.sin(abs * 13) * 10} y={1000} r={520} power={flicker(Math.round(abs * 30), 'hd', 0.1)} ambient={0.05} />
      </AbsoluteFill>
    );
  },
};

const karanBegs: Shot = {
  name: 'Karan CU — "Mat khol" (L8)',
  from: 59,
  to: 61.4,
  in: 'whip',
  render: ({ t, abs }) => {
    const H = 3000;
    const h = handheld(abs, 1.8);
    return (
      <Camera x={h.x} y={h.y} scale={interpolate(t, [0, 2.4], [1.0, 1.06])}>
        <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 70% 60%, #2a2016, #050403 70%)' }} />
        <Character id="karan" x={520} y={feetFor(760, H)} height={H} expr="terrified" sweat headTurn={0.3} gaze={[0.5, 0]} light={{ dir: 1, hard: 0.35 }} />
        <LightPool x={980} y={1400} r={1300} dark={0.75} color="255,240,210" warm={0.2} />
      </Camera>
    );
  },
};

const rahulDecides: Shot = {
  name: 'Rahul profile — reaches',
  from: 61.4,
  to: 62.4,
  in: 'cut',
  render: ({ t, abs }) => {
    const H = 3300;
    const reach = interpolate(t, [0.2, 1.0], [10, 70], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return (
      <Camera scale={interpolate(t, [0, 1], [1.05, 1.12])}>
        <AbsoluteFill style={{ background: '#030202' }} />
        <Character id="rahul" view="side" x={360} y={feetFor(760, H)} height={H} expr="worried" armR={[reach, 10]} light={{ dir: 1, hard: 0.6 }} />
        <LightPool x={1050} y={850} r={1200} dark={0.85} color="255,240,210" warm={0.18} />
      </Camera>
    );
  },
};

const doorOpens: Shot = {
  name: 'Over-shoulder — door creaks open',
  from: 62.4,
  to: 65,
  in: 'cut',
  render: ({ t, abs }) => {
    const open = interpolate(t, [0, 1.8], [0, 0.8], { extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
    const power = flicker(Math.round(abs * 30), 'open', 0.1);
    return (
      <AbsoluteFill>
        <Camera scale={interpolate(t, [0, 2.6], [1.0, 1.14])} origin="50% 45%">
          <AbsoluteFill style={{ background: 'linear-gradient(180deg,#1b1611,#29211a 70%,#0f0b08 70%,#17110c)' }} />
          <WoodenDoor x={240} y={360} width={600} open={open} />
          <Dust count={40} seed="open-dust" area={{ x: 240, y: 300, w: 600, h: 1300 }} fall={0.3} opacity={0.5} />
        </Camera>
        <TorchDarkness x={interpolate(t, [0, 2], [700, 560], { extrapolateRight: 'clamp' })} y={950} r={460} power={power} ambient={0.06} />
        {/* Rahul's head & shoulder, foreground */}
        <Character id="rahul" view="back" x={-30} y={3300} height={3000} filter="blur(5px) brightness(0.35)" />
      </AbsoluteFill>
    );
  },
};

export const ACT2: Shot[] = [clock, sleeping, underDoor, karanSitsUp, darkWalk, povWalk, handle, karanBegs, rahulDecides, doorOpens];
export const _u2 = [random];
