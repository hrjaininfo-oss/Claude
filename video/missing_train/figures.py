"""Characters for "रहस्यमयी ट्रेन", drawn in code as rim-lit cinematic silhouettes.

person(who, pose, ph, hpx, ...) -> (RGBA sprite, anchors)
  anchors["foot"] is the point between the feet; other anchors (toy, lantern, hand)
  are where glows are added by the scene.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

SS = 2  # supersampling

FIG = {  # proportions as fractions of full height (head top ~0, feet 1)
    "aarav":  dict(hr=0.064, hy=0.075, sy=0.188, py=0.52, th=0.245, sn=0.235, ua=0.16, fa=0.15,
                   lw=0.084, aw=0.062, tw=(0.095, 0.076), fill=(17, 19, 28)),
    "master": dict(hr=0.064, hy=0.09, sy=0.2, py=0.53, th=0.235, sn=0.23, ua=0.155, fa=0.145,
                   lw=0.084, aw=0.064, tw=(0.098, 0.094), fill=(20, 17, 16), stoop=0.045),
    "girl":   dict(hr=0.1, hy=0.11, sy=0.26, py=0.575, th=0.2, sn=0.2, ua=0.15, fa=0.135,
                   lw=0.085, aw=0.065, tw=(0.082, 0.078), fill=(22, 20, 34)),
    "boy":    dict(hr=0.1, hy=0.11, sy=0.26, py=0.575, th=0.2, sn=0.2, ua=0.15, fa=0.135,
                   lw=0.088, aw=0.066, tw=(0.084, 0.078), fill=(28, 20, 16)),
    "mother": dict(hr=0.066, hy=0.082, sy=0.192, py=0.53, th=0.24, sn=0.235, ua=0.155, fa=0.145,
                   lw=0.075, aw=0.058, tw=(0.084, 0.088), fill=(26, 16, 20)),
}
HEIGHT_M = {"aarav": 1.74, "master": 1.66, "girl": 1.08, "boy": 1.0, "mother": 1.56, "hug": 1.74}


def pose_angles(pose, ph):
    """Joint angles (radians from straight down, + = forward)."""
    s, c = math.sin(ph), math.cos(ph)
    P = dict(lf=(0.05, 0.0), lb=(-0.05, -0.02), af=(0.12, 0.28), ab=(-0.1, 0.05), lean=0.0, tilt=0.0, bob=0.0)
    if pose in ("walk", "run"):
        a = 0.42 if pose == "walk" else 0.75
        t1, t2 = a * s, -a * s
        P["lf"] = (t1, t1 - 0.9 * max(0.0, -t1) - 0.1)
        P["lb"] = (t2, t2 - 0.9 * max(0.0, -t2) - 0.1)
        if pose == "walk":
            P["af"], P["ab"] = (-0.32 * s, -0.32 * s + 0.25), (0.32 * s, 0.32 * s + 0.25)
            P["bob"] = -0.012 * abs(c)
        else:
            P["af"], P["ab"] = (-0.8 * s, -0.8 * s + 1.4), (0.8 * s, 0.8 * s + 1.4)
            P["lean"], P["bob"] = 0.06, -0.025 * abs(c)
    elif pose == "sit":
        P["lf"], P["lb"] = (1.45, 0.05), (1.4, 0.0)
        P["af"], P["ab"] = (0.55, 1.35), (0.45, 1.3)
    elif pose == "sit_sad":
        P["lf"], P["lb"] = (1.45, 0.05), (1.4, 0.0)
        P["af"], P["ab"] = (0.9, 2.2), (0.8, 2.1)
        P["tilt"], P["lean"] = 0.25, 0.04
    elif pose == "reach":
        P["af"] = (1.25, 1.45)
    elif pose == "shout":
        P["af"] = (2.3, 2.75 + 0.12 * s)
        P["lean"] = 0.03
    elif pose == "lantern":
        P["af"] = (0.38, 0.12)
    elif pose == "lantern_shout":
        P["af"], P["ab"] = (0.38, 0.12), (2.2, 2.7 + 0.12 * s)
    elif pose == "hold":
        P["af"], P["ab"] = (0.28, 1.45), (0.22, 1.4)
    elif pose == "photo":
        P["af"], P["ab"] = (0.75, 1.5), (0.6, 1.45)
        P["tilt"] = 0.18
    elif pose == "read":
        P["af"], P["ab"] = (0.6, 1.55), (0.5, 1.5)
        P["tilt"] = 0.3
    elif pose == "talk":
        P["af"] = (0.45 + 0.12 * s, 1.15 + 0.2 * s)
    elif pose == "hug":
        P["af"], P["ab"] = (1.25, 2.1), (1.15, 2.0)
        P["lean"] = 0.04
    elif pose == "cook":
        P["af"], P["ab"] = (0.75, 1.3 + 0.25 * s), (0.5, 1.2)
        P["lean"] = 0.05
    elif pose == "clap":
        P["af"], P["ab"] = (0.9, 1.6 + 0.25 * s), (0.85, 1.65 - 0.25 * s)
    elif pose == "arms_open":
        P["af"], P["ab"] = (1.6, 1.9), (1.4, 1.7)
    elif pose == "stumble":
        P["af"], P["ab"] = (1.9, 2.3), (-0.9, -0.5)
        P["lean"] = -0.06
        P["lf"], P["lb"] = (0.3, 0.1), (-0.25, -0.3)
    return P


def _thick(d, pts, w, fill=255):
    d.line(pts, fill=fill, width=max(1, int(w)), joint="curve")
    r = w / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def _rim(mask, ld, k, col, strength=1.0, blur=1.2):
    """Light along the edges of the mask that face the light direction ld."""
    dx, dy = int(round(-ld[0] * k)), int(round(-ld[1] * k))
    sh = ImageChops.offset(mask, dx, dy)
    rim = ImageChops.subtract(mask, sh).filter(ImageFilter.GaussianBlur(blur))
    rim = ImageChops.multiply(rim, mask)
    r = np.asarray(rim, np.float32)[..., None] / 255.0 * strength
    return r * np.array(col, np.float32)[None, None, :]


_LUT = [0 if v < 96 else (255 if v > 160 else (v - 96) * 255 // 64) for v in range(256)]


def _smooth(m, hpx):
    return m.filter(ImageFilter.GaussianBlur(max(1.0, hpx * SS * 0.009))).point(_LUT)


def _finish(front, back, fill, rim, ld, hpx, acc=None, alpha=1.0, rim_k=None):
    front, back = _smooth(front, hpx), _smooth(back, hpx)
    mask = ImageChops.lighter(front, back)
    fa = np.asarray(front, np.float32)[..., None] / 255.0
    ba = np.asarray(back, np.float32)[..., None] / 255.0
    f = np.array(fill, np.float32)
    col = f * fa + f * 0.55 * ba * (1 - fa)
    k = rim_k or max(2, int(hpx * SS * 0.012))
    col += _rim(mask, ld, k, rim, 1.0, blur=max(1.0, hpx * SS * 0.004))
    col += _rim(mask, ld, k * 3, rim, 0.25, blur=max(2.0, hpx * SS * 0.01))
    a = np.asarray(mask, np.float32) * alpha
    out = np.dstack([np.clip(col, 0, 255), a]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA")
    if acc is not None:
        img = Image.alpha_composite(img, acc)
    return img


def person(who, pose="stand", ph=0.0, hpx=300, rim=(150, 170, 210), ld=(-0.8, -0.6), alpha=1.0, fill=None):
    """Profile view, facing right."""
    if who == "hug":
        return hug(ph, hpx, rim, ld)
    if pose in ("back", "back_walk", "front"):
        return person_back(who, pose, ph, hpx, rim, ld, alpha)
    F = FIG[who]
    fill = fill or F["fill"]
    U = hpx * SS
    cw, chh = int(U * 1.3), int(U * 1.32)
    ox, top = cw / 2, U * 0.25
    P = pose_angles(pose, ph)

    def leg(a):
        hip = np.array([0.0, F["py"]])
        knee = hip + F["th"] * np.array([math.sin(a[0]), math.cos(a[0])])
        ank = knee + F["sn"] * np.array([math.sin(a[1]), math.cos(a[1])])
        return hip, knee, ank
    lf, lb = leg(P["lf"]), leg(P["lb"])
    foot_y = max(lf[2][1], lb[2][1]) + F["lw"] * 0.35
    dy = 1.0 - foot_y + P["bob"]
    lean = P["lean"]

    def T(p, k=1.0):  # unit -> canvas px (apply lean for upper body)
        x, y = p
        if k:
            x += lean * (F["py"] - y) / F["py"] * 1.6
        return (ox + x * U, top + (y + dy) * U)

    sh = np.array([0.0, F["sy"]])

    def arm(a):
        el = sh + F["ua"] * np.array([math.sin(a[0]), math.cos(a[0])])
        ha = el + F["fa"] * np.array([math.sin(a[1]), math.cos(a[1])])
        return sh, el, ha
    af, ab = arm(P["af"]), arm(P["ab"])

    front = Image.new("L", (cw, chh), 0)
    back = Image.new("L", (cw, chh), 0)
    df, db = ImageDraw.Draw(front), ImageDraw.Draw(back)
    lw, aw = F["lw"] * U, F["aw"] * U

    # back limbs
    hip, kn, an = lb
    _thick(db, [T(hip, 0), T(kn, 0), T(an, 0)], lw)
    _thick(db, [T(an, 0), T(an + np.array([0.06, 0.0]), 0)], lw * 0.55)
    s_, e_, h_ = ab
    _thick(db, [T(s_), T(e_), T(h_)], aw)

    # torso / clothes
    t0, t1 = F["tw"]
    py, sy = F["py"], F["sy"]
    if who == "mother":
        poly = [(-t0, sy - 0.01), (t0 * 0.9, sy - 0.01), (t1 + 0.03, py), (0.16, 0.985), (-0.17, 0.985), (-t1 - 0.03, py)]
        df.polygon([T(p, 1 if p[1] < py else 0) for p in poly], fill=255)
    elif who == "girl":
        poly = [(-t0, sy), (t0, sy), (0.1, py - 0.08), (0.2, 0.66), (-0.19, 0.66), (-0.1, py - 0.08)]
        df.polygon([T(p, 1 if p[1] < py else 0) for p in poly], fill=255)
    elif who == "master":
        poly = [(-t0, sy - 0.005), (t0, sy - 0.005), (t1 + 0.02, py), (t1 + 0.05, 0.76), (-t1 - 0.04, 0.76), (-t1 - 0.01, py)]
        df.polygon([T(p, 1 if p[1] < py else 0) for p in poly], fill=255)
    else:
        bot = py + (0.06 if who == "aarav" else 0.02)
        poly = [(-t0 * 0.7, sy - 0.012), (t0 * 0.6, sy - 0.012), (t0 + 0.01, sy + 0.06), (t0 * 0.95, sy + 0.17),
                (t1 + 0.01, bot), (-t1 - 0.005, bot), (-t0 * 0.92, sy + 0.2), (-t0 - 0.005, sy + 0.05)]
        df.polygon([T(p) for p in poly], fill=255)
        for sx_ in (-t0 * 0.55, t0 * 0.45):
            cx_, cy_ = T((sx_, sy + 0.03)); rr = 0.045 * U
            df.ellipse([cx_ - rr, cy_ - rr, cx_ + rr, cy_ + rr], fill=255)
        if who == "aarav":  # backpack
            df.rounded_rectangle([T((-t0 - 0.045, sy + 0.035))[0], T((-t0 - 0.045, sy + 0.035))[1],
                                  T((-t0 + 0.02, py - 0.07))[0], T((-t0 + 0.02, py - 0.07))[1]],
                                 radius=int(0.02 * U), fill=255)
    # neck + head
    st = F.get("stoop", 0.0) + P["tilt"] * 0.06
    hc = np.array([0.012 + st, F["hy"] + P["tilt"] * 0.02])
    _thick(df, [T(sh), T(hc + np.array([0, F["hr"] * 0.6]))], F["hr"] * U * 1.0)
    hx, hy = T(hc)
    r = F["hr"] * U
    df.ellipse([hx - r * 0.92, hy - r, hx + r * 0.95, hy + r * 1.02], fill=255)
    df.polygon([(hx + r * 0.85, hy + r * 0.05), (hx + r * 1.12, hy + r * 0.32), (hx + r * 0.8, hy + r * 0.45)], fill=255)  # nose
    if who == "aarav":
        df.polygon([(hx - r * 0.95, hy - r * 0.1), (hx - r * 0.6, hy - r * 1.15), (hx + r * 0.6, hy - r * 1.2),
                    (hx + r * 0.95, hy - r * 0.6), (hx + r * 0.2, hy - r * 0.75)], fill=255)
    elif who == "master":
        df.rectangle([hx - r * 0.95, hy - r * 1.45, hx + r * 0.8, hy - r * 0.55], fill=255)  # cap crown
        df.polygon([(hx + r * 0.5, hy - r * 0.75), (hx + r * 1.55, hy - r * 0.55), (hx + r * 0.5, hy - r * 0.45)], fill=255)
        df.ellipse([hx + r * 0.6, hy + r * 0.35, hx + r * 1.1, hy + r * 0.6], fill=255)  # moustache
    elif who in ("girl", "boy"):
        if who == "girl":
            for k in (0.0, 0.55):
                cx, cy = hx - r * 1.05, hy + r * (0.15 + k)
                df.ellipse([cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32], fill=255)
        df.chord([hx - r * 1.0, hy - r * 1.08, hx + r * 0.98, hy + r * 0.6], 180, 360, fill=255)
    elif who == "mother":
        poly = [(hx + r * 0.75, hy - r * 0.95), (hx - r * 0.2, hy - r * 1.3), (hx - r * 1.35, hy - r * 0.5),
                (hx - r * 1.55, hy + r * 1.4), T((-t0 - 0.03, sy + 0.12)), T((-t0, sy)), (hx - r * 0.2, hy + r * 1.0),
                (hx + r * 0.6, hy - r * 0.2)]
        df.polygon(poly, fill=255)
    # front limbs
    hip, kn, an = lf
    _thick(df, [T(hip, 0), T(kn, 0), T(an, 0)], lw)
    _thick(df, [T(an, 0), T(an + np.array([0.065, 0.0]), 0)], lw * 0.55)
    s_, e_, h_ = af
    _thick(df, [T(s_), T(e_), T(h_)], aw)
    if who == "mother":  # pallu over the front shoulder
        df.polygon([T((t0 * 0.6, sy)), T((t0 + 0.02, sy + 0.05)), T((t1 + 0.035, py + 0.05)), T((0.0, py - 0.02))], fill=255)

    # accessories (coloured)
    acc = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
    da = ImageDraw.Draw(acc)
    anchors = {}
    hand = T(h_)
    anchors["hand"] = hand
    if who == "girl" and pose in ("hold", "stand", "talk"):
        hx2, hy2 = (T(h_) if pose == "hold" else (T(h_)[0] + 0.02 * U, T(h_)[1]))
        tw_, th_ = 0.15 * U, 0.07 * U
        x0, y0 = hx2 - tw_ * 0.35, hy2 - th_ * 0.6
        da.rounded_rectangle([x0, y0, x0 + tw_ * 0.62, y0 + th_], radius=int(th_ * 0.15), fill=(205, 28, 30, 255))
        da.rectangle([x0 + tw_ * 0.62, y0 - th_ * 0.45, x0 + tw_, y0 + th_], fill=(225, 36, 34, 255))
        da.rectangle([x0 + tw_ * 0.68, y0 - th_ * 0.3, x0 + tw_ * 0.92, y0 + th_ * 0.15], fill=(255, 214, 120, 255))
        da.rectangle([x0 + tw_ * 0.12, y0 - th_ * 0.55, x0 + tw_ * 0.24, y0], fill=(120, 16, 18, 255))
        for wx in (0.12, 0.4, 0.8):
            cx = x0 + tw_ * wx
            da.ellipse([cx - th_ * 0.22, y0 + th_ * 0.8, cx + th_ * 0.22, y0 + th_ * 1.24], fill=(20, 16, 16, 255))
        anchors["toy"] = (x0 + tw_ * 0.5, y0 + th_ * 0.4)
        # ribbon
        rx, ry = T(hc)
        da.ellipse([rx - r * 1.3, ry - r * 0.2, rx - r * 0.85, ry + r * 0.2], fill=(170, 30, 40, 255))
    if who == "master" and pose.startswith("lantern"):
        lx, ly = hand
        L = 0.075 * U
        da.line([lx, ly, lx, ly + L * 0.4], fill=(30, 26, 20, 255), width=max(1, int(U * 0.006)))
        da.rectangle([lx - L * 0.5, ly + L * 0.4, lx + L * 0.5, ly + L * 0.55], fill=(30, 26, 20, 255))
        da.rounded_rectangle([lx - L * 0.4, ly + L * 0.55, lx + L * 0.4, ly + L * 1.35], radius=int(L * 0.2), fill=(255, 196, 90, 255))
        da.ellipse([lx - L * 0.15, ly + L * 0.75, lx + L * 0.15, ly + L * 1.15], fill=(255, 250, 220, 255))
        da.rectangle([lx - L * 0.5, ly + L * 1.35, lx + L * 0.5, ly + L * 1.5], fill=(30, 26, 20, 255))
        anchors["lantern"] = (lx, ly + L * 0.95)
    if who == "master" and pose == "photo":
        hx2, hy2 = hand
        pw, ph_ = 0.07 * U, 0.09 * U
        da.rectangle([hx2 - pw * 0.2, hy2 - ph_, hx2 + pw * 0.8, hy2], fill=(222, 205, 170, 255))
        da.rectangle([hx2 - pw * 0.1, hy2 - ph_ * 0.92, hx2 + pw * 0.7, hy2 - ph_ * 0.2], fill=(120, 98, 70, 255))
        anchors["photo"] = (hx2 + pw * 0.3, hy2 - ph_ * 0.5)
    anchors["head"] = T(hc)
    img = _finish(front, back, fill, rim, ld, hpx, acc, alpha)
    img = img.resize((cw // SS, chh // SS), Image.LANCZOS)
    an = {k: (v[0] / SS, v[1] / SS) for k, v in anchors.items()}
    an["foot"] = (ox / SS, (top + U) / SS)
    return img, an


def person_back(who, pose, ph, hpx, rim, ld, alpha=1.0):
    """Seen from behind (or front): symmetric silhouette, walking away."""
    F = FIG[who]
    U = hpx * SS
    cw, chh = int(U * 0.8), int(U * 1.15)
    ox, top = cw / 2, U * 0.1
    front = Image.new("L", (cw, chh), 0)
    back = Image.new("L", (cw, chh), 0)
    d = ImageDraw.Draw(front)
    walking = pose == "back_walk"
    s = math.sin(ph) if walking else 0.0
    bob = -0.01 * abs(math.cos(ph)) if walking else 0.0

    def T(x, y):
        return (ox + x * U, top + (y + bob) * U)
    t0, t1 = F["tw"]
    sy, py = F["sy"], F["py"]
    lw = F["lw"] * U
    for side, ph2 in ((-1, s), (1, -s)):
        lift = 0.04 * max(0.0, ph2)
        _thick(d, [T(side * 0.045, py), T(side * 0.05, 0.985 - lift)], lw)
        _thick(d, [T(side * (t0 * 1.7), sy + 0.02), T(side * (t0 * 1.75 + 0.012), py + 0.04 - 0.025 * ph2)], F["aw"] * U)
    if who == "mother":
        d.polygon([T(-t0 * 1.6, sy), T(t0 * 1.6, sy), T(0.17, 0.985), T(-0.17, 0.985)], fill=255)
    elif who == "girl":
        d.polygon([T(-t0 * 1.4, sy), T(t0 * 1.4, sy), T(0.17, 0.66), T(-0.17, 0.66)], fill=255)
    else:
        bot = py + (0.06 if who == "aarav" else 0.03)
        d.polygon([T(-t0 * 1.85, sy - 0.005), T(t0 * 1.85, sy - 0.005), T(t1 * 1.55, bot), T(-t1 * 1.55, bot)], fill=255)
    r = F["hr"] * U
    hx, hy = T(0, F["hy"])
    _thick(d, [T(0, sy), (hx, hy + r * 0.6)], r * 1.0)
    d.ellipse([hx - r, hy - r * 1.02, hx + r, hy + r], fill=255)
    if who == "master":
        d.rectangle([hx - r * 1.0, hy - r * 1.45, hx + r * 1.0, hy - r * 0.55], fill=255)
        d.rectangle([hx - r * 1.25, hy - r * 0.7, hx + r * 1.25, hy - r * 0.5], fill=255)
    if who == "girl":
        for sd in (-1, 1):
            d.ellipse([hx + sd * r * 1.05 - r * 0.32, hy + r * 0.1, hx + sd * r * 1.05 + r * 0.32, hy + r * 0.74], fill=255)
    if who == "aarav":  # backpack
        bd = ImageDraw.Draw(back)
        d.rounded_rectangle([*T(-0.08, sy + 0.025), *T(0.08, py - 0.02)], radius=int(0.03 * U), fill=255)
    acc = None
    if who == "aarav":
        acc = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
        ImageDraw.Draw(acc).rounded_rectangle([*T(-0.07, sy + 0.035), *T(0.07, py - 0.03)], radius=int(0.025 * U), fill=(0, 0, 0, 90))
    img = _finish(front, back, F["fill"], rim, ld, hpx, acc, alpha)
    img = img.resize((cw // SS, chh // SS), Image.LANCZOS)
    return img, {"foot": (ox / SS, (top + U) / SS), "head": (hx / SS, hy / SS)}


def hug(ph, hpx, rim, ld):
    a, aa = person("aarav", "hug", ph, hpx, rim, ld)
    m, ma = person("mother", "hug", ph, int(hpx * 0.92), rim, ld)
    m = m.transpose(Image.FLIP_LEFT_RIGHT)
    W_ = a.width + int(hpx * 0.2)
    out = Image.new("RGBA", (W_, a.height), (0, 0, 0, 0))
    fx = W_ / 2
    mfx = m.width - ma["foot"][0]
    out.alpha_composite(m, (int(fx + hpx * 0.05 - mfx), int(aa["foot"][1] - ma["foot"][1])))
    out.alpha_composite(a, (int(fx - hpx * 0.08 - aa["foot"][0]), 0))
    return out, {"foot": (fx, aa["foot"][1])}


def toy_train(w=160):
    """Small red toy train sprite (for the end card)."""
    hgt = int(w * 0.55)
    img = Image.new("RGBA", (w * SS, hgt * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = w * SS
    d.rounded_rectangle([0.05 * u, 0.2 * u, 0.62 * u, 0.42 * u], radius=int(0.03 * u), fill=(205, 28, 30, 255))
    d.rectangle([0.6 * u, 0.06 * u, 0.92 * u, 0.42 * u], fill=(225, 36, 34, 255))
    d.rectangle([0.66 * u, 0.1 * u, 0.86 * u, 0.22 * u], fill=(255, 214, 120, 255))
    d.rectangle([0.14 * u, 0.06 * u, 0.24 * u, 0.2 * u], fill=(120, 16, 18, 255))
    d.rectangle([0.56 * u, 0.02 * u, 0.96 * u, 0.07 * u], fill=(120, 16, 18, 255))
    for cx in (0.16, 0.42, 0.78):
        d.ellipse([(cx - 0.07) * u, 0.36 * u, (cx + 0.07) * u, 0.5 * u], fill=(24, 18, 18, 255))
        d.ellipse([(cx - 0.025) * u, 0.405 * u, (cx + 0.025) * u, 0.455 * u], fill=(200, 180, 120, 255))
    return img.resize((w, hgt), Image.LANCZOS)
