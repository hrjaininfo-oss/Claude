# Ramayan story Shorts

Three ready-made vertical videos (1080×1920, 9:16) with Hindi voiceover:

| File | Story | Length |
|---|---|---|
| `hanuman_short.mp4` | हनुमान जी की लंका छलाँग (Hanuman's leap to Lanka) | 53 s |
| `gilahri_short.mp4` | गिलहरी और राम सेतु (The squirrel and Ram Setu) | 44 s |
| `shabari_short.mp4` | शबरी के बेर (Shabari's berries) | 45 s |

**Characters (they act out the story as it is narrated):** Hanuman, Shri Ram, Lakshman, Shabari, Jambavan, Rishi Matang and the vanar sena, drawn in code as backlit silhouettes with gold ornaments (crown, necklace, gada) and a rim light. Ram and Hanuman also have a golden aura. Hanuman grows to giant size, then flies across the ocean.

**Editing style:** a question hook for the first 3 seconds, captions that show 2–3 words at a time with the spoken word in yellow, a zoom punch and whoosh on every cut, a slow zoom and pan on each background, flash, shake and boom on the climax, drums that speed up (in the Hanuman video), and a "follow" call to action at the end.

## Re-make or change a video

```bash
pip install numpy pillow soundfile kokoro-onnx
python3 video/ramayan/make_short.py video/ramayan/stories/hanuman.json
python3 video/ramayan/make_short.py video/ramayan/stories/hanuman.json --preview   # still frames only, fast
```

On the first run it downloads the offline Hindi voice model (about 350 MB, into `.models/`) and the fonts (into `fonts/`). It also needs `ffmpeg`.

- **Change the words:** edit `lines` in `stories/<story>.json`. Each line is spoken and captioned.
  - A plain line, such as `"सामने था, सौ योजन का विशाल समुद्र।"`, is read by the narrator.
  - For a character to say a line, write `{"by": "hanuman", "text": "जय श्री राम!"}`. You can also give the character's number in the scene's `chars` list, for example `"by": 2`. That character speaks in their own voice, their mouth moves with the words, and a name tag appears above the caption.
  - Voices are set in `VOICES` in `make_short.py`. Each character has its own pitch and speed: Ram is calm, Hanuman is deep, Jambavan is old and deep, the vanars are lively, Shabari is an old woman, the squirrel is small. A story can override these with `"voices"`, and a character can use another voice, for example `"voice": "vanar2"`.
- **Change the narrator's voice:** set `"voice"` to `hm_omega` or `hm_psi` (male) or `hf_alpha` or `hf_beta` (female). `"speed"` sets how fast it speaks.
- **Characters and what they do:** each scene has a `chars` list. Example:
  `{"who": "ram", "act": ["walk", "bless"], "x": -0.05, "to": 0.37, "move": 0.6, "y": 0.97, "h": 0.38}`
  - `who`: `ram`, `lakshman`, `hanuman`, `vanar`, `jambavan`, `shabari`, `sage` or `squirrel`.
  - `act`: what the character does. Give one action, or a list with one action per narration line, so the movement follows what is being said. Actions:
    - Looping: `idle`, `walk`, `carry_walk`, `sweep`, `laugh`, `point`, `cheer`, `talk`, `eat`, `offer` (kneeling with a bowl), `namaste`, `namaste_bow`, `wait`, `sad`, `sit`, `fly`, `stroke`, and `hop` or `shake` (squirrel only).
    - One-off, timed to the line: `bless` (hand rises), `power` (Hanuman raises his gada), `hesitate` (Lakshman raises a hand), `lift_stroke` (Ram lifts the squirrel, then strokes its back).
  - `x` and `to`: the character walks from `x` to `to` during the first `move` part of the scene (0.6 means 60%), then does its `act`. `move_act` changes the walking action, for example to `sweep` or `hop`.
  - `y` sets where the feet go and `h` sets the height, as fractions of the frame. `flip: true` makes the character face left.
  - `anim`: `grow` (gets bigger from line number `grow_line`) or `fly` (flies across the screen).
- **Use your own pictures:** put `1.jpg`, `2.jpg` and so on (one per scene, in scene order) in `assets/<story>/`, for example `assets/hanuman/1.jpg`. These replace the drawn backgrounds and characters, and keep all the zoom and caption effects.
- **Your own voice recording:** not wired in yet.

## Source notes
- Hanuman: Kishkindha Kand (end) and Sundar Kand, Valmiki Ramayan.
- Squirrel: a folk and South Indian tradition, not in the Valmiki Ramayan.
- Shabari: in Valmiki she offers fruits to Ram. The tasted berries come from later devotional tradition.
