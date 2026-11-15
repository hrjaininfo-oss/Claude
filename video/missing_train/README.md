# रहस्यमयी ट्रेन – THE MISSING TRAIN

A cinematic Hindi short film, about 7 minutes long, 1920×1080 (16:9) with letterbox bars. Everything is made in code: the drawings, the animation, the voices, the music and the sound effects.

**File:** `missing_train.mp4`

## What is in it

| # | Scene | What you see and hear |
|---|---|---|
| — | Title | Rain, a far-off headlight in the fog, thunder, a distant whistle |
| 1 | The midnight announcement | An empty station (धुंधगढ़) in the rain, the station clock at 11:45, Aarav on the bench, the "platform number 2" announcement over an old loudspeaker, then the lights go out with thunder |
| 2 | The train in the fog | A headlight grows out of the fog, an old black steam train pulls in and brakes, and the station master runs up with a lantern |
| 3 | The little girl | The door slides open by itself to show the girl with a glowing red toy train. Aarav steps in and the door slams shut |
| 4 | No driver | Empty, flickering carriages and a driver's cab with no one inside: the lever moves by itself and the gauges twitch. Then the train announces "यात्री आरव शर्मा!" |
| 5 | Childhood outside the window | The night outside turns into his childhood home with his mother at the chulha. A memory of him playing with her. Aarav's tear |
| 6 | The newspaper | The camera pushes in from the headline to the photo, and the girl in the photo has the toy train, which glows red. Then she is standing behind him, lit blue, and speaks with an echo |
| 7 | The last chance | A screech and a jolt, the station outside, the station master shouting, Aarav jumps down |
| 8 | Who was the girl? | The train pulls away with one window glowing red. The station master's old photograph of his daughter |
| 9 | Home | Dawn, the door opens, Aarav and his mother embrace, the narrator's closing words, and the final message card |

**Voices** (offline Kokoro Hindi TTS):

- Narrator: deep male.
- आरव: young male.
- स्टेशन मास्टर: old, deep.
- बच्ची: a child's voice. In the reveal it echoes like a ghost.
- माँ: female.
- Station and train announcements: an old loudspeaker sound with echo.

**Editing:**

- Cuts and crossfades, dips to black between scenes, and lightning flashes.
- Camera push-ins and pans, handheld drift, and a jolt shake.
- Letterbox (2.4:1), colour grading for each scene (cold night, warm lamp light, sepia memory, dawn), film grain and a vignette.

**Mix:**

- Stereo. Rain and train ambience are wide; voices are in the centre.
- Effects follow the action: the train arrives from right to left and leaves to the right, the station master runs in from the left, and the far-off train crosses the frame in the epilogue.
- Music and ambience drop under the dialogue.
- Mastered to −14 LUFS (the YouTube/streaming standard) with a −1.5 dBTP true-peak limit.

**Subtitles:** Hindi, in the bottom letterbox bar, with each speaker's name in their own colour.

**Sound:**

- Wet footsteps, a lantern creak, a heartbeat that speeds up, reversed swells into each reveal, cinematic hits.
- Rain, thunder (near and far), a clock ticking, the train's rumble and rail clacks, steam puffs, the whistle, brakes, the door slam, a sting on each reveal, and morning birds.
- Music: a dark drone and a heartbeat for the mystery, and a sad piano theme in D minor for the memories.
- At the end, a warm piano theme in D major.

## Re-make or change it

```bash
pip install numpy pillow soundfile kokoro-onnx
python3 video/missing_train/make_film.py                 # full film (about 15–25 min on 4 cores)
python3 video/missing_train/make_film.py --preview       # still frames of every shot, into .preview/
python3 video/missing_train/make_film.py --shots 7,8     # only some shots, as a short clip
```

It reuses the voice model and fonts of `video/ramayan` (downloaded on the first run) and needs `ffmpeg`.

Everything about the film is in `story.json`, one entry per shot:

- **Dialogue:** `lines`. A plain line is the narrator. To give a line to a character, write `{"by": "aarav", "text": "..."}`. The speakers are `aarav`, `master`, `girl`, `mother`, `announce`, `train` and `news`.
  - `say` changes what is spoken without changing the subtitle (for example, numbers: subtitle `2`, spoken `दो`).
  - `gap` is the pause after a line. `wait` is a pause before it.
  - `"fx": "ghost"` adds the echo.
- **Timing references:** `"L2"` means the start of line 2 and `"L2e"` its end. `"end-3"` means 3 s before the shot ends. Offsets such as `"L1+0.5"` work too.
- **Characters:** `chars`. Each has a `pose` and a `face` (`r` or `l`).
  - Position: `X`/`Z` in metres on the platform and carriage sets, or `x`/`y`/`h` in pixels on the other sets.
  - `keys` makes a character move, `poses` changes the pose at a set time, and `show` makes them appear or disappear.
  - Poses: `stand`, `walk`, `run`, `sit`, `sit_sad`, `reach`, `shout`, `lantern`, `lantern_shout`, `hold`, `photo`, `read`, `hug`, `cook`, `clap`, `stumble`, `back`, `back_walk`.
- **Camera:** `cam` is a list of `[time, zoom, x, y]`. `shake` and `jolts` shake the picture.
- **Look:**
  - `rain` and `fog` set how much rain and fog there is (0–1).
  - `grade` sets the colour: `night`, `cold`, `warm`, `sepia`, `dawn`.
  - `flash` adds lightning, and `fade_in`/`fade_out` fade from or to black.
  - `cards` adds text on screen.
- **Sound:**
  - `amb` sets the ambience: `rain`, `rain_in`, `rumble`, `cab`, `tick`, `birds`, `wind`.
  - `music` sets the music: `drone`, `heart`, `tension`, `sad`, `warm`.
  - `sfx` is a list of `[name, time, volume, pan]`. The pan is −1 (left) to 1 (right), or `[from, to]` to sweep. The names are in `sound.py`.
- **Transitions:** `xfade` crossfades from the previous shot, in seconds.

The files:

- `figures.py` draws the characters.
- `sets.py` draws the locations.
- `sound.py` makes the music and effects.
- `make_film.py` puts it all together.

## Change from the script

The script says "रात के 12 बजे हैं", but the station clock shows 11:45. So the narrator says "रात के बारह बजने को हैं" (it is almost midnight), and the clock line says "ग्यारह बजकर पैंतालीस मिनट". All other dialogue is exactly as written.
