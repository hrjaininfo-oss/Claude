"""Animated character silhouettes for the Ramayan Shorts, drawn in code.

    img = character("hanuman", act="walk", phase=0.25, prog=0.0, sil=(20, 8, 4), light=(255, 210, 140))

* phase (0..1) moves through a looping action (a walk step, a broom swing ...).
* prog (0..1) is how far the current narration line has got, used by one-off
  actions (raising a hand, lifting the squirrel ...).

The image is the full canvas (CW x CH); the feet are at (OX, OY). The figure is
about 1000 units tall. Each figure faces right, with gold ornaments, a rim
light and (for Ram and Hanuman) a soft golden aura.
"""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CW, CH, OX, OY = 1500, 1800, 750, 1650
GOLD = (255, 196, 80)
BERRY = (200, 30, 30)
TAU = 2 * math.pi

BODIES = {
    "ram":      dict(crown=True, hair=True, orn=True, aura=True, bow=True),
    "lakshman": dict(crown=True, hair=True, orn=True, bow=True),
    "hanuman":  dict(crown=True, muzzle=True, tail=True, orn=True, aura=True, bulky=True, gada=True),
    "vanar":    dict(muzzle=True, tail=True, bare=True),
    "jambavan": dict(bear=True, bulky=True, hunch=14),
    "shabari":  dict(saree=True, veil=True, hunch=24),
    "sage":     dict(sage=True, robe=True, hunch=6),
    "squirrel": dict(),
}

# arm presets: elbow_back, hand_back, elbow_front, hand_front (upright frame, feet at 0,0)
ARMS = {
    "down":    ((-105, -560), (-110, -400), (105, -560), (112, -400)),
    "bless":   ((-105, -560), (-110, -400), (150, -610), (170, -770)),
    "namaste": ((-40, -590), (70, -660), (130, -600), (80, -665)),
    "point":   ((-105, -560), (-110, -400), (210, -705), (340, -730)),
    "extend":  ((-105, -560), (-110, -400), (175, -600), (310, -620)),
    "up":      ((-150, -870), (-140, -1020), (150, -870), (140, -1020)),
    "carry":   ((-150, -870), (-60, -1010), (150, -870), (60, -1010)),
    "laugh":   ((-150, -560), (-20, -520), (150, -560), (30, -520)),
    "gada":    ((-105, -560), (-110, -400), (160, -590), (200, -500)),
    "power":   ((-105, -560), (-110, -400), (170, -880), (150, -1040)),
    "staff":   ((-105, -560), (-110, -400), (150, -620), (190, -600)),
    "broom":   ((-40, -560), (90, -420), (120, -560), (150, -400)),
    "offer":   ((10, -600), (230, -640), (140, -600), (250, -650)),
    "fly":     ((-100, -560), (-90, -420), (70, -930), (80, -1100)),
    "stop":    ((-105, -560), (-110, -400), (190, -660), (230, -820)),
}

CYCLE = {  # seconds per loop of each action
    "idle": 3.2, "walk": 1.0, "carry_walk": 1.2, "sweep": 1.3, "laugh": 0.7, "point": 0.8, "cheer": 0.6,
    "talk": 1.2, "eat": 2.2, "offer": 2.0, "namaste_bow": 2.6, "wait": 4.0, "fly": 0.8, "sad": 3.0,
    "stroke": 1.1, "lift_stroke": 1.1, "shake": 0.25, "hop": 0.5, "sit": 3.2, "bless": 3.2,
    "power": 3.2, "hesitate": 3.0,
}
ONE_SHOT = {"bless", "power", "hesitate", "lift_stroke"}   # these also depend on line progress


def ease(t):
    t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3


def lerp2(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def _rot(p, c, deg):
    a = math.radians(deg); x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def _limb(d, pts, w, col):
    d.line(pts, fill=col, width=int(w), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)


def _curve(d, pts, w0, w1, col, n=220):
    pts = np.array(pts, float)
    for i in range(n + 1):
        s = i / n * (len(pts) - 1); k = min(int(s), len(pts) - 2); u = s - k
        p0, p1, p2, p3 = pts[max(k - 1, 0)], pts[k], pts[k + 1], pts[min(k + 2, len(pts) - 1)]
        q = 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
        r = (w0 + (w1 - w0) * i / n) / 2
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)


def _P(p):
    return (OX + p[0], OY + p[1])


UPPER = ("head", "neck", "sh_b", "sh_f", "el_b", "el_f", "ha_b", "ha_f")


def _base(arms, kneel=False):
    J = dict(head=(14, -845), neck=(4, -765), sh_b=(-92, -732), sh_f=(92, -732),
             hip_b=(-52, -440), hip_f=(52, -440), kn_b=(-48, -225), kn_f=(52, -228), ft_b=(-52, -22), ft_f=(62, -22))
    eb, hb, ef, hf = ARMS[arms]
    J.update(el_b=eb, ha_b=hb, el_f=ef, ha_f=hf)
    if kneel:
        for k in UPPER + ("hip_b", "hip_f"):
            J[k] = (J[k][0] - 20, J[k][1] + 210)
        J.update(kn_b=(70, -40), kn_f=(110, -42), ft_b=(-150, -18), ft_f=(-120, -18))
    return J


def _walk_legs(J, ph, stride=105, lift=55):
    for side, off in (("f", 0.0), ("b", 0.5)):
        a = TAU * (ph + off); hip = J["hip_" + side]
        up = max(0.0, math.cos(a))
        fx = hip[0] + 10 + stride * math.sin(a); fy = -22 - lift * up
        J["ft_" + side] = (fx, fy)
        J["kn_" + side] = ((hip[0] + fx) / 2 + 28 + 25 * up, (hip[1] + fy) / 2 - 8 - 0.4 * lift * up)


def _swing_arms(J, ph, amt=85):
    s = math.sin(TAU * ph)
    J["ha_f"] = (95 - amt * s, -405 + 15 * abs(s)); J["el_f"] = (100 - amt * 0.45 * s, -565)
    J["ha_b"] = (-95 + amt * s, -405 + 15 * abs(s)); J["el_b"] = (-100 + amt * 0.45 * s, -565)


ACT_ARMS = {"walk": "down", "idle": "down", "carry_walk": "carry", "sweep": "broom", "laugh": "laugh", "point": "point",
            "cheer": "up", "talk": "extend", "eat": "extend", "offer": "offer", "namaste_bow": "namaste", "wait": "staff",
            "fly": "fly", "sad": "down", "stroke": "extend", "lift_stroke": "extend", "bless": "down", "power": "gada",
            "hesitate": "down", "namaste": "namaste"}


def pose_for(who, act, ph, prog):
    ex = dict(hunch=0.0, items=set(), dy_all=0.0, dy_up=0.0, head=None)
    kneel = act == "offer"
    arms = ACT_ARMS.get(act, "down")
    if who == "hanuman" and arms == "down" and act != "sad": arms = "gada"
    J = _base(arms, kneel); s = math.sin(TAU * ph)
    if act in ("idle", "namaste"):
        ex["dy_up"] = 5 * s
    elif act == "walk":
        _walk_legs(J, ph)
        if arms == "down": _swing_arms(J, ph)
        ex["dy_up"] = -10 * abs(s)
    elif act == "carry_walk":
        _walk_legs(J, ph, 80, 40); ex["dy_up"] = -8 * abs(s); ex["items"].add("rock")
    elif act == "sweep":
        J["ha_f"] = (150 + 80 * s, -400 + 15 * abs(s)); J["el_f"] = (120 + 30 * s, -560)
        J["ha_b"] = (90 + 80 * s, -430); J["ft_f"] = (62 + 15 * s, -22); ex["items"].add("broom")
    elif act == "laugh":
        ex["hunch"] = -10 + 12 * (0.5 + 0.5 * s); ex["dy_up"] = 8 * math.sin(TAU * ph * 2); ex["head"] = (-10, -850)
    elif act == "point":
        u = 0.5 + 0.5 * s
        J["ha_f"] = (300 + 50 * u, -720 - 40 * u); J["el_f"] = (200 + 15 * u, -700 - 15 * u)
    elif act == "cheer":
        J["ha_f"] = (140 + 30 * s, -1020); J["ha_b"] = (-140 - 30 * s, -1020)
        ex["dy_all"] = -70 * max(0.0, s)
    elif act == "talk":
        u = 0.5 + 0.5 * s
        J["ha_f"] = lerp2((280, -580), (300, -760), u); J["el_f"] = lerp2((170, -590), (190, -660), u)
        ex["head"] = (14 + 6 * s, -845)
    elif act == "eat":
        u = 0.5 - 0.5 * math.cos(TAU * ph)
        J["ha_f"] = lerp2((270, -600), (70, -800), u); J["el_f"] = lerp2((175, -590), (165, -640), u)
        ex["items"].add("berry")
    elif act == "offer":
        J["ha_f"] = (J["ha_f"][0] + 20 * s, J["ha_f"][1]); J["ha_b"] = (J["ha_b"][0] + 20 * s, J["ha_b"][1])
        ex["hunch"] = 4 * s; ex["items"].add("bowl")
    elif act == "namaste_bow":
        ex["hunch"] = 18 * (0.5 - 0.5 * math.cos(TAU * ph))
    elif act == "wait":
        ex["hunch"] = 4 * s; ex["items"].add("staff")
    elif act == "sad":
        ex["hunch"] = 22; ex["head"] = (40, -800)
    elif act == "bless":
        u = ease(prog * 2.5)
        J["el_f"] = lerp2(ARMS["down"][2], ARMS["bless"][2], u); J["ha_f"] = lerp2(ARMS["down"][3], ARMS["bless"][3], u)
    elif act == "power":
        u = ease(prog * 2.0)
        J["el_f"] = lerp2(ARMS["gada"][2], ARMS["power"][2], u); J["ha_f"] = lerp2(ARMS["gada"][3], ARMS["power"][3], u)
        J["ha_b"] = lerp2(ARMS["gada"][1], (-200, -820), u); J["el_b"] = lerp2(ARMS["gada"][0], (-170, -660), u)
        J["ft_f"] = lerp2(J["ft_f"], (130, -22), u); J["kn_f"] = lerp2(J["kn_f"], (110, -240), u)
    elif act == "hesitate":
        u = ease(prog * 2.5)
        J["el_f"] = lerp2(ARMS["down"][2], ARMS["stop"][2], u); J["ha_f"] = lerp2(ARMS["down"][3], ARMS["stop"][3], u)
        ex["hunch"] = -7 * u; ex["head"] = (14 - 18 * u, -845)
    elif act in ("lift_stroke", "stroke"):
        u = ease(prog * 2.2) if act == "lift_stroke" else 1.0
        J["ha_f"] = lerp2((200, -260), (300, -620), u); J["el_f"] = lerp2((150, -420), (175, -600), u)
        if u > 0.95:
            J["ha_b"] = (250 + 55 * s, -700); J["el_b"] = (120, -620)
        ex["items"].add("squirrel")
    elif act == "fly":
        J["kn_f"] = (90 + 20 * s, -240); J["ft_f"] = (20 + 30 * s, -60)
        J["kn_b"] = (-40, -230 + 15 * s); J["ft_b"] = (-60, -20)
    return J, ex, kneel


def character(who, act="idle", phase=0.0, prog=0.0, sil=(14, 8, 6), light=(255, 210, 140), stripes=False, mouth=0.0):
    """mouth: 0 (closed) .. 1 (wide open), for speaking."""
    B = dict(BODIES[who]); col = sil + (255,)
    if who == "squirrel":
        return _squirrel_fig(act, phase, col, light, stripes, mouth)
    if act == "sit":
        return _seated(B, sil, light, phase)
    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    orn = []
    J, ex, kneel = pose_for(who, act, phase, prog)
    bulky = B.get("bulky")
    if ex["head"]: J["head"] = ex["head"]
    for k in UPPER:
        J[k] = (J[k][0], J[k][1] + ex["dy_up"])
    hunch = B.get("hunch", 0) + ex["hunch"]
    if hunch:
        c = ((J["hip_b"][0] + J["hip_f"][0]) / 2, J["hip_b"][1])
        for k in UPPER:
            J[k] = _rot(J[k], c, hunch)
    if ex["dy_all"]:
        J = {k: (v[0], v[1] + ex["dy_all"]) for k, v in J.items()}
    P = {k: _P(v) for k, v in J.items()}
    sw = 1.25 if bulky else 1.0
    arm_w, leg_w = 60 * sw, 70 * sw
    items = ex["items"]; gy0 = OY + ex["dy_all"]

    if B.get("tail"):
        hx, hy = P["hip_b"]; wv = math.sin(TAU * phase) * 40
        if act == "fly":
            _curve(d, [(hx, hy), (hx - 60 + wv, hy + 200), (hx + 20 - wv, hy + 420), (hx - 40 + wv, hy + 600)], 56, 22, col)
        else:
            _curve(d, [(hx, hy), (hx - 170, hy + 60), (hx - 280, hy - 200), (hx - 230 + wv * 0.5, hy - 470), (hx - 120 + wv, hy - 520), (hx - 110 + wv, hy - 420)],
                   56 if bulky else 46, 22, col)
    _limb(d, [P["sh_b"], P["el_b"], P["ha_b"]], arm_w, col)
    if B.get("bow") and act not in ("lift_stroke", "stroke", "walk"):
        hx, hy = P["ha_b"]
        pts = [(hx - 40 - 75 * math.sin(math.pi * s_), hy - 470 + 900 * s_) for s_ in np.linspace(0, 1, 40)]
        d.line(pts, fill=col, width=26, joint="curve"); d.line([pts[0], pts[-1]], fill=col, width=6)
        orn.append(("line", pts, 5))
    if B.get("bow"):
        qx, qy = P["sh_b"]
        d.polygon([(qx - 40, qy - 60), (qx - 5, qy - 75), (qx - 60, qy + 230), (qx - 95, qy + 215)], fill=col)
        for k in range(3):
            d.line([(qx - 30 - k * 14, qy - 60), (qx - 5 - k * 14, qy - 170)], fill=col, width=7)
    if who == "hanuman" and act == "fly":
        gx, gy = P["ha_b"]
        d.line([(gx, gy - 40), (gx - 10, gy + 260)], fill=col, width=28)
        d.ellipse([gx - 95, gy + 230, gx + 85, gy + 410], fill=col); orn.append(("ell", [gx - 95, gy + 230, gx + 85, gy + 410], 7))
    _limb(d, [P["hip_b"], P["kn_b"], P["ft_b"]], leg_w, col)
    _limb(d, [P["hip_f"], P["kn_f"], P["ft_f"]], leg_w, col)
    for k in ("ft_b", "ft_f"):
        x, y = P[k]; fwd = -1 if kneel else 1
        d.ellipse([x - 30 + 25 * fwd, y - 22, x + 30 + 45 * fwd, y + 22], fill=col)
    sb, sf, hb, hf = P["sh_b"], P["sh_f"], P["hip_b"], P["hip_f"]
    wide = 18 if bulky else 0
    d.polygon([(sb[0] - 12 - wide, sb[1]), (sf[0] + 12 + wide, sf[1]), (hf[0] + 16, hf[1]), (hb[0] - 16, hb[1])], fill=col)
    for p in (sb, sf):
        r = (arm_w + 14) / 2; d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    if bulky:
        cx, cy = (sb[0] + sf[0] + hb[0] + hf[0]) / 4, (sb[1] + sf[1]) / 2 + 90
        d.ellipse([cx - 120, cy - 110, cx + 125, cy + 110], fill=col)
    if B.get("saree") or B.get("robe"):
        lo = min(P["ft_f"][0], P["ft_b"][0]); hi = max(P["ft_f"][0], P["ft_b"][0])
        if kneel:
            d.polygon([(hb[0] - 40, hb[1] - 20), (hf[0] + 30, hf[1] - 20), (P["kn_f"][0] + 60, gy0), (P["ft_b"][0] - 40, gy0)], fill=col)
        else:
            d.polygon([(hb[0] - 30, hb[1] - 30), (hf[0] + 30, hf[1] - 30), (hi + 75, gy0 - 5), (lo - 75, gy0 - 5)], fill=col)
            if B.get("saree"):
                orn.append(("line", [(lo - 60, gy0 - 30), (hi + 60, gy0 - 30)], 6))
    elif not B.get("bare") and not B.get("bear"):
        d.polygon([(hb[0] - 22, hb[1] - 12), (hf[0] + 22, hf[1] - 12), (P["kn_f"][0] + 70, P["kn_f"][1] + 60), (P["kn_b"][0] - 70, P["kn_b"][1] + 60)], fill=col)
        orn.append(("line", [(hb[0] - 22, hb[1] - 14), (hf[0] + 22, hf[1] - 14)], 8))
    _limb(d, [P["neck"], P["head"]], 64 * sw, col)
    hx, hy = P["head"]; R = 70 if B.get("bear") else 58
    if B.get("hair"):
        d.ellipse([hx - 72, hy - 40, hx + 25, hy + 140], fill=col)
    d.ellipse([hx - R, hy - R, hx + R, hy + R], fill=col)
    if B.get("muzzle"):
        jaw = 30 * mouth + (8 * max(0.0, math.sin(TAU * phase * 2)) if act == "laugh" else 0)
        d.ellipse([hx + 20, hy - 8, hx + 88, hy + 30], fill=col)                  # upper muzzle
        d.ellipse([hx + 14, hy + 8 + jaw * 0.6, hx + 78, hy + 50 + jaw], fill=col)  # lower jaw drops when speaking
        d.ellipse([hx - 30, hy - 20, hx + 2, hy + 18], fill=col)
        if mouth > 0.05:
            orn.append(("cut", [(hx + 92, hy + 22), (hx + 40, hy + 26 + jaw * 0.4), (hx + 86, hy + 34 + jaw)], 0))
    if B.get("bear"):
        for ex_, ey in ((hx - 48, hy - 58), (hx + 22, hy - 66)):
            d.ellipse([ex_ - 24, ey - 24, ex_ + 24, ey + 24], fill=col)
        jaw = 30 * mouth
        d.ellipse([hx + 30, hy - 10, hx + 110, hy + 30], fill=col)
        d.ellipse([hx + 26, hy + 6 + jaw * 0.6, hx + 100, hy + 48 + jaw], fill=col)
        if mouth > 0.05:
            orn.append(("cut", [(hx + 114, hy + 22), (hx + 55, hy + 26 + jaw * 0.4), (hx + 104, hy + 34 + jaw)], 0))
        d.polygon([(hx - 20, hy + 40), (hx + 70, hy + 40), (hx + 30, hy + 150)], fill=col)
    if not (B.get("muzzle") or B.get("bear")):
        d.ellipse([hx + R - 40, hy + 18 + 26 * mouth, hx + R + 4, hy + 52 + 26 * mouth], fill=col)   # chin
        d.ellipse([hx + R - 14, hy - 12, hx + R + 14, hy + 14], fill=col)                             # nose
        if mouth > 0.05:
            orn.append(("cut", [(hx + R + 14, hy + 22), (hx + R - 16 - 14 * mouth, hy + 30 + 6 * mouth), (hx + R + 10, hy + 34 + 24 * mouth)], 0))
    if B.get("sage"):
        d.ellipse([hx - 30, hy - 120, hx + 35, hy - 50], fill=col)
        d.polygon([(hx - 10, hy + 30), (hx + 62, hy + 25), (hx + 45, hy + 210), (hx + 5, hy + 180)], fill=col)
    if B.get("veil"):
        d.ellipse([hx - R - 14, hy - R - 16, hx + R + 6, hy + R], fill=col)
        d.polygon([(hx - R - 16, hy + 10), (hx - 10, hy - R - 14), (hx + 30, hy - R + 4), (P["sh_b"][0] + 10, P["sh_b"][1]),
                   (P["hip_b"][0] - 40, P["hip_b"][1] + 40), (P["hip_b"][0] - 110, P["hip_b"][1] + 10)], fill=col)
        d.polygon([(hx + 8, hy - R - 16), (hx + R + 22, hy - 20), (hx + R + 10, hy + 40), (P["sh_f"][0] + 30, P["sh_f"][1] + 30), (P["sh_b"][0], P["sh_b"][1])], fill=col)
        orn.append(("line", [(hx - 6, hy - R - 16), (hx + R + 22, hy - 20), (hx + R + 10, hy + 40), (P["sh_f"][0] + 30, P["sh_f"][1] + 30)], 6))
    if B.get("crown"):
        cr = [(hx - 50, hy - 38), (hx - 44, hy - 110), (hx - 22, hy - 92), (hx, hy - 178), (hx + 22, hy - 92), (hx + 44, hy - 110), (hx + 50, hy - 38)]
        d.polygon(cr, fill=col); orn.append(("line", cr + [cr[0]], 6))
    _limb(d, [P["sh_f"], P["el_f"], P["ha_f"]], arm_w, col)
    hx2, hy2 = P["ha_f"]
    if B.get("gada") and act != "fly":
        gx, gy = hx2, hy2
        d.line([(gx, gy + 110), (gx, gy - 230)], fill=col, width=30)
        d.ellipse([gx - 100, gy - 430, gx + 100, gy - 230], fill=col)
        d.ellipse([gx - 22, gy - 470, gx + 22, gy - 420], fill=col)
        orn.append(("ell", [gx - 100, gy - 430, gx + 100, gy - 230], 7)); orn.append(("line", [(gx - 96, gy - 330), (gx + 96, gy - 330)], 6))
    if "staff" in items or (who == "sage" and act not in ("bless", "talk")):
        d.line([(hx2 + 6, gy0 - 5), (hx2 - 10, hy2 - 430)], fill=col, width=22)
    if "broom" in items:
        bx, by = P["ha_f"]
        d.line([(bx - 40, by - 120), (bx + 60, by + 230)], fill=col, width=16)
        d.polygon([(bx + 40, by + 200), (bx + 70, by + 210), (bx + 170, by + 380), (bx - 10, by + 400)], fill=col)
    if "rock" in items:
        cx = (P["ha_b"][0] + P["ha_f"][0]) / 2; cy = (P["ha_b"][1] + P["ha_f"][1]) / 2
        d.ellipse([cx - 150, cy - 170, cx + 150, cy + 10], fill=col)
        orn.append(("text", (cx, cy - 80), 0))
    if "bowl" in items:
        cx, cy = P["ha_f"][0] + 10, P["ha_f"][1] - 20
        d.chord([cx - 95, cy - 60, cx + 95, cy + 60], 0, 180, fill=col)
        for k in range(7):
            bx = cx - 66 + k * 22; r = 15
            d.ellipse([bx - r, cy - 22 - r - (k % 2) * 14, bx + r, cy - 22 + r - (k % 2) * 14], fill=BERRY + (255,))
    if "berry" in items:
        d.ellipse([hx2 - 18, hy2 - 34, hx2 + 18, hy2 + 2], fill=BERRY + (255,))
    if "squirrel" in items:
        _tiny_squirrel(d, hx2 - 10, hy2 - 22, 0.75, col, prog > 0.3 or act == "stroke")
    if B.get("orn"):
        nx, ny = P["neck"]
        orn.append(("arc", [nx - 80, ny - 40, nx + 90, ny + 120], 6))
        for s_, e_ in (("sh_f", "el_f"), ("sh_b", "el_b")):
            a, b = P[s_], P[e_]; mx, my = a[0] + (b[0] - a[0]) * 0.45, a[1] + (b[1] - a[1]) * 0.45
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1; px, py = -dy / L * 26, dx / L * 26
            orn.append(("line", [(mx - px, my - py), (mx + px, my + py)], 8))
    return _finish(img, orn, B, light)


def _tiny_squirrel(d, x, y, s, col, stripes):
    d.ellipse([x - 40 * s, y - 110 * s, x + 30 * s, y], fill=col)
    d.ellipse([x + 5 * s, y - 150 * s, x + 62 * s, y - 95 * s], fill=col)
    d.polygon([(x + 18 * s, y - 135 * s), (x + 26 * s, y - 175 * s), (x + 40 * s, y - 140 * s)], fill=col)
    _curve(d, [(x - 40 * s, y - 20 * s), (x - 110 * s, y - 100 * s), (x - 80 * s, y - 220 * s), (x - 20 * s, y - 230 * s)], 50 * s, 30 * s, col)
    if stripes:
        for k in (-1, 0, 1):
            d.line([(x - 30 * s, y - 60 * s + k * 15 * s), (x + 15 * s, y - 85 * s + k * 15 * s)], fill=(255, 236, 180, 255), width=max(3, int(7 * s)))


def _squirrel_fig(act, phase, col, light, stripes, mouth=0.0):
    """Squirrel about 1000 units tall (with tail): idle tail sway, hop, shake."""
    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    s = 3.6; x, y = OX, OY; wv = math.sin(TAU * phase)
    if act == "hop":
        y -= 160 * abs(math.sin(math.pi * phase))
    d.ellipse([x - 40 * s, y - 120 * s, x + 30 * s, y], fill=col)
    d.ellipse([x + 5 * s, y - 165 * s, x + 65 * s, y - 105 * s], fill=col)
    d.polygon([(x + 18 * s, y - 150 * s), (x + 26 * s, y - 192 * s), (x + 40 * s, y - 155 * s)], fill=col)
    d.ellipse([x + 55 * s, y - 140 * s, x + 75 * s, y - 128 * s], fill=col)
    for k in range(26):
        q = k / 25; sway = wv * 22 * s * q * q
        cx = x - 45 * s - 70 * s * math.sin(math.pi * q * 0.85) + (40 * s * (q - 0.75) / 0.25 if q > 0.75 else 0) + sway
        cy = y - 15 * s - 230 * s * q
        rr = (18 + 30 * math.sin(math.pi * min(q * 1.2, 1))) * s
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
    d.ellipse([x + 10 * s, y - 30 * s, x + 45 * s, y + 5 * s], fill=col)
    if stripes:
        for k in (-1, 0, 1):
            d.line([(x - 30 * s, y - 70 * s + k * 16 * s), (x + 18 * s, y - 95 * s + k * 16 * s)], fill=(255, 236, 180, 255), width=int(7 * s))
    cuts = [("cut", [(x + 78 * s, y - 126 * s), (x + 58 * s, y - 122 * s), (x + 76 * s, y - (118 - 10 * mouth) * s)], 0)] if mouth > 0.05 else []
    out = _finish(img, cuts, {"aura": stripes}, light)
    if act == "shake":
        out = out.rotate(14 * wv, Image.BILINEAR, center=(OX, OY - 300))
    return out


def _seated(B, sil, light, phase):
    """Hanuman sitting cross-legged, head bowed, gada beside him (gentle breathing)."""
    col = sil + (255,); img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(img); orn = []
    br = 6 * math.sin(TAU * phase)
    _curve(d, [_P((-120, -40)), _P((-300, -20)), _P((-330, -120)), _P((-260, -170 + br * 3))], 50, 22, col)
    d.ellipse([OX - 200, OY - 150, OX + 210, OY], fill=col)
    d.polygon([_P((-90, -110)), _P((95, -110)), _P((120, -440 + br)), _P((-95, -450 + br))], fill=col)
    d.ellipse([OX - 125, OY - 420 + br, OX + 140, OY - 220], fill=col)
    head = _P((70, -530 + br)); hx, hy = head
    _limb(d, [_P((10, -450 + br)), head], 62, col)
    d.ellipse([hx - 58, hy - 58, hx + 58, hy + 58], fill=col)
    d.ellipse([hx + 22, hy - 2, hx + 88, hy + 52], fill=col)
    cr = [(hx - 50, hy - 38), (hx - 44, hy - 110), (hx - 22, hy - 92), (hx, hy - 178), (hx + 22, hy - 92), (hx + 44, hy - 110), (hx + 50, hy - 38)]
    d.polygon(cr, fill=col); orn.append(("line", cr + [cr[0]], 6))
    for sh, el, ha in (((-90, -420), (-150, -250), (-80, -140)), ((110, -420), (170, -250), (150, -130))):
        _limb(d, [_P((sh[0], sh[1] + br)), _P(el), _P(ha)], 54, col)
    gx, gy = _P((300, -10))
    d.line([(gx, gy), (gx - 60, gy - 420)], fill=col, width=30)
    d.ellipse([gx - 165, gy - 620, gx + 35, gy - 420], fill=col); orn.append(("ell", [gx - 165, gy - 620, gx + 35, gy - 420], 7))
    nx, ny = _P((20, -450)); orn.append(("arc", [nx - 80, ny - 30, nx + 90, ny + 120], 6))
    return _finish(img, orn, B, light)


_TXT = None


def _finish(img, orn, B, light):
    global _TXT
    cuts = [o for o in orn if o[0] == "cut"]
    if cuts:
        m = Image.new("L", img.size, 255); md = ImageDraw.Draw(m)
        for _, pts, _w in cuts: md.polygon(pts, fill=0)
        img.putalpha(Image.fromarray(np.minimum(np.asarray(img.getchannel("A")), np.asarray(m))))
    a = img.getchannel("A")
    small = a.resize((CW // 4, CH // 4))
    sh = Image.new("L", a.size, 0); sh.paste(a, (-9, 7))
    rim = Image.fromarray(np.clip(np.asarray(a, np.int16) - np.asarray(sh, np.int16), 0, 255).astype(np.uint8))
    er = small.filter(ImageFilter.MinFilter(3)).resize(a.size)
    edge = Image.fromarray((np.clip(np.asarray(a, np.int16) - np.asarray(er, np.int16), 0, 255) * 0.45).astype(np.uint8))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    if B.get("aura"):
        g = small.filter(ImageFilter.GaussianBlur(16)).resize(a.size).point(lambda v: int(min(255, v * 1.6) * 0.75))
        out.paste(Image.new("RGBA", img.size, GOLD + (255,)), (0, 0), g)
    out = Image.alpha_composite(out, img)
    out.paste(Image.new("RGBA", img.size, light + (255,)), (0, 0), Image.fromarray(np.maximum(np.asarray(rim), np.asarray(edge))))
    d = ImageDraw.Draw(out)
    for kind, pts, w in orn:
        if kind == "line": d.line(pts, fill=GOLD + (255,), width=w, joint="curve")
        elif kind == "ell": d.ellipse(pts, outline=GOLD + (255,), width=w)
        elif kind == "arc": d.arc(pts, 20, 160, fill=GOLD + (255,), width=w)
        elif kind == "text":
            if _TXT is None:
                _TXT = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "NotoSansDevanagari-Bold.ttf"), 80)
            d.text(pts, "राम", font=_TXT, fill=(255, 170, 60, 255), anchor="mm")
    return out
