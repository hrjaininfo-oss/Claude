import React from 'react';
import { C } from '../theme';

/** Silhouette of an old ancestral haveli: chhatris, arches and jharokhas (1600 px wide). */
export const Haveli: React.FC<{ x: number; y: number; scale?: number }> = ({ x, y, scale = 1 }) => {
  const W = 1600;
  const arches = [0, 1, 2, 3, 4, 5, 6];
  return (
    <svg
      width={W * scale}
      height={1000 * scale}
      viewBox={`0 0 ${W} 1000`}
      style={{ position: 'absolute', left: x, top: y, overflow: 'visible' }}
    >
      <defs>
        <linearGradient id="hav" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0d1018" />
          <stop offset="1" stopColor="#05060a" />
        </linearGradient>
      </defs>
      <g fill="url(#hav)">
        {/* chhatris (domed kiosks) */}
        {[220, 800, 1380].map((cx, i) => (
          <g key={cx}>
            <path d={`M${cx - 70} 250 Q${cx} ${i === 1 ? 120 : 160} ${cx + 70} 250 Z`} />
            <rect x={cx - 4} y={i === 1 ? 90 : 130} width={8} height={40} />
            <rect x={cx - 80} y={250} width={160} height={18} />
            <rect x={cx - 70} y={268} width={14} height={60} />
            <rect x={cx + 56} y={268} width={14} height={60} />
          </g>
        ))}
        {/* upper storey */}
        <rect x={60} y={320} width={1480} height={260} />
        {/* parapet */}
        {new Array(37).fill(0).map((_, i) => (
          <rect key={i} x={60 + i * 40} y={300} width={22} height={24} />
        ))}
        {/* lower storey */}
        <rect x={0} y={580} width={W} height={420} />
        <rect x={-20} y={570} width={W + 40} height={18} />
      </g>
      {/* jharokha windows on upper storey (all dark) */}
      {arches.map((i) => (
        <path
          key={`w${i}`}
          d={`M${150 + i * 210} 540 L${150 + i * 210} 430 Q${200 + i * 210} 370 ${250 + i * 210} 430 L${250 + i * 210} 540 Z`}
          fill="#020203"
          stroke="#161a24"
          strokeWidth={4}
        />
      ))}
      {/* lower arcade */}
      {arches.map((i) =>
        i === 3 ? null : (
          <path
            key={`a${i}`}
            d={`M${130 + i * 210} 1000 L${130 + i * 210} 760 Q${200 + i * 210} 660 ${270 + i * 210} 760 L${270 + i * 210} 1000 Z`}
            fill="#010102"
          />
        ),
      )}
      {/* main gate (centre) */}
      <path d="M690 1000 L690 720 Q800 590 910 720 L910 1000 Z" fill="#000" stroke="#1d1a14" strokeWidth={10} />
      <rect x={692} y={720} width={4} height={280} fill={C.woodDark} />
    </svg>
  );
};

/** Bare tree silhouette for roadside framing. */
export const DeadTree: React.FC<{ x: number; y: number; h: number; flip?: boolean }> = ({ x, y, h, flip }) => (
  <svg
    width={h * 0.7}
    height={h}
    viewBox="0 0 350 500"
    style={{ position: 'absolute', left: x, top: y - h, transform: flip ? 'scaleX(-1)' : undefined }}
  >
    <g stroke="#020305" strokeLinecap="round" fill="none">
      <path d="M175 500 L170 300 L150 180 L120 80" strokeWidth={26} />
      <path d="M170 300 L240 200 L300 150" strokeWidth={16} />
      <path d="M155 210 L80 160 L30 150" strokeWidth={12} />
      <path d="M240 200 L250 110 L230 40" strokeWidth={9} />
      <path d="M150 180 L190 90" strokeWidth={9} />
      <path d="M120 80 L90 30" strokeWidth={6} />
      <path d="M80 160 L60 100" strokeWidth={6} />
    </g>
  </svg>
);
