#!/usr/bin/env python3
"""Render video/scenes.json to an MP4.

Usage:  python3 video/make_video.py [scenes.json] [output.mp4]
Needs:  Python 3 with Pillow, and ffmpeg on PATH.

scenes.json uses the same format as the browser editor (editor.html ->
"Scene data (JSON)"), so you can edit in either place. For a "photo" scene,
set "image" to a file path relative to scenes.json.
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "scenes.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "claude_intro.mp4")
FPS = 30
SIZES = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1080, 1080)}
PALETTES = {
    "cream": dict(bg="#FAF7F2", ink="#1F1E1D", muted="#6E6962", accent="#CC785C"),
    "night": dict(bg="#14161B", ink="#F2EFE9", muted="#9A968F", accent="#E3A46F"),
    "ocean": dict(bg="#0F2A3D", ink="#F4F7FA", muted="#9FB3C2", accent="#5FC2B8"),
    "paper": dict(bg="#FFFFFF", ink="#141414", muted="#5F5F5F", accent="#2F5BEA"),
}
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu/", "/Library/Fonts/", "C:/Windows/Fonts/"]

def font(names, size):
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, int(size))
    return ImageFont.load_default()

def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def ease(t):
    return 1 - (1 - min(max(t, 0), 1)) ** 3

def wrap(d, text, f, max_w):
    out, line = [], ""
    for w in str(text).split():
        test = (line + " " + w).strip()
        if d.textlength(test, font=f) > max_w and line:
            out.append(line); line = w
        else:
            line = test
    out.append(line)
    return out

def main():
    P = json.load(open(SRC, encoding="utf-8"))
    W, H = SIZES.get(P.get("aspect", "16:9"), SIZES["16:9"])
    u = min(W, H) / 720
    pal = dict(PALETTES.get(P.get("palette", "cream"), PALETTES["cream"]))
    if P.get("accent"): pal["accent"] = P["accent"]
    BG, INK, MUTED, ACC = (rgb(pal[k]) for k in ("bg", "ink", "muted", "accent"))
    serif = P.get("font", "serif") == "serif"
    HEAD = ["DejaVuSerif-Bold.ttf", "georgiab.ttf", "Georgia Bold.ttf"] if serif else ["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"]
    BODY = ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf"]
    scenes = P["scenes"]; total = sum(float(s["dur"]) for s in scenes)
    portrait = H > W

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if P.get("music", True):
        cmd += ["-f", "lavfi", "-i", "sine=frequency=220:sample_rate=44100", "-f", "lavfi", "-i", "sine=frequency=330:sample_rate=44100",
                "-filter_complex", "[1][2]amix=inputs=2,volume=0.04,tremolo=f=0.25:d=0.6[a]", "-map", "0:v", "-map", "[a]", "-shortest", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    gi = 0
    for s in scenes:
        dur = float(s["dur"]); lines = [l for l in s.get("lines", []) if l.strip()]
        anim = s.get("anim", "rise"); layout = s.get("layout", "list")
        A = (lambda k, t: 1) if anim == "none" else (lambda k, t: ease((t - k) * 1.5))
        photo = None
        if s.get("image") and not str(s["image"]).startswith("("):
            ip = os.path.join(os.path.dirname(os.path.abspath(SRC)), s["image"])
            if os.path.exists(ip): photo = Image.open(ip).convert("RGB")
        for f in range(int(round(dur * FPS))):
            t = f / FPS
            im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
            def spark(cx, cy, r):
                for k in range(8):
                    a = t * 0.6 + k * math.pi / 4; L = r * (1 if k % 2 == 0 else .65) * ease(t * 1.5)
                    d.line([(cx, cy), (cx + L * math.cos(a), cy + L * math.sin(a))], fill=ACC, width=max(3, int(r / 6)))
            if layout == "photo":
                if photo:
                    sc = max(W / photo.width, H / photo.height) * (1 + 0.04 * t / max(dur, 1))
                    ph = photo.resize((int(photo.width * sc), int(photo.height * sc)))
                    im.paste(ph, ((W - ph.width) // 2, (H - ph.height) // 2))
                grad = Image.linear_gradient("L").resize((W, H)).point(lambda v: max(0, (v - 115)) * 1.4)
                im.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), grad); d = ImageDraw.Draw(im)
                mx = (56 if portrait else 90) * u
                fh, fb = font(HEAD, 60 * u), font(BODY, 30 * u)
                hl = wrap(d, s.get("heading", ""), fh, W - 2 * mx); sub = [w for l in lines for w in wrap(d, l, fb, W - 2 * mx)]
                y = H - (110 if portrait else 70) * u - len(sub) * 42 * u - (len(hl) - 1) * 68 * u
                for i, l in enumerate(hl): d.text((mx, y + i * 68 * u), l, font=fh, fill=mix((0, 0, 0), (255, 255, 255), A(0, t)), anchor="ls")
                by = y + (len(hl) - 1) * 68 * u + 22 * u; d.rectangle([mx, by, mx + 160 * u * ease(t), by + 5 * u], fill=ACC)
                for i, l in enumerate(sub): d.text((mx, by + 48 * u + i * 42 * u), l, font=fb, fill=mix((0, 0, 0), (230, 230, 230), A(.5 + i * .3, t)), anchor="ls")
            elif layout == "title":
                fh, fb = font(HEAD, 84 * u), font(BODY, 34 * u)
                hl = wrap(d, s.get("heading", ""), fh, W - 120 * u); sub = [w for l in lines for w in wrap(d, l, fb, W - 120 * u)]
                y = (H - ((150 * u if P.get("logo", True) else 0) + len(hl) * 92 * u + len(sub) * 46 * u + 20 * u)) / 2
                if P.get("logo", True): spark(W / 2, y + 60 * u, 60 * u); y += 150 * u
                for i, l in enumerate(hl): d.text((W / 2, y + 70 * u + i * 92 * u), l, font=fh, fill=mix(BG, INK, A(0, t)), anchor="ms")
                y += len(hl) * 92 * u + 20 * u
                for i, l in enumerate(sub): d.text((W / 2, y + 30 * u + i * 46 * u), l, font=fb, fill=mix(BG, MUTED, A(.6 + i * .3, t)), anchor="ms")
            else:
                mx, top = (56 if portrait else 160) * u, (150 if portrait else 110) * u
                if P.get("logo", True): spark(mx + 28 * u if portrait else 110 * u, top - 90 * u if portrait else top, 28 * u)
                fh, fb = font(HEAD, 50 * u), font(BODY, 34 * u)
                hl = wrap(d, s.get("heading", ""), fh, W - mx - 40 * u)
                for i, l in enumerate(hl): d.text((mx, top + i * 58 * u), l, font=fh, fill=INK, anchor="lm")
                ul = top + (len(hl) - 1) * 58 * u + 40 * u
                d.rectangle([mx, ul, mx + 220 * u * ease(t), ul + 5 * u], fill=ACC)
                y = ul + 90 * u
                for i, l in enumerate(lines):
                    a = A(.5 + i * .6, t); off = (1 - a) * 30 * u if anim == "rise" else 0
                    for j, w in enumerate(wrap(d, l, fb, W - mx - 40 * u - off)):
                        d.text((mx + off + (32 * u if j else 0), y), w, font=fb, fill=mix(BG, INK, a), anchor="ls"); y += 46 * u
                    y += 24 * u
            fade = min(1, t / 0.4, (dur - t) / 0.4)
            if fade < 1: im = Image.blend(Image.new("RGB", (W, H), BG), im, max(fade, 0))
            d = ImageDraw.Draw(im)
            if P.get("watermark"):
                d.text((W - 28 * u, H - 26 * u), P["watermark"], font=font(BODY, 20 * u), fill=MUTED, anchor="rs")
            if P.get("bar", True):
                d.rectangle([0, H - 6 * u, W * gi / (total * FPS), H], fill=ACC)
            gi += 1
            p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
