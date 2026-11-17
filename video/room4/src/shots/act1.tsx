import React from 'react';
import { AbsoluteFill, interpolate } from 'remotion';
import { Shot, clamp01, ease, handheld, ramp } from '../edit';
import { BEATS, walkPhase } from '../timeline';
import { Camera, Dust, Glow, flicker, joltAt } from '../components/fx';
import { Lantern, WoodenDoor } from '../components/props';
import { Character, HeldLantern } from '../rig/Character';
import { Car, CorridorSide, ForegroundPillars, HaveliFacade, LightPool, MoonGrade, RoadParallax, Sky } from '../sets/sets';

/** Feet position that puts a character's head centre at `headY` for a given rig height. */
export const feetFor = (headY: number, h: number) => headY + 0.885 * h;

const Blur: React.FC<{ px: number; children: React.ReactNode; dim?: number }> = ({ px, children, dim = 0 }) => (
  <AbsoluteFill style={{ filter: `blur(${px}px) brightness(${1 - dim})` }}>{children}</AbsoluteFill>
);

/* ===================================================== SCENE 1 — HOOK (0:00–0:08) */
const hook: Shot = {
  name: 'Hook — door 4',
  from: 0,
  to: 8,
  in: 'dip',
  render: ({ t, frame }) => {
    const knocks = BEATS.hookKnocks.map((s) => Math.round(s * 30));
    const jolt = joltAt(frame, knocks, 9);
    const light = flicker(frame, 'hook-lamp', 0.4);
    const push = interpolate(t, [0, 8], [1.15, 1.42]);
    const shadowX = interpolate(t, [4.9, 6.4], [-300, 1300], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const h = handheld(t, 0.6);
    return (
      <AbsoluteFill style={{ background: '#050302' }}>
        <Camera scale={push} x={h.x} y={h.y} shake={jolt * 7} origin="50% 40%">
          <AbsoluteFill style={{ background: 'radial-gradient(ellipse at 30% 40%, #3a2e22 0%, #1a130d 55%, #070504 100%)' }} />
          <WoodenDoor x={200} y={300} width={680} jolt={jolt} numberOpacity={0.75} />
          {/* light under the door, a shadow passes behind it */}
          <div style={{ position: 'absolute', left: 205, top: 300 + 680 * 2.05 - 6, width: 670, height: 12, overflow: 'hidden' }}>
            <div style={{ position: 'absolute', inset: 0, background: '#ffb24a', boxShadow: '0 0 30px #ffb24a', opacity: 0.85 * light }} />
            <div style={{ position: 'absolute', left: shadowX, width: 160, height: 12, background: '#000' }} />
          </div>
          <AbsoluteFill style={{ opacity: 0.3 + jolt }}>
            <Dust count={70} seed="hook-dust" area={{ x: 190, y: 200, w: 700, h: 1500 }} fall={1 + jolt * 3} />
          </AbsoluteFill>
        </Camera>
        <Glow x={-60} y={760} r={900} intensity={0.55 * light} />
        <AbsoluteFill style={{ background: `rgba(0,0,0,${0.3 - light * 0.15 + jolt * 0.12})` }} />
      </AbsoluteFill>
    );
  },
};

/* ===================================================== SCENE 2 — ARRIVAL (0:08–0:20) */
const road: Shot = {
  name: 'Road — car at night',
  from: 8,
  to: 11.5,
  in: 'dip',
  render: ({ t }) => {
    const h = handheld(t, 1.2);
    return (
      <Camera scale={1.05} x={h.x} y={h.y}>
        <RoadParallax t={t} travel={t * 950} />
        <Car x={230} y={1210} t={t} />
        <MoonGrade />
      </Camera>
    );
  },
};

const haveliWide: Shot = {
  name: 'Haveli — establishing',
  from: 11.5,
  to: 13.6,
  in: 'whip',
  render: ({ t, abs }) => {
    const carX = interpolate(abs, [11.5, BEATS.carStop], [-760, 90], { extrapolateRight: 'clamp', easing: (x) => 1 - Math.pow(1 - x, 3) });
    const lights = abs < BEATS.headlightsOff ? 1 : 0;
    const push = interpolate(t, [0, 2.1], [1.0, 1.08]);
    const lamp = flicker(Math.round(t * 30), 'gate', 0.35);
    return (
      <Camera scale={push} origin="55% 80%">
        <Sky t={abs} moonX={860} moonY={360} horizon={1500} />
        <HaveliFacade x={-260} y={660} t={t} />
        <AbsoluteFill style={{ top: 1660, background: 'linear-gradient(180deg,#1c1610,#2a2016)' }} />
        <Character id="vikram" x={560} y={1665} height={300} expr="warm" armR={[20, 70]} holdR={<HeldLantern glow={lamp} />} light={{ dir: 1 }} />
        <Glow x={600} y={1560} r={360} intensity={0.6 * lamp} />
        <Car x={carX} y={1600} scale={0.75} t={abs} lights={lights} moving={abs < BEATS.carStop} />
        <MoonGrade amount={0.4} />
      </Camera>
    );
  },
};

const vikramGate: Shot = {
  name: 'Vikram at the gate (L1)',
  from: 13.6,
  to: 16.5,
  in: 'cut',
  render: ({ t, abs }) => {
    const H = 2500;
    const lamp = flicker(Math.round(abs * 30), 'vg', 0.3);
    const push = interpolate(t, [0, 2.9], [1.0, 1.07]);
    const wave = abs < 14.6 ? Math.sin(abs * 12) * 12 : 0;
    const h = handheld(abs, 0.8);
    return (
      <Camera scale={push} x={h.x} y={h.y} origin="50% 35%">
        <Blur px={10} dim={0.25}>
          <Sky t={abs} moonX={180} moonY={260} horizon={1700} />
          <HaveliFacade x={-1300} y={-300} scale={2.6} t={abs} />
        </Blur>
        <Character
          id="vikram"
          x={540}
          y={feetFor(640, H)}
          height={H}
          expr="warm"
          gaze={[-0.15, 0]}
          headTilt={-2}
          armL={[abs < 14.8 ? 105 + wave : interpolate(abs, [14.8, 15.2], [105, 8], { extrapolateRight: 'clamp' }), abs < 14.8 ? 40 : 10]}
          armR={[18, 85]}
          holdR={<HeldLantern glow={lamp} />}
          light={{ dir: 1, hard: 0.15 }}
        />
        <LightPool x={760} y={1150} r={1250} dark={0.6} warm={0.25 * lamp} />
        <MoonGrade amount={0.3} />
      </Camera>
    );
  },
};

const friendsTwoShot: Shot = {
  name: 'Rahul & Karan two-shot (L2 whisper)',
  from: 16.5,
  to: 20,
  in: 'cut',
  render: ({ t, abs }) => {
    const H = 2300;
    const lean = interpolate(abs, [16.6, 17.0], [0, -5], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const rahulLook = interpolate(abs, [17.4, 17.8], [0, 0.8], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const push = interpolate(t, [0, 3.5], [1.0, 1.06]);
    const h = handheld(abs, 0.8);
    return (
      <Camera scale={push} x={h.x} y={h.y}>
        <Blur px={12} dim={0.35}>
          <Sky t={abs} moonX={850} moonY={300} horizon={1600} />
          <HaveliFacade x={-700} y={300} scale={1.8} t={abs} />
        </Blur>
        <Glow x={540} y={1050} r={260} intensity={0.5} />
        <Character id="rahul" x={300} y={feetFor(760, H)} height={H} expr={rahulLook > 0.5 ? 'worried' : 'neutral'} gaze={[rahulLook, 0]} headTurn={rahulLook * 0.3} light={{ dir: -0.6 }} />
        <Character
          id="karan"
          x={800}
          y={feetFor(740, H)}
          height={H}
          expr="whisper"
          headTurn={-0.55}
          gaze={[-0.9, 0.1]}
          headTilt={-5}
          lean={lean}
          light={{ dir: -0.6 }}
          armL={[30, 110]}
        />
        <LightPool x={540} y={900} r={1300} dark={0.55} color="150,180,255" warm={0.12} />
        <MoonGrade amount={0.45} />
      </Camera>
    );
  },
};

/* ===================================================== SCENE 3 — THE WARNING (0:20–0:32) */
const corridorWalk: Shot = {
  name: 'Corridor tracking — Vikram leads',
  from: 20,
  to: 24.5,
  in: 'dip',
  render: ({ t, abs }) => {
    const ph = (o: number) => walkPhase(abs, 20 + o, 0.5);
    const scroll = t * 330;
    const lamp = flicker(Math.round(abs * 30), 'cw', 0.35);
    const H = 1150;
    return (
      <AbsoluteFill>
        <CorridorSide scroll={scroll} lampX={800} lampY={1200} lamp={lamp} dark={0.82} />
        <Character id="karan" view="side" x={150} y={1830} height={H} walk={ph(0.26)} expr="worried" light={{ dir: 1, hard: 0.2 }} />
        <Character id="rahul" view="side" x={400} y={1830} height={H} walk={ph(0.13)} expr="curious" light={{ dir: 1, hard: 0.2 }} />
        <Character id="vikram" view="side" x={680} y={1830} height={H * 1.04} walk={ph(0)} armR={[32, 58]} holdR={<HeldLantern glow={lamp} />} expr="serious" light={{ dir: 1, hard: 0.2 }} />
        <Glow x={820} y={1260} r={520} intensity={0.45 * lamp} />
        <ForegroundPillars scroll={scroll} />
      </AbsoluteFill>
    );
  },
};

const DoorWall: React.FC<{ blur?: number; dim?: number }> = ({ blur = 0, dim = 0 }) => (
  <Blur px={blur} dim={dim}>
    <AbsoluteFill style={{ background: 'linear-gradient(180deg,#2a2119 0%,#4a3b2c 55%,#2a2119 66%,#18110b 66%,#2a1e14 100%)' }} />
    <WoodenDoor x={300} y={240} width={480} numberOpacity={0.85} />
  </Blur>
);

const vikramWarns: Shot = {
  name: 'Vikram MCU at door 4 (L3)',
  from: 24.5,
  to: 28.2,
  in: 'cut',
  render: ({ t, abs }) => {
    const H = 2700;
    const turn = interpolate(abs, [24.5, 24.9], [0.7, 0], { extrapolateRight: 'clamp' });
    const lamp = flicker(Math.round(abs * 30), 'vw', 0.3);
    const push = interpolate(t, [0, 3.7], [1.0, 1.1]);
    const h = handheld(abs, 0.5);
    return (
      <Camera scale={push} x={h.x} y={h.y} origin="50% 35%">
        <Camera x={-260} scale={1.2}>
          <DoorWall blur={7} dim={0.3} />
        </Camera>
        <Character id="vikram" x={600} y={feetFor(700, H)} height={H} expr="serious" headTurn={turn} gaze={[-0.1, 0.05]} light={{ dir: -1, hard: 0.45 }} />
        <LightPool x={200} y={1500} r={1350} dark={0.7} warm={0.3 * lamp} />
        <MoonGrade amount={0.25} />
      </Camera>
    );
  },
};

const rahulAsks: Shot = {
  name: 'Rahul CU (L4)',
  from: 28.2,
  to: 30.0,
  in: 'cut',
  render: ({ t, abs }) => {
    const H = 3000;
    const h = handheld(abs, 0.6);
    return (
      <Camera scale={interpolate(t, [0, 1.8], [1.02, 1.08])} x={h.x} y={h.y}>
        <Camera x={240} scale={1.3}>
          <DoorWall blur={9} dim={0.35} />
        </Camera>
        <Character id="karan" x={900} y={feetFor(820, 2400)} height={2400} expr="worried" headTurn={-0.4} filter="blur(6px) brightness(0.6)" />
        <Character id="rahul" x={420} y={feetFor(720, H)} height={H} expr="curious" headTurn={0.35} gaze={[0.6, 0]} light={{ dir: 1, hard: 0.3 }} />
        <LightPool x={1000} y={1300} r={1300} dark={0.7} warm={0.25} />
        <MoonGrade amount={0.25} />
      </Camera>
    );
  },
};

const vikramLeaves: Shot = {
  name: 'Vikram walks away (L5)',
  from: 30.0,
  to: 32.0,
  in: 'cut',
  render: ({ abs }) => {
    const walking = abs >= 30.5;
    const vx = walking ? interpolate(abs, [30.5, 32], [700, 80]) : 720;
    const lamp = flicker(Math.round(abs * 30), 'vl', 0.35);
    const light = interpolate(abs, [30.5, 32], [1, 0.35], { extrapolateLeft: 'clamp' });
    return (
      <AbsoluteFill>
        <Camera scale={1.0} y={-60}>
          <DoorWall />
        </Camera>
        <Character
          id="vikram"
          view="side"
          flip
          x={vx}
          y={1860}
          height={1250}
          walk={walking ? walkPhase(abs, 30.5, 0.5) : undefined}
          armR={[30, 60]}
          holdR={<HeldLantern glow={lamp} />}
          expr="serious"
          light={{ dir: 1, hard: 0.3 }}
          headTilt={walking ? 0 : -3}
        />
        <Character id="rahul" view="back" x={250} y={2350} height={1500} light={{ dir: 1 }} />
        <Character id="karan" view="back" x={880} y={2380} height={1480} light={{ dir: -1 }} />
        <LightPool x={vx - 140} y={1250} r={1000 * light + 300} dark={0.85} warm={0.3 * lamp * light} />
      </AbsoluteFill>
    );
  },
};

export const ACT1: Shot[] = [hook, road, haveliWide, vikramGate, friendsTwoShot, corridorWalk, vikramWarns, rahulAsks, vikramLeaves];
export { Blur };
export const _unused = [clamp01, ease, ramp, Lantern];
