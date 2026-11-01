#!/usr/bin/env python3
"""Make a vertical (9:16, 1080x1920) Ramayan story Short.

Usage:
    python3 video/ramayan/make_short.py video/ramayan/stories/hanuman.json [out.mp4]

What it does:
  * Hindi voiceover with the offline Kokoro TTS model (voice "hm_omega").
  * Shorts-style captions: 2-3 words at a time, the spoken word in yellow,
    each group "pops" in.
  * Hook title for the first 3 seconds, zoom punch on every cut, whoosh SFX,
    flash / shake / boom on the climax, generated tanpura-and-drum music.
  * Animated backgrounds drawn in code. To use your own pictures instead,
    put 1.jpg, 2.jpg ... (one per scene) in video/ramayan/assets/<story>/.

Needs: Python 3, Pillow (with raqm), numpy, soundfile, kokoro-onnx, ffmpeg.
The TTS model (~350 MB) is downloaded once into video/ramayan/.models/.
"""
import hashlib, json, math, os, random, subprocess, sys, urllib.request
import numpy as np
from PIL import ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import character, CYCLE, ONE_SHOT, OX as COX, OY as COY
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, SR = 1080, 1920, 30, 24000
OV = 1.15                                   # background is drawn 15% larger for zoom/pan
BW, BH = int(W * OV), int(H * OV)
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FONT_DIR = os.path.join(HERE, "fonts")
FONT_CAP = os.path.join(FONT_DIR, "NotoSansDevanagari-Black.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "NotoSansDevanagari-Bold.ttf")
FONT_TITLE = os.path.join(FONT_DIR, "RozhaOne-Regular.ttf")
FONT_SRC = {  # Google Fonts (SIL Open Font License), fetched once from the npm registry
    FONT_CAP: ("noto-sans-devanagari", "900Black/NotoSansDevanagari_900Black.ttf"),
    FONT_BOLD: ("noto-sans-devanagari", "700Bold/NotoSansDevanagari_700Bold.ttf"),
    FONT_TITLE: ("rozha-one", "400Regular/RozhaOne_400Regular.ttf"),
}


def ensure_fonts():
    import io, tarfile
    os.makedirs(FONT_DIR, exist_ok=True)
    for dst, (pkg, member) in FONT_SRC.items():
        if os.path.exists(dst): continue
        print("Downloading font", os.path.basename(dst), "...")
        meta = json.load(urllib.request.urlopen(f"https://registry.npmjs.org/@expo-google-fonts/{pkg}"))
        url = meta["versions"][meta["dist-tags"]["latest"]]["dist"]["tarball"]
        with tarfile.open(fileobj=io.BytesIO(urllib.request.urlopen(url).read())) as tf:
            open(dst, "wb").write(tf.extractfile("package/" + member).read())


ensure_fonts()

THEMES = {  # sky top, sky bottom (horizon), sea, silhouette, sun colour
    "night":  ((6, 8, 26), (38, 30, 78), (10, 16, 40), (4, 4, 12), (235, 235, 255)),
    "dusk":   ((44, 18, 60), (255, 128, 64), (60, 30, 60), (24, 10, 22), (255, 214, 120)),
    "storm":  ((30, 36, 52), (120, 128, 150), (34, 44, 62), (8, 10, 14), (200, 200, 210)),
    "gold":   ((40, 12, 0), (196, 104, 18), (60, 24, 4), (30, 10, 0), (255, 220, 140)),
    "fire":   ((30, 0, 0), (255, 96, 10), (70, 12, 4), (20, 2, 0), (255, 230, 150)),
    "dawn":   ((50, 40, 110), (255, 170, 90), (60, 70, 120), (26, 20, 50), (255, 236, 170)),
    "day":    ((40, 110, 200), (250, 200, 140), (30, 90, 150), (30, 30, 40), (255, 244, 200)),
    "forest": ((24, 60, 48), (236, 196, 110), (30, 50, 30), (8, 22, 14), (255, 236, 170)),
    "rain":   ((20, 30, 36), (90, 110, 110), (30, 40, 40), (8, 14, 14), (200, 210, 210)),
    "autumn": ((60, 30, 20), (240, 150, 70), (60, 30, 10), (26, 10, 4), (255, 210, 130)),
}


def ease(t):
    t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3


def back(t):  # overshoot "pop"
    t = min(max(t, 0.0), 1.0); c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


# ---------------------------------------------------------------- voice
def ensure_models():
    d = os.path.join(HERE, ".models"); os.makedirs(d, exist_ok=True)
    for f in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        p = os.path.join(d, f)
        if not os.path.exists(p):
            print("Downloading", f, "...")
            urllib.request.urlretrieve(MODEL_URL + f, p)
    return d


_tts = None
def tts(text, voice, speed):
    global _tts
    cdir = os.path.join(HERE, ".cache"); os.makedirs(cdir, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16]
    cp = os.path.join(cdir, key + ".npy")
    if os.path.exists(cp):
        return np.load(cp)
    if _tts is None:
        from kokoro_onnx import Kokoro
        d = ensure_models()
        _tts = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
    a, sr = _tts.create(text, voice=voice, speed=speed, lang="hi")
    assert sr == SR
    a = np.asarray(a, dtype=np.float32)
    nz = np.where(np.abs(a) > 0.02)[0]          # trim leading/trailing silence
    if len(nz):
        a = a[max(0, nz[0] - 600): nz[-1] + 1800]
    np.save(cp, a)
    return a


# Character voices: Kokoro voice, speed, pitch shift in semitones. A story can override with "voices".
VOICES = {
    "narrator": ("hm_omega", 1.0, 0.0),
    "hanuman":  ("hm_psi", 1.0, -1.5),
    "ram":      ("hm_psi", 0.92, 0.0),
    "lakshman": ("hm_omega", 1.0, 1.5),
    "jambavan": ("hm_omega", 0.9, -4.0),
    "vanar":    ("hm_psi", 1.08, 3.0),
    "vanar2":   ("hm_omega", 1.08, 2.0),
    "sage":     ("hm_omega", 0.88, -3.0),
    "shabari":  ("hf_beta", 0.86, -2.0),
    "squirrel": ("hf_alpha", 1.05, 5.0),
}
NAMES = {"hanuman": "हनुमान", "ram": "श्री राम", "lakshman": "लक्ष्मण", "jambavan": "जाम्बवान", "vanar": "वानर",
         "sage": "ऋषि मतंग", "shabari": "शबरी", "squirrel": "गिलहरी"}
NAME_COL = {"hanuman": (210, 70, 20), "ram": (40, 90, 200), "lakshman": (190, 140, 20), "jambavan": (110, 70, 40),
            "vanar": (40, 140, 70), "sage": (230, 110, 0), "shabari": (130, 60, 150), "squirrel": (20, 140, 150)}


def speak(text, prof):
    """TTS in a character's voice; the pitch shift keeps the speaking speed."""
    voice, speed, st = prof
    r = 2 ** (st / 12)
    a = tts(text, voice, round(min(2.0, max(0.5, speed / r)), 3))
    if st:
        n = int(len(a) / r); a = np.interp(np.arange(n) * r, np.arange(len(a)), a).astype(np.float32)
    return a


def envelope(a):
    """Mouth opening per video frame (0..1) from the loudness of the speech."""
    hop = SR // FPS; n = len(a) // hop + 1
    e = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(a) else 0 for i in range(n)])
    return np.clip(e / (np.percentile(e, 90) + 1e-6), 0, 1)


# ---------------------------------------------------------------- music & sfx
def tone(freq, dur, harm=10, decay=1.5, bright=0.8):
    t = np.arange(int(dur * SR)) / SR
    s = sum((1 / k ** bright) * np.sin(2 * np.pi * freq * k * t * (1 + 0.0007 * k)) for k in range(1, harm + 1))
    return (s * np.exp(-t / decay)).astype(np.float32)


def add(buf, sig, at):
    i = int(at * SR)
    if i >= len(buf): return
    n = min(len(sig), len(buf) - i); buf[i:i + n] += sig[:n]


def kick(dur=0.6, f0=50, f1=140, dec=6.0):
    t = np.arange(int(dur * SR)) / SR
    f = f0 + f1 * np.exp(-t * 22)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * dec)).astype(np.float32)


def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc); y[i] = acc
    return y


def whoosh(dur=0.55, rng=None):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    x = (rng or np.random).standard_normal(n).astype(np.float32)
    y = lowpass(x, 0.02 + 0.35 * np.sin(np.pi * t) ** 2)
    return (y * np.sin(np.pi * t) ** 1.5 * 2.2).astype(np.float32)


def boom(rng):
    k = kick(2.2, 35, 120, 1.8)
    n = rng.standard_normal(len(k)).astype(np.float32)
    nl = lowpass(n, np.full(len(n), 0.04)) * np.exp(-np.arange(len(n)) / SR * 2.5) * 3
    return k * 1.4 + nl


def make_music(T, mood, build_at, climax_at, rng):
    out = np.zeros(int(T * SR) + SR, np.float32)
    sa = 130.81                                  # tanpura on C
    pat = [sa * 1.5 / 2, sa, sa, sa / 2]         # Pa Sa Sa Sa(low)
    t, i = 0.0, 0
    while t < T:
        add(out, tone(pat[i % 4], 3.0, 14, 1.6, 0.7) * 0.10, t); t += 0.62; i += 1
    tt = np.arange(len(out)) / SR                # soft pad
    out += (0.025 * (np.sin(2 * np.pi * sa * tt) + 0.6 * np.sin(2 * np.pi * sa * 1.5 * tt))
            * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt))).astype(np.float32)
    scale = [0, 2, 4, 7, 9, 12, 14, 16]          # Bhupali, flute-like line
    t, idx = 1.5, 3
    while t < T - 1:
        if mood == "epic" and build_at <= t < climax_at + 1.5:
            t += 1.0; continue
        idx = int(np.clip(idx + rng.choice([-2, -1, 1, 2]), 0, len(scale) - 1))
        f = 523.25 * 2 ** (scale[idx] / 12); d = rng.choice([1.2, 1.6, 2.4])
        n = np.arange(int(d * SR)) / SR
        env = np.minimum(n / 0.15, 1) * np.exp(-n / (d * 0.6))
        vib = np.sin(2 * np.pi * f * n + 0.004 * f / 5 * np.sin(2 * np.pi * 5 * n))
        add(out, ((vib + 0.25 * np.sin(4 * np.pi * f * n)) * env * 0.045).astype(np.float32), t)
        t += d + rng.choice([0.0, 0.4, 0.8])
    if mood == "epic":                           # heartbeat drums that speed up into the climax
        t = 0.8
        while t < T - 0.5:
            if t < build_at:
                gap, vol = 1.6, 0.18
            elif t < climax_at:
                p = (t - build_at) / max(climax_at - build_at, 0.1)
                gap, vol = 0.55 - 0.33 * p, 0.25 + 0.25 * p
            elif t < climax_at + 4:
                gap, vol = 0.45, 0.35
            else:
                gap, vol = 1.6, 0.12
            add(out, kick() * vol, t)
            if t >= build_at and t < climax_at + 4:
                add(out, tone(196, 0.3, 4, 0.08, 1.2) * vol * 0.5, t + gap / 2)
            t += gap
    return out[:int(T * SR)]


# ---------------------------------------------------------------- drawing helpers
def vgrad(w, h, top, bot, split=None):
    a = np.linspace(0, 1, h)[:, None, None]
    g = np.array(top)[None, None] * (1 - a) + np.array(bot)[None, None] * a
    return Image.fromarray(np.repeat(g, w, 1).astype(np.uint8))


def radial_mask(size, power=2.0):
    y, x = np.mgrid[-1:1:size * 1j, -1:1:size * 1j]
    r = np.clip(1 - np.sqrt(x * x + y * y), 0, 1) ** power
    return Image.fromarray((r * 255).astype(np.uint8))


GLOW = radial_mask(512, 2.2)


def glow(img, cx, cy, r, color, strength=1.0):
    m = GLOW.resize((int(r * 2), int(r * 2)))
    if strength < 1: m = m.point(lambda v: int(v * strength))
    img.paste(Image.new("RGB", m.size, color), (int(cx - r), int(cy - r)), m)


def make_mandala(size=1000, col=(255, 206, 110)):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = size / 2
    rings = [(60, 150, 8, .30), (150, 260, 12, .22), (260, 380, 16, .16), (380, 470, 24, .11)]
    for r0, r1, n, wdt in rings:
        for k in range(n):
            a0 = 2 * math.pi * k / n; pts_l, pts_r = [], []
            for s in np.linspace(0, 1, 18):
                r = r0 + (r1 - r0) * s; off = wdt * math.sin(math.pi * s)
                pts_l.append((c + r * math.cos(a0 - off), c + r * math.sin(a0 - off)))
                pts_r.append((c + r * math.cos(a0 + off), c + r * math.sin(a0 + off)))
            d.line(pts_l + pts_r[::-1] + [pts_l[0]], fill=col + (255,), width=4)
        d.ellipse([c - r1, c - r1, c + r1, c + r1], outline=col + (150,), width=3)
        for k in range(n * 2):
            a = 2 * math.pi * k / (n * 2) + math.pi / (n * 2)
            x, y = c + r1 * math.cos(a), c + r1 * math.sin(a)
            d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=col + (220,))
    d.ellipse([c - 40, c - 40, c + 40, c + 40], outline=col + (255,), width=5)
    g = im.filter(ImageFilter.GaussianBlur(10))
    return Image.alpha_composite(g, im)


def make_rays(size=2200, n=18):
    im = Image.new("L", (size, size), 0); d = ImageDraw.Draw(im); c = size / 2
    for k in range(n):
        a = 2 * math.pi * k / n; w = math.pi / n * 0.45
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a - w), c + c * 1.5 * math.sin(a - w)),
                   (c + c * 1.5 * math.cos(a + w), c + c * 1.5 * math.sin(a + w))], fill=60)
    im = im.filter(ImageFilter.GaussianBlur(18))
    fall = radial_mask(size, 1.0)
    return Image.fromarray((np.asarray(im, np.float32) * np.asarray(fall, np.float32) / 255).astype(np.uint8))


def ridge(rng, w, base, amp, n=6):
    """Jagged mountain line by midpoint displacement."""
    pts = [(0.0, base - rng.uniform(0, amp)), (w * 0.5, base - amp * 1.3), (float(w), base - rng.uniform(0, amp))]
    disp = amp * 0.7
    for _ in range(n):
        new = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            new += [(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + rng.uniform(-disp, disp))]
        pts = new + [pts[-1]]; disp *= 0.55
    return pts


def squirrel(d, x, y, s, col, stripes=None):
    # simple sitting squirrel silhouette facing right, with a big bushy tail
    d.ellipse([x - 40 * s, y - 120 * s, x + 30 * s, y], fill=col)                  # body
    d.ellipse([x + 5 * s, y - 165 * s, x + 65 * s, y - 105 * s], fill=col)          # head
    d.polygon([(x + 18 * s, y - 150 * s), (x + 26 * s, y - 192 * s), (x + 40 * s, y - 155 * s)], fill=col)  # ear
    d.ellipse([x + 55 * s, y - 140 * s, x + 75 * s, y - 128 * s], fill=col)         # nose
    for k in range(26):                                                            # bushy tail curling up behind
        q = k / 25
        cx = x - 45 * s - 70 * s * math.sin(math.pi * q * 0.85) + (40 * s * (q - 0.75) / 0.25 if q > 0.75 else 0)
        cy = y - 15 * s - 230 * s * q
        rr = (18 + 30 * math.sin(math.pi * min(q * 1.2, 1))) * s
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
    d.ellipse([x + 10 * s, y - 30 * s, x + 45 * s, y + 5 * s], fill=col)             # foot
    if stripes:
        for k in (-1, 0, 1):
            d.line([(x - 30 * s, y - 70 * s + k * 16 * s), (x + 18 * s, y - 95 * s + k * 16 * s)], fill=stripes, width=int(7 * s))


def build_static(bg, idx, rng, story_dir):
    """Static (oversized) background for one scene."""
    custom = None
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(HERE, "assets", story_dir, f"{idx + 1}.{ext}")
        if os.path.exists(p): custom = p; break
    if custom:
        ph = Image.open(custom).convert("RGB")
        sc = max(BW / ph.width, BH / ph.height)
        ph = ph.resize((int(ph.width * sc) + 1, int(ph.height * sc) + 1), Image.LANCZOS)
        return ph.crop(((ph.width - BW) // 2, (ph.height - BH) // 2, (ph.width - BW) // 2 + BW, (ph.height - BH) // 2 + BH)), None, True

    top, hor, sea, sil, sunc = THEMES[bg.get("theme", "dusk")]
    el = set(bg.get("el", []))
    hy = int(BH * (0.60 if "sea" in el else 0.70))
    im = vgrad(BW, BH, top, hor); d = ImageDraw.Draw(im, "RGBA")
    fg = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); dfg = ImageDraw.Draw(fg)   # drawn over the waves
    if "stars" in el:
        for _ in range(260):
            x, y, r = rng.uniform(0, BW), rng.uniform(0, hy * 0.85), rng.choice([1.5, 2, 2.5, 3.5])
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, int(rng.uniform(80, 255))))
    if "sun" in el or "moon" in el:
        sx, sy = BW * (0.66 if "moon" in el else 0.5), hy - (BH * 0.33 if "moon" in el else BH * 0.07)
        glow(im, sx, sy, 520, lerp(hor, sunc, 0.6), 0.85); glow(im, sx, sy, 260, sunc, 0.9)
        r = 95 if "moon" in el else 130
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=sunc + (255,))
    if "mountain" in el:
        d.polygon(ridge(rng, BW, hy - 120, 140) + [(BW, BH), (0, BH)], fill=lerp(sil, hor, 0.45) + (255,))
        d.polygon(ridge(rng, BW, hy + 40, 200) + [(BW, BH), (0, BH)], fill=sil + (255,))
    if "sea" in el:
        im.paste(vgrad(BW, BH - hy, lerp(sea, hor, 0.5), sea), (0, hy)); d = ImageDraw.Draw(im, "RGBA")
        if "sun" in el or "moon" in el:  # reflection
            for k in range(26):
                y = hy + 8 + k * 26; w = (k * 9 + 40) * rng.uniform(0.6, 1.3)
                d.rectangle([BW / 2 - w + (BW * 0.16 if "moon" in el else 0), y, BW / 2 + w + (BW * 0.16 if "moon" in el else 0), y + 6],
                            fill=sunc + (int(150 - k * 5),))
    if "cliff" in el:
        pts = [(0, hy - 260), (BW * 0.22, hy - 300), (BW * 0.34, hy - 240), (BW * 0.40, hy + 60), (BW * 0.46, BH), (0, BH)]
        dfg.polygon(pts, fill=sil + (255,))
    if "shore" in el:
        dfg.polygon(ridge(rng, BW, BH * 0.87, 40, 7) + [(BW, BH), (0, BH)], fill=sil + (255,))
    if "bridge" in el:
        for k in range(40, -1, -1):
            dd = (k / 40) ** 1.8; y = hy + 8 + (BH - hy) * dd * 0.95
            half = 20 + BW * 0.30 * dd; n = 5; sw = half * 2 / n
            for j in range(n):
                x = BW / 2 - half + j * sw + rng.uniform(-sw * 0.1, sw * 0.1)
                c = lerp(sil, sea, rng.uniform(0.1, 0.5))
                dfg.ellipse([x, y - sw * 0.28, x + sw * 1.05, y + sw * 0.28], fill=c + (255,))
                if k > 26 and j in (1, 3) and rng.random() < 0.6:
                    f = ImageFont.truetype(FONT_BOLD, int(sw * 0.32))
                    dfg.text((x + sw * 0.52, y), "राम", font=f, fill=(255, 170, 60, 230), anchor="mm")
    if "trees" in el:
        for layer, (base, colt) in enumerate([(hy - 40, lerp(sil, hor, 0.5)), (hy + 120, lerp(sil, hor, 0.25)), (BH * 0.98, sil)]):
            x = rng.uniform(-80, 0) if layer < 2 else BW + 999   # front layer: ground only, so characters stand out
            while x < BW + 80:
                h = rng.uniform(260, 520) * (0.7 + 0.3 * layer); wdt = h * rng.uniform(0.35, 0.5)
                if rng.random() < 0.55:
                    for k in range(4):
                        yy = base - h * (k / 4); ww = wdt * (1 - k / 5)
                        d.polygon([(x - ww / 2, yy), (x + ww / 2, yy), (x, yy - h * 0.4)], fill=colt + (255,))
                else:
                    d.rectangle([x - 12, base - h * 0.5, x + 12, base], fill=colt + (255,))
                    d.ellipse([x - wdt * 0.8, base - h, x + wdt * 0.8, base - h * 0.35], fill=colt + (255,))
                x += wdt * rng.uniform(0.5, 1.0)
            d.rectangle([0, base - 5, BW, BH], fill=colt + (255,)) if layer == 2 else None
    if "path" in el:
        pts_l = [(BW * 0.5 - 30 - 330 * ((y - hy) / (BH - hy)) ** 1.3 + 90 * math.sin(y / 200), y) for y in range(hy, BH, 20)]
        pts_r = [(x + 60 + 660 * ((y - hy) / (BH - hy)) ** 1.3, y) for x, y in pts_l]
        d.polygon(pts_l + pts_r[::-1], fill=lerp(hor, sil, 0.45) + (200,))
    if "hut" in el:
        x, y = BW * 0.68, hy + 150
        d.rectangle([x - 150, y - 170, x + 150, y], fill=lerp(sil, hor, 0.15) + (255,))
        d.polygon([(x - 210, y - 150), (x, y - 330), (x + 210, y - 150)], fill=sil + (255,))
        d.rectangle([x - 40, y - 110, x + 40, y], fill=(255, 190, 90, 220))
    if "berries" in el:
        cx, cy = BW / 2, BH * 0.80
        d.ellipse([cx - 330, cy - 70, cx + 330, cy + 120], fill=(40, 90, 30, 255))      # leaf bowl (dona)
        d.ellipse([cx - 300, cy - 60, cx + 300, cy + 60], fill=(70, 130, 45, 255))
        for k in range(26):
            bx, by = cx + rng.uniform(-240, 240), cy - 10 + rng.uniform(-40, 30) - (k > 16) * 40
            r = rng.uniform(26, 36)
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=(190, 30, 30, 255))
            d.ellipse([bx - r * 0.5, by - r * 0.6, bx - r * 0.1, by - r * 0.25], fill=(255, 140, 140, 200))
    if "squirrel" in el:
        stripes = (255, 236, 180) if bg.get("theme") == "gold" else None
        sx, sy, s = (BW * 0.5, BH * 0.93, 2.0) if "bridge" not in el else (BW * 0.30, BH * 0.86, 1.6)
        if stripes:
            glow(im, sx, sy - 140 * s, 300 * s / 1.6, (255, 220, 140), 0.9); d = ImageDraw.Draw(im, "RGBA")
        squirrel(dfg, sx, sy, s, sil + (255,), stripes)
    return im, (fg if fg.getbbox() else None), False


class Particles:
    def __init__(self, kind, rng, n):
        self.kind = kind
        self.p = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.4, 1.0), rng.uniform(0, 6.28), rng.uniform(0.5, 1.5)) for _ in range(n)]

    def draw(self, d, t):
        for x0, y0, sp, ph, sz in self.p:
            k = self.kind
            if k == "embers":
                y = (y0 - t * 260 * sp) % H; x = x0 + 30 * math.sin(t * 2 * sp + ph); r = 4 * sz
                c = (255, int(120 + 100 * sp), 40, int(200 * sp))
            elif k == "fireflies":
                x = x0 + 60 * math.sin(t * 0.7 * sp + ph); y = y0 * 0.9 + 40 * math.cos(t * 0.5 + ph); r = 4 * sz
                c = (220, 255, 120, int(255 * (0.5 + 0.5 * math.sin(t * 3 * sp + ph))))
            elif k == "rain":
                x = (x0 - t * 200) % W; y = (y0 + t * 1900 * sp) % H
                d.line([(x, y), (x - 10, y + 50 * sp)], fill=(200, 220, 230, 120), width=3); continue
            elif k == "leaves":
                y = (y0 + t * 160 * sp) % H; x = x0 + 90 * math.sin(t * 1.3 * sp + ph); r = 9 * sz
                c = (230, int(110 + 60 * sp), 30, 230)
                d.ellipse([x - r * 1.6, y - r * 0.7, x + r * 1.6, y + r * 0.7], fill=c); continue
            else:  # dust
                y = (y0 - t * 30 * sp) % H; x = x0 + 25 * math.sin(t * 0.6 + ph); r = 2.5 * sz
                c = (255, 230, 170, int(150 * (0.5 + 0.5 * math.sin(t * 2 + ph))))
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)


# ---------------------------------------------------------------- captions
FCAP = ImageFont.truetype(FONT_CAP, 104)
FHOOK = ImageFont.truetype(FONT_TITLE, 92)
FTAG = ImageFont.truetype(FONT_BOLD, 40)
FOUT = ImageFont.truetype(FONT_BOLD, 50)
_cap_cache = {}


def caption_img(words, active):
    key = (tuple(words), active)
    if key in _cap_cache: return _cap_cache[key]
    tmp = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    sp = 26; ws = [tmp.textlength(w, font=FCAP) for w in words]
    lines, cur, cw = [], [], 0             # wrap into max 2 lines
    for i, w in enumerate(ws):
        if cur and cw + sp + w > W - 140: lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += (sp if len(cur) > 1 else 0) + w
    lines.append(cur)
    lh = 150; img = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for li, ln in enumerate(lines):
        tot = sum(ws[i] for i in ln) + sp * (len(ln) - 1); x = (W - tot) / 2; y = 30 + li * lh + lh * 0.62
        for i in ln:
            col = (255, 214, 0) if i == active else (255, 255, 255)
            d.text((x + 6, y + 8), words[i], font=FCAP, fill=(0, 0, 0, 150), anchor="ls", stroke_width=12, stroke_fill=(0, 0, 0, 150))
            d.text((x, y), words[i], font=FCAP, fill=col, anchor="ls", stroke_width=12, stroke_fill=(0, 0, 0))
            x += ws[i] + sp
    _cap_cache[key] = img
    return img


def chunk_words(words, maxc=16, maxw=3):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or len(" ".join(cur + [w])) > maxc): out.append(cur); cur = []
        cur.append(w)
        if w[-1] in ",।!?": out.append(cur); cur = []
    if cur: out.append(cur)
    merged = []                                  # avoid a lonely last word
    for c in out:
        if merged and len(c) == 1 and len(merged[-1]) <= 3 and merged[-1][-1][-1] not in ",।!?":
            merged[-1] = merged[-1] + c
        else:
            merged.append(c)
    return merged


def word_weight(w):
    return len(w.strip(",।!?")) + (6 if w[-1] in ",।!?" else 1)


def pill(d, cx, cy, text, font, fg, bgc, padx=36, pady=18):
    tw = d.textlength(text, font=font); bb = font.getbbox(text)
    h = bb[3] - bb[1]
    d.rounded_rectangle([cx - tw / 2 - padx, cy - h / 2 - pady, cx + tw / 2 + padx, cy + h / 2 + pady + 10], radius=28, fill=bgc)
    d.text((cx, cy + 5), text, font=font, fill=fg, anchor="mm")


# ---------------------------------------------------------------- main
def main():
    src = [a for a in sys.argv[1:] if not a.startswith("--")][0]
    story = json.load(open(src, encoding="utf-8"))
    name = os.path.splitext(os.path.basename(src))[0]
    preview = "--preview" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[1] if len(args) > 1 else os.path.join(HERE, f"{name}_short.mp4")
    voice, speed = story.get("voice", "hm_omega"), float(story.get("speed", 1.0))
    rng = np.random.default_rng(7); prng = random.Random(7)

    # 1. voice + timeline
    print("Voiceover ...")
    voice_parts, timeline, cur = [], [], 0.45
    scenes = story["scenes"]
    for si, sc in enumerate(scenes):
        s0 = cur; caps = []; lts = []
        chars_ = sc.get("chars", [])
        for line in sc["lines"]:
            text, by = (line, None) if isinstance(line, str) else (line["text"], line.get("by"))
            ci = None
            if isinstance(by, int): ci = by
            elif by: ci = next((i for i, c in enumerate(chars_) if c["who"] == by), None)
            who = chars_[ci]["who"] if ci is not None else None
            vkey = (chars_[ci].get("voice", who) if ci is not None else "narrator")
            prof = tuple(story.get("voices", {}).get(vkey, VOICES.get(vkey, VOICES["narrator"])))
            if vkey == "narrator" and "voices" not in story: prof = (voice, speed, 0.0)
            a = speak(text, prof); voice_parts.append((cur, a)); dur = len(a) / SR
            lts.append((cur, cur + dur, ci, envelope(a)))
            label = who
            words = text.split(); wts = [word_weight(w) for w in words]; tot = sum(wts)
            wt, acc = [], 0
            for w, x in zip(words, wts):
                wt.append((cur + dur * acc / tot, cur + dur * (acc + x) / tot)); acc += x
            k = 0
            for ch in chunk_words(words):
                caps.append((ch, wt[k:k + len(ch)], label)); k += len(ch)
            cur += dur + 0.22
        cur += 0.35
        timeline.append(dict(start=s0, end=cur, caps=caps, lines=lts))
    T = cur + 1.6
    timeline[-1]["end"] = T
    print(f"Duration {T:.1f}s")

    # 2. audio mix
    vo = np.zeros(int(T * SR) + SR, np.float32)
    for at, a in voice_parts: add(vo, a, at)
    fx_list = [sc.get("fx", []) for sc in scenes]
    build_at = next((timeline[i]["start"] for i, f in enumerate(fx_list) if "build" in f), T)
    climax_at = next((timeline[i]["start"] for i, f in enumerate(fx_list) if "boom" in f), T)
    mus = make_music(T + 1, story.get("music", "calm"), build_at, climax_at, rng)[:len(vo)]
    mus = np.pad(mus, (0, len(vo) - len(mus)))
    env = np.convolve(np.abs(vo), np.ones(4800) / 4800, mode="same")   # duck music under voice
    duck = 1 - 0.55 * np.clip(env / 0.03, 0, 1)
    sfx = np.zeros_like(vo)
    for i, tl in enumerate(timeline[1:], 1):
        add(sfx, whoosh(rng=rng) * 0.35, max(tl["start"] - 0.3, 0))
        if "boom" in fx_list[i]: add(sfx, boom(rng) * 0.55, tl["start"])
    mix = vo * 1.0 + mus * 0.55 * duck + sfx
    mix = mix[:int(T * SR)]; mix /= max(1e-6, np.abs(mix).max() / 0.95)
    import soundfile as sf
    wav = os.path.join(HERE, ".cache", f"{name}_mix.wav"); sf.write(wav, mix, SR)

    # 3. pre-render backgrounds
    print("Backgrounds ...")
    statics = [build_static(sc["bg"], i, np.random.default_rng(100 + i), name) for i, sc in enumerate(scenes)]
    mandala = make_mandala(); rays = make_rays()
    yy, xx = np.mgrid[-1:1:H * 1j, -1:1:W * 1j]
    vign = Image.fromarray((175 * np.clip((np.sqrt(xx * xx + yy * yy) - 0.75) / 0.7, 0, 1) ** 1.3).astype(np.uint8))
    black = Image.new("RGB", (W, H), (0, 0, 0)); white = Image.new("RGB", (W, H), (255, 255, 255))
    char_cache = {}; cache_scene = [-1]

    def char_frame(si, ci, c, act, phase, prog, mouth=0.0):
        """Pre-scaled, cropped character image + feet anchor, cached per scene."""
        if cache_scene[0] != si: char_cache.clear(); cache_scene[0] = si
        oneshot = act in ONE_SHOT
        qp = min(int(prog * 40), 16) if oneshot else 0
        qi = 0 if (oneshot and qp < 16) else int(phase * 12) % 12
        qm = int(round(mouth * 3))
        key = (ci, act, qi, qp, qm)
        if key not in char_cache:
            _, _, _, sil_c, sun_c = THEMES[scenes[si]["bg"].get("theme", "dusk")]
            im = character(c["who"], act, qi / 12, qp / 40, sil=sil_c, light=lerp(sun_c, (255, 255, 255), 0.2), stripes=c.get("stripes", False), mouth=qm / 3)
            if c.get("flip"): im = ImageOps.mirror(im)
            f = c.get("h", 0.3) * (H if c.get("anim") == "fly" else BH) / 1000
            im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
            bb = im.getbbox() or (0, 0, 1, 1)
            char_cache[key] = (im.crop(bb), COX * f - bb[0], COY * f - bb[1])
        return char_cache[key]

    parts = {k: Particles(k, prng, n) for k, n in (("embers", 70), ("fireflies", 40), ("dust", 60), ("rain", 160), ("leaves", 28))}

    # 4. frames -> ffmpeg
    print("Rendering frames ...")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out]
    p = None if preview else subprocess.Popen(cmd, stdin=subprocess.PIPE)
    shots = {int((tl["start"] + 0.6 * (tl["end"] - tl["start"])) * FPS): i for i, tl in enumerate(timeline)}
    shots[int(1.5 * FPS)] = "hook"
    nframes = int(T * FPS); si = 0
    for fi in range(nframes):
        if preview and fi not in shots: continue
        t = fi / FPS
        while si < len(timeline) - 1 and t >= timeline[si]["end"]: si += 1
        tl, sc = timeline[si], scenes[si]; lt = t - tl["start"]; dur = tl["end"] - tl["start"]
        el = set(sc["bg"].get("el", [])); fx = sc.get("fx", []); static, fgl, custom = statics[si]
        # Ken Burns + punch zoom + shake
        z = 1 + 0.07 * (lt / dur) + 0.10 * (1 - ease(lt / 0.35))
        if "build" in fx: z += 0.06 * (lt / dur) ** 2
        cw = W * OV / z
        cw = min(BW, cw); ch = cw * H / W
        pan = (1 if si % 2 else -1) * (BW - cw) * 0.3 * (lt / dur - 0.5)
        cx, cy = BW / 2 + pan, BH / 2
        shake = 0
        if "shake" in fx: shake = 26 * max(0, 1 - lt / 1.8)
        if "build" in fx: shake = max(shake, 10 * (lt / dur) ** 2)
        if shake:
            cx += prng.uniform(-shake, shake); cy += prng.uniform(-shake, shake)
        cx = min(max(cx, cw / 2), BW - cw / 2); cy = min(max(cy, ch / 2), BH - ch / 2)
        frame = static.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        d = ImageDraw.Draw(frame, "RGBA")
        top, hor, sea, sil, sunc = THEMES[sc["bg"].get("theme", "dusk")]
        if not custom:
            if "rays" in el:
                rr = rays.rotate(t * 6, Image.BILINEAR)
                ry = H * 0.42 if "sea" not in el else H * 0.50
                frame.paste(Image.new("RGB", rr.size, sunc), (int(W / 2 - rr.width / 2), int(ry - rr.height / 2)), rr)
            if "aura" in el:
                r = 300 + 500 * ease(lt / dur) + 25 * math.sin(t * 6)
                glow(frame, W / 2, H * (0.44 if "hut" not in el else 0.52), r, (255, 220, 130), 0.85)
            if "mandala" in el:
                m = mandala.rotate(t * 10, Image.BILINEAR); a = 0.55
                m.putalpha(m.getchannel("A").point(lambda v: int(v * a)))
                frame.paste(m, (int(W / 2 - m.width / 2), int(H * 0.38 - m.height / 2)), m)
            if "waves" in el:
                base = H * 0.66
                for k in range(5):
                    yb = base + k * (H - base) / 5; amp = 10 + k * 9; spd = 0.6 + k * 0.35
                    pts = [(x, yb + amp * math.sin(x / (160 + k * 40) + t * spd * 2 + k)) for x in range(0, W + 40, 40)]
                    col = lerp(sea, (0, 0, 0), 0.15 + k * 0.12)
                    d.polygon(pts + [(W, H), (0, H)], fill=col + (110,))
                    d.line(pts, fill=lerp(sea, sunc, 0.5) + (90,), width=3)
            if fgl is not None:
                fgf = fgl.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
                frame.paste(fgf, (0, 0), fgf)
            k_ = W / cw; x0, y0 = cx - cw / 2, cy - ch / 2
            li = 0
            for j, ln_ in enumerate(tl["lines"]):
                if t >= ln_[0]: li = j
            l0, l1, spk, env = tl["lines"][li]; lprog = min(1.0, max(0.0, (t - l0) / max(l1 - l0, 0.1)))
            for ci, c in enumerate(sc.get("chars", [])):
                acts = c.get("act", "idle"); act = acts[min(li, len(acts) - 1)] if isinstance(acts, list) else acts
                x = c.get("x", 0.5); sc_ = 1.0
                if "to" in c:
                    mp = min(1.0, lt / (dur * c.get("move", 0.6)))
                    x = x + (c["to"] - x) * mp
                    if mp < 1: act = c.get("move_act", "walk")
                an = c.get("anim")
                if an == "grow":
                    g0 = tl["lines"][min(c.get("grow_line", 0), len(tl["lines"]) - 1)][0]
                    sc_ = 0.42 + 0.58 * ease((t - g0) / max(tl["end"] - g0, 0.1) / 0.7) if t >= g0 else 0.42
                mo = 0.0
                if spk == ci and l0 <= t < l1:
                    mo = float(env[min(int((t - l0) * FPS), len(env) - 1)])
                    if act in ("idle", "namaste"): act = "talk" if c["who"] not in ("squirrel",) else act
                cim, ax, ay = char_frame(si, ci, c, act, (t / CYCLE.get(act, 2.0)) % 1.0, lprog, mo)
                if an == "fly":
                    q = min(1.0, lt / (dur * 0.9)); fx_ = (-0.1 + 1.2 * q) * W; fy_ = (0.85 - 0.75 * math.sin(math.pi * q * 0.9)) * H
                    ty = -(0.75 * math.sin(math.pi * (q + 0.01) * 0.9) - 0.75 * math.sin(math.pi * q * 0.9)) * H
                    ang = math.degrees(math.atan2(-ty, 1.2 * W * 0.01))
                    im2 = cim.rotate(ang - 90, Image.BILINEAR, expand=True)
                    frame.paste(im2, (int(fx_ - im2.width / 2), int(fy_ - im2.height / 2)), im2)
                    continue
                kk = k_ * sc_
                im2 = cim.resize((max(1, int(cim.width * kk)), max(1, int(cim.height * kk))), Image.BILINEAR)
                fxp = (x * BW - x0) * k_; fyp = (c.get("y", 0.95) * BH - y0) * k_
                frame.paste(im2, (int(fxp - ax * kk), int(fyp - ay * kk)), im2)
            if "leap" in el:
                p_ = min(1.0, lt / (dur * 0.9)); mask = Image.new("L", (W // 4, H // 4), 0); md = ImageDraw.Draw(mask)
                for k in range(60):
                    q = p_ - 0.04 - k * 0.012
                    if q < 0: break
                    x = (-0.1 + 1.2 * q) * W / 4; y = (0.85 - 0.75 * math.sin(math.pi * q * 0.9)) * H / 4
                    r = max(1, 22 - k * 0.35)
                    md.ellipse([x - r, y - r, x + r, y + r], fill=int(255 * (1 - k / 60)))
                big = mask.filter(ImageFilter.GaussianBlur(8)).resize((W, H))
                frame.paste(Image.new("RGB", (W, H), (255, 150, 40)), (0, 0), big)
                frame.paste(white, (0, 0), mask.filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.9)).resize((W, H)))
            d = ImageDraw.Draw(frame, "RGBA")
            for k in ("embers", "fireflies", "dust", "rain", "leaves"):
                if k in el: parts[k].draw(d, t)
        frame.paste(black, (0, 0), vign)
        # flash on cut
        if "flash" in fx and lt < 0.5:
            frame = Image.blend(frame, white, 0.85 * (1 - lt / 0.5))
        if lt < 0.12 and si > 0:
            frame = Image.blend(frame, black, 0.5 * (1 - lt / 0.12))
        d = ImageDraw.Draw(frame, "RGBA")
        # top tag + progress bar
        d.rectangle([0, 0, W * t / T, 10], fill=(255, 140, 0, 255))
        pill(d, W / 2, 140, story.get("tag", "रामायण"), FTAG, (255, 255, 255), (200, 60, 20, 220))
        # hook title (first 3.2 s)
        if t < 3.4:
            a = ease(t / 0.4) * (1 - ease((t - 3.0) / 0.4))
            hook = story["hook"]; hw = d.textlength(hook, font=FHOOK)
            lines = [hook] if hw < W - 140 else [" ".join(hook.split()[:len(hook.split()) // 2]), " ".join(hook.split()[len(hook.split()) // 2:])]
            y0 = 330 - 60 * (1 - a)
            for li, ln in enumerate(lines):
                tw = d.textlength(ln, font=FHOOK)
                d.rounded_rectangle([W / 2 - tw / 2 - 30, y0 + li * 130 - 70, W / 2 + tw / 2 + 30, y0 + li * 130 + 62],
                                    radius=20, fill=(255, 214, 0, int(240 * a)))
                d.text((W / 2, y0 + li * 130), ln, font=FHOOK, fill=(20, 10, 0, int(255 * a)), anchor="mm")
        # captions
        for words, wt, label in tl["caps"]:
            c0, c1 = wt[0][0], wt[-1][1] + 0.12
            if c0 - 0.05 <= t < c1:
                act = max([i for i, (a0, _) in enumerate(wt) if t >= a0] or [0])
                img = caption_img(words, act)
                s = 0.75 + 0.25 * back((t - c0 + 0.05) / 0.18)
                if s != 1:
                    img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
                frame.paste(img, (int(W / 2 - img.width / 2), int(H * 0.64 - img.height / 2)), img)
                if label:                                # who is speaking
                    d = ImageDraw.Draw(frame, "RGBA")
                    pill(d, W / 2, H * 0.64 - img.height / 2 - 34, NAMES.get(label, label), FTAG, (255, 255, 255), NAME_COL.get(label, (60, 60, 60)) + (235,))
                break
        # outro
        if t > T - 2.6:
            a = ease((t - (T - 2.6)) / 0.4)
            d = ImageDraw.Draw(frame, "RGBA")
            pill(d, W / 2, H * 0.78, story.get("outro", ""), FOUT, (255, 255, 255, int(255 * a)), (200, 60, 20, int(230 * a)))
        if preview:
            frame.save(os.path.join(HERE, ".cache", f"preview_{name}_{shots[fi]}.png")); continue
        p.stdin.write(frame.tobytes())
        if fi % 300 == 0: print(f"  {fi}/{nframes}", flush=True)
    if preview:
        print("Preview frames in", os.path.join(HERE, ".cache")); return
    p.stdin.close(); p.wait()
    print("Wrote", out)


if __name__ == "__main__":
    main()
