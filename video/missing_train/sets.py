"""Locations ("sets") of the film, drawn in code.

Each set is a dict of functions that receive the shot context `c` (see make_film.Ctx):
  static(c)        -> {"base": PIL image (RGB, or RGBA if "bg" is given), "layers": {name: uint8 array}}
  bg(c, t)         -> RGB image under an RGBA base (window views, cab view)          [optional]
  lights(c, t)     -> {layer name: intensity}                                        [optional]
  pre(c, t, img)   -> draw moving things behind the characters                       [optional]
  post(c, t, img)  -> draw things in front of the characters                         [optional]
  persp            -> (vx, vy, f, floorY): characters are placed by X (m) and Z (m)  [optional]
  rim, ld          -> rim-light colour and light direction for characters
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import figures

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "..", "ramayan", "fonts")
F_BOLD = os.path.join(FONT_DIR, "NotoSansDevanagari-Bold.ttf")
F_BLACK = os.path.join(FONT_DIR, "NotoSansDevanagari-Black.ttf")
F_TITLE = os.path.join(FONT_DIR, "RozhaOne-Regular.ttf")
_fonts = {}


def font(path, size):
    k = (path, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    return _fonts[k]


# ------------------------------------------------------------------ helpers
def vgrad(w, h, top, bot, y0=0, y1=None):
    y1 = h if y1 is None else y1
    t = np.clip((np.arange(h) - y0) / max(1, y1 - y0), 0, 1)[:, None]
    a = np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t
    return Image.fromarray(np.repeat(a[:, None, :], w, 1).astype(np.uint8))


_rad = {}


def radial(r, p=2.2):
    k = (r, p)
    if k not in _rad:
        y, x = np.mgrid[0:2 * r, 0:2 * r]
        d = np.sqrt((x - r + 0.5) ** 2 + (y - r + 0.5) ** 2) / r
        _rad[k] = (np.clip(1 - d, 0, 1) ** p).astype(np.float32)
    return _rad[k]


def add_mask(img, m, cx, cy, color, k=1.0):
    """Additive light: float mask m centred at (cx, cy) on an RGB PIL image (in place)."""
    if k <= 0.003: return
    mh, mw = m.shape
    x0, y0 = int(cx - mw / 2), int(cy - mh / 2)
    bx0, by0 = max(0, x0), max(0, y0)
    bx1, by1 = min(img.width, x0 + mw), min(img.height, y0 + mh)
    if bx1 <= bx0 or by1 <= by0: return
    sub = m[by0 - y0:by1 - y0, bx0 - x0:bx1 - x0]
    reg = np.asarray(img.crop((bx0, by0, bx1, by1)), np.float32)
    reg += sub[..., None] * (np.array(color, np.float32) * k)
    img.paste(Image.fromarray(np.clip(reg, 0, 255).astype(np.uint8)), (bx0, by0))


def glow(img, cx, cy, r, color, k=1.0, p=2.2):
    r = max(2, int(r))
    add_mask(img, radial(r, p), cx, cy, color, k)


_streak = {}


def streak(img, cx, cy, w, color, k=1.0):
    w = max(8, int(w))
    if w not in _streak:
        x = np.linspace(-1, 1, 2 * w)
        y = np.linspace(-1, 1, max(4, w // 14))
        _streak[w] = (np.exp(-(y[:, None] / 0.35) ** 2) * (1 - np.abs(x[None, :])) ** 3).astype(np.float32)
    add_mask(img, _streak[w], cx, cy, color, k)


def light_layer(draw_fn, blur, size=(W, H)):
    """Draw light shapes on black and blur -> uint8 array to add with an intensity."""
    im = Image.new("RGB", size, 0)
    draw_fn(im, ImageDraw.Draw(im))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, np.uint8)


def ridge(rng, w, base, amp, n=7):
    xs = np.linspace(0, w, 60)
    y = np.full(60, float(base))
    for k in range(1, n):
        y += amp / k * np.sin(xs / w * k * math.pi * rng.uniform(1, 3) + rng.uniform(0, 6))
    return [(0, 2000)] + list(zip(xs, y)) + [(w, 2000)]


def noise_tex(w, h, scale, seed, blur=0):
    rng = np.random.default_rng(seed)
    a = rng.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return im


class Persp:
    def __init__(s, vx, vy, f):
        s.vx, s.vy, s.f = vx, vy, f

    def p(s, X, Y, Z):
        Z = max(Z, 0.3)
        return (s.vx + s.f * X / Z, s.vy + s.f * Y / Z)

    def quad(s, d, pts, fill, outline=None):
        d.polygon([s.p(*q) for q in pts], fill=fill, outline=outline)


# ------------------------------------------------------------------ smoke puffs
_puff = {}


def puff_mask(r, a):
    r = max(4, int(r) // 6 * 6)
    a = max(1, min(10, int(a * 10)))
    k = (r, a)
    if k not in _puff:
        m = radial(r, 1.4) * (a / 10.0) * 255
        _puff[k] = Image.fromarray(m.astype(np.uint8))
    return _puff[k]


def smoke(img, t, src, t0=0.0, rate=14, life=3.2, col=(70, 72, 80), up=90, drift=(60, 0), r0=26, grow=70, a0=0.55, seed=1):
    """src(tb) -> (x, y) emitter position at birth time tb."""
    rng = np.random.default_rng(seed)
    jit = rng.uniform(-1, 1, 4000)
    first = max(t0, t - life)
    i0, i1 = int(first * rate), int(t * rate)
    for i in range(i0, i1 + 1):
        tb = i / rate
        if tb < t0 or tb > t: continue
        age = t - tb
        if age >= life: continue
        p = src(tb)
        if p is None: continue
        x = p[0] + drift[0] * age + jit[i % 4000] * 20 * age
        y = p[1] - up * age * (1 - 0.2 * age / life) + drift[1] * age
        r = r0 + grow * age
        a = a0 * (1 - age / life) ** 1.3 * min(1, age * 6)
        m = puff_mask(r, a)
        img.paste(col, (int(x - m.width / 2), int(y - m.height / 2)), m)


# ------------------------------------------------------------------ the train (side view)
_train = {}


def train_strip(cars=4, scale=1.0, ghost_window=None):
    k = (cars, scale, ghost_window)
    if k in _train: return _train[k]
    s = scale
    CL, LL, TL, GAP = int(980 * s), int(1050 * s), int(430 * s), int(26 * s)
    Ht = int(450 * s)
    total = cars * (CL + GAP) + TL + GAP + LL + int(40 * s)
    img = Image.new("RGBA", (total, Ht), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    halo = Image.new("L", (total, Ht), 0)
    dh = ImageDraw.Draw(halo)
    body, panel, dark = (24, 17, 19, 255), (38, 28, 28, 255), (10, 9, 11, 255)
    rail_y = int(440 * s)
    num = font(F_BOLD, int(26 * s))
    x = 0
    win_list = []
    for ci in range(cars):
        d.rectangle([x, 120 * s, x + CL, 362 * s], fill=body)
        d.chord([x - 10 * s, 70 * s, x + CL + 10 * s, 160 * s], 180, 360, fill=(16, 12, 14, 255))
        d.rectangle([x, 112 * s, x + CL, 124 * s], fill=(52, 44, 44, 255))
        d.line([x, 300 * s, x + CL, 300 * s], fill=panel, width=max(1, int(3 * s)))
        d.line([x, 150 * s, x + CL, 150 * s], fill=panel, width=max(1, int(2 * s)))
        d.rectangle([x + 10 * s, 362 * s, x + CL - 10 * s, 384 * s], fill=dark)
        for dx in (0, CL - 64 * s):
            d.rectangle([x + dx, 132 * s, x + dx + 64 * s, 358 * s], fill=(14, 10, 12, 255))
            d.rectangle([x + dx + 16 * s, 160 * s, x + dx + 48 * s, 214 * s], fill=(200, 140, 60, 255))
        for wi in range(7):
            wx = x + 100 * s + wi * 112 * s
            win_list.append((ci, wi, wx))
            dh.rounded_rectangle([wx - 16 * s, 150 * s, wx + 86 * s, 266 * s], radius=int(20 * s), fill=150)
        d.text((x + CL / 2, 330 * s), "०२५", font=num, fill=(120, 96, 60, 255), anchor="mm")
        for bx in (130 * s, CL - 130 * s):
            for wx in (-48 * s, 48 * s):
                cx = x + bx + wx
                d.ellipse([cx - 30 * s, rail_y - 60 * s, cx + 30 * s, rail_y], fill=dark)
                d.ellipse([cx - 8 * s, rail_y - 38 * s, cx + 8 * s, rail_y - 22 * s], fill=(60, 56, 56, 255))
            d.rectangle([x + bx - 90 * s, 380 * s, x + bx + 90 * s, 398 * s], fill=dark)
        x += CL + GAP
    # tender
    d.rectangle([x, 160 * s, x + TL, 360 * s], fill=(18, 14, 16, 255))
    d.rectangle([x, 150 * s, x + TL, 166 * s], fill=(44, 36, 36, 255))
    for cx in (x + 90 * s, x + 215 * s, x + 340 * s):
        d.ellipse([cx - 40 * s, rail_y - 80 * s, cx + 40 * s, rail_y], fill=dark)
    x += TL + GAP
    L0 = x
    # loco (front to the right)
    d.rectangle([L0 + 30 * s, 84 * s, L0 + 270 * s, 330 * s], fill=(16, 12, 14, 255))         # cab
    d.rectangle([L0 + 10 * s, 70 * s, L0 + 290 * s, 92 * s], fill=(28, 22, 22, 255))
    d.rectangle([L0 + 80 * s, 120 * s, L0 + 200 * s, 200 * s], fill=(255, 120, 30, 255))       # firebox glow window
    dh.rectangle([L0 + 60 * s, 100 * s, L0 + 220 * s, 220 * s], fill=200)
    d.rounded_rectangle([L0 + 260 * s, 150 * s, L0 + 960 * s, 305 * s], radius=int(40 * s), fill=(20, 16, 18, 255))  # boiler
    for bx in range(int(L0 + 320 * s), int(L0 + 900 * s), int(110 * s)):
        d.line([bx, 152 * s, bx, 303 * s], fill=(34, 28, 28, 255), width=max(1, int(4 * s)))
    d.rounded_rectangle([L0 + 880 * s, 138 * s, L0 + 985 * s, 318 * s], radius=int(30 * s), fill=(12, 10, 12, 255))  # smokebox
    d.polygon([(L0 + 800 * s, 150 * s), (L0 + 870 * s, 150 * s), (L0 + 880 * s, 62 * s), (L0 + 790 * s, 62 * s)], fill=(14, 11, 12, 255))  # chimney
    d.rectangle([L0 + 780 * s, 50 * s, L0 + 890 * s, 66 * s], fill=(22, 18, 18, 255))
    d.chord([L0 + 520 * s, 110 * s, L0 + 610 * s, 190 * s], 180, 360, fill=(26, 20, 20, 255))  # dome
    d.rectangle([L0 + 260 * s, 305 * s, L0 + 990 * s, 322 * s], fill=(10, 8, 10, 255))
    for cx in (L0 + 340 * s, L0 + 520 * s, L0 + 700 * s):
        d.ellipse([cx - 86 * s, rail_y - 172 * s, cx + 86 * s, rail_y], fill=dark)
        d.ellipse([cx - 70 * s, rail_y - 156 * s, cx + 70 * s, rail_y - 16 * s], outline=(46, 40, 40, 255), width=max(1, int(4 * s)))
        for a in range(0, 360, 30):
            ra = math.radians(a)
            d.line([cx, rail_y - 86 * s, cx + 66 * s * math.cos(ra), rail_y - 86 * s + 66 * s * math.sin(ra)], fill=(30, 26, 26, 255), width=max(1, int(4 * s)))
    d.line([L0 + 340 * s, rail_y - 60 * s, L0 + 700 * s, rail_y - 60 * s], fill=(80, 76, 76, 255), width=max(1, int(9 * s)))
    d.ellipse([L0 + 860 * s, rail_y - 80 * s, L0 + 940 * s, rail_y], fill=dark)
    d.polygon([(L0 + 960 * s, 330 * s), (L0 + 1045 * s, rail_y - 6 * s), (L0 + 960 * s, rail_y - 6 * s)], fill=(14, 12, 12, 255))  # cowcatcher
    d.rectangle([L0 + 975 * s, 300 * s, L0 + 1000 * s, 335 * s], fill=(80, 20, 18, 255))
    d.rounded_rectangle([L0 + 930 * s, 104 * s, L0 + 1000 * s, 152 * s], radius=int(8 * s), fill=(26, 22, 22, 255))  # headlamp
    d.ellipse([L0 + 975 * s, 112 * s, L0 + 1004 * s, 144 * s], fill=(255, 244, 210, 255))
    # windows (warm, empty) and halo
    for ci, wi, wx in win_list:
        col = (255, 196, 96, 255)
        if ghost_window == (ci, wi):
            col = (255, 90, 70, 255)
        d.rounded_rectangle([wx, 165 * s, wx + 70 * s, 250 * s], radius=int(9 * s), fill=col)
        d.rectangle([wx + 4 * s, 236 * s, wx + 66 * s, 250 * s], fill=(200, 120, 50, 255))
        d.line([wx, 205 * s, wx + 70 * s, 205 * s], fill=(120, 70, 30, 255), width=max(1, int(3 * s)))
        if ghost_window == (ci, wi):
            gx = wx + 35 * s
            d.ellipse([gx - 11 * s, 186 * s, gx + 11 * s, 208 * s], fill=(30, 10, 14, 255))
            d.polygon([(gx - 16 * s, 250 * s), (gx + 16 * s, 250 * s), (gx + 10 * s, 208 * s), (gx - 10 * s, 208 * s)], fill=(30, 10, 14, 255))
    halo = halo.filter(ImageFilter.GaussianBlur(26 * s))
    hal = Image.new("RGBA", (total, Ht), (255, 170, 70, 0))
    hal.putalpha(halo.point(lambda v: int(v * 0.55)))
    out = Image.alpha_composite(img, hal)
    # keep fully transparent outside train + halo
    meta = {"len": total, "h": Ht, "rail": rail_y, "chimney": (L0 + 835 * s, 50 * s), "lamp": (L0 + 995 * s, 128 * s),
            "loco": L0}
    _train[k] = (out, meta)
    return _train[k]


def place_train(img, x_front, rail_y, scale=1.0, facing_left=True, ghost_window=None):
    """Draw the side-view train with its locomotive front at x_front, wheels on rail_y. Returns world anchors."""
    spr, m = train_strip(4, scale, ghost_window)
    if facing_left:
        key = ("flip", 4, scale, ghost_window)
        if key not in _train:
            _train[key] = spr.transpose(Image.FLIP_LEFT_RIGHT)
        spr = _train[key]
        x0 = x_front - (m["len"] - m["lamp"][0]) + 0
        x0 = int(x_front - (m["len"] - (m["loco"] + 1045 * scale)))
        chim = (x0 + m["len"] - m["chimney"][0], rail_y - m["rail"] + m["chimney"][1])
        lamp = (x0 + m["len"] - m["lamp"][0], rail_y - m["rail"] + m["lamp"][1])
    else:
        x0 = int(x_front - (m["loco"] + 1045 * scale))
        chim = (x0 + m["chimney"][0], rail_y - m["rail"] + m["chimney"][1])
        lamp = (x0 + m["lamp"][0], rail_y - m["rail"] + m["lamp"][1])
    y0 = int(rail_y - m["rail"])
    if x0 < img.width and x0 + spr.width > 0:
        cx0 = max(0, -x0)
        cx1 = min(spr.width, img.width - x0)
        part = spr.crop((cx0, 0, cx1, spr.height))
        img.paste(part, (x0 + cx0, y0), part)
    return {"chimney": chim, "lamp": lamp}


# ================================================================== SET: station (side view)
STATION_NAME = "धुंधगढ़"


def station_static(c):
    rng = np.random.default_rng(11)
    img = vgrad(W, H, (5, 7, 16), (30, 36, 54), 0, 640)
    cl = Image.new("L", (W, H), 0)
    dc = ImageDraw.Draw(cl)
    for _ in range(45):
        x, y, r = rng.uniform(0, W), rng.uniform(60, 440), rng.uniform(60, 220)
        dc.ellipse([x - r * 1.9, y - r * 0.55, x + r * 1.9, y + r * 0.55], fill=int(rng.uniform(40, 110)))
    cl = cl.filter(ImageFilter.GaussianBlur(45))
    img = Image.composite(Image.new("RGB", (W, H), (46, 52, 70)), img, cl)
    d = ImageDraw.Draw(img)
    d.polygon(ridge(rng, W, 560, 30), fill=(11, 14, 22))
    d.polygon(ridge(rng, W, 600, 18), fill=(8, 10, 16))
    # building + canopy
    d.rectangle([330, 372, 1400, 650], fill=(25, 24, 31))
    for x in range(330, 1400, 34):
        d.line([x, 372, x, 650], fill=(29, 28, 35), width=2)
    for x in (420, 1170):
        d.rectangle([x, 450, x + 130, 570], fill=(48, 38, 28))
        d.line([x + 65, 450, x + 65, 570], fill=(20, 18, 20), width=6)
        d.line([x, 510, x + 130, 510], fill=(20, 18, 20), width=6)
    d.rectangle([800, 470, 900, 650], fill=(13, 12, 17))
    d.rectangle([790, 460, 910, 472], fill=(36, 34, 40))
    d.polygon([(110, 332), (1500, 332), (1530, 374), (80, 374)], fill=(13, 13, 19))
    d.line([(80, 374), (1530, 374)], fill=(44, 44, 56), width=4)
    for x in range(190, 1500, 260):
        d.rectangle([x - 8, 374, x + 8, 650], fill=(17, 17, 23))
        d.rectangle([x - 14, 640, x + 14, 652], fill=(22, 22, 28))
    # clock
    cx, cy, r = 640, 420, 36
    d.line([cx, 374, cx, cy - r], fill=(20, 20, 24), width=4)
    d.ellipse([cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5], fill=(30, 28, 30))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(196, 190, 166))
    d.line([cx, cy, cx - r * 0.85, cy], fill=(20, 20, 20), width=3)
    a = math.radians(-90 + (11.75 / 12) * 360)
    d.line([cx, cy, cx + r * 0.5 * math.cos(a), cy + r * 0.5 * math.sin(a)], fill=(20, 20, 20), width=5)
    # signboard (beyond the canopy)
    for x in (1600, 1830):
        d.rectangle([x - 7, 470, x + 7, 650], fill=(20, 20, 24))
    d.rectangle([1560, 452, 1870, 548], fill=(20, 18, 10))
    d.rectangle([1566, 458, 1864, 542], fill=(214, 176, 38))
    d.text((1715, 488), STATION_NAME, font=font(F_BLACK, 50), fill=(18, 16, 12), anchor="mm")
    d.text((1715, 528), "DHUNDHGARH", font=font(F_BOLD, 20), fill=(30, 26, 14), anchor="mm")
    # bench
    d.rectangle([660, 594, 860, 608], fill=(30, 22, 18))
    d.rectangle([660, 556, 860, 570], fill=(30, 22, 18))
    for x in (672, 848):
        d.rectangle([x - 4, 556, x + 4, 650], fill=(18, 16, 16))
    # platform, edge, track
    d.rectangle([0, 650, W, 704], fill=(38, 40, 47))
    d.rectangle([0, 700, W, 709], fill=(120, 104, 40))
    d.rectangle([0, 709, W, 800], fill=(20, 20, 25))
    for x in range(0, W, 90):
        d.line([x, 709, x, 800], fill=(26, 26, 31), width=2)
    d.line([0, 755, W, 755], fill=(26, 26, 31), width=2)
    d.rectangle([0, 800, W, H], fill=(13, 13, 17))
    for x in range(-20, W, 46):
        d.rectangle([x, 868, x + 30, 892], fill=(30, 25, 22))
    for y in (860, 902):
        d.rectangle([0, y, W, y + 7], fill=(62, 64, 72))
        d.line([0, y, W, y], fill=(130, 136, 150), width=2)
    # lamp fittings
    for x in (420, 1000, 1360):
        d.line([x, 374, x, 396], fill=(20, 20, 24), width=3)
        d.polygon([(x - 22, 396), (x + 22, 396), (x + 12, 384), (x - 12, 384)], fill=(30, 30, 34))

    def lamps(im, dl):
        for x in (420, 1000, 1360):
            dl.ellipse([x - 9, 394, x + 9, 408], fill=(255, 230, 170))
            dl.ellipse([x - 260, 640, x + 260, 712], fill=(110, 80, 40))
            dl.rectangle([x - 26, 660, x + 26, 800], fill=(80, 58, 30))
            dl.ellipse([x - 160, 380, x + 160, 650], fill=(30, 22, 12))
        dl.ellipse([1500, 420, 1930, 580], fill=(60, 50, 20))
    L = light_layer(lamps, 26)
    im2 = Image.fromarray(L)
    for x in (420, 1000, 1360):
        glow(im2, x, 402, 300, (255, 170, 80), 0.5)
        glow(im2, x, 402, 60, (255, 220, 160), 0.9)
    return {"base": img, "layers": {"lamps": np.asarray(im2)}}


def flicker(t, seed=0, rate=13):
    i = int(t * rate)
    v = (math.sin(i * 12.9898 + seed * 78.233) * 43758.5453) % 1.0
    return v


def station_lights(c, t):
    off = c.cue("off", 1e9)
    fl = c.cue("flicker", off - 1.2)
    if t >= off: return {"lamps": 0.0}
    if t >= fl:
        return {"lamps": 1.0 if flicker(t, 3, 17) > 0.45 else 0.12}
    return {"lamps": 1.0 if flicker(t, 1, 9) > 0.03 else 0.7}


def station_pre(c, t, img):
    if "arrive" in c.cues:
        t0, t1 = c.cue("arrive"), c.cue("stop")
        p = min(max((t - t0) / max(0.1, t1 - t0), 0), 1)
        p = 1 - (1 - p) ** 2.4
        xf = W + 500 + (c.sh.get("stop_x", 260) - W - 500) * p
        an = place_train(img, xf, 930, 1.0, True)
        vel = (1 - p)

        def src(tb):
            pp = min(max((tb - t0) / max(0.1, t1 - t0), 0), 1); pp = 1 - (1 - pp) ** 2.4
            x = W + 500 + (c.sh.get("stop_x", 260) - W - 500) * pp
            return (x + (an["chimney"][0] - xf), an["chimney"][1])
        smoke(img, t, src, t0=t0 - 1, rate=12, col=(64, 66, 74), up=110, drift=(40, 0), r0=30, grow=90, a0=0.7)
        glow(img, an["lamp"][0], an["lamp"][1], 340, (255, 220, 160), 0.85)
        glow(img, an["lamp"][0], an["lamp"][1], 60, (255, 250, 230), 1.0)
        streak(img, an["lamp"][0], an["lamp"][1], 900, (255, 220, 170), 0.7)
        c.state["train_v"] = vel


# ================================================================== SET: clock close-up
def clock_static(c):
    img = vgrad(W, H, (10, 10, 16), (24, 24, 32))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 210], fill=(12, 12, 18))
    d.line([0, 210, W, 210], fill=(40, 40, 50), width=6)
    cx, cy, r = 960, 560, 300
    d.rectangle([cx - 14, 210, cx + 14, cy - r], fill=(22, 22, 26))
    d.ellipse([cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30], fill=(36, 30, 26))
    d.ellipse([cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18], fill=(70, 58, 40))
    face = Image.new("RGB", (2 * r, 2 * r), (206, 198, 170))
    fn = noise_tex(2 * r, 2 * r, 6, 4, 2)
    face = Image.composite(Image.new("RGB", face.size, (176, 160, 124)), face, fn.point(lambda v: int(v * 0.5)))
    m = Image.new("L", face.size, 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * r, 2 * r], fill=255)
    img.paste(face, (cx - r, cy - r), m)
    f = font(F_BOLD, 52)
    for h in range(1, 13):
        a = math.radians(-90 + h * 30)
        d.text((cx + r * 0.78 * math.cos(a), cy + r * 0.78 * math.sin(a)), str(h), font=f, fill=(30, 26, 22), anchor="mm")
    for k in range(60):
        a = math.radians(-90 + k * 6)
        r1 = r * (0.93 if k % 5 else 0.89)
        d.line([cx + r1 * math.cos(a), cy + r1 * math.sin(a), cx + r * 0.97 * math.cos(a), cy + r * 0.97 * math.sin(a)], fill=(40, 34, 28), width=3 if k % 5 else 6)
    d.line([cx - r * 0.5, cy - r * 0.7, cx + r * 0.1, cy + r * 0.2, cx + r * 0.05, cy + r * 0.8], fill=(230, 226, 210), width=2)  # crack

    def lamp(im, dl):
        dl.ellipse([cx - 500, 120, cx + 500, 560], fill=(70, 50, 24))
    L = light_layer(lamp, 60)
    return {"base": img, "layers": {"lamp": L}}


def clock_lights(c, t):
    return {"lamp": 1.0 if flicker(t, 2, 11) > 0.06 else 0.6}


def clock_post(c, t, img):
    d = ImageDraw.Draw(img)
    cx, cy, r = 960, 560, 300
    sec = int(t) + 40
    mins = 44 + (sec / 60.0)
    hrs = 11 + mins / 60
    for ang, ln, wd in ((hrs / 12 * 360, 0.5, 16), (mins / 60 * 360, 0.75, 10), (sec / 60 * 360, 0.85, 3)):
        a = math.radians(-90 + ang)
        d.line([cx - r * 0.12 * math.cos(a), cy - r * 0.12 * math.sin(a), cx + r * ln * math.cos(a), cy + r * ln * math.sin(a)],
               fill=(20, 18, 16) if wd > 3 else (150, 20, 20), width=wd)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(20, 18, 16))


# ================================================================== SET: track view (headlight in fog)
TV = Persp(960, 560, 900)


def track_static(c):
    rng = np.random.default_rng(5)
    img = vgrad(W, H, (4, 6, 12), (34, 40, 54), 0, 560)
    d = ImageDraw.Draw(img)
    d.polygon(ridge(rng, W, 548, 20), fill=(16, 20, 28))
    d.rectangle([0, 560, W, H], fill=(14, 14, 18))
    P = TV
    for i in range(160):
        z = 2.0 * 1.035 ** i
        P.quad(d, [(-1.3, 1.5, z), (1.3, 1.5, z), (1.3, 1.5, z + 0.25), (-1.3, 1.5, z + 0.25)], fill=(30, 26, 24))
    for X in (-0.75, 0.75):
        d.polygon([P.p(X - 0.04, 1.5, 1.2), P.p(X + 0.04, 1.5, 1.2), P.p(X + 0.04, 1.5, 400), P.p(X - 0.04, 1.5, 400)], fill=(90, 94, 106))
    # platform on the left
    P.quad(d, [(-30, 0.5, 1.0), (-2.0, 0.5, 1.0), (-2.0, 0.5, 400), (-30, 0.5, 400)], fill=(34, 36, 42))
    P.quad(d, [(-2.0, 0.5, 1.0), (-2.0, 1.5, 1.0), (-2.0, 1.5, 400), (-2.0, 0.5, 400)], fill=(20, 20, 24))
    d.polygon([P.p(-2.2, 0.5, 1.0), P.p(-2.0, 0.5, 1.0), P.p(-2.0, 0.5, 400), P.p(-2.2, 0.5, 400)], fill=(120, 104, 40))
    for z in (6, 14, 30, 60):
        P.quad(d, [(-4.0, 0.5, z), (-3.8, 0.5, z), (-3.8, -3.5, z), (-4.0, -3.5, z)], fill=(14, 14, 18))
    # signal post with red light on the right
    sx, sy = P.p(2.6, -3.2, 18)
    d.line([P.p(2.6, 1.5, 18), (sx, sy)], fill=(16, 16, 20), width=6)
    d.rectangle([sx - 16, sy - 30, sx + 16, sy + 30], fill=(12, 12, 14))
    glow(img, sx, sy - 12, 70, (255, 40, 30), 0.9)
    glow(img, sx, sy - 12, 10, (255, 160, 150), 1.0)
    return {"base": img, "layers": {}}


def track_pre(c, t, img):
    t0, t1 = c.cue("approach", 0.0), c.cue("near", c.dur)
    p = min(max((t - t0) / max(0.1, t1 - t0), 0), 1)
    z = 420 * (12 / 420) ** (p ** 0.85)
    P = TV
    fogk = min(1.0, 26 / z)
    col = tuple(int(30 * (1 - fogk) + 8 * fogk) for _ in range(3))
    d = ImageDraw.Draw(img)
    # loco front
    P.quad(d, [(-1.5, 1.45, z), (1.5, 1.45, z), (1.5, -2.6, z), (-1.5, -2.6, z)], fill=col)
    cx, cy = P.p(0, -0.6, z)
    rr = 1.25 * P.f / z
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=tuple(max(0, v - 4) for v in col))
    d.polygon([P.p(-0.35, -2.6, z), P.p(0.35, -2.6, z), P.p(0.45, -3.5, z), P.p(-0.45, -3.5, z)], fill=col)
    d.polygon([P.p(-1.5, 0.9, z), P.p(1.5, 0.9, z), P.p(0.6, 1.5, z), P.p(-0.6, 1.5, z)], fill=col)
    for bx in (-1.15, 1.15):
        bxp, byp = P.p(bx, 0.5, z)
        br = 0.2 * P.f / z
        d.ellipse([bxp - br, byp - br, bxp + br, byp + br], fill=(70, 20, 18) if z < 60 else col)
    lx, ly = P.p(0, -1.95, z)
    smoke(img, t, lambda tb: P.p(0, -3.6, 420 * (12 / 420) ** (min(max((tb - t0) / max(0.1, t1 - t0), 0), 1) ** 0.85)),
          t0=t0, rate=10, col=(56, 58, 66), up=60, drift=(30, -10), r0=max(6, 40 * 30 / z), grow=60, a0=0.5)
    k = 0.35 + 0.65 * p
    glow(img, lx, ly, 120 + 9000 / z, (255, 225, 170), 0.55 * k)
    glow(img, lx, ly, 18 + 1200 / z, (255, 250, 235), 1.0)
    streak(img, lx, ly, 300 + 30000 / z, (200, 220, 255), 0.6 * k)
    c.state["z"] = z


# ================================================================== SET: platform (perspective)
PP = Persp(980, 500, 820)
FLOOR = 1.55


def platform_static(c):
    rng = np.random.default_rng(8)
    P = PP
    img = vgrad(W, H, (5, 7, 15), (26, 30, 44), 0, 520)
    d = ImageDraw.Draw(img)
    d.polygon(ridge(rng, W, 495, 10), fill=(14, 17, 25))
    d.rectangle([0, 505, W, H], fill=(14, 14, 18))
    # track bed + rails
    P.quad(d, [(1.6, 2.55, 0.8), (12, 2.55, 0.8), (12, 2.55, 400), (1.6, 2.55, 400)], fill=(15, 14, 17))
    for i in range(140):
        z = 1.2 * 1.04 ** i
        P.quad(d, [(1.9, 2.55, z), (4.3, 2.55, z), (4.3, 2.55, z + 0.25), (1.9, 2.55, z + 0.25)], fill=(30, 26, 23))
    for X in (2.35, 3.85):
        P.quad(d, [(X - 0.04, 2.5, 0.8), (X + 0.04, 2.5, 0.8), (X + 0.04, 2.5, 400), (X - 0.04, 2.5, 400)], fill=(84, 88, 100))
    # platform floor + edge
    P.quad(d, [(-12, FLOOR, 0.7), (1.6, FLOOR, 0.7), (1.6, FLOOR, 400), (-12, FLOOR, 400)], fill=(34, 36, 43))
    for i in range(70):
        z = 1.0 * 1.06 ** i
        a, b = P.p(-12, FLOOR, z), P.p(1.6, FLOOR, z)
        d.line([a, b], fill=(30, 32, 38), width=1)
    P.quad(d, [(1.35, FLOOR, 0.7), (1.6, FLOOR, 0.7), (1.6, FLOOR, 400), (1.35, FLOOR, 400)], fill=(126, 108, 42))
    # building wall (left)
    P.quad(d, [(-4.5, FLOOR, 1.0), (-4.5, -2.0, 1.0), (-4.5, -2.0, 400), (-4.5, FLOOR, 400)], fill=(24, 23, 30))
    for z0 in (4, 11, 19, 30, 46):
        P.quad(d, [(-4.5, 0.2, z0), (-4.5, -1.1, z0), (-4.5, -1.1, z0 + 1.6), (-4.5, 0.2, z0 + 1.6)], fill=(46, 36, 26))
    for z0 in (7.5, 24):
        P.quad(d, [(-4.5, FLOOR, z0), (-4.5, -0.6, z0), (-4.5, -0.6, z0 + 1.1), (-4.5, FLOOR, z0 + 1.1)], fill=(12, 11, 16))
    # benches
    for z0 in (6, 15):
        P.quad(d, [(-4.0, 1.05, z0), (-3.4, 1.05, z0), (-3.4, 1.05, z0 + 1.8), (-4.0, 1.05, z0 + 1.8)], fill=(34, 26, 20))
        P.quad(d, [(-4.0, 0.6, z0), (-4.0, 1.05, z0), (-4.0, 1.05, z0 + 1.8), (-4.0, 0.6, z0 + 1.8)], fill=(28, 22, 18))
    # canopy underside + fascia
    P.quad(d, [(-4.5, -2.0, 0.7), (1.2, -2.0, 0.7), (1.2, -2.0, 400), (-4.5, -2.0, 400)], fill=(12, 12, 18))
    P.quad(d, [(1.2, -2.0, 0.7), (1.2, -2.5, 0.7), (1.2, -2.5, 400), (1.2, -2.0, 400)], fill=(20, 20, 27))
    for i in range(40):
        z = 1.5 + i * 2.5
        d.line([P.p(-4.5, -2.0, z), P.p(1.2, -2.0, z)], fill=(18, 18, 25), width=max(1, int(8 / z * 3)))
    # pillars (far to near)
    for z in sorted([3.5 + 5 * k for k in range(16)], reverse=True):
        w = 0.14
        P.quad(d, [(-1.9 - w, FLOOR, z), (-1.9 + w, FLOOR, z), (-1.9 + w, -2.0, z), (-1.9 - w, -2.0, z)], fill=(17, 17, 22))
    # signboard on the far platform
    sx0, sy0 = P.p(-0.6, -1.2, 22)
    sx1, sy1 = P.p(0.6, -0.6, 22)
    d.rectangle([sx0, sy0, sx1, sy1], fill=(170, 140, 30))
    d.text(((sx0 + sx1) / 2, (sy0 + sy1) / 2), STATION_NAME, font=font(F_BLACK, max(10, int((sy1 - sy0) * 0.6))), fill=(20, 18, 12), anchor="mm")
    # lamp fittings
    for z in range(5, 80, 6):
        x, y = P.p(-0.4, -1.6, z)
        rr = max(1.5, 0.15 * P.f / z)
        d.line([P.p(-0.4, -2.0, z), (x, y)], fill=(22, 22, 26), width=1)
        d.ellipse([x - rr, y - rr * 0.6, x + rr, y + rr * 0.6], fill=(36, 36, 40))

    def lamps(im, dl):
        for z in range(5, 80, 6):
            x, y = P.p(-0.4, -1.6, z)
            rr = 0.13 * P.f / z
            dl.ellipse([x - rr, y - rr * 0.6, x + rr, y + rr * 0.6], fill=(255, 220, 160))
            a, b = P.p(-2.5, FLOOR, z - 1.5), P.p(1.3, FLOOR, z + 1.5)
            dl.ellipse([a[0], b[1], b[0], a[1]], fill=(70, 52, 28))
    L = light_layer(lamps, 10)
    im2 = Image.fromarray(L)
    for z in range(5, 80, 6):
        x, y = P.p(-0.4, -1.6, z)
        glow(im2, x, y, 1.6 * P.f / z, (170, 190, 230), 0.45)
    # departing-train layer drawn per frame; platform "blur" variant for close-ups
    base = img
    if c.sh.get("blur"):
        base = base.filter(ImageFilter.GaussianBlur(c.sh["blur"]))
        im2 = im2.filter(ImageFilter.GaussianBlur(c.sh["blur"]))
    return {"base": base, "layers": {"lamps": np.asarray(im2)}}


def platform_lights(c, t):
    k = c.sh.get("lamps", 0.0)
    if k and flicker(t, 4, 7) < 0.08: k *= 0.4
    return {"lamps": k}


def draw_side_train(c, t, img, zoff, ghost=False, door_open=None):
    """Train standing at the platform, seen in perspective; zoff moves it away (+Z)."""
    P = PP
    X0 = 1.8
    d = ImageDraw.Draw(img)
    gl = Image.new("L", (W // 4, H // 4), 0)
    dg = ImageDraw.Draw(gl)

    def q4(pts):
        return [(x / 4, y / 4) for x, y in (P.p(*p) for p in pts)]
    CAR, GAP = 22.0, 0.8
    cars = []
    for k in range(6):
        z0 = -10 + k * (CAR + GAP) + zoff
        cars.append((z0, z0 + CAR, k))
    for z0, z1, k in reversed(cars):
        if z1 < 0.5: continue
        za, zb = max(z0, 0.5), z1
        P.quad(d, [(X0, 1.25, za), (X0, -2.3, za), (X0, -2.3, zb), (X0, 1.25, zb)], fill=(22, 16, 18))
        P.quad(d, [(X0, -2.3, za), (X0 + 1.2, -2.85, za), (X0 + 1.2, -2.85, zb), (X0, -2.3, zb)], fill=(14, 11, 13))
        P.quad(d, [(X0, 1.25, za), (X0, 1.6, za), (X0, 1.6, zb), (X0, 1.25, zb)], fill=(8, 8, 10))
        P.quad(d, [(X0, 1.25, zb), (X0 + 3, 1.25, zb), (X0 + 3, -2.3, zb), (X0, -2.3, zb)], fill=(16, 12, 14))
        wz = z0 + 2.2
        wi = 0
        while wz < z1 - 2.0:
            if wz + 1.0 > 0.5:
                a = max(wz, 0.5)
                red = ghost and k == 1 and wi == 4
                col = (255, 92, 70) if red else (214, 150, 70)
                P.quad(d, [(X0, -1.05, a), (X0, -0.05, a), (X0, -0.05, wz + 1.0), (X0, -1.05, wz + 1.0)], fill=col)
                dg.polygon(q4([(X0, -1.25, a), (X0, 0.15, a), (X0, 0.15, wz + 1.2), (X0, -1.25, wz + 1.2)]), fill=230 if not red else 255)
                dg.polygon(q4([(X0 - 0.2, FLOOR, a), (X0 - 2.6, FLOOR, a + 0.6), (X0 - 2.6, FLOOR, wz + 2.0), (X0 - 0.2, FLOOR, wz + 1.0)]), fill=70)
                if red:
                    gx, gy = P.p(X0, -0.55, wz + 0.5)
                    hh = 0.55 * P.f / max(wz + 0.5, 0.5)
                    d.ellipse([gx - hh * 0.18, gy - hh * 0.5, gx + hh * 0.18, gy - hh * 0.15], fill=(40, 10, 14))
                    d.polygon([(gx - hh * 0.25, gy + hh * 0.5), (gx + hh * 0.25, gy + hh * 0.5), (gx + hh * 0.15, gy - hh * 0.15), (gx - hh * 0.15, gy - hh * 0.15)], fill=(40, 10, 14))
            wz += 1.9; wi += 1
        for dz in (0.3, CAR - 1.2):
            a = z0 + dz
            if a + 0.9 < 0.5: continue
            opened = door_open is not None and k == door_open[0] and dz == 0.3
            col = (255, 200, 110) if opened else (14, 10, 12)
            P.quad(d, [(X0, 1.25, max(a, 0.5)), (X0, -1.7, max(a, 0.5)), (X0, -1.7, a + 0.9), (X0, 1.25, a + 0.9)], fill=col)
            if opened:
                dg.polygon(q4([(X0, 1.4, max(a, 0.5)), (X0, -1.9, max(a, 0.5)), (X0, -1.9, a + 1.1), (X0, 1.4, a + 1.1)]), fill=255)
                dg.polygon(q4([(X0, FLOOR, a), (X0 - 3.0, FLOOR, a - 0.5), (X0 - 3.0, FLOOR, a + 2.2), (X0, FLOOR, a + 1.0)]), fill=120)
    if zoff > 0.5:  # tail lamp of last visible car (the first one, nearest)
        z0 = cars[0][0]
        if z0 > 0.6:
            tx, ty = P.p(X0 + 1.5, 0.4, z0)
            glow(img, tx, ty, 2.0 * P.f / z0 + 20, (255, 30, 20), 0.9)
    gl = gl.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
    ga = np.asarray(gl, np.float32)[..., None] / 255.0
    arr = np.asarray(img, np.float32) + ga * np.array([150, 95, 40], np.float32)
    img.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)))


def platform_pre(c, t, img):
    tr = c.sh.get("train")
    if not tr: return
    zoff = 0.0
    if tr == "depart":
        t0 = c.cue("depart", 0.0)
        u = max(0.0, t - t0)
        zoff = 0.35 * u * u + 0.2 * u
    door = None
    if "door_open" in c.sh:
        if c.cue("door_close", 1e9) > t >= c.cue("door_from", 0.0):
            door = (c.sh["door_open"],)
    zoff += c.sh.get("train_z", 0.0)
    draw_side_train(c, t, img, zoff, ghost=c.sh.get("ghost", False), door_open=door)
    if tr == "depart":
        P = PP
        sx, sy = P.p(2.6, -3.0, max(1.0, 40 + zoff))
        smoke(img, t, lambda tb: P.p(2.6, -3.2, 40 + 0.35 * max(0, tb - c.cue("depart", 0)) ** 2), t0=0,
              rate=8, col=(52, 54, 62), up=40, drift=(-20, -10), r0=20, grow=60, a0=0.45)


# ================================================================== SET: train door (close-up)
def door_static(c):
    rng = np.random.default_rng(3)
    img = Image.new("RGB", (W, H), (18, 13, 15))
    d = ImageDraw.Draw(img)
    nz = noise_tex(W, H, 3, 9, 1)
    img = Image.composite(Image.new("RGB", (W, H), (30, 22, 22)), img, nz.point(lambda v: int(v * 0.45)))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 130], fill=(12, 9, 11))
    d.rectangle([0, 128, W, 150], fill=(44, 36, 36))
    for y in (300, 880):
        d.line([0, y, W, y], fill=(40, 30, 30), width=5)
    for x in range(20, W, 70):
        for y in (312, 868):
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(48, 38, 36))
    # windows either side
    for wx in (180, 1440):
        d.rounded_rectangle([wx, 330, wx + 300, 600], radius=24, fill=(235, 170, 80))
        d.rectangle([wx + 10, 560, wx + 290, 600], fill=(190, 110, 46))
        d.line([wx, 470, wx + 300, 470], fill=(110, 64, 28), width=8)
    # vestibule interior (seen when the door opens)
    d.rectangle([760, 210, 1160, 930], fill=(150, 98, 46))
    vi = vgrad(400, 720, (210, 150, 70), (90, 56, 30))
    img.paste(vi, (760, 210))
    d = ImageDraw.Draw(img)
    d.rectangle([760, 210, 1160, 260], fill=(80, 50, 26))
    d.rectangle([1040, 300, 1160, 930], fill=(110, 70, 34))
    d.ellipse([930, 228, 990, 256], fill=(255, 240, 200))
    d.rectangle([740, 190, 1180, 210], fill=(30, 22, 22))
    d.rectangle([740, 190, 760, 940], fill=(30, 22, 22))
    d.rectangle([1160, 190, 1180, 940], fill=(30, 22, 22))
    # steps + platform
    d.rectangle([780, 930, 1140, 960], fill=(30, 26, 26))
    d.rectangle([0, 960, W, H], fill=(28, 28, 33))
    for x in range(-200, W, 160):
        d.ellipse([x, 990, x + 140, 1010], fill=(46, 46, 56))

    def lit(im, dl):
        dl.rectangle([760, 210, 1160, 930], fill=(120, 80, 34))
        dl.polygon([(760, 960), (1160, 960), (1500, H), (420, H)], fill=(120, 84, 40))
        for wx in (180, 1440):
            dl.rounded_rectangle([wx - 30, 300, wx + 330, 630], radius=40, fill=(80, 54, 22))
    L = light_layer(lit, 40)
    return {"base": img, "layers": {"inside": L}}


def door_frac(c, t):
    o0, c0 = c.cue("open", 1e9), c.cue("close", 1e9)
    if t < o0: return 0.0
    if t < c0: return min(1.0, (t - o0) / 1.6) ** 0.7
    return max(0.0, 1 - (t - c0) / 0.5)


def door_lights(c, t):
    return {"inside": 0.15 + 0.85 * door_frac(c, t)}


def door_post(c, t, img):
    f = door_frac(c, t)
    d = ImageDraw.Draw(img)
    x0 = 760 + 420 * f
    d.rectangle([x0, 205, x0 + 400, 935], fill=(20, 14, 16))
    d.rectangle([x0 + 8, 213, x0 + 392, 927], outline=(40, 30, 30), width=4)
    d.rounded_rectangle([x0 + 120, 300, x0 + 280, 470], radius=14, fill=(210, 150, 70) if f > 0 else (130, 90, 44))
    d.rectangle([x0 + 340, 560, x0 + 352, 680], fill=(90, 80, 70))
    d.rectangle([740, 190, 760, 940], fill=(30, 22, 22))


# ================================================================== SET: carriage interior
IP = Persp(960, 470, 760)
IFL = 1.5


def interior_static(c):
    P = IP
    img = Image.new("RGB", (W, H), (12, 9, 8))
    d = ImageDraw.Draw(img)
    ZE = 26
    # end wall + door
    a, b = P.p(-1.45, -1.05, ZE), P.p(1.45, IFL, ZE)
    d.rectangle([a, b], fill=(38, 28, 20))
    a, b = P.p(-0.45, -0.6, ZE), P.p(0.45, IFL, ZE)
    d.rectangle([a, b], fill=(20, 14, 12))
    a2, b2 = P.p(-0.25, -0.4, ZE), P.p(0.25, 0.3, ZE)
    d.rectangle([a2, b2], fill=(90, 110, 130))
    # floor, ceiling, walls
    P.quad(d, [(-1.45, IFL, 0.6), (1.45, IFL, 0.6), (1.45, IFL, ZE), (-1.45, IFL, ZE)], fill=(28, 20, 16))
    P.quad(d, [(-0.35, IFL, 0.6), (0.35, IFL, 0.6), (0.35, IFL, ZE), (-0.35, IFL, ZE)], fill=(48, 16, 16))
    P.quad(d, [(-1.45, -1.05, 0.6), (1.45, -1.05, 0.6), (1.45, -1.05, ZE), (-1.45, -1.05, ZE)], fill=(34, 28, 22))
    for sd in (-1, 1):
        P.quad(d, [(sd * 1.45, -1.05, 0.6), (sd * 1.45, IFL, 0.6), (sd * 1.45, IFL, ZE), (sd * 1.45, -1.05, ZE)], fill=(44, 30, 20))
        P.quad(d, [(sd * 1.45, -0.62, 0.6), (sd * 1.1, -0.62, 0.6), (sd * 1.1, -0.62, ZE), (sd * 1.45, -0.62, ZE)], fill=(24, 18, 14))
    for i in range(30):
        z = 1.0 + i * 0.9
        d.line([P.p(-1.45, -1.05, z), P.p(1.45, -1.05, z)], fill=(28, 22, 18), width=1)
    win = Image.new("L", (W, H), 0)
    dw = ImageDraw.Draw(win)
    bays = [2.9 + 1.9 * k for k in range(12)]
    for z in reversed(bays):
        for sd in (-1, 1):
            # window between backrests
            q = [(sd * 1.45, -0.45, z + 0.75), (sd * 1.45, 0.35, z + 0.75), (sd * 1.45, 0.35, z + 1.6), (sd * 1.45, -0.45, z + 1.6)]
            P.quad(d, q, fill=(10, 14, 26))
            dw.polygon([P.p(*p) for p in q], fill=255)
            P.quad(d, [(sd * 1.45, -0.05, z + 0.75), (sd * 1.45, -0.02, z + 0.75), (sd * 1.45, -0.02, z + 1.6), (sd * 1.45, -0.05, z + 1.6)], fill=(60, 40, 24))
            for zz, face in ((z, 1), (z + 1.2, -1)):
                # seat block
                P.quad(d, [(sd * 0.45, 1.0, zz), (sd * 1.45, 1.0, zz), (sd * 1.45, 1.0, zz + 0.55), (sd * 0.45, 1.0, zz + 0.55)], fill=(30, 54, 42))
                P.quad(d, [(sd * 0.45, 1.0, zz), (sd * 0.45, IFL, zz), (sd * 0.45, IFL, zz + 0.55), (sd * 0.45, 1.0, zz + 0.55)], fill=(18, 30, 24))
                bz = zz + (0.55 if face == 1 else 0.0)
                P.quad(d, [(sd * 0.45, 1.0, bz), (sd * 0.45, -0.1, bz), (sd * 0.45, -0.1, bz + 0.12), (sd * 0.45, 1.0, bz + 0.12)], fill=(22, 38, 30))
                P.quad(d, [(sd * 0.45, -0.1, bz), (sd * 1.45, -0.1, bz), (sd * 1.45, -0.1, bz + 0.12), (sd * 0.45, -0.1, bz + 0.12)], fill=(40, 30, 20))
                if zz > 3.2:
                    P.quad(d, [(sd * 0.45, 1.0, bz), (sd * 1.45, 1.0, bz), (sd * 1.45, -0.1, bz), (sd * 0.45, -0.1, bz)], fill=(26, 46, 36))
    lamps_z = [3 + 3 * k for k in range(8)]
    for z in lamps_z:
        x, y = P.p(0, -1.0, z)
        rr = 0.18 * P.f / z
        d.ellipse([x - rr, y - rr * 0.5, x + rr, y + rr * 0.5], fill=(70, 60, 40))

    def lamps(im, dl):
        for z in lamps_z:
            x, y = P.p(0, -1.0, z)
            rr = 0.14 * P.f / z
            dl.ellipse([x - rr, y - rr * 0.5, x + rr, y + rr * 0.5], fill=(255, 230, 170))
            a, b = P.p(-1.4, IFL, z - 1.2), P.p(1.4, IFL, z + 1.2)
            dl.ellipse([a[0], b[1], b[0], a[1]], fill=(90, 64, 30))
            for sd in (-1, 1):
                q = [P.p(sd * 0.45, 1.0, z - 1), P.p(sd * 1.45, 1.0, z - 1), P.p(sd * 1.45, 1.0, z + 1), P.p(sd * 0.45, 1.0, z + 1)]
                dl.polygon(q, fill=(26, 20, 10))
    L = light_layer(lamps, 14)
    im2 = Image.fromarray(L)
    for z in lamps_z:
        x, y = P.p(0, -1.0, z)
        glow(im2, x, y, 2.4 * P.f / z, (255, 180, 90), 0.5)
    Lw = np.asarray(win.filter(ImageFilter.GaussianBlur(3)), np.uint8)
    winc = np.stack([Lw * 0.25, Lw * 0.4, Lw * 0.7], -1).astype(np.uint8)
    warmwin = np.stack([Lw * 0.9, Lw * 0.6, Lw * 0.28], -1).astype(np.uint8)
    lamps_a = np.asarray(im2)
    ghost = (lamps_a[..., ::-1].astype(np.float32) * np.array([0.5, 0.8, 1.0])).astype(np.uint8)
    return {"base": img, "layers": {"lamps": lamps_a, "ghost": ghost, "win": winc, "warmwin": warmwin}}


def interior_lights(c, t):
    fl = c.sh.get("flicker", 0.05)
    k = 1.0
    if flicker(t, 5, 12) < fl: k = 0.25
    gh = 0.0
    if "ghost" in c.cues:
        gh = min(1.0, max(0.0, (t - c.cue("ghost")) / 1.5))
        k *= 1 - 0.6 * gh
    if "jolt" in c.cues:
        j = c.cue("jolt")
        if j <= t < j + 1.6:
            k = 1.0 if flicker(t, 9, 20) > 0.5 else 0.1
    pas = 0.0
    ph = (t * 0.7) % 1.0
    if ph < 0.12: pas = math.sin(ph / 0.12 * math.pi)
    win = 0.25 + 0.75 * pas
    warm = 0.0
    if "station" in c.cues and t >= c.cue("station"):
        win, warm = 0.0, 1.0
    return {"lamps": k, "ghost": gh, "win": win, "warmwin": warm}


# ================================================================== SET: driver's cab
def cab_static(c):
    img = Image.new("RGBA", (W, H), (20, 19, 22, 255))
    nz = noise_tex(W, H, 4, 12, 1)
    img = Image.composite(Image.new("RGBA", (W, H), (32, 28, 28, 255)), img, nz.point(lambda v: int(v * 0.5)))
    d = ImageDraw.Draw(img)
    hole = Image.new("L", (W, H), 255)
    dh = ImageDraw.Draw(hole)
    wins = [(300, 170, 900, 540), (1020, 170, 1620, 540)]
    for w in wins:
        d.rounded_rectangle([w[0] - 26, w[1] - 26, w[2] + 26, w[3] + 26], radius=60, fill=(12, 12, 14, 255))
        dh.rounded_rectangle(w, radius=40, fill=0)
    img.putalpha(hole)
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(4)
    for w in wins:  # raindrops on glass
        for _ in range(140):
            x, y = rng.uniform(w[0], w[2]), rng.uniform(w[1], w[3])
            r = rng.uniform(2, 6)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(150, 160, 180, int(rng.uniform(40, 110))))
    # boiler backplate / controls
    d.chord([360, 600, 1560, 1400], 180, 360, fill=(26, 22, 22, 255))
    d.rectangle([840, 800, 1080, 960], fill=(14, 10, 10, 255))
    d.rectangle([860, 870, 1060, 890], fill=(255, 110, 20, 255))  # firebox gap
    for gx, gy in ((720, 700), (960, 650), (1200, 700)):
        d.ellipse([gx - 64, gy - 64, gx + 64, gy + 64], fill=(40, 34, 30, 255))
        d.ellipse([gx - 52, gy - 52, gx + 52, gy + 52], fill=(170, 160, 128, 255))
    for x in (560, 1360):
        d.rectangle([x - 12, 600, x + 12, 960], fill=(46, 40, 34, 255))
    d.line([(400, 760), (640, 760)], fill=(60, 52, 44, 255), width=16)
    # empty driver's seat (right)
    d.rounded_rectangle([1560, 720, 1760, 800], radius=20, fill=(28, 22, 20, 255))
    d.rounded_rectangle([1720, 540, 1790, 800], radius=24, fill=(24, 20, 18, 255))
    d.rectangle([1650, 800, 1670, 960], fill=(18, 16, 16, 255))

    def fire(im, dl):
        dl.ellipse([560, 700, 1360, 1150], fill=(160, 70, 16))
        dl.ellipse([820, 840, 1100, 920], fill=(255, 140, 40))
    Lf = light_layer(fire, 50)

    def gauge(im, dl):
        for gx, gy in ((720, 700), (960, 650), (1200, 700)):
            dl.ellipse([gx - 90, gy - 90, gx + 90, gy + 90], fill=(60, 70, 40))
    Lg = light_layer(gauge, 30)
    return {"base": img, "layers": {"fire": Lf, "gauge": Lg}}


CP = Persp(960, 380, 700)


def cab_bg(c, t):
    img = vgrad(W, H, (6, 8, 16), (30, 36, 52), 0, 380).copy()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 380, W, H], fill=(12, 12, 16))
    P = CP
    sp = c.sh.get("speed", 14.0)
    off = (t * sp) % 0.8
    zs = [1.2 + k * 0.8 - off for k in range(200)]
    for z in reversed(zs):
        if z < 0.9: continue
        P.quad(d, [(-1.3, 2.4, z), (1.3, 2.4, z), (1.3, 2.4, z + 0.25), (-1.3, 2.4, z + 0.25)], fill=(32, 28, 26))
    for X in (-0.75, 0.75):
        d.polygon([P.p(X - 0.05, 2.4, 0.9), P.p(X + 0.05, 2.4, 0.9), P.p(X + 0.05, 2.4, 300), P.p(X - 0.05, 2.4, 300)], fill=(100, 104, 116))
    poff = (t * sp) % 25
    for k in range(10):
        z = 2 + k * 25 - poff
        if z < 1: continue
        for sd in (-1, 1):
            a, b = P.p(sd * 4.2, 2.4, z), P.p(sd * 4.2, -5, z)
            d.line([a, b], fill=(18, 18, 22), width=max(1, int(0.25 * P.f / z)))
    glow(img, 960, 400, 520, (200, 210, 230), 0.25)
    glow(img, 960, 600, 360, (255, 230, 180), 0.25)
    return img


def cab_lights(c, t):
    return {"fire": 0.65 + 0.35 * flicker(t, 6, 14), "gauge": 0.7}


def cab_post(c, t, img):
    d = ImageDraw.Draw(img)
    for i, (gx, gy) in enumerate(((720, 700), (960, 650), (1200, 700))):
        a = math.radians(200 + 60 * i + 25 * math.sin(t * (1.3 + i) + i) + 6 * math.sin(t * 9 + i))
        d.line([gx, gy, gx + 44 * math.cos(a), gy + 44 * math.sin(a)], fill=(150, 20, 20), width=4)
        d.ellipse([gx - 6, gy - 6, gx + 6, gy + 6], fill=(20, 18, 16))
    # the throttle lever moves on its own
    ang = math.radians(-120 + 18 * math.sin(t * 0.8))
    px, py = 1300, 900
    ex, ey = px + 260 * math.cos(ang), py + 260 * math.sin(ang)
    d.line([px, py, ex, ey], fill=(70, 62, 52), width=18)
    d.ellipse([ex - 22, ey - 22, ex + 22, ey + 22], fill=(120, 30, 24))
    d.ellipse([px - 30, py - 30, px + 30, py + 30], fill=(40, 36, 32))


# ================================================================== SET: window — childhood memory outside
def memory_house(w, h, rng, people=True):
    img = vgrad(w, h, (255, 196, 120), (255, 236, 190), 0, int(h * 0.62))
    d = ImageDraw.Draw(img)
    glow(img, w * 0.78, h * 0.42, h * 0.6, (255, 220, 150), 0.5)
    d.polygon(ridge(rng, w, h * 0.6, h * 0.04), fill=(190, 150, 100))
    d.rectangle([0, h * 0.7, w, h], fill=(176, 130, 82))
    # house
    hx0, hx1, hy0, hy1 = w * 0.18, w * 0.7, h * 0.36, h * 0.78
    d.rectangle([hx0, hy0, hx1, hy1], fill=(200, 140, 90))
    d.polygon([(hx0 - w * 0.04, hy0 + 6), (hx1 + w * 0.04, hy0 + 6), (hx1 - w * 0.03, h * 0.22), (hx0 + w * 0.03, h * 0.22)], fill=(130, 56, 36))
    for k in range(14):
        x = hx0 - w * 0.03 + k * (hx1 - hx0 + w * 0.06) / 14
        d.line([x, hy0 + 4, x + w * 0.004, h * 0.23], fill=(110, 46, 30), width=2)
    dx0, dx1 = w * 0.4, w * 0.5
    d.rectangle([dx0, h * 0.48, dx1, hy1], fill=(255, 210, 130))
    d.rectangle([hx0 + w * 0.05, h * 0.47, hx0 + w * 0.13, h * 0.6], fill=(90, 60, 40))
    d.rectangle([hx1 - w * 0.12, h * 0.47, hx1 - w * 0.05, h * 0.6], fill=(90, 60, 40))
    # tulsi planter + chulha
    d.rectangle([w * 0.78, h * 0.66, w * 0.84, h * 0.78], fill=(190, 110, 70))
    for k in range(7):
        d.ellipse([w * 0.79 + k * 6, h * 0.6 - (k % 3) * 8, w * 0.79 + k * 6 + 22, h * 0.64], fill=(60, 110, 50))
    d.chord([w * 0.53, h * 0.72, w * 0.61, h * 0.82], 180, 360, fill=(120, 80, 60))
    return img, (w * 0.57, h * 0.73)


def window_static(c):
    rng = np.random.default_rng(21)
    img = Image.new("RGBA", (W, H), (30, 22, 16, 255))
    nz = noise_tex(W, H, 3, 2, 1)
    img = Image.composite(Image.new("RGBA", (W, H), (44, 32, 22, 255)), img, nz.point(lambda v: int(v * 0.5)))
    hole = Image.new("L", (W, H), 255)
    ImageDraw.Draw(hole).rounded_rectangle([380, 190, 1460, 830], radius=50, fill=0)
    img.putalpha(hole)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([350, 160, 1490, 860], radius=70, outline=(70, 50, 30, 255), width=34)
    d.rectangle([380, 500, 1460, 520], fill=(66, 46, 28, 255))
    for x in range(400, 1460, 54):  # window bars
        d.rectangle([x, 190, x + 8, 830], fill=(40, 34, 30, 255))
    d.rectangle([300, 860, 1540, 920], fill=(56, 40, 26, 255))
    mem, fire_at = memory_house(1080, 640, rng)
    c.state["mem"] = mem
    c.state["fire_at"] = (380 + fire_at[0], 190 + fire_at[1])

    def lamp(im, dl):
        dl.ellipse([1300, -200, 2300, 700], fill=(80, 56, 26))
    return {"base": img, "layers": {"lamp": light_layer(lamp, 80)}}


def window_bg(c, t):
    img = Image.new("RGB", (W, H), (8, 10, 20))
    d = ImageDraw.Draw(img)
    for k in range(9):
        y = 260 + k * 60
        x = (k * 377 - t * 1400 * (1 + 0.2 * k)) % 2400 - 200
        d.line([x, y, x + 260, y], fill=(50, 60, 90), width=3)
    ch = c.cue("change", 1e9)
    p = min(max((t - ch) / 2.5, 0), 1)
    if p > 0:
        mem = c.state["mem"].copy()
        fx, fy = c.state["fire_at"][0] - 380, c.state["fire_at"][1] - 190
        glow(mem, fx, fy - 6, 40, (255, 140, 40), 0.6 + 0.4 * flicker(t, 3, 10))
        smoke(mem, t, lambda tb: (fx, fy - 20), 0, rate=4, col=(230, 220, 210), up=40, drift=(8, 0), r0=10, grow=30, a0=0.35, life=4)
        big = Image.new("RGB", (W, H), (0, 0, 0))
        big.paste(mem, (380, 190))
        img = Image.blend(img, big, p)
    return img


def window_lights(c, t):
    return {"lamp": 0.8 if flicker(t, 8, 9) > 0.05 else 0.4}


def window_post(c, t, img):
    tc = c.cue("touch", 1e9)
    if t > tc + 0.8:
        k = 0.5 + 0.5 * math.sin((t - tc) * 3)
        glow(img, c.sh.get("touch_x", 1390), c.sh.get("touch_y", 520), 140, (255, 220, 160), 0.25 * k)


# ================================================================== SET: childhood memory (full frame)
def mem_static(c):
    rng = np.random.default_rng(31)
    img, _ = memory_house(W, H, rng)
    img = img.filter(ImageFilter.GaussianBlur(3))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 820, W, H], fill=(170, 124, 76))
    # tree on the right
    d.polygon([(1700, 830), (1730, 380), (1760, 830)], fill=(70, 46, 30))
    for k in range(12):
        x, y, r = 1730 + rng.uniform(-200, 200), 360 + rng.uniform(-120, 80), rng.uniform(70, 130)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(int(rng.uniform(70, 100)), int(rng.uniform(100, 130)), 50))
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    return {"base": img, "layers": {}}


def mem_post(c, t, img):
    rng = np.random.default_rng(7)
    for k in range(36):
        x0, y0 = rng.uniform(0, W), rng.uniform(150, 950)
        x = (x0 + 18 * t + 30 * math.sin(t * 0.5 + k)) % W
        y = y0 - 10 * t % 900
        glow(img, x, y, rng.uniform(6, 16), (255, 240, 200), 0.6 * (0.5 + 0.5 * math.sin(t * 2 + k)))


# ================================================================== SET: newspaper (high-res, camera zooms in)
NS = 2.2


def news_static(c):
    S = NS
    Wb, Hb = int(W * S), int(H * S)
    img = vgrad(Wb, Hb, (24, 18, 14), (12, 9, 8))
    nz = noise_tex(Wb, Hb, 8, 3, 2)
    img = Image.composite(Image.new("RGB", (Wb, Hb), (36, 26, 20)), img, nz.point(lambda v: int(v * 0.4)))
    pw, ph = int(1500 * S), int(900 * S)
    paper = Image.new("RGB", (pw, ph), (212, 196, 152))
    pn = noise_tex(pw, ph, 5, 6, 1)
    paper = Image.composite(Image.new("RGB", (pw, ph), (178, 156, 108)), paper, pn.point(lambda v: int(v * 0.5)))
    st = noise_tex(pw, ph, 120, 7, 40)
    paper = Image.composite(Image.new("RGB", (pw, ph), (160, 128, 80)), paper, st.point(lambda v: max(0, v - 150) * 2))
    d = ImageDraw.Draw(paper)
    u = S
    d.text((pw / 2, 70 * u), "दैनिक समाचार", font=font(F_TITLE, int(92 * u)), fill=(28, 22, 18), anchor="mm")
    d.line([40 * u, 128 * u, pw - 40 * u, 128 * u], fill=(40, 32, 26), width=int(5 * u))
    d.text((60 * u, 146 * u), "पुराना अंक", font=font(F_BOLD, int(22 * u)), fill=(60, 50, 40), anchor="lm")
    d.text((pw - 60 * u, 146 * u), "मूल्य: 1 रुपया", font=font(F_BOLD, int(22 * u)), fill=(60, 50, 40), anchor="rm")
    d.line([40 * u, 164 * u, pw - 40 * u, 164 * u], fill=(40, 32, 26), width=int(2 * u))
    d.text((pw / 2, 230 * u), "रहस्यमयी ट्रेन अचानक गायब!", font=font(F_BLACK, int(84 * u)), fill=(20, 16, 14), anchor="mm")
    d.text((pw / 2, 310 * u), "ट्रेन में बैठे सभी यात्री लापता — आज तक कोई सुराग नहीं", font=font(F_BOLD, int(36 * u)), fill=(40, 32, 26), anchor="mm")
    # photo
    px0, py0, px1, py1 = 60 * u, 360 * u, 800 * u, 840 * u
    photo = vgrad(int(px1 - px0), int(py1 - py0), (120, 116, 110), (70, 66, 62))
    pd = ImageDraw.Draw(photo)
    ph_w, ph_h = photo.size
    tr, _ = train_strip(4, 0.55 * u)
    tr = tr.crop((tr.width - int(ph_w * 1.25), 0, tr.width, tr.height))
    tr = tr.transpose(Image.FLIP_LEFT_RIGHT)
    photo.paste(tr, (int(-ph_w * 0.05), int(ph_h * 0.36)), tr)
    pd.rectangle([0, ph_h * 0.36 + tr.height - 6 * u, ph_w, ph_h], fill=(60, 58, 56))
    gx, gy = ph_w * 0.62, ph_h * 0.36 + tr.height - 8 * u
    g, ga = figures.person("girl", "hold", 0, int(ph_h * 0.36), rim=(200, 200, 200), ld=(-0.7, -0.7))
    c.state["girl_photo"] = (px0 + gx - ga["foot"][0] + ga["toy"][0], py0 + gy - ga["foot"][1] + ga["toy"][1])
    photo.paste(g, (int(gx - ga["foot"][0]), int(gy - ga["foot"][1])), g)
    photo = photo.convert("L").convert("RGB")
    gn = noise_tex(ph_w, ph_h, 1, 8, 0)
    photo = Image.blend(photo, Image.merge("RGB", [gn] * 3), 0.12)
    paper.paste(photo, (int(px0), int(py0)))
    d.rectangle([px0, py0, px1, py1], outline=(30, 26, 22), width=int(3 * u))
    d.text((px0, py1 + 22 * u), "फाइल फोटो: लापता ट्रेन", font=font(F_BOLD, int(20 * u)), fill=(50, 42, 34), anchor="lm")
    # text columns (greeked)
    rng = np.random.default_rng(2)
    for col in range(2):
        cx0 = 840 * u + col * 320 * u
        y = 370 * u
        while y < 860 * u:
            ln = rng.uniform(0.6, 1.0) * 290 * u
            d.rectangle([cx0, y, cx0 + ln, y + 9 * u], fill=(120, 106, 80))
            y += 22 * u
            if rng.random() < 0.08: y += 18 * u
    d.line([pw * 0.5, 0, pw * 0.5, ph], fill=(170, 150, 104), width=int(3 * u))
    # torn / worn edges
    m = Image.new("L", (pw, ph), 255)
    dm = ImageDraw.Draw(m)
    for x in range(0, pw, int(10 * u)):
        dm.rectangle([x, 0, x + 10 * u, rng.uniform(0, 14) * u], fill=0)
        dm.rectangle([x, ph - rng.uniform(0, 14) * u, x + 10 * u, ph], fill=0)
    paper = paper.rotate(-2.5, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
    m = m.rotate(-2.5, resample=Image.BICUBIC, expand=True)
    ox, oy = int((Wb - paper.width) / 2), int((Hb - paper.height) / 2 + 30 * S)
    sh = Image.new("L", (Wb, Hb), 0)
    sh.paste(m.point(lambda v: v // 2), (ox + int(20 * S), oy + int(26 * S)))
    sh = sh.filter(ImageFilter.GaussianBlur(20 * S))
    img = Image.composite(Image.new("RGB", (Wb, Hb), (0, 0, 0)), img, sh)
    img.paste(paper, (ox, oy), m)
    c.state["news_off"] = (ox, oy)
    toy = c.state["girl_photo"]
    toy = (ox + toy[0] + 0, oy + toy[1])

    def lamp(im, dl):
        dl.ellipse([-Wb * 0.2, -Hb * 0.4, Wb * 0.8, Hb * 0.9], fill=(70, 54, 30))
    L = light_layer(lamp, int(120 * S), (Wb, Hb))
    red = Image.new("RGB", (Wb, Hb), 0)
    glow(red, toy[0], toy[1], 40 * S, (255, 30, 20), 1.0)
    return {"base": img, "layers": {"lamp": L, "red": np.asarray(red)}}


def news_lights(c, t):
    r = 0.0
    if "red" in c.cues:
        r = min(1.0, max(0, (t - c.cue("red")) / 1.0)) * (0.8 + 0.2 * math.sin(t * 6))
    return {"lamp": 1.0 if flicker(t, 4, 10) > 0.05 else 0.6, "red": r}


# ================================================================== SET: old photograph in the station master's hand
PS = 1.5


def photo_static(c):
    S = PS
    Wb, Hb = int(W * S), int(H * S)
    rng = np.random.default_rng(41)
    img = vgrad(Wb, Hb, (8, 10, 18), (20, 18, 24))
    for _ in range(24):
        x, y, r = rng.uniform(0, Wb), rng.uniform(0, Hb), rng.uniform(40, 140) * S
        col = (255, 180, 90) if rng.random() < 0.6 else (120, 150, 220)
        glow(img, x, y, r, col, rng.uniform(0.1, 0.3), p=0.8)
    img = img.filter(ImageFilter.GaussianBlur(6 * S))
    pw, ph = int(560 * S), int(720 * S)
    card = Image.new("RGB", (pw, ph), (222, 210, 180))
    inner = vgrad(pw - int(60 * S), ph - int(150 * S), (170, 140, 100), (110, 86, 60))
    di = ImageDraw.Draw(inner)
    iw, ih = inner.size
    glow(inner, iw / 2, ih * 0.4, iw * 0.6, (255, 230, 190), 0.25)
    g, ga = figures.person("girl", "hold", 0, int(ih * 0.82), rim=(255, 230, 190), ld=(-0.7, -0.7), fill=(84, 60, 44))
    gx, gy = iw * 0.5, ih * 0.97
    inner.paste(g, (int(gx - ga["foot"][0]), int(gy - ga["foot"][1])), g)
    inner = Image.blend(inner, Image.merge("RGB", [noise_tex(iw, ih, 1, 3, 0)] * 3), 0.08)
    # keep the toy train red (hand-tinted look)
    toy = (gx - ga["foot"][0] + ga["toy"][0], gy - ga["foot"][1] + ga["toy"][1])
    card.paste(inner, (int(30 * S), int(30 * S)))
    dc = ImageDraw.Draw(card)
    dc.text((pw / 2, ph - 60 * S), "मेरी गुड़िया", font=font(F_BOLD, int(40 * S)), fill=(60, 44, 30), anchor="mm")
    wear = noise_tex(pw, ph, 60, 5, 20)
    card = Image.composite(Image.new("RGB", (pw, ph), (150, 120, 80)), card, wear.point(lambda v: max(0, v - 160) * 2))
    card = card.rotate(-5, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0))
    m = Image.new("L", (pw, ph), 255).rotate(-5, resample=Image.BICUBIC, expand=True)
    ox, oy = int(Wb / 2 - card.width / 2), int(Hb / 2 - card.height / 2 - 20 * S)
    img.paste(card, (ox, oy), m)
    d = ImageDraw.Draw(img)
    # hand: thumb over the bottom edge, fingers below
    hx, hy = Wb / 2 + 40 * S, oy + card.height - 60 * S
    d.rounded_rectangle([hx - 250 * S, hy + 30 * S, hx + 160 * S, Hb], radius=int(120 * S), fill=(30, 22, 20))
    d.rounded_rectangle([hx - 60 * S, hy - 40 * S, hx + 70 * S, hy + 70 * S], radius=int(50 * S), fill=(38, 28, 24))
    d.rounded_rectangle([hx - 300 * S, hy + 120 * S, hx - 150 * S, Hb], radius=int(60 * S), fill=(26, 20, 18))
    red = Image.new("RGB", (Wb, Hb), 0)
    ang = math.radians(5)
    tx, ty = toy[0] + 30 * S - pw / 2, toy[1] + 30 * S - ph / 2
    rx = tx * math.cos(ang) - ty * math.sin(ang) + card.width / 2 + ox
    ry = tx * math.sin(ang) + ty * math.cos(ang) + card.height / 2 + oy
    glow(red, rx, ry, 50 * S, (255, 40, 30), 0.8)

    def lamp(im, dl):
        dl.ellipse([-Wb * 0.3, -Hb * 0.3, Wb * 0.7, Hb * 0.8], fill=(90, 60, 24))
    L = light_layer(lamp, int(100 * S), (Wb, Hb))
    return {"base": img, "layers": {"lamp": L, "red": np.asarray(red)}}


def photo_lights(c, t):
    return {"lamp": 0.85 + 0.15 * flicker(t, 2, 6), "red": 0.6 + 0.4 * math.sin(t * 2)}


# ================================================================== SET: home at dawn
def home_static(c):
    rng = np.random.default_rng(51)
    img = vgrad(W, H, (60, 70, 130), (255, 176, 110), 0, 620)
    glow(img, 1500, 600, 520, (255, 200, 130), 0.6)
    glow(img, 1500, 600, 90, (255, 240, 200), 1.0)
    d = ImageDraw.Draw(img)
    d.polygon(ridge(rng, W, 610, 20), fill=(120, 80, 80))
    d.rectangle([0, 680, W, H], fill=(110, 76, 52))
    d.polygon([(0, 1000), (760, 760), (980, 760), (900, H), (0, H)], fill=(140, 100, 64))
    # house
    d.rectangle([360, 400, 1200, 780], fill=(190, 128, 82))
    for y in range(410, 780, 26):
        d.line([360, y, 1200, y], fill=(178, 118, 76), width=2)
    d.polygon([(320, 410), (1240, 410), (1150, 260), (410, 260)], fill=(120, 52, 34))
    for k in range(30):
        x = 330 + k * 31
        d.line([x, 408, x + 25 * (k - 15) / 15 + 10, 264], fill=(100, 42, 28), width=3)
    d.rectangle([470, 470, 600, 590], fill=(70, 46, 30))
    d.rectangle([1000, 470, 1110, 590], fill=(70, 46, 30))
    d.rectangle([838, 532, 982, 782], fill=(60, 40, 26))  # door frame
    d.rectangle([850, 545, 970, 780], fill=(255, 214, 140))  # lit inside
    glow(img, 910, 680, 120, (255, 210, 140), 0.3)
    d = ImageDraw.Draw(img)
    d.rectangle([1300, 700, 1370, 790], fill=(190, 110, 70))  # tulsi
    for k in range(8):
        d.ellipse([1300 + k * 8, 640 - (k % 3) * 10, 1300 + k * 8 + 26, 700], fill=(50, 100, 46))
    # trees
    for tx in (160, 1700, 1860):
        d.polygon([(tx - 14, 780), (tx, 380), (tx + 14, 780)], fill=(40, 28, 26))
        for k in range(9):
            x, y, r = tx + rng.uniform(-150, 150), 380 + rng.uniform(-110, 80), rng.uniform(60, 110)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(int(rng.uniform(40, 60)), int(rng.uniform(50, 70)), 46))
    return {"base": img, "layers": {}}


def home_pre(c, t, img):
    o = c.cue("open", 1e9)
    f = min(max((t - o) / 1.2, 0), 1)
    d = ImageDraw.Draw(img)
    w = 60 * (1 - f) + 10 * f
    d.rectangle([850, 545, 850 + w, 780], fill=(110, 66, 36))
    d.rectangle([970 - w, 545, 970, 780], fill=(110, 66, 36))
    if f < 1:
        d.line([910, 545, 910, 780], fill=(60, 38, 22), width=3)
    for k in range(5):  # birds
        bx = (k * 300 + t * (60 + 10 * k)) % (W + 200) - 100
        by = 160 + 40 * k + 8 * math.sin(t * 3 + k)
        s = 10 + 2 * k
        fl = 6 * math.sin(t * 9 + k)
        d.line([(bx - s, by - fl), (bx, by), (bx + s, by - fl)], fill=(40, 30, 40), width=3)


# ================================================================== SET: epilogue landscape
def epi_static(c):
    rng = np.random.default_rng(61)
    img = vgrad(W, H, (70, 90, 160), (255, 190, 120), 0, 600)
    glow(img, 1350, 560, 700, (255, 210, 140), 0.55)
    glow(img, 1350, 560, 110, (255, 245, 210), 1.0)
    d = ImageDraw.Draw(img)
    d.polygon(ridge(rng, W, 580, 26), fill=(140, 100, 110))
    d.rectangle([0, 620, W, H], fill=(150, 130, 70))
    for y in range(640, H, 24):
        d.line([0, y, W, y + 10], fill=(140, 122, 64), width=2)
    # railway embankment far away
    d.rectangle([0, 640, W, 652], fill=(90, 70, 60))
    d.line([0, 640, W, 640], fill=(255, 220, 170), width=2)
    # small house left
    d.rectangle([180, 600, 440, 760], fill=(170, 112, 74))
    d.polygon([(160, 604), (460, 604), (420, 540), (200, 540)], fill=(110, 48, 32))
    d.rectangle([290, 670, 330, 760], fill=(255, 210, 140))
    # charpai (cot)
    d.rectangle([480, 742, 640, 752], fill=(110, 70, 40))
    for x in (486, 634):
        d.rectangle([x - 3, 742, x + 3, 782], fill=(80, 50, 30))
    return {"base": img, "layers": {}}


def epi_pre(c, t, img):
    d = ImageDraw.Draw(img)
    for k in range(7):
        bx = (k * 260 + t * (40 + 6 * k)) % (W + 200) - 100
        by = 200 + 35 * k + 8 * math.sin(t * 2 + k)
        s, fl = 8 + k, 5 * math.sin(t * 8 + k)
        d.line([(bx - s, by - fl), (bx, by), (bx + s, by - fl)], fill=(50, 40, 50), width=2)
    tp = c.cue("train", 1e9)
    if t > tp:  # a tiny train crosses far away in the morning light
        x = -400 + (t - tp) * 160
        spr, m = train_strip(4, 0.08)
        img.paste(spr, (int(x), 640 - int(m["rail"])), spr)


# ================================================================== SET: black / title
def black_static(c):
    return {"base": Image.new("RGB", (W, H), (0, 0, 0)), "layers": {}}


def title_static(c):
    s = track_static(c)
    b = Image.blend(s["base"], Image.new("RGB", (W, H), 0), 0.35)
    return {"base": b, "layers": {}}


def title_pre(c, t, img):
    c.sh.setdefault("_", 0)
    lx, ly = TV.p(0, -1.95, 300)
    glow(img, lx, ly, 160, (255, 225, 170), 0.35 + 0.1 * math.sin(t * 2))
    glow(img, lx, ly, 20, (255, 250, 235), 0.9)
    streak(img, lx, ly, 700, (200, 220, 255), 0.35)


SETS = {
    "title":    dict(static=title_static, pre=title_pre),
    "station":  dict(static=station_static, lights=station_lights, pre=station_pre, rim=(130, 150, 200), ld=(-0.4, -0.9)),
    "clock":    dict(static=clock_static, lights=clock_lights, post=clock_post),
    "track":    dict(static=track_static, pre=track_pre),
    "platform": dict(static=platform_static, lights=platform_lights, pre=platform_pre, persp=(980, 500, 820, FLOOR),
                     rim=(255, 190, 120), ld=(0.9, -0.4)),
    "door":     dict(static=door_static, lights=door_lights, post=door_post, rim=(255, 190, 110), ld=(0.9, -0.3)),
    "interior": dict(static=interior_static, lights=interior_lights, persp=(960, 470, 760, IFL), rim=(255, 196, 120), ld=(0.0, -1.0)),
    "cab":      dict(static=cab_static, bg=cab_bg, lights=cab_lights, post=cab_post, rim=(255, 140, 60), ld=(0.6, 0.5)),
    "window":   dict(static=window_static, bg=window_bg, lights=window_lights, post=window_post, rim=(255, 200, 140), ld=(-0.9, -0.3)),
    "memory":   dict(static=mem_static, post=mem_post, rim=(255, 230, 170), ld=(0.8, -0.5)),
    "news":     dict(static=news_static, lights=news_lights),
    "photo":    dict(static=photo_static, lights=photo_lights),
    "home":     dict(static=home_static, pre=home_pre, rim=(255, 200, 130), ld=(0.9, -0.3)),
    "epilogue": dict(static=epi_static, pre=epi_pre, rim=(255, 210, 150), ld=(0.9, -0.3)),
    "black":    dict(static=black_static),
}
