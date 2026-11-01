"""Character silhouettes for the Ramayan Shorts, drawn in code.

Each figure is drawn facing right on a large transparent canvas with its feet
at the bottom centre, filled in a dark silhouette colour, with gold ornaments,
a rim light and (for Ram and Hanuman) a soft golden aura.

    img = character("hanuman", "gada", sil=(20, 8, 4), light=(255, 210, 140))
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CW, CH, OX, OY = 1500, 1700, 750, 1600       # canvas size and feet origin
GOLD = (255, 196, 80)
BERRY = (200, 30, 30)

# body type -> settings
BODIES = {
    "ram":      dict(crown=True, hair=True, orn=True, aura=True, bow=True),
    "lakshman": dict(crown=True, hair=True, orn=True, bow=True, scale=0.94),
    "hanuman":  dict(crown=True, muzzle=True, tail=True, orn=True, aura=True, bulky=True),
    "vanar":    dict(muzzle=True, tail=True, scale=0.9, bare=True),
    "jambavan": dict(bear=True, bulky=True, hunch=14),
    "shabari":  dict(saree=True, veil=True, hunch=24, scale=0.9),
    "sage":     dict(sage=True, robe=True, hunch=6),
}

# arm presets: (elbow_back, hand_back, elbow_front, hand_front), upright frame
ARMS = {
    "down":    ((-105, -560), (-110, -400), (105, -560), (112, -400)),
    "bless":   ((-105, -560), (-110, -400), (150, -610), (170, -770)),
    "namaste": ((-40, -590), (70, -660), (130, -600), (80, -665)),
    "point":   ((-105, -560), (-110, -400), (210, -705), (340, -730)),
    "extend":  ((-105, -560), (-110, -400), (175, -600), (310, -620)),
    "mouth":   ((-105, -560), (-110, -400), (165, -630), (70, -800)),
    "up":      ((-150, -870), (-140, -1020), (150, -870), (140, -1020)),
    "carry":   ((-150, -870), (-60, -1010), (150, -870), (60, -1010)),
    "laugh":   ((-150, -560), (-20, -520), (150, -560), (30, -520)),
    "gada":    ((-105, -560), (-110, -400), (150, -600), (190, -560)),
    "staff":   ((-105, -560), (-110, -400), (150, -620), (190, -600)),
    "broom":   ((-40, -560), (90, -420), (120, -560), (150, -400)),
    "offer":   ((10, -600), (230, -640), (140, -600), (250, -650)),
    "fly":     ((-100, -560), (-90, -420), (70, -930), (80, -1100)),
    "stop":    ((-105, -560), (-110, -400), (190, -660), (230, -820)),
}


def _rot(p, c, deg):
    a = math.radians(deg); x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def _limb(d, pts, w, col):
    d.line(pts, fill=col, width=int(w), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)


def _curve(d, pts, w0, w1, col, n=220):
    """Thick tapering Catmull-Rom-ish curve through pts."""
    pts = np.array(pts, float)
    for i in range(n + 1):
        s = i / n * (len(pts) - 1); k = min(int(s), len(pts) - 2); u = s - k
        p0, p1, p2, p3 = pts[max(k - 1, 0)], pts[k], pts[k + 1], pts[min(k + 2, len(pts) - 1)]
        q = 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
        r = (w0 + (w1 - w0) * i / n) / 2
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=col)


def _P(p):
    return (OX + p[0], OY + p[1])


def _skeleton(arms, pose):
    J = dict(head=(14, -845), neck=(4, -765), sh_b=(-92, -732), sh_f=(92, -732),
             hip_b=(-52, -440), hip_f=(52, -440), kn_b=(-48, -225), kn_f=(52, -228), ft_b=(-52, -22), ft_f=(62, -22))
    eb, hb, ef, hf = ARMS.get(arms, ARMS["down"])
    J.update(el_b=eb, ha_b=hb, el_f=ef, ha_f=hf)
    if arms == "laugh":
        J["head"] = (-2, -850)
    if pose == "kneel":                      # kneeling: drop the upper body, knees forward on the ground
        dy = 210
        for k in ("head", "neck", "sh_b", "sh_f", "el_b", "el_f", "ha_b", "ha_f", "hip_b", "hip_f"):
            J[k] = (J[k][0] - 20, J[k][1] + dy)
        J.update(kn_b=(70, -40), kn_f=(110, -42), ft_b=(-150, -18), ft_f=(-120, -18))
    return J


def character(who, arms="down", pose="stand", sil=(14, 8, 6), light=(255, 210, 140), hold=None):
    B = dict(BODIES[who]); bulky = B.get("bulky"); col = sil + (255,)
    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    orn = []                                  # gold ornament draw calls, applied on top

    if pose == "sit":
        return _seated(who, B, sil, light)

    J = _skeleton(arms, pose)
    hunch = B.get("hunch", 0) + (50 if pose == "bowdown" else 0)
    if pose == "bowdown":
        J = _skeleton("extend", "kneel"); J["el_f"] = (200, -330); J["ha_f"] = (300, -120)
        J["el_b"] = (150, -330); J["ha_b"] = (260, -110)
    if hunch:                                 # bend the upper body forward around the hips
        c = ((J["hip_b"][0] + J["hip_f"][0]) / 2, J["hip_b"][1])
        for k in ("head", "neck", "sh_b", "sh_f", "el_b", "el_f", "ha_b", "ha_f"):
            J[k] = _rot(J[k], c, hunch)
    P = {k: _P(v) for k, v in J.items()}
    sw = 1.25 if bulky else 1.0
    arm_w, leg_w = 60 * sw, 70 * sw

    # tail behind everything
    if B.get("tail"):
        hx, hy = P["hip_b"]
        if arms == "fly":
            _curve(d, [(hx, hy), (hx - 60, hy + 200), (hx + 20, hy + 420), (hx - 40, hy + 600)], 56, 22, col)
        else:
            _curve(d, [(hx, hy), (hx - 170, hy + 60), (hx - 280, hy - 200), (hx - 230, hy - 470), (hx - 120, hy - 520), (hx - 110, hy - 420)],
                   56 if bulky else 46, 22, col)
    # back arm and weapon behind
    _limb(d, [P["sh_b"], P["el_b"], P["ha_b"]], arm_w, col)
    if B.get("bow") and arms in ("down", "bless", "point", "stop", "mouth"):   # bow held in back hand, quiver on back
        hx, hy = P["ha_b"]
        pts = [(hx - 40 - 75 * math.sin(math.pi * s), hy - 470 + 900 * s) for s in np.linspace(0, 1, 40)]
        d.line(pts, fill=col, width=26, joint="curve"); d.line([pts[0], pts[-1]], fill=col, width=6)
        orn.append(("line", pts, 5))
    if B.get("bow"):
        qx, qy = P["sh_b"]
        d.polygon([(qx - 40, qy - 60), (qx - 5, qy - 75), (qx - 60, qy + 230), (qx - 95, qy + 215)], fill=col)
        for k in range(3):
            d.line([(qx - 30 - k * 14, qy - 60), (qx - 5 - k * 14, qy - 170)], fill=col, width=7)
    # legs
    if pose != "sit":
        _limb(d, [P["hip_b"], P["kn_b"], P["ft_b"]], leg_w, col)
        _limb(d, [P["hip_f"], P["kn_f"], P["ft_f"]], leg_w, col)
        for k in ("ft_b", "ft_f"):
            x, y = P[k]; fwd = -1 if pose == "kneel" else 1
            d.ellipse([x - 30 + 25 * fwd, y - 22, x + 30 + 45 * fwd, y + 22], fill=col)
    # torso
    sb, sf, hb, hf = P["sh_b"], P["sh_f"], P["hip_b"], P["hip_f"]
    wide = 18 if bulky else 0
    d.polygon([(sb[0] - 12 - wide, sb[1]), (sf[0] + 12 + wide, sf[1]), (hf[0] + 16, hf[1]), (hb[0] - 16, hb[1])], fill=col)
    for p in (sb, sf):
        r = (arm_w + 14) / 2; d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    if bulky:
        cx, cy = (sb[0] + sf[0] + hb[0] + hf[0]) / 4, (sb[1] + sf[1]) / 2 + 90
        d.ellipse([cx - 120, cy - 110, cx + 125, cy + 110], fill=col)
    # lower garment
    if B.get("saree") or B.get("robe"):
        gx = 75 if pose != "kneel" else 0
        if pose == "kneel":
            d.polygon([(hb[0] - 40, hb[1] - 20), (hf[0] + 30, hf[1] - 20), (P["kn_f"][0] + 60, OY), (P["ft_b"][0] - 40, OY)], fill=col)
        else:
            d.polygon([(hb[0] - 30, hb[1] - 30), (hf[0] + 30, hf[1] - 30), (P["ft_f"][0] + gx, OY - 5), (P["ft_b"][0] - gx, OY - 5)], fill=col)
    elif not B.get("bare") and not B.get("bear"):
        d.polygon([(hb[0] - 22, hb[1] - 12), (hf[0] + 22, hf[1] - 12), (P["kn_f"][0] + 70, P["kn_f"][1] + 60), (P["kn_b"][0] - 70, P["kn_b"][1] + 60)], fill=col)
        orn.append(("line", [(hb[0] - 22, hb[1] - 14), (hf[0] + 22, hf[1] - 14)], 8))
    # neck + head
    _limb(d, [P["neck"], P["head"]], 64 * sw, col)
    hx, hy = P["head"]; R = 70 if B.get("bear") else 58
    if B.get("hair"):
        d.ellipse([hx - 72, hy - 40, hx + 25, hy + 140], fill=col)
    d.ellipse([hx - R, hy - R, hx + R, hy + R], fill=col)
    if B.get("muzzle"):
        d.ellipse([hx + 20, hy - 8, hx + 88, hy + 48], fill=col)
        d.ellipse([hx - 30, hy - 20, hx + 2, hy + 18], fill=col)
    if B.get("bear"):
        for ex, ey in ((hx - 48, hy - 58), (hx + 22, hy - 66)):
            d.ellipse([ex - 24, ey - 24, ex + 24, ey + 24], fill=col)
        d.ellipse([hx + 30, hy - 10, hx + 110, hy + 45], fill=col)
        d.polygon([(hx - 20, hy + 40), (hx + 70, hy + 40), (hx + 30, hy + 150)], fill=col)    # beard
    if B.get("sage"):
        d.ellipse([hx - 30, hy - 120, hx + 35, hy - 50], fill=col)                       # jata
        d.polygon([(hx - 10, hy + 30), (hx + 62, hy + 25), (hx + 45, hy + 210), (hx + 5, hy + 180)], fill=col)
    if B.get("veil"):                         # saree pallu over the head, gold border along its edge
        d.ellipse([hx - R - 14, hy - R - 16, hx + R + 6, hy + R], fill=col)
        d.polygon([(hx + 8, hy - R - 16), (hx + R + 22, hy - 20), (hx + R + 10, hy + 40), (P["sh_f"][0] + 30, P["sh_f"][1] + 30), (P["sh_b"][0], P["sh_b"][1])], fill=col)
        orn.append(("line", [(hx - 6, hy - R - 16), (hx + R + 22, hy - 20), (hx + R + 10, hy + 40), (P["sh_f"][0] + 30, P["sh_f"][1] + 30)], 6))
        d.polygon([(hx - R - 16, hy + 10), (hx - 10, hy - R - 14), (hx + 30, hy - R + 4), (P["sh_b"][0] + 10, P["sh_b"][1]),
                   (P["hip_b"][0] - 40, P["hip_b"][1] + 40), (P["hip_b"][0] - 110, P["hip_b"][1] + 10)], fill=col)
    if B.get("crown"):
        cr = [(hx - 50, hy - 38), (hx - 44, hy - 110), (hx - 22, hy - 92), (hx, hy - 178), (hx + 22, hy - 92), (hx + 44, hy - 110), (hx + 50, hy - 38)]
        d.polygon(cr, fill=col); orn.append(("line", cr + [cr[0]], 6))
    # front arm last
    _limb(d, [P["sh_f"], P["el_f"], P["ha_f"]], arm_w, col)
    hx2, hy2 = P["ha_f"]
    if arms == "gada" or (who == "hanuman" and arms == "down"):
        gx, gy = (hx2, hy2) if arms == "gada" else (P["ha_f"][0] + 10, P["ha_f"][1])
        d.line([(gx + 10, OY - 10), (gx, gy - 160)], fill=col, width=30)
        d.ellipse([gx - 100, gy - 360, gx + 100, gy - 160], fill=col)
        d.ellipse([gx - 22, gy - 400, gx + 22, gy - 350], fill=col)
        orn.append(("ell", [gx - 100, gy - 360, gx + 100, gy - 160], 7)); orn.append(("line", [(gx - 96, gy - 260), (gx + 96, gy - 260)], 6))
    if arms == "fly" and who == "hanuman":                  # gada carried in the back hand
        gx, gy = P["ha_b"]
        d.line([(gx, gy - 40), (gx - 10, gy + 260)], fill=col, width=28)
        d.ellipse([gx - 95, gy + 230, gx + 85, gy + 410], fill=col); orn.append(("ell", [gx - 95, gy + 230, gx + 85, gy + 410], 7))
    if arms == "staff":
        d.line([(hx2 + 6, OY - 5), (hx2 - 10, hy2 - 430)], fill=col, width=22)
    if arms == "broom":
        bx, by = P["ha_f"]
        d.line([(bx - 40, by - 120), (bx + 60, by + 230)], fill=col, width=16)
        d.polygon([(bx + 40, by + 200), (bx + 70, by + 210), (bx + 170, by + 380), (bx - 10, by + 400)], fill=col)
    if arms == "carry":
        cx = (P["ha_b"][0] + P["ha_f"][0]) / 2; cy = (P["ha_b"][1] + P["ha_f"][1]) / 2
        d.ellipse([cx - 150, cy - 170, cx + 150, cy + 10], fill=col)
    if arms in ("offer",) or hold == "bowl":
        cx, cy = P["ha_f"][0] + 10, P["ha_f"][1] - 20
        d.chord([cx - 95, cy - 60, cx + 95, cy + 60], 0, 180, fill=col)
        for k in range(7):
            bx = cx - 66 + k * 22; r = 15
            d.ellipse([bx - r, cy - 22 - r - (k % 2) * 14, bx + r, cy - 22 + r - (k % 2) * 14], fill=BERRY + (255,))
    if arms == "mouth" and who in ("shabari", "ram"):
        d.ellipse([hx2 - 16, hy2 - 30, hx2 + 16, hy2 + 2], fill=BERRY + (255,))
    if hold == "squirrel":
        _tiny_squirrel(d, hx2 - 10, hy2 - 22, 0.75, col, light)
    if B.get("orn"):                                          # necklace, armbands
        nx, ny = P["neck"]
        orn.append(("arc", [nx - 80, ny - 40, nx + 90, ny + 120], 6))
        for s_, e_ in (("sh_f", "el_f"), ("sh_b", "el_b")):
            a, b = P[s_], P[e_]; mx, my = a[0] + (b[0] - a[0]) * 0.45, a[1] + (b[1] - a[1]) * 0.45
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1; px, py = -dy / L * 26, dx / L * 26
            orn.append(("line", [(mx - px, my - py), (mx + px, my + py)], 8))
    return _finish(img, orn, B, light)


def _tiny_squirrel(d, x, y, s, col, light):
    d.ellipse([x - 40 * s, y - 110 * s, x + 30 * s, y], fill=col)
    d.ellipse([x + 5 * s, y - 150 * s, x + 62 * s, y - 95 * s], fill=col)
    d.polygon([(x + 18 * s, y - 135 * s), (x + 26 * s, y - 175 * s), (x + 40 * s, y - 140 * s)], fill=col)
    _curve(d, [(x - 40 * s, y - 20 * s), (x - 110 * s, y - 100 * s), (x - 80 * s, y - 220 * s), (x - 20 * s, y - 230 * s)], 50 * s, 30 * s, col)
    for k in (-1, 0, 1):
        d.line([(x - 30 * s, y - 60 * s + k * 15 * s), (x + 15 * s, y - 85 * s + k * 15 * s)], fill=light + (255,), width=max(3, int(7 * s)))


def _seated(who, B, sil, light):
    """Hanuman sitting cross-legged, head bowed, gada beside him."""
    col = sil + (255,); img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); d = ImageDraw.Draw(img); orn = []
    _curve(d, [_P((-120, -40)), _P((-300, -20)), _P((-330, -120)), _P((-260, -170))], 50, 22, col)          # tail on the ground
    d.ellipse([OX - 200, OY - 150, OX + 210, OY], fill=col)                                                # crossed legs
    d.polygon([_P((-90, -110)), _P((95, -110)), _P((120, -440)), _P((-95, -450))], fill=col)               # torso
    d.ellipse([OX - 125, OY - 420, OX + 140, OY - 220], fill=col)
    head = _P((70, -530)); hx, hy = head
    _limb(d, [_P((10, -450)), head], 62, col)
    d.ellipse([hx - 58, hy - 58, hx + 58, hy + 58], fill=col)
    d.ellipse([hx + 22, hy - 2, hx + 88, hy + 52], fill=col)
    cr = [(hx - 50, hy - 38), (hx - 44, hy - 110), (hx - 22, hy - 92), (hx, hy - 178), (hx + 22, hy - 92), (hx + 44, hy - 110), (hx + 50, hy - 38)]
    d.polygon(cr, fill=col); orn.append(("line", cr + [cr[0]], 6))
    for sh, el, ha in (((-90, -420), (-150, -250), (-80, -140)), ((110, -420), (170, -250), (150, -130))):
        _limb(d, [_P(sh), _P(el), _P(ha)], 54, col)
    gx, gy = _P((300, -10))
    d.line([(gx, gy), (gx - 60, gy - 420)], fill=col, width=30)
    d.ellipse([gx - 165, gy - 620, gx + 35, gy - 420], fill=col); orn.append(("ell", [gx - 165, gy - 620, gx + 35, gy - 420], 7))
    nx, ny = _P((20, -450)); orn.append(("arc", [nx - 80, ny - 30, nx + 90, ny + 120], 6))
    return _finish(img, orn, B, light)


def _finish(img, orn, B, light):
    a = img.getchannel("A")
    small = a.resize((CW // 4, CH // 4))
    # rim light: the part of the silhouette not covered by a copy shifted down-left
    sh = Image.new("L", a.size, 0); sh.paste(a, (-9, 7))
    rim = Image.fromarray(np.clip(np.asarray(a, np.int16) - np.asarray(sh, np.int16), 0, 255).astype(np.uint8))
    rim = rim.filter(ImageFilter.GaussianBlur(2))
    # thin outline everywhere for separation from dark backgrounds
    er = small.filter(ImageFilter.MinFilter(3)).resize(a.size)
    edge = Image.fromarray((np.clip(np.asarray(a, np.int16) - np.asarray(er, np.int16), 0, 255) * 0.45).astype(np.uint8))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    if B.get("aura"):
        g = small.filter(ImageFilter.GaussianBlur(16)).resize(a.size).point(lambda v: int(min(255, v * 1.6) * 0.75))
        out.paste(Image.new("RGBA", img.size, GOLD + (255,)), (0, 0), g)
    out = Image.alpha_composite(out, img)
    lay = Image.new("RGBA", img.size, light + (255,))
    out.paste(lay, (0, 0), Image.fromarray(np.maximum(np.asarray(rim), np.asarray(edge))))
    d = ImageDraw.Draw(out)
    for kind, pts, w in orn:
        if kind == "line": d.line(pts, fill=GOLD + (255,), width=w, joint="curve")
        elif kind == "ell": d.ellipse(pts, outline=GOLD + (255,), width=w)
        elif kind == "arc": d.arc(pts, 20, 160, fill=GOLD + (255,), width=w)
    bb = out.getbbox()
    return out.crop((0, bb[1], CW, CH)) if bb else out
