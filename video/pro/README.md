# Meet Claude — professional cut

A 62.5-second 1080p explainer, edited to a 96 BPM music grid (every cut lands on a bar line, 2.5 s).

**Output:** `video/claude_intro_pro.mp4` (1920×1080, 30 fps, H.264 + AAC, mastered to −16 LUFS)

## Edit decision list

| Time | Scene | Look | Transition in | Sound |
|---|---|---|---|---|
| 0:00 | Cold open: *Notices. Reconciliations. Drafts. Deadlines.* → *What if you had a thinking partner for all of it?* | Dark | — | Beat-synced hits, riser |
| 0:05 | Logo reveal: spark draws on, wordmark rises | Light | Diagonal accent band wipe | Impact + music drop |
| 0:10 | What is Claude: kinetic statement + three traits | Light | Zoom-through | Whoosh |
| 0:17.5 | 01 — What it does: five capability cards | Light | Whip pan with motion blur | Whoosh, card pops |
| 0:27.5 | 02 — In a CA practice: chat demo (notice summary) | Dark | Iris (circle) wipe | Music breaks down, typing |
| 0:40 | 03 — Spot the gaps: GSTR-3B vs 2B reconciliation | Light | Push up | Music returns, row pops |
| 0:47.5 | Use it where you work: claude.ai / Claude Code / API | Dark | Straight accent wipe | Whoosh |
| 0:52.5 | Workflow: context → ask → verify; *You stay the expert.* | Light | Dip | Step pops |
| 0:57.5 | End card: claude.ai | Dark | Hard cut on the bar | Impact + bell, fade |

The demo and the reconciliation figures are illustrative and are labelled that way on screen.

## Rebuild

Needs Node with Playwright (Chromium), Python 3 with numpy, and ffmpeg.

```bash
node video/pro/render.js            # picture: renders every frame of composition.html
python3 video/pro/audio.py          # score + sound effects (original, synthesised)
bash video/pro/mix.sh               # mix, master to -16 LUFS, mux -> video/claude_intro_pro.mp4
node video/pro/render.js --frames 6.8,30 --out /tmp/stills   # check single frames
```

To change text, timing or animation, edit `composition.html` (each scene's timing is in `seek()`; scene windows are in `RANGES`). Fonts: Instrument Serif (in `fonts/`, SIL Open Font License), Inter Display / Inter, JetBrains Mono.
