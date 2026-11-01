# Ramayan story Shorts

Three ready-made vertical videos (1080×1920, 9:16) with Hindi voiceover:

| File | Story | Length |
|---|---|---|
| `hanuman_short.mp4` | हनुमान जी की लंका छलाँग (Hanuman's leap to Lanka) | 53 s |
| `gilahri_short.mp4` | गिलहरी और राम सेतु (The squirrel and Ram Setu) | 44 s |
| `shabari_short.mp4` | शबरी के बेर (Shabari's berries) | 45 s |

**Editing style:** a question hook for the first 3 seconds, captions that show 2–3 words at a time with the spoken word in yellow, a zoom punch and whoosh on every cut, a slow zoom and pan on each background, flash, shake and boom on the climax, drums that speed up (in the Hanuman video), and a "follow" call to action at the end.

## Re-make or change a video

```bash
pip install numpy pillow soundfile kokoro-onnx
python3 video/ramayan/make_short.py video/ramayan/stories/hanuman.json
python3 video/ramayan/make_short.py video/ramayan/stories/hanuman.json --preview   # still frames only, fast
```

On the first run it downloads the offline Hindi voice model (about 350 MB, into `.models/`) and the fonts (into `fonts/`). It also needs `ffmpeg`.

- **Change the words:** edit `lines` in `stories/<story>.json`. Each line is spoken and captioned.
- **Change the voice:** set `"voice"` to `hm_omega` or `hm_psi` (male) or `hf_alpha` or `hf_beta` (female). `"speed"` sets how fast it speaks.
- **Use your own pictures:** put `1.jpg`, `2.jpg` and so on (one per scene, in scene order) in `assets/<story>/`, for example `assets/hanuman/1.jpg`. These replace the drawn backgrounds and keep all the zoom and caption effects.
- **Your own voice recording:** not wired in yet.

## Source notes
- Hanuman: Kishkindha Kand (end) and Sundar Kand, Valmiki Ramayan.
- Squirrel: a folk and South Indian tradition, not in the Valmiki Ramayan.
- Shabari: in Valmiki she offers fruits to Ram. The tasted berries come from later devotional tradition.
