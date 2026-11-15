#!/usr/bin/env python3
"""रहस्यमयी ट्रेन – THE MISSING TRAIN: a cinematic Hindi short film (16:9, 1920x1080) made in code.

Usage:
    python3 video/missing_train/make_film.py                   # full film -> video/missing_train/missing_train.mp4
    python3 video/missing_train/make_film.py --preview         # a few still frames of every shot (fast)
    python3 video/missing_train/make_film.py --shots 5,6       # only these shots (for checking)

The story, dialogue, staging, camera moves, music and sound effects are all in story.json.
Needs: Python 3, numpy, Pillow (with raqm), soundfile, kokoro-onnx, ffmpeg.
Uses the Hindi voice model and fonts of video/ramayan (downloaded on first run).
"""
import argparse, bisect, json, math, os, re, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "ramayan"))
import make_short as ms          # Hindi TTS (Kokoro) + fonts
import figures, sets, sound
from sets import font, F_BOLD, F_BLACK, F_TITLE

W, H, FPS, SR = 1920, 1080, 24, ms.SR
BAR = 120                          # letterbox bars (2.4:1 picture)

# ------------------------------------------------------------------ voices
VOICES = {  # Kokoro voice, speed, pitch (semitones)
    "narrator": ("hm_omega", 0.96, -1.0),
    "aarav":    ("hm_psi", 1.0, 0.5),
    "master":   ("hm_omega", 0.88, -3.0),
    "girl":     ("hf_alpha", 1.0, 4.0),
    "mother":   ("hf_beta", 0.9, -1.0),
    "announce": ("hf_beta", 0.95, 0.0),
    "train":    ("hf_alpha", 0.88, -2.0),
    "news":     ("hm_omega", 0.88, -1.5),
}
NAMES = {"aarav": "आरव", "master": "स्टेशन मास्टर", "girl": "बच्ची", "mother": "माँ",
         "announce": "अनाउंसमेंट", "train": "अनाउंसमेंट", "news": "अखबार की खबर"}
NAME_COL = {"aarav": (120, 180, 255), "master": (255, 190, 90), "girl": (255, 110, 110), "mother": (255, 160, 200),
            "announce": (180, 220, 180), "train": (180, 220, 180), "news": (230, 210, 160)}


def voice(who, text, room, fx):
    a = ms.speak(text, VOICES[who])
    dry = len(a) / SR
    if who in ("announce", "train"):
        return sound.pa(a) * (0.8 if who == "announce" else 0.75), dry
    if fx == "ghost":
        return sound.reverb(a, 0.55, 1.0, echo=0.3, dly=0.24), dry
    wet, dec = {"out": (0.22, 0.6), "in": (0.2, 0.35), "dry": (0.06, 0.2), "big": (0.35, 1.0)}.get(room, (0.15, 0.4))
    if who == "girl": wet += 0.12
    return sound.reverb(a, wet, dec), dry


# ------------------------------------------------------------------ timeline
def tref(v, lt, dur, default=0.0):
    if v is None: return default
    if isinstance(v, (int, float)): return float(v)
    m = re.match(r"^\s*(L(\d+)(e?)|end|start)\s*([+-]\s*[\d.]+)?\s*$", v)
    if not m: raise ValueError("bad time reference: " + v)
    if m.group(1) == "end": base = dur
    elif m.group(1) == "start": base = 0.0
    else:
        s, e = lt[int(m.group(2))]
        base = e if m.group(3) else s
    return base + (float(m.group(4).replace(" ", "")) if m.group(4) else 0.0)


class Ctx:
    def __init__(s, i, sh, start):
        s.i, s.sh, s.start = i, sh, start
        s.lt, s.speak, s.state, s.cues = [], [], {}, {}
        s.dur = 0.0

    def cue(s, name, default=None):
        return s.cues.get(name, default)

    def t(s, v, default=0.0):
        return tref(v, s.lt, s.dur, default)


def build(story):
    shots, vo, subs, t = [], [], [], 0.0
    for i, sh in enumerate(story["shots"]):
        c = Ctx(i, sh, t)
        cur = sh.get("pre", 1.0)
        for ln in sh.get("lines", []):
            if isinstance(ln, str): ln = {"text": ln}
            who = ln.get("by", "narrator")
            cur += ln.get("wait", 0.0)
            a, d = voice(who, ln.get("say", ln["text"]), ln.get("room", sh.get("room", "out")), ln.get("fx"))
            c.lt.append((cur, cur + d))
            c.speak.append((cur, cur + d, who))
            vo.append((t + cur, a, ln.get("gain", 1.0)))
            if not sh.get("nosubs"): subs.append((t + cur, t + cur + max(d, 1.5) + 0.35, who, ln["text"]))
            cur += d + ln.get("gap", 0.75 if who == "narrator" else 0.55)
        c.dur = max(cur + sh.get("post", 0.6), sh.get("min", 0))
        for k, v in sh.get("cues", {}).items():
            c.cues[k] = c.t(v)
        shots.append(c)
        t += c.dur
    return shots, vo, subs, t


# ------------------------------------------------------------------ screen-space layers
_rain, _fog, _vig, _grain = {}, {}, None, []


def rain_layer(kind):
    if kind in _rain: return _rain[kind]
    rng = np.random.default_rng(1 if kind == "far" else 2)
    im = Image.new("RGBA", (W, 2 * H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    n, L, a, wd = (1700, (26, 50), (35, 80), 1) if kind == "far" else (420, (60, 110), (45, 100), 2)
    for _ in range(n):
        x, y = rng.uniform(-100, W), rng.uniform(0, 2 * H)
        ln = rng.uniform(*L)
        d.line([x, y, x + ln * 0.18, y + ln], fill=(190, 200, 220, int(rng.uniform(*a))), width=wd)
    _rain[kind] = im
    return im


def fog_layer():
    if "f" in _fog: return _fog["f"]
    n = sets.noise_tex(2 * W, H, 140, 13, 60)
    v = np.asarray(n, np.float32) / 255.0
    yy = np.linspace(0, 1, H)[:, None]
    prof = np.exp(-((yy - 0.55) / 0.22) ** 2)
    a = np.clip((v - 0.3) * 1.6, 0, 1) * prof * 150
    rgba = np.dstack([np.full_like(a, 150), np.full_like(a, 158), np.full_like(a, 172), a]).astype(np.uint8)
    _fog["f"] = Image.fromarray(rgba, "RGBA")
    return _fog["f"]


def vignette():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W]
        d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        _vig = np.clip(1.15 - 0.55 * d ** 2, 0.25, 1.0).astype(np.float32)[..., None]
    return _vig


def grain(i):
    if not _grain:
        rng = np.random.default_rng(9)
        for _ in range(6):
            _grain.append(rng.normal(0, 3.2, (H, W, 1)).astype(np.float32))
    return _grain[(i // 2) % len(_grain)]


GRADE = {  # multiply, lift
    "night": ((0.92, 0.98, 1.12), (0, 2, 6)),
    "cold": ((0.85, 0.95, 1.18), (0, 3, 9)),
    "warm": ((1.08, 1.0, 0.86), (6, 3, 0)),
    "sepia": ((1.1, 0.98, 0.78), (14, 8, 0)),
    "dawn": ((1.05, 1.0, 0.94), (4, 2, 4)),
    "none": ((1, 1, 1), (0, 0, 0)),
}


# ------------------------------------------------------------------ text
_txt = {}


def text_img(text, size, col=(240, 240, 240), path=F_BOLD, glow_col=None, maxw=1600):
    k = (text, size, col, path, glow_col)
    if k in _txt: return _txt[k]
    f = font(path, size)
    lines, cur = [], ""
    for w in text.split():
        t2 = (cur + " " + w).strip()
        if f.getlength(t2) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = t2
    lines.append(cur)
    lh = int(size * 1.45)
    im = Image.new("RGBA", (maxw + 120, lh * len(lines) + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text((im.width / 2, 30 + lh * i + lh / 2), ln, font=f, fill=col + (255,), anchor="mm")
    if glow_col:
        g = Image.new("RGBA", im.size, glow_col + (0,))
        g.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(size * 0.25)))
        im = Image.alpha_composite(g, im)
    _txt[k] = im
    return im


def sub_img(who, text):
    k = ("sub", who, text)
    if k in _txt: return _txt[k]
    size = 38
    f = font(F_BOLD, size)
    label = (NAMES.get(who, "") + ":  ") if who != "narrator" else ""
    maxw = 1640
    words, lines, cur = text.split(), [], label
    first = True
    for w in words:
        t2 = (cur + " " + w) if cur and not (first and label) else (cur + w)
        if f.getlength(t2) > maxw and cur.strip():
            lines.append(cur); cur = w
        else:
            cur = t2
        first = False
    lines.append(cur)
    lh = int(size * 1.35)
    im = Image.new("RGBA", (W, lh * len(lines) + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base_col = (225, 225, 230) if who == "narrator" else (255, 255, 255)
    for i, ln in enumerate(lines):
        y = 5 + lh * i + lh / 2
        tw = f.getlength(ln)
        x = (W - tw) / 2
        if i == 0 and label:
            d.text((x, y), label.strip(), font=f, fill=NAME_COL.get(who, (255, 255, 255)) + (255,), anchor="lm")
            lw = f.getlength(label)
            d.text((x + lw, y), ln[len(label):].strip(), font=f, fill=base_col + (255,), anchor="lm")
        else:
            d.text((x, y), ln, font=f, fill=base_col + (255,), anchor="lm")
    _txt[k] = im
    return im


# ------------------------------------------------------------------ characters
_spr = {}


def sprite(who, pose, ph, h, face, rim, ld, alpha):
    pb = int((ph % (2 * math.pi)) / (2 * math.pi) * 16) if pose in ("walk", "run", "back_walk", "talk", "shout", "lantern_shout", "cook", "clap") else 0
    hb = max(12, int(h / 3) * 3)
    k = (who, pose, pb, hb, face, rim, ld)
    if k not in _spr:
        if len(_spr) > 1500: _spr.clear()
        im, an = figures.person(who, pose, pb / 16 * 2 * math.pi, hb, rim=rim, ld=(ld if face == "r" else (-ld[0], ld[1])))
        if face == "l":
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
            an = {kk: (im.width - v[0], v[1]) for kk, v in an.items()}
        _spr[k] = (im, an)
    im, an = _spr[k]
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    return im, an


def interp_keys(c, spec, t):
    keys = [(c.t(k[0]), k[1]) for k in spec.get("keys", [])]
    out = {k: spec[k] for k in ("X", "Z", "x", "y", "h") if k in spec}
    if not keys: return out
    prev = (0.0, dict(out))
    state = dict(out)
    for tk, kv in keys:
        if t >= tk:
            state.update(kv); prev = (tk, dict(state))
        else:
            # move from prev state to kv between the previous key time and tk
            p = (t - prev[0]) / max(1e-3, tk - prev[0])
            if spec.get("ease", True): p = p * p * (3 - 2 * p)
            for kk, vv in kv.items():
                state[kk] = prev[1].get(kk, vv) + (vv - prev[1].get(kk, vv)) * p
            break
    return state


def draw_chars(c, t, img, S):
    specs = c.sh.get("chars", [])
    sd = sets.SETS[c.sh["set"]]
    persp = sd.get("persp")
    items = []
    for sp in specs:
        show = sp.get("show")
        alpha = sp.get("alpha", 1.0)
        if show:
            t_in, t_out = c.t(show[0]), c.t(show[1], 1e9) if len(show) > 1 else 1e9
            if t < t_in or t > t_out + 0.5: continue
            alpha *= min(1.0, (t - t_in) / sp.get("fade", 0.5)) if t < t_in + sp.get("fade", 0.5) else 1.0
            if t > t_out: alpha *= max(0.0, 1 - (t - t_out) / 0.5)
        pose, face = sp.get("pose", "stand"), sp.get("face", "r")
        for pk in sp.get("poses", []):
            if t >= c.t(pk[0]):
                pose = pk[1]
                if len(pk) > 2: face = pk[2]
        st = interp_keys(c, sp, t)
        who = sp["who"]
        if persp:
            vx, vy, f, fl = persp
            Z = st["Z"]
            x, y, h = vx + f * st["X"] / Z, vy + f * fl / Z, f * figures.HEIGHT_M[who] / Z
        else:
            x, y, h = st.get("x", 0), st.get("y", 0), st.get("h", 100)
        h *= sp.get("scale", 1.0)
        if pose == "stand" and any(s <= t <= e and w == who for s, e, w in c.speak) and sp.get("talk", True):
            pose = "talk"
        rate = {"walk": 1.7, "back_walk": 1.7, "run": 2.6, "talk": 0.9, "shout": 3.0, "lantern_shout": 3.0, "cook": 1.2, "clap": 2.5}.get(pose, 0)
        ph = 2 * math.pi * rate * t + sp.get("phase", 0)
        if "orbit" in sp:
            o = sp["orbit"]
            a = 2 * math.pi * t / o["period"] + o.get("a0", 0)
            x, y = o["cx"] + o["rx"] * math.cos(a), o["cy"] + o["ry"] * math.sin(a)
            face = "l" if math.sin(a) > 0 else "r"
            h = o["h"] * (1 + 0.08 * math.sin(a))
        items.append((y, who, pose, ph, x, y, h, face, alpha, sp))
    items.sort(key=lambda r: (r[9].get("z_order", 0), r[0]))
    rim0, ld0 = sd.get("rim", (150, 170, 210)), sd.get("ld", (-0.8, -0.6))
    for _, who, pose, ph, x, y, h, face, alpha, sp in items:
        if alpha <= 0.01 or h < 8: continue
        rim = tuple(sp.get("rim", rim0))
        ld = tuple(sp.get("ld", ld0))
        im, an = sprite(who, pose, ph, h * S, face, rim, ld, alpha)
        fx, fy = an["foot"]
        ox, oy = int(x * S - fx), int(y * S - fy)
        img.paste(im, (ox, oy), im)
        if "toy" in an and sp.get("toy_glow", True):
            sets.glow(img, ox + an["toy"][0], oy + an["toy"][1], h * S * 0.22, (255, 40, 30), 0.55 * alpha)
        if "lantern" in an:
            lx, ly = ox + an["lantern"][0], oy + an["lantern"][1]
            sets.glow(img, lx, ly, h * S * 1.1, (255, 170, 80), 0.5 * alpha)
            sets.glow(img, lx, ly, h * S * 0.12, (255, 230, 170), 0.9 * alpha)
        if sp.get("aura"):
            hx, hy = ox + an["head"][0], oy + an["head"][1]
            sets.glow(img, hx, hy + h * S * 0.3, h * S * 0.8, tuple(sp["aura"]), 0.25 * alpha)
        if sp.get("tear") and t >= c.t(sp["tear"]):
            hx, hy = ox + an["head"][0], oy + an["head"][1]
            p = ((t - c.t(sp["tear"])) % 2.2) / 2.2
            sets.glow(img, hx + h * S * 0.035 * (1 if face == "r" else -1), hy + h * S * (0.01 + 0.06 * p), max(4, h * S * 0.012), (220, 235, 255), 0.9)


# ------------------------------------------------------------------ frame rendering
_static = {}


def get_static(c):
    if c.i not in _static:
        sd = sets.SETS[c.sh["set"]]
        st = sd["static"](c)
        _static[c.i] = st
    return _static[c.i]


def ease3(p):
    p = min(max(p, 0.0), 1.0)
    return p * p * (3 - 2 * p)


def camera(c, t):
    keys = c.sh.get("cam", [[0, 1.0, 0.5, 0.5]])
    ks = [(c.t(k[0]), k[1], k[2], k[3]) for k in keys]
    if t <= ks[0][0]: z, cx, cy = ks[0][1:]
    elif t >= ks[-1][0]: z, cx, cy = ks[-1][1:]
    else:
        for a, b in zip(ks, ks[1:]):
            if a[0] <= t <= b[0]:
                p = ease3((t - a[0]) / max(1e-3, b[0] - a[0]))
                z, cx, cy = (a[i] + (b[i] - a[i]) * p for i in (1, 2, 3))
                break
    sh = c.sh.get("shake", 0.0)
    for j in c.sh.get("jolts", []):
        tj = c.t(j)
        if tj <= t < tj + 1.5:
            sh += 18 * math.exp(-(t - tj) * 3)
    dx = sh * (math.sin(t * 23.1) + 0.5 * math.sin(t * 41.7)) / W
    dy = sh * (math.cos(t * 19.3) + 0.5 * math.sin(t * 37.9)) / H
    # gentle handheld drift
    hd = c.sh.get("handheld", 0.0012)
    dx += hd * math.sin(t * 0.7 + c.i)
    dy += hd * math.cos(t * 0.53 + c.i)
    return z, cx + dx, cy + dy


def render(c, t, fi):
    sd = sets.SETS[c.sh["set"]]
    st = get_static(c)
    base = st["base"]
    S = base.width / W
    if "bg" in sd:
        img = sd["bg"](c, t)
        if img.size != base.size: img = img.resize(base.size)
        img = Image.alpha_composite(img.convert("RGBA"), base).convert("RGB")
    else:
        img = base.copy()
    lights = sd["lights"](c, t) if "lights" in sd else {}
    if lights and any(v > 0.004 for v in lights.values()):
        arr = np.asarray(img, np.float32)
        for k, v in lights.items():
            if v > 0.004 and k in st["layers"]:
                arr = arr + st["layers"][k].astype(np.float32) * v
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if "pre" in sd: sd["pre"](c, t, img)
    draw_chars(c, t, img, S)
    if "post" in sd: sd["post"](c, t, img)
    # camera
    z, cx, cy = camera(c, t)
    bw, bh = base.width / z, base.height / z
    x0 = min(max(cx * base.width - bw / 2, 0), base.width - bw)
    y0 = min(max(cy * base.height - bh / 2, 0), base.height - bh)
    img = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + bw, y0 + bh))
    # atmosphere
    fog = c.sh.get("fog", 0)
    if fog:
        fl = fog_layer()
        off = int((t * 30 + c.i * 300) % W)
        part = fl.crop((off, 0, off + W, H))
        if fog < 1:
            part = part.copy(); part.putalpha(part.getchannel("A").point(lambda v: int(v * fog)))
        img = Image.alpha_composite(img.convert("RGBA"), part)
    rn = c.sh.get("rain", 0)
    if rn:
        img = img.convert("RGBA")
        for kind, sp in (("far", 1300), ("near", 2100)):
            if kind == "near" and rn < 0.6: continue
            rl = rain_layer(kind)
            off = int((t * sp) % H)
            img = Image.alpha_composite(img, rl.crop((0, H - off, W, 2 * H - off)))
    img = img.convert("RGB")
    # grade, vignette, grain, flashes, fades
    mul, lift = GRADE[c.sh.get("grade", "night")]
    arr = np.asarray(img, np.float32) * (vignette() * np.array(mul, np.float32)) + np.array(lift, np.float32)
    arr += grain(fi)
    fl = 0.0
    for f in c.sh.get("flash", []):
        tf = c.t(f)
        if tf <= t < tf + 1.0:
            u = t - tf
            fl = max(fl, math.exp(-u * 9) + (0.6 * math.exp(-(u - 0.18) * 12) if u > 0.18 else 0))
    if fl > 0.01:
        arr = arr * (1 + 1.6 * fl) + np.array((70, 80, 110), np.float32) * fl
    dark = 1.0
    fi_, fo_ = c.sh.get("fade_in", 0), c.sh.get("fade_out", 0)
    if fi_ and t < fi_: dark *= ease3(t / fi_)
    if fo_ and t > c.dur - fo_: dark *= ease3((c.dur - t) / fo_)
    for b in c.sh.get("blackouts", []):
        tb = c.t(b[0]); te = c.t(b[1]) if len(b) > 1 else 1e9
        if tb <= t < te: dark *= 0.25
    if dark < 0.999: arr *= dark
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    # titles / cards inside the picture
    for card in c.sh.get("cards", []):
        t0 = c.t(card.get("at", 0)); t1 = c.t(card.get("until"), 1e9) if card.get("until") is not None else 1e9
        if t < t0 or t > t1 + 1.0: continue
        a = min(1.0, (t - t0) / card.get("fade", 1.2))
        if t > t1: a *= max(0.0, 1 - (t - t1) / 1.0)
        a *= dark if card.get("with_fade", True) else 1.0
        path = {"title": F_TITLE, "black": F_BLACK}.get(card.get("font", "bold"), F_BOLD)
        ti = text_img(card["text"], card.get("size", 60), tuple(card.get("color", (240, 240, 240))), path,
                      tuple(card["glow"]) if card.get("glow") else None, card.get("maxw", 1500))
        sc = 1.0 + card.get("grow", 0.0) * (t - t0)
        if abs(sc - 1) > 0.002:
            ti = ti.resize((int(ti.width * sc), int(ti.height * sc)), Image.BICUBIC)
        if a < 0.999:
            ti = ti.copy(); ti.putalpha(ti.getchannel("A").point(lambda v: int(v * a)))
        img.paste(ti, (int(W / 2 - ti.width / 2), int(card.get("y", 540) - ti.height / 2)), ti)
    if c.sh.get("toy"):
        toy = toy_sprite()
        t0 = c.t(c.sh["toy"])
        if t > t0:
            x = -200 + (t - t0) * 140
            img.paste(toy, (int(x), 800 + int(2 * math.sin(t * 20))), toy)
            sets.glow(img, x + 80, 830, 60, (255, 40, 30), 0.35)
    # letterbox
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, BAR], fill=(0, 0, 0))
    d.rectangle([0, H - BAR, W, H], fill=(0, 0, 0))
    return img


_toy = []


def toy_sprite():
    if not _toy: _toy.append(figures.toy_train(170))
    return _toy[0]


SHOTS, SUBS, STARTS = [], [], []


def frame(fi):
    t = fi / FPS
    i = max(0, bisect.bisect_right(STARTS, t) - 1)
    c = SHOTS[i]
    tl = t - c.start
    img = render(c, tl, fi)
    xf = c.sh.get("xfade", 0)
    if xf and i > 0 and tl < xf:
        p = SHOTS[i - 1]
        prev = render(p, p.dur + tl, fi)
        img = Image.blend(prev, img, ease3(tl / xf))
    for s, e, who, text in SUBS:
        if s - 0.15 <= t <= e:
            a = min(1.0, (t - s + 0.15) / 0.15, (e - t) / 0.2)
            si = sub_img(who, text)
            if a < 0.999:
                si = si.copy(); si.putalpha(si.getchannel("A").point(lambda v: int(v * a)))
            img.paste(si, (0, int(H - BAR / 2 - si.height / 2)), si)
    return img


def frame_bytes(fi):
    return frame(fi).tobytes()


# ------------------------------------------------------------------ audio
def bed_gains(shots, key, n):
    names = set()
    for c in shots: names |= set(c.sh.get(key, {}).keys())
    out = {}
    for nm in names:
        g = np.zeros(n, np.float32)
        for c in shots:
            a, b = int(c.start * SR), min(n, int((c.start + c.dur) * SR))
            g[a:b] = c.sh.get(key, {}).get(nm, 0.0)
        k = int(0.9 * SR)
        cs = np.cumsum(np.concatenate([[0], g]))
        sm = (cs[k:] - cs[:-k]) / k
        g2 = np.concatenate([np.full(k // 2, sm[0]), sm, np.full(n - len(sm) - k // 2, sm[-1])])[:n]
        out[nm] = g2.astype(np.float32)
    return out


def make_audio(shots, vo, T):
    """Stereo mix: voices centre, ambience wide (decorrelated L/R), music widened,
    effects panned to follow the action, voice ducking, soft limiting."""
    n = int(T * SR) + SR
    rng = np.random.default_rng(42)
    vox = np.zeros(n, np.float32)
    for at, a, g in vo:
        sound.add(vox, a, at, g)
    e = np.abs(vox)
    k = int(0.25 * SR)
    cs = np.cumsum(np.concatenate([[0], e]))
    env = np.zeros(n, np.float32)
    env[k // 2:k // 2 + len(cs) - k] = (cs[k:] - cs[:-k]) / k
    duck = 1 - 0.55 * np.clip(env / 0.04, 0, 1)
    mix = np.stack([vox, vox], 1)
    for nm, g in bed_gains(shots, "amb", n).items():
        L = sound.AMB[nm](n, np.random.default_rng(100 + len(nm)))[:n]
        R = sound.AMB[nm](n, np.random.default_rng(200 + len(nm)))[:n]
        gg = g * 0.42 * (0.55 + 0.45 * duck)
        mix[:, 0] += L * gg; mix[:, 1] += R * gg
    for nm, g in bed_gains(shots, "music", n).items():
        m = sound.MUSIC[nm](n, rng)[:n] * g * 0.5 * duck
        d = int(0.011 * SR)
        mix[:, 0] += m; mix[:, 1] += np.concatenate([np.zeros(d, np.float32), m[:-d]]) * 0.92 + m * 0.08
    for c in shots:
        for ev in c.sh.get("sfx", []):
            nm, at = ev[0], c.t(ev[1]) + c.start
            gg = ev[2] if len(ev) > 2 else 0.8
            p = ev[3] if len(ev) > 3 else 0.0
            p0, p1 = (p, p) if not isinstance(p, list) else p
            sig = sound.pan(sound.SFX[nm](rng), p0, p1)
            i = int(at * SR)
            if i < 0: sig, i = sig[-i:], 0
            m_ = min(len(sig), n - i)
            if m_ > 0: mix[i:i + m_] += sig[:m_] * gg
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.95
    return mix[:int(T * SR)].astype(np.float32)


# ------------------------------------------------------------------ main
def main():
    global SHOTS, SUBS, STARTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", default=os.path.join(HERE, "story.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "missing_train.mp4"))
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--shots", default="")
    ap.add_argument("--pv_dir", default=os.path.join(HERE, ".preview"))
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()
    story = json.load(open(args.story, encoding="utf-8"))
    print("Voices ...")
    SHOTS, vo, SUBS, T = build(story)
    STARTS = [c.start for c in SHOTS]
    print(f"Film length: {T:.1f} s ({T / 60:.2f} min), {len(SHOTS)} shots")
    for c in SHOTS:
        print(f"  {c.i:2d} {c.sh['set']:9s} {c.start:7.1f}s  {c.dur:5.1f}s  {c.sh.get('name', '')}")
    only = [int(x) for x in args.shots.split(",") if x.strip()]
    if args.preview:
        os.makedirs(args.pv_dir, exist_ok=True)
        for c in SHOTS:
            if only and c.i not in only: continue
            ts = [c.dur * 0.15, c.dur * 0.55, c.dur * 0.92] + [v + 0.6 for v in c.cues.values() if v < c.dur]
            for j, tt in enumerate(ts[:6]):
                fi = int((c.start + tt) * FPS)
                frame(fi).save(os.path.join(args.pv_dir, f"s{c.i:02d}_{j}.jpg"), quality=85)
            print("  preview shot", c.i)
        return
    print("Audio ...")
    mix = make_audio(SHOTS, vo, T)
    import soundfile as sf
    os.makedirs(os.path.join(HERE, ".cache"), exist_ok=True)
    if only:
        t0 = min(SHOTS[i].start for i in only)
        t1 = max(SHOTS[i].start + SHOTS[i].dur for i in only)
        out = args.out.replace(".mp4", f"_shots_{'_'.join(map(str, only))}.mp4")
    else:
        t0, t1, out = 0.0, T, args.out
    wav = os.path.join(HERE, ".cache", "mix.wav")
    sf.write(wav, mix[int(t0 * SR):int(t1 * SR)], SR)
    frames = range(int(t0 * FPS), int(t1 * FPS))
    print(f"Video: {len(frames)} frames with {args.jobs} workers ...")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "1500k",
           "-bufsize", "3000k", "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    st = time.time()
    import multiprocessing as mp
    with mp.get_context("fork").Pool(args.jobs) as pool:
        for k, b in enumerate(pool.imap(frame_bytes, frames, chunksize=12)):
            p.stdin.write(b)
            if k % 240 == 0:
                el = time.time() - st
                print(f"  {k}/{len(frames)}  {el:.0f}s elapsed", flush=True)
    p.stdin.close(); p.wait()
    print("Done:", out, f"({os.path.getsize(out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
