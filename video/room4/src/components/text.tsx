import React from 'react';
import { AbsoluteFill, Audio, Sequence, interpolate, random, staticFile, useCurrentFrame } from 'remotion';
import { FONT_SUB, FONT_TITLE } from '../fonts';
import { AUDIO, TITLES, sec } from '../timeline';
import story from '../story.json';
import { LINES } from '../time';
import { SPEAKER_COLOR as SC } from '../rig/looks';

type SubtitleStyle = 'dialogue' | 'whisper' | 'sfx' | 'glitch' | 'aside';
type Subtitle = { start: number; end: number; speaker?: string; text: string; style?: SubtitleStyle };
const NAMES: Record<string, string> = { vikram: 'Vikram', rahul: 'Rahul', karan: 'Karan' };
/** Subtitles follow the real voice timing (from lipsync.json), held a little after the voice ends. */
const SUBTITLES: Subtitle[] = story.lines.map((l) => {
  const real = LINES.find((x) => x.id === l.id);
  const end = Math.min(l.end, (real?.end ?? l.end) + 0.6);
  return { start: l.start, end, speaker: NAMES[l.speaker], text: l.text, style: (l as { style?: SubtitleStyle }).style ?? 'dialogue' };
});
const ON_SCREEN_TEXT = TITLES;
import { GlitchLayer } from './fx';

const SPEAKER_COLOR: Record<string, string> = { Vikram: SC.vikram, Rahul: SC.rahul, Karan: SC.karan };

const SubtitleCard: React.FC<{ sub: Subtitle }> = ({ sub }) => {
  const frame = useCurrentFrame(); // local to the subtitle's Sequence
  const len = sec(sub.end - sub.start);
  const style = sub.style ?? 'dialogue';
  const appear = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: 'clamp' });
  const fade = interpolate(frame, [len - 6, len], [1, 0], { extrapolateLeft: 'clamp' });
  const opacity = Math.min(appear, fade);
  const pop = interpolate(frame, [0, 6], [0.92, 1], { extrapolateRight: 'clamp' });

  const isSfx = style === 'sfx';
  const isWhisper = style === 'whisper' || style === 'aside';
  const isGlitch = style === 'glitch';

  const glitchAmount = isGlitch ? (random(`gsub-${Math.floor(frame / 4)}`) > 0.35 ? 1 : 0.15) : 0;

  const card = (
    <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 420 }}>
      <div style={{ maxWidth: 920, textAlign: 'center', transform: `scale(${pop})` }}>
        {sub.speaker && (
          <div
            style={{
              display: 'inline-block',
              fontFamily: FONT_SUB,
              fontWeight: 800,
              fontSize: 30,
              letterSpacing: 4,
              textTransform: 'uppercase',
              color: '#0a0a0a',
              background: SPEAKER_COLOR[sub.speaker] ?? '#ddd',
              padding: '4px 14px',
              borderRadius: 6,
              marginBottom: 14,
              opacity: 0.92,
            }}
          >
            {sub.speaker}
          </div>
        )}
        <div
          style={{
            fontFamily: isSfx ? FONT_TITLE : FONT_SUB,
            fontWeight: isSfx ? 400 : 800,
            fontStyle: isWhisper ? 'italic' : 'normal',
            fontSize: isSfx ? 46 : isWhisper ? 54 : 60,
            lineHeight: 1.18,
            color: isSfx ? '#bdb6a8' : isWhisper ? '#d8d2e8' : isGlitch ? '#ffe9e9' : '#ffffff',
            letterSpacing: isSfx ? 3 : 0,
            textShadow:
              '0 0 6px rgba(0,0,0,1), 0 3px 0 rgba(0,0,0,0.95), 3px 0 0 rgba(0,0,0,0.9), -3px 0 0 rgba(0,0,0,0.9), 0 -3px 0 rgba(0,0,0,0.9)',
          }}
        >
          {sub.text}
        </div>
      </div>
    </AbsoluteFill>
  );

  return (
    <AbsoluteFill style={{ opacity }}>
      {isGlitch ? (
        <GlitchLayer amount={glitchAmount} seed="subglitch">
          {card}
        </GlitchLayer>
      ) : (
        card
      )}
    </AbsoluteFill>
  );
};

/** All burned-in subtitles, driven entirely by timeline.ts. */
export const Subtitles: React.FC = () => (
  <>
    {SUBTITLES.map((s, i) => (
      <Sequence key={i} from={sec(s.start)} durationInFrames={sec(s.end - s.start)} name={`Sub: ${s.text}`}>
        <SubtitleCard sub={s} />
      </Sequence>
    ))}
  </>
);

/** Typewriter title card (hook line and "Part 2?"). */
const TitleCard: React.FC<{ text: string; len: number; glitch: boolean }> = ({ text, len, glitch }) => {
  const frame = useCurrentFrame();
  const chars = Math.floor(interpolate(frame, [0, Math.min(len * 0.6, text.length * 2.2)], [0, text.length], {
    extrapolateRight: 'clamp',
  }));
  const fade = interpolate(frame, [len - 8, len], [1, 0], { extrapolateLeft: 'clamp' });
  const jitter = (random(`tt-${frame}`) - 0.5) * 2;
  const body = (
    <AbsoluteFill style={{ justifyContent: glitch ? 'center' : 'flex-start', alignItems: 'center', paddingTop: glitch ? 0 : 1180 }}>
      <div
        style={{
          fontFamily: FONT_TITLE,
          fontSize: glitch ? 150 : 76,
          color: glitch ? '#e8e2d6' : '#efe6d4',
          textAlign: 'center',
          maxWidth: 900,
          lineHeight: 1.2,
          transform: `translate(${jitter}px, ${jitter * 0.5}px)`,
          textShadow: '0 0 18px rgba(179,18,27,0.65), 0 0 2px #000, 0 4px 10px #000',
        }}
      >
        {text.slice(0, chars)}
        <span style={{ opacity: chars < text.length && frame % 10 < 5 ? 1 : 0 }}>▌</span>
      </div>
    </AbsoluteFill>
  );
  return (
    <AbsoluteFill style={{ opacity: fade }}>
      {glitch ? <GlitchLayer amount={random(`pt2-${Math.floor(frame / 5)}`) > 0.6 ? 1 : 0.1}>{body}</GlitchLayer> : body}
    </AbsoluteFill>
  );
};

export const OnScreenText: React.FC = () => (
  <>
    {ON_SCREEN_TEXT.map((t, i) => (
      <Sequence key={i} from={sec(t.start)} durationInFrames={sec(t.end - t.start)} name={`Title: ${t.text}`}>
        <TitleCard text={t.text} len={sec(t.end - t.start)} glitch={t.text.startsWith('Part')} />
      </Sequence>
    ))}
  </>
);

/** Audio stems built by audio/build_audio.py. */
export const AudioTracks: React.FC = () => (
  <>
    {AUDIO.dialogue.src && <Audio src={staticFile(AUDIO.dialogue.src)} volume={AUDIO.dialogue.volume} />}
    {AUDIO.sfx.src && <Audio src={staticFile(AUDIO.sfx.src)} volume={AUDIO.sfx.volume} />}
    {AUDIO.music.src && <Audio src={staticFile(AUDIO.music.src)} volume={AUDIO.music.volume} />}
  </>
);
