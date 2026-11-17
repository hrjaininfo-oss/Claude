import React from 'react';
import { random, useCurrentFrame } from 'remotion';
import { FONT_TITLE } from '../fonts';
import { C } from '../theme';
import { flicker } from './fx';

/* ------------------------------------------------------------------ */
/*  Human silhouettes (no realistic people — shapes and shadows only)  */
/* ------------------------------------------------------------------ */

type PersonProps = {
  x: number; // feet centre
  y: number; // feet baseline
  height: number;
  variant?: 'rahul' | 'karan' | 'vikram';
  facing?: 'front' | 'back';
  lean?: number; // degrees
  rimColor?: string; // edge light colour
  rim?: number; // 0..1 rim light strength
  walk?: number; // walk-cycle phase (radians); undefined = standing
  opacity?: number;
};

/** A flat silhouette in a 200×500 design box. */
export const Person: React.FC<PersonProps> = ({
  x,
  y,
  height,
  variant = 'rahul',
  lean = 0,
  rimColor = C.lantern,
  rim = 0,
  walk,
  opacity = 1,
}) => {
  const s = height / 500;
  const swing = walk === undefined ? 0 : Math.sin(walk) * 9;
  const bob = walk === undefined ? 0 : Math.abs(Math.sin(walk)) * -6;
  const shawl = variant === 'vikram';
  const cap = variant === 'karan';
  const body = shawl
    ? // Vikram: long kurta + shawl, broader shoulders
      'M52 112 Q100 92 148 112 L170 250 L160 330 L150 330 L146 300 L142 330 L58 330 L54 300 L50 330 L40 330 L30 250 Z'
    : 'M60 112 Q100 98 140 112 L160 262 Q152 272 143 263 L138 205 L136 318 L64 318 L62 205 L57 263 Q48 272 40 262 Z';
  return (
    <svg
      width={200 * s}
      height={500 * s}
      viewBox="0 0 200 500"
      style={{
        position: 'absolute',
        left: x - 100 * s,
        top: y - 500 * s,
        overflow: 'visible',
        transform: `rotate(${lean}deg) translateY(${bob * s}px)`,
        transformOrigin: '50% 100%',
        opacity,
        filter: rim > 0 ? `drop-shadow(${-3 * rim}px 0 ${6 * rim}px ${rimColor})` : undefined,
      }}
    >
      <g fill={C.silhouette}>
        <ellipse cx={100} cy={60} rx={33} ry={38} />
        {cap && <path d="M64 50 Q100 8 136 50 L150 56 L64 56 Z" />}
        {shawl && <path d="M62 40 Q100 -2 138 40 L140 70 Q100 52 60 70 Z" />}
        <rect x={88} y={90} width={24} height={26} />
        <path d={body} />
        {/* legs */}
        <path
          d={`M66 ${shawl ? 325 : 312} L${86 + swing} 490 L${106 + swing} 490 L98 ${shawl ? 325 : 312} Z`}
        />
        <path
          d={`M102 ${shawl ? 325 : 312} L${96 - swing} 490 L${116 - swing} 490 L134 ${shawl ? 325 : 312} Z`}
        />
      </g>
    </svg>
  );
};

/* ------------------------------------------------------------------ */
/*  The wooden door of Room No. 4                                       */
/* ------------------------------------------------------------------ */

export const WoodenDoor: React.FC<{
  x: number;
  y: number;
  width: number;
  numberOpacity?: number;
  handleShake?: number; // 0..1
  open?: number; // 0 closed → 1 swung open
  jolt?: number; // whole-door knock jolt 0..1
  showNumber?: boolean;
}> = ({ x, y, width, numberOpacity = 0.75, handleShake = 0, open = 0, jolt = 0, showNumber = true }) => {
  const frame = useCurrentFrame();
  const h = width * 2.05;
  const hx = handleShake ? (random(`hx${frame}`) - 0.5) * 16 * handleShake : 0;
  const hr = handleShake ? (random(`hr${frame}`) - 0.5) * 34 * handleShake : 0;
  const jx = jolt ? (random(`jx${frame}`) - 0.5) * 10 * jolt : 0;
  const planks = 6;
  // When opening, the slab rotates on its left hinge in perspective.
  const swing = open * 88;
  return (
    <div style={{ position: 'absolute', left: x, top: y, width, height: h, perspective: 2200 }}>
      {/* frame / architrave */}
      <div
        style={{
          position: 'absolute',
          inset: -width * 0.07,
          background: `linear-gradient(90deg, #1a0f08, #2b1a0f 30%, #1a0f08)`,
          borderRadius: `${width * 0.5}px ${width * 0.5}px 4px 4px`,
          boxShadow: 'inset 0 0 40px rgba(0,0,0,0.9)',
        }}
      />
      {/* black void behind the door */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          borderRadius: `${width * 0.46}px ${width * 0.46}px 0 0`,
          background: 'radial-gradient(ellipse at 50% 40%, #0b0907, #000 70%)',
        }}
      />
      {/* door slab */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transformOrigin: '0% 50%',
          transform: `translateX(${jx}px) rotateY(${-swing}deg)`,
          borderRadius: `${width * 0.46}px ${width * 0.46}px 0 0`,
          overflow: 'hidden',
          background: C.wood,
          boxShadow: 'inset 0 0 80px rgba(0,0,0,0.85)',
        }}
      >
        {new Array(planks).fill(0).map((_, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: (i * width) / planks,
              top: 0,
              width: width / planks,
              height: '100%',
              background: `linear-gradient(90deg, rgba(0,0,0,0.55), rgba(90,58,34,${0.25 + random(`pl${i}`) * 0.2}) 40%, rgba(0,0,0,0.45))`,
              borderRight: '2px solid rgba(0,0,0,0.6)',
            }}
          />
        ))}
        {/* wood grain streaks */}
        {new Array(26).fill(0).map((_, i) => (
          <div
            key={`g${i}`}
            style={{
              position: 'absolute',
              left: random(`gx${i}`) * width,
              top: random(`gy${i}`) * h,
              width: 2,
              height: 80 + random(`gh${i}`) * 200,
              background: 'rgba(0,0,0,0.35)',
              borderRadius: 2,
            }}
          />
        ))}
        {/* iron cross bands + studs */}
        {[0.3, 0.72].map((p) => (
          <div
            key={p}
            style={{
              position: 'absolute',
              left: 0,
              top: h * p,
              width: '100%',
              height: width * 0.05,
              background: 'linear-gradient(180deg,#2a2a2a,#0d0d0d)',
              boxShadow: '0 4px 8px rgba(0,0,0,0.7)',
            }}
          >
            {new Array(7).fill(0).map((_, i) => (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: `${8 + i * 14}%`,
                  top: '18%',
                  width: width * 0.03,
                  height: width * 0.03,
                  borderRadius: '50%',
                  background: 'radial-gradient(circle at 35% 35%, #6a6a6a, #111)',
                }}
              />
            ))}
          </div>
        ))}
        {/* faded painted "4" */}
        {showNumber && (
          <div
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: h * 0.1,
              textAlign: 'center',
              fontFamily: FONT_TITLE,
              fontSize: width * 0.42,
              color: '#d9cdb2',
              opacity: numberOpacity,
              textShadow: '0 0 2px rgba(0,0,0,0.8)',
              WebkitMaskImage:
                'repeating-linear-gradient(12deg, #000 0px, #000 9px, rgba(0,0,0,0.35) 11px, #000 15px), radial-gradient(circle, #000 55%, rgba(0,0,0,0.5))',
              filter: 'blur(0.6px)',
            }}
          >
            4
          </div>
        )}
        {/* handle ring */}
        <div
          style={{
            position: 'absolute',
            left: width * 0.74 + hx,
            top: h * 0.5,
            width: width * 0.11,
            height: width * 0.11,
            transform: `rotate(${hr}deg)`,
            transformOrigin: '50% 0%',
          }}
        >
          <div
            style={{
              position: 'absolute',
              left: '30%',
              top: -width * 0.03,
              width: '40%',
              height: width * 0.05,
              borderRadius: 4,
              background: 'radial-gradient(circle at 40% 30%, #8a7a5a, #2a2418)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              inset: 0,
              borderRadius: '50%',
              border: `${width * 0.016}px solid #6b5b3d`,
              boxShadow: '0 4px 6px rgba(0,0,0,0.8), inset 0 0 4px rgba(255,220,150,0.3)',
            }}
          />
        </div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/*  Hanging lantern                                                      */
/* ------------------------------------------------------------------ */

export const Lantern: React.FC<{ x: number; y: number; size?: number; seed?: string; on?: number }> = ({
  x,
  y,
  size = 70,
  seed = 'lantern',
  on = 1,
}) => {
  const frame = useCurrentFrame();
  const f = flicker(frame, seed, 0.35) * on;
  const sway = Math.sin(frame / 40) * 3;
  return (
    <div
      style={{
        position: 'absolute',
        left: x - size / 2,
        top: y - size,
        width: size,
        height: size * 1.5,
        transform: `rotate(${sway}deg)`,
        transformOrigin: '50% 0%',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: -size * 2.6,
          top: -size * 2.2,
          width: size * 6.2,
          height: size * 6.2,
          borderRadius: '50%',
          background: `radial-gradient(circle, rgba(255,190,90,${0.55 * f}) 0%, rgba(255,150,60,${0.18 * f}) 35%, transparent 70%)`,
          mixBlendMode: 'screen',
        }}
      />
      <div style={{ position: 'absolute', left: '45%', top: -size * 0.4, width: '10%', height: size * 0.45, background: '#111' }} />
      <div
        style={{
          position: 'absolute',
          left: '15%',
          top: size * 0.05,
          width: '70%',
          height: size * 0.95,
          borderRadius: `${size * 0.3}px ${size * 0.3}px ${size * 0.12}px ${size * 0.12}px`,
          border: `${size * 0.05}px solid #1a1208`,
          background: `radial-gradient(ellipse at 50% 60%, rgba(255,240,190,${f}) 0%, rgba(255,170,70,${0.85 * f}) 40%, rgba(120,60,20,${0.7 * f}) 100%)`,
          boxShadow: `0 0 ${30 * f}px ${10 * f}px rgba(255,170,70,0.5)`,
        }}
      />
    </div>
  );
};

/* ------------------------------------------------------------------ */
/*  One-point-perspective haveli corridor                               */
/* ------------------------------------------------------------------ */

/** A side door drawn on the corridor wall, in a 1080×1920 SVG space. */
const SideDoor: React.FC<{ side: 'L' | 'R'; t: number; label: string }> = ({ side, t, label }) => {
  // t: 0 near the camera … 1 at the vanishing point
  const vx = 540;
  const vy = 900;
  const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
  const t2 = Math.min(1, t + 0.08);
  const wallX = (k: number) => (side === 'L' ? lerp(0, vx - 140, k) : lerp(1080, vx + 140, k));
  const top = (k: number) => lerp(260, vy - 230, k);
  const floor = (k: number) => lerp(1920, vy + 300, k);
  const x1 = wallX(t);
  const x2 = wallX(t2);
  const doorTop = (k: number) => lerp(top(k), floor(k), 0.28);
  const pts = `${x1},${doorTop(t)} ${x2},${doorTop(t2)} ${x2},${floor(t2)} ${x1},${floor(t)}`;
  const cx = (x1 + x2) / 2;
  const cy = lerp(doorTop(t), floor(t), 0.16);
  const fs = Math.max(8, 90 * (1 - t));
  return (
    <g>
      <polygon points={pts} fill="#1d120a" stroke="#0a0604" strokeWidth={4 * (1 - t) + 1} />
      <text x={cx} y={cy} fill="#a89878" opacity={0.55} fontSize={fs} fontFamily={FONT_TITLE} textAnchor="middle">
        {label}
      </text>
    </g>
  );
};

export const Corridor: React.FC<{ lightLevel?: number; doors?: { side: 'L' | 'R'; t: number; label: string }[] }> = ({
  lightLevel = 1,
  doors = [
    { side: 'L', t: 0.05, label: '1' },
    { side: 'R', t: 0.22, label: '2' },
    { side: 'L', t: 0.42, label: '3' },
    { side: 'R', t: 0.6, label: '4' },
  ],
}) => (
  <svg width={1080} height={1920} viewBox="0 0 1080 1920" style={{ position: 'absolute', inset: 0 }}>
    <defs>
      <linearGradient id="floorG" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0" stopColor="#2a1d14" />
        <stop offset="1" stopColor="#070504" />
      </linearGradient>
      <linearGradient id="wallL" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stopColor="#3b322a" />
        <stop offset="1" stopColor="#0c0a08" />
      </linearGradient>
      <linearGradient id="wallR" x1="1" y1="0" x2="0" y2="0">
        <stop offset="0" stopColor="#3b322a" />
        <stop offset="1" stopColor="#0c0a08" />
      </linearGradient>
    </defs>
    <g opacity={lightLevel}>
      {/* ceiling */}
      <polygon points="0,0 1080,0 1080,260 680,670 400,670 0,260" fill="#0d0a08" />
      {/* walls */}
      <polygon points="0,260 400,670 400,1200 0,1920" fill="url(#wallL)" />
      <polygon points="1080,260 680,670 680,1200 1080,1920" fill="url(#wallR)" />
      {/* floor with tiles */}
      <polygon points="0,1920 400,1200 680,1200 1080,1920" fill="url(#floorG)" />
      {[0.15, 0.32, 0.5, 0.66, 0.8, 0.9].map((k) => {
        const y = 1920 - (1920 - 1200) * k;
        const xl = 0 + 400 * k;
        const xr = 1080 - 400 * k;
        return <line key={k} x1={xl} y1={y} x2={xr} y2={y} stroke="#000" strokeOpacity={0.5} strokeWidth={3 * (1 - k) + 1} />;
      })}
      {/* beams on ceiling */}
      {[0.1, 0.35, 0.6, 0.82].map((k) => {
        const yl = 260 + (670 - 260) * k;
        const xl = 400 * k;
        const xr = 1080 - 400 * k;
        return <line key={k} x1={xl} y1={yl} x2={xr} y2={yl} stroke="#000" strokeWidth={26 * (1 - k) + 4} />;
      })}
      {/* far end: dark arch */}
      <rect x={400} y={670} width={280} height={530} fill="#050404" />
      <path d="M455 1200 L455 820 Q540 740 625 820 L625 1200 Z" fill="#000" />
      {doors.map((d) => (
        <SideDoor key={d.label} {...d} />
      ))}
    </g>
  </svg>
);
