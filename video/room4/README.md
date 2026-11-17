# Room No. 4 — 90 s vertical horror short (Remotion)

1080×1920, 30 fps, 90 s. Dark illustrated style (silhouettes and shadows only), burned-in Hinglish subtitles, **no audio** (tracks are left empty for your music and voiceover).

## Run

```bash
npm install
npm run studio          # live preview / scrub in the browser
npm run render          # → out/room4.mp4
npm run still -- --frame=2220   # single frame (here 1:14, the "1987" close-up)
```

If Remotion can't download its own headless Chrome (offline / firewalled machine), point it at a local one:

```bash
REMOTION_BROWSER=/path/to/chrome-headless-shell npm run render
```

## Where things live

| File | What it controls |
|---|---|
| `src/timeline.ts` | **All timings**: scene start/end, every subtitle line, on-screen titles, story beats (knocks, door push, black-out), audio slots |
| `src/Room4.tsx` | Assembles scenes → vignette + grain → titles → subtitles → audio |
| `src/scenes/Scene1Hook.tsx` … `Scene7Twist.tsx` | One component per scene |
| `src/components/fx.tsx` | Camera (push/pan/shake), flicker, torch darkness, dust, grain, vignette, glitch |
| `src/components/props.tsx` | Silhouettes, Room 4 door (shaking handle, swing-open), lantern, corridor |
| `src/components/haveli.tsx` | Haveli and tree silhouettes |
| `src/components/text.tsx` | Subtitle styles (dialogue / whisper / sfx / glitch), typewriter titles, audio tracks |

Each scene is also registered as its own composition (`Scene1-hook` … `Scene7-twist`) for quick previewing in Studio.

| Scene | Time | Shots |
|---|---|---|
| 1 Hook | 0:00–0:08 | Door close-up, three knocks shake it, typewriter "Never open room number 4." |
| 2 Arrival | 0:08–0:20 | Headlights on dirt road → haveli with single lantern, Vikram at gate, Karan whispers |
| 3 Warning | 0:20–0:32 | Corridor walk → stop at door 4, Vikram walks away and takes the light |
| 4 Night | 0:32–0:48 | 2:13 AM clock insert → dark room, knocks shake camera, feet shadow under door, Karan sits up |
| 5 Door | 0:48–1:05 | Torch-beam POV down corridor → handle rattles, silence, door creaks open |
| 6 Reveal | 1:05–1:20 | Torch sweeps empty room → sepia photo of three men → crash zoom on "1987" |
| 7 Twist | 1:20–1:30 | Vikram half-lit in doorway, glitch on his line, torch flickers, black-out, "Part 2?" |

## Adding audio

Put files in `public/audio/` and set them in `src/timeline.ts`:

```ts
export const AUDIO = {
  music: { src: 'audio/bg-music.mp3', volume: 0.6 },
  voiceover: { src: 'audio/voiceover.wav', volume: 1 },
  sfx: [{ src: 'audio/knock.wav', startAt: 1.4 }],
};
```

Story beats in `BEATS` (e.g. `hookKnocks: [1.4, 2.1, 2.8]`, `doorPushOpen: 62.4`) give you the exact SFX timings. If the voiceover is paced differently, move the matching `SUBTITLES` lines.

Fonts (Special Elite, Caveat, Inter; SIL OFL) are bundled in `public/fonts/`.
