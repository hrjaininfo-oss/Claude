# Room No. 4 — 90 s vertical horror short (Remotion)

1080×1920, 30 fps, 90 s, with voices, sound effects and music. Coloured 2D characters with real faces, expressions,
blinking, lip-sync to the voice track, walk cycles and posable arms. 28 shots edited with cuts, whips, flashes and crash zooms.

## Make the video

```bash
npm install
pip install numpy scipy soundfile kokoro-onnx      # for the sound
python3 audio/build_audio.py                       # voices + SFX + music + lip-sync data
npm run studio                                     # preview and scrub
npm run render                                     # → out/room4.mp4
```

- The first `build_audio.py` run downloads the offline Hindi voice model (about 350 MB) into `audio/.models/`. It also needs `ffmpeg`.
- If Remotion can't download its headless Chrome, point it at a local one: `REMOTION_BROWSER=/path/to/chrome-headless-shell npm run render`.

## How it fits together

| File | What it does |
|---|---|
| `src/story.json` | **The script.** Each dialogue line: start/end, speaker, Hinglish subtitle text, Devanagari text for the voice, and style (`aside`, `whisper`, `glitch`). Also titles, story beats (knocks, door push, black-out) and walk timings for footsteps. Both the video and the audio read this file. |
| `audio/build_audio.py` | Builds `public/audio/dialogue.mp3`, `sfx.mp3`, `music.mp3` (plus `mix.mp3`) and `src/generated/lipsync.json` |
| `src/shots/act1.tsx` … `act3.tsx` | The edit: every shot with its time range, incoming transition and camera move |
| `src/rig/Character.tsx` | The character rig: front, side and back views, expressions, auto-blink, lip-sync, walk cycle, arms holding props, half-lit lighting |
| `src/rig/looks.ts` | How Rahul, Karan and Vikram look (skin, hair, clothes, glasses, mustache, shawl) |
| `src/sets/sets.tsx` | Night sky, road with car, haveli, scrolling corridor, guest room, dusty room and the 1987 photo |
| `src/components/fx.tsx` | Camera moves and shake, flicker, torch beam, dust, grain, vignette, glitch |

## Shot list

| Time | Shot | Sound |
|---|---|---|
| 0:00 | Door 4 close-up, three knocks, a shadow passes under the door, title types on | Knocks, low boom, music-box lullaby |
| 0:08 | Car on the dirt road (moving background and trees) | Engine, gravel, wind, crickets |
| 0:11.5 | Haveli wide, car pulls in, headlights off, Vikram at the gate with a lantern | Skid, car doors, footsteps |
| 0:13.6 | Vikram waves: "Aa gaye tum dono? Bahut saal ho gaye." | Voice + lip-sync |
| 0:16.5 | Two-shot: Karan leans in and whispers, Rahul's eyes shift | Whispered aside |
| 0:20 | Side tracking shot: Vikram leads with the lantern, all three walking | Footsteps in step with the walk |
| 0:24.5 | Vikram close-up at Room 4: the warning | Low boom, creak |
| 0:28.2 | Rahul close-up: "Kyun? What's inside?" | |
| 0:30 | Vikram walks away and the light leaves with him | Footsteps fading |
| 0:32 | 2:13 AM clock | Ticks |
| 0:35.5 | Both asleep, three knocks, Karan's eyes open | Knocks, room tone |
| 0:40 | Feet shadow under the door: "Rahul… Karan…" | Ghost whisper (left/right) |
| 0:44.2 | Karan bolts upright: "Tune suna?" | Boom, breathing, heartbeat |
| 0:48 | Dark corridor: Rahul with phone torch, Karan clutching him | Wooden floor creaks, heartbeat speeding up |
| 0:52 | Torch POV: whisper "Rahul…" stops at door 4 | Riser |
| 0:56 | Handle rattles (extreme close-up) | Metal rattle, then sudden silence |
| 0:59 | Karan: "Mat khol, Rahul!" | |
| 1:01.4 | Rahul profile, reaching for the door | Silence |
| 1:02.4 | Door creaks open into black | Long creak |
| 1:05 | Torch sweeps the empty room | Room tone |
| 1:10.5 | Photo found: the same three faces in sepia | Boom + string stinger |
| 1:14 | Crash zoom on "1987" | Whoosh + hit |
| 1:16.4 | Faces lit from below: "Yeh… hum hain?" | Dissonant strings |
| 1:20 | They turn their heads towards a sound behind them | Floorboard creak |
| 1:21.2 | Vikram in the doorway, half his face in shadow | Sub drop |
| 1:23.5 | Vikram extreme close-up: "Tum log wapas aa gaye." | Glitched voice |
| 1:26.8 | Torch flickers, cutting between the friends and Vikram | Electrical buzz |
| 1:27.9 | Black, then "Part 2?" | Silence, then final hit and lullaby |

## Changing things

- **Words or timing:** edit `src/story.json`, run `python3 audio/build_audio.py`, then render. Subtitles and mouth movement follow the new voice automatically.
- **Your own voiceover or music:** replace `public/audio/dialogue.mp3` or `music.mp3` (keep the 90 s length), or set a stem's `src` to `null` in `src/timeline.ts`. If you replace the dialogue, keep each line at the same start time: the mouths still move to the generated voice timing in `src/generated/lipsync.json`.
- **Voices:** set them under `voices` in `story.json` (`hm_omega` or `hm_psi` for male, `hf_alpha` or `hf_beta` for female), with `speed` and `pitch` in semitones.
- **Rig preview:** the `RigTest` and `FaceTest` compositions in Studio show every view and expression.

Fonts (Special Elite, Caveat, Inter; SIL OFL) are in `public/fonts/`. All the sound is generated by `build_audio.py`, so there are no third-party audio files.
