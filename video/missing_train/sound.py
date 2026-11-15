"""Sound design for "रहस्यमयी ट्रेन": ambience beds, music cues and sound effects, all synthesised."""
import numpy as np

SR = 24000


def band(x, lo, hi, soft=0.15):
    """FFT band-pass with soft edges (fast for long signals)."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if lo > 0:
        g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** (2 / soft * 0.1 + 2))
    if hi < SR / 2:
        g *= 1 / (1 + (f / hi) ** (2 / soft * 0.1 + 2))
    return np.fft.irfft(X * g, n).astype(np.float32)


def norm(x, peak=1.0):
    m = np.abs(x).max()
    return (x / m * peak).astype(np.float32) if m > 0 else x


def env(n, a, r):
    e = np.ones(n, np.float32)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def add(buf, sig, at, g=1.0):
    i = int(at * SR)
    if i < 0:
        sig, i = sig[-i:], 0
    if i >= len(buf): return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n] * g


def reverb(a, wet=0.3, dec=0.6, echo=0.0, dly=0.32):
    n = int(dec * 2.5 * SR)
    t = np.arange(n) / SR
    ir = np.random.default_rng(5).standard_normal(n) * np.exp(-t / dec * 2.3)
    ir /= np.sqrt((ir ** 2).sum())
    L = len(a) + n
    m = 1 << (L - 1).bit_length()
    rv = np.fft.irfft(np.fft.rfft(a, m) * np.fft.rfft(ir, m), m)[:L]
    out = np.pad(a, (0, n)) + wet * rv
    if echo:
        d = int(dly * SR)
        for k in range(1, 4):
            out[d * k:] += (echo ** k) * out[:-d * k] if d * k < len(out) else 0
    return out.astype(np.float32)


# ---------------------------------------------------------------- ambience beds (full length)
def rain(n, rng):
    x = rng.standard_normal(n).astype(np.float32)
    hiss = band(x, 600, 9000) * 0.5
    low = band(rng.standard_normal(n).astype(np.float32), 60, 500) * 0.6
    drops = np.zeros(n, np.float32)
    k = int(n / SR * 40)
    pos = rng.integers(0, n - 200, k)
    click = band(rng.standard_normal(160).astype(np.float32), 1500, 7000) * np.exp(-np.arange(160) / 25)
    for p, a in zip(pos, rng.uniform(0.2, 1.0, k)):
        drops[p:p + 160] += click * a
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * np.arange(n) / SR * 0.07)
    return norm((hiss + low + drops * 0.6) * lfo, 0.5)


def rain_inside(n, rng):
    return norm(band(rain(n, rng), 80, 1400), 0.5)


def rumble(n, rng, period=1.05, hard=False):
    """Inside a running train: low rumble plus the clickety-clack of rail joints."""
    base = band(rng.standard_normal(n).astype(np.float32), 25, 260 if not hard else 600)
    base = norm(base, 0.45)
    clk = np.zeros(n, np.float32)
    L = int(0.09 * SR)
    burst = (band(rng.standard_normal(L).astype(np.float32), 500, 3500) * 0.6
             + np.sin(2 * np.pi * 70 * np.arange(L) / SR)) * np.exp(-np.arange(L) / (0.02 * SR))
    burst = norm(burst, 0.9)
    t = 0.3
    while t < n / SR - 0.5:
        for d, a in ((0, 1.0), (0.14, 0.8)):
            add(clk, burst, t + d, a * rng.uniform(0.7, 1.0))
        t += period
    out = base + clk * (0.5 if not hard else 0.8)
    if hard:
        out += norm(band(rng.standard_normal(n).astype(np.float32), 2500, 7000), 0.08)
    return norm(out, 0.6)


def birds(n, rng):
    out = np.zeros(n, np.float32)
    t = 0.5
    while t < n / SR - 1:
        f0 = rng.uniform(2600, 4200)
        for k in range(rng.integers(2, 6)):
            d = rng.uniform(0.05, 0.12)
            tt = np.arange(int(d * SR)) / SR
            f = f0 + rng.uniform(-900, 900) * tt / d
            s = np.sin(2 * np.pi * np.cumsum(f) / SR + 3 * np.sin(2 * np.pi * 30 * tt)) * np.sin(np.pi * tt / d) ** 2
            add(out, s.astype(np.float32), t + k * rng.uniform(0.1, 0.18), rng.uniform(0.2, 0.6))
        t += rng.uniform(0.6, 2.2)
    wind = band(rng.standard_normal(n).astype(np.float32), 100, 900)
    return norm(out + norm(wind, 0.15), 0.5)


def ticks(n, rng):
    out = np.zeros(n, np.float32)
    L = int(0.03 * SR)
    c = band(rng.standard_normal(L).astype(np.float32), 1500, 6000) * np.exp(-np.arange(L) / 80)
    c2 = c * 0.6
    t = 0.2
    i = 0
    while t < n / SR:
        add(out, c if i % 2 == 0 else c2, t)
        t += 1.0; i += 1
    return norm(reverb(out, 0.5, 0.4)[:n], 0.6)


def wind(n, rng):
    x = band(rng.standard_normal(n).astype(np.float32), 80, 700)
    tt = np.arange(n) / SR
    return norm(x * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * tt) * np.sin(2 * np.pi * 0.13 * tt)), 0.5)


AMB = {"rain": rain, "rain_in": rain_inside, "rumble": rumble, "birds": birds, "tick": ticks, "wind": wind,
       "cab": lambda n, r: rumble(n, r, 0.8, True)}


# ---------------------------------------------------------------- music beds (full length)
def piano(f, d=3.0):
    t = np.arange(int(d * SR)) / SR
    s = sum((0.6 ** (k - 1)) * np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k * k)) * np.exp(-t * (1.2 + 0.8 * k))
            for k in range(1, 7))
    return (s * np.minimum(t / 0.004, 1)).astype(np.float32)


def pad(n, freqs, rng):
    tt = np.arange(n) / SR
    s = np.zeros(n, np.float32)
    for f in freqs:
        for det in (-0.6, 0.6):
            s += np.sin(2 * np.pi * (f + det) * tt + rng.uniform(0, 6)).astype(np.float32)
    return s / (2 * len(freqs))


NOTE = {n: 440 * 2 ** ((i - 9) / 12) for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())}


def hz(name):
    return NOTE[name[:-1]] * 2 ** (int(name[-1]) - 4)


def tune(n, rng, chords, melody, bpm, vol=1.0):
    """Piano melody over sustained chords; chords change every bar (4 beats)."""
    out = np.zeros(n, np.float32)
    beat = 60 / bpm
    bar = 4 * beat
    T = n / SR
    t, ci = 0.0, 0
    while t < T:
        ch = chords[ci % len(chords)]
        seg = int(bar * SR) + int(0.5 * SR)
        p = pad(seg, [hz(x) for x in ch], rng) * env(seg, 0.8, 0.9) * 0.35
        add(out, p, t)
        add(out, piano(hz(ch[0]) / 2, 4.0) * 0.35, t)
        t += bar; ci += 1
    t, mi = beat * 2, 0
    while t < T:
        nm, ln = melody[mi % len(melody)]
        if nm != "-":
            add(out, piano(hz(nm), 3.0) * 0.32 * rng.uniform(0.85, 1.0), t)
        t += ln * beat; mi += 1
    return norm(reverb(out, 0.45, 1.2)[:n], 0.5 * vol)


def sad(n, rng):
    chords = [("D3", "F3", "A3"), ("A#2", "D3", "F3"), ("F3", "A3", "C4"), ("A2", "C#3", "E3")]
    mel = [("D5", 1), ("F5", 1), ("E5", 1), ("D5", 1), ("C5", 1.5), ("A4", 2.5),
           ("A#4", 1), ("C5", 1), ("D5", 1), ("F5", 1), ("E5", 2), ("-", 2),
           ("A4", 1), ("D5", 1.5), ("C5", 0.5), ("A#4", 1), ("A4", 2), ("F4", 2),
           ("G4", 1), ("A4", 1), ("C#5", 1), ("E5", 1), ("D5", 4)]
    return tune(n, rng, chords, mel, 64)


def warm(n, rng):
    chords = [("D3", "F#3", "A3"), ("A2", "C#3", "E3"), ("B2", "D3", "F#3"), ("G2", "B2", "D3")]
    mel = [("F#5", 1), ("E5", 1), ("D5", 1), ("A4", 1), ("E5", 2), ("C#5", 2),
           ("D5", 1), ("F#5", 1), ("B5", 1), ("A5", 1), ("G5", 2), ("F#5", 2),
           ("E5", 1), ("F#5", 1), ("A5", 2), ("D5", 4), ("-", 2), ("A4", 1), ("B4", 1)]
    return tune(n, rng, chords, mel, 72)


def drone(n, rng):
    tt = np.arange(n) / SR
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.06 * tt)
    s = (np.sin(2 * np.pi * 55 * tt) + 0.7 * np.sin(2 * np.pi * 55.4 * tt) + 0.5 * np.sin(2 * np.pi * 82.6 * tt)
         + 0.25 * np.sin(2 * np.pi * 116.5 * tt + np.sin(2 * np.pi * 0.2 * tt)))
    air = band(rng.standard_normal(n).astype(np.float32), 200, 1200) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.03 * tt))
    s = s * lfo / 2.4 + norm(air, 0.35)
    # distant, slow music-box like notes (minor, sparse)
    t = 4.0
    notes = ["A5", "C6", "E5", "D#6", "B5", "F5"]
    i = 0
    while t < n / SR - 3:
        add(s, piano(hz(notes[i % len(notes)]), 3.5) * 0.12, t)
        t += rng.uniform(5, 9); i += 1
    return norm(reverb(s.astype(np.float32), 0.5, 1.5)[:n], 0.5)


def heart(n, rng):
    out = np.zeros(n, np.float32)
    L = int(0.35 * SR)
    t_ = np.arange(L) / SR
    k = np.sin(2 * np.pi * np.cumsum(45 + 60 * np.exp(-t_ * 30)) / SR) * np.exp(-t_ * 14)
    t = 0.2
    while t < n / SR - 1:
        add(out, k, t); add(out, k * 0.7, t + 0.28)
        t += 0.92
    return norm(out, 0.7)


def tension(n, rng):
    tt = np.arange(n) / SR
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 7 * tt)
    s = sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) for f in (880, 932.3, 987.8, 1046.5))
    return norm((s * trem / 4).astype(np.float32), 0.25) + heart(n, rng) * 0.8


MUSIC = {"sad": sad, "warm": warm, "drone": drone, "heart": heart, "tension": tension}


# ---------------------------------------------------------------- one-shot effects
def thunder(rng):
    n = int(6 * SR); t = np.arange(n) / SR
    crack = band(rng.standard_normal(n).astype(np.float32), 800, 8000) * np.exp(-t * 9)
    roll = band(rng.standard_normal(n).astype(np.float32), 25, 260) * np.exp(-t * 0.7)
    roll *= 0.6 + 0.4 * np.abs(band(rng.standard_normal(n).astype(np.float32), 0.5, 4))
    return norm(norm(crack, 0.6) + norm(roll, 1.0) * np.minimum(t / 0.08, 1), 1.0)


def chime(rng):
    out = np.zeros(int(2.6 * SR), np.float32)
    for i, f in enumerate((1046.5, 880.0, 698.5)):
        t = np.arange(int(1.6 * SR)) / SR
        b = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)) * np.exp(-t * 2.5)
        add(out, b.astype(np.float32), i * 0.38)
    return norm(reverb(out, 0.4, 0.8), 0.7)


def whistle(rng, d=2.6):
    n = int(d * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
    s = sum(a * np.sin(2 * np.pi * f * vib * t) for f, a in ((392, 1), (494, 0.8), (587, 0.7), (784, 0.25)))
    s = s * env(n, 0.18, 0.6) + band(rng.standard_normal(n).astype(np.float32), 1500, 5000) * 0.2 * env(n, 0.1, 0.6)
    return norm(reverb(s.astype(np.float32), 0.7, 1.6, echo=0.35, dly=0.45), 0.9)


def brakes(rng, d=3.2):
    n = int(d * SR); t = np.arange(n) / SR
    f = 2700 + 300 * np.sin(2 * np.pi * 3 * t) + 120 * rng.standard_normal(n).cumsum() / np.sqrt(n)
    sq = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t)) * env(n, 0.3, 1.0)
    hs = band(rng.standard_normal(n).astype(np.float32), 2000, 8000) * np.exp(-t * 0.5)
    return norm(sq * 0.4 + hs * 0.6 * env(n, 0.05, 0.5), 0.8)


def hiss(rng, d=2.0):
    n = int(d * SR)
    return norm(band(rng.standard_normal(n).astype(np.float32), 1500, 9000) * env(n, 0.05, 1.4), 0.7)


def puff(rng, a=1.0):
    n = int(0.28 * SR); t = np.arange(n) / SR
    return (band(rng.standard_normal(n).astype(np.float32), 150, 2500) * np.exp(-t * 14) * a).astype(np.float32)


def chugs(rng, d, r0, r1, a0=1.0, a1=1.0):
    out = np.zeros(int(d * SR) + SR, np.float32)
    t = 0.0
    while t < d:
        p = t / d
        add(out, puff(rng, a0 + (a1 - a0) * p), t)
        t += 1 / (r0 + (r1 - r0) * p)
    return norm(out, 0.8)


def door_slide(rng):
    n = int(1.4 * SR); t = np.arange(n) / SR
    roll = band(rng.standard_normal(n).astype(np.float32), 80, 900) * env(n, 0.1, 0.3)
    sq = np.sin(2 * np.pi * np.cumsum(900 + 400 * np.sin(2 * np.pi * 1.3 * t)) / SR) * 0.15 * env(n, 0.3, 0.6)
    k = np.zeros(n, np.float32); add(k, slam(rng)[:int(0.5 * SR)] * 0.4, 1.2)
    return norm(roll + sq + k, 0.7)


def slam(rng):
    n = int(1.5 * SR); t = np.arange(n) / SR
    k = np.sin(2 * np.pi * np.cumsum(50 + 120 * np.exp(-t * 25)) / SR) * np.exp(-t * 7)
    nz = band(rng.standard_normal(n).astype(np.float32), 300, 5000) * np.exp(-t * 25)
    return norm(reverb((k + nz * 0.6).astype(np.float32), 0.5, 0.7)[:n], 1.0)


def boom(rng):
    n = int(4 * SR); t = np.arange(n) / SR
    k = np.sin(2 * np.pi * np.cumsum(32 + 90 * np.exp(-t * 6)) / SR) * np.exp(-t * 1.2)
    nz = band(rng.standard_normal(n).astype(np.float32), 20, 200) * np.exp(-t * 1.5)
    return norm(k + norm(nz, 0.5), 1.0)


def sting(rng):
    n = int(4 * SR); t = np.arange(n) / SR
    cl = sum(np.sin(2 * np.pi * f * t) for f in (622, 659, 698, 1244, 1318)) / 5 * np.exp(-t * 1.1)
    cl *= np.minimum(t / 0.01, 1)
    return norm(boom(rng)[:n] + cl * 0.7, 1.0)


def screech(rng, d=1.8):
    n = int(d * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * (1 - 0.08 * t) * t) for f in (1900, 2870, 3410)) / 3
    s = s * env(n, 0.02, 0.6) + band(rng.standard_normal(n).astype(np.float32), 2000, 8000) * 0.4 * env(n, 0.01, 0.5)
    out = np.zeros(int((d + 3) * SR), np.float32)
    add(out, s.astype(np.float32), 0)
    add(out, boom(rng) * 0.9, d * 0.7)
    return norm(out, 1.0)


def riser(rng, d=3.0):
    n = int(d * SR); t = np.arange(n) / SR; p = t / d
    sw = np.sin(2 * np.pi * np.cumsum(200 + 900 * p ** 2) / SR) * 0.3
    nz = band(rng.standard_normal(n).astype(np.float32), 300, 6000)
    return norm((sw + norm(nz, 0.5)) * p ** 2, 0.8)


def whoosh(rng, d=1.2):
    n = int(d * SR); t = np.linspace(0, 1, n)
    return norm(band(rng.standard_normal(n).astype(np.float32), 200, 3000) * np.sin(np.pi * t) ** 2, 0.7)


def rustle(rng, d=1.4):
    out = np.zeros(int(d * SR), np.float32)
    for _ in range(14):
        L = int(rng.uniform(0.03, 0.12) * SR)
        b = band(rng.standard_normal(L).astype(np.float32), 1500, 9000) * np.hanning(L)
        add(out, b, rng.uniform(0, d - 0.15), rng.uniform(0.3, 1))
    return norm(out, 0.6)


def steps(rng, d=2.0, rate=2.0):
    out = np.zeros(int(d * SR) + SR, np.float32)
    L = int(0.08 * SR); t_ = np.arange(L) / SR
    s = (band(rng.standard_normal(L).astype(np.float32), 200, 3000) * np.exp(-t_ * 50)
         + np.sin(2 * np.pi * 90 * t_) * np.exp(-t_ * 40) * 0.5)
    t = 0.0
    while t < d:
        add(out, s, t, rng.uniform(0.6, 1.0)); t += 1 / rate
    return norm(out, 0.6)


def bell(rng):
    n = int(3 * SR); t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in ((523, 1, 1.2), (1046, 0.5, 2), (1569, 0.3, 3), (2617, 0.15, 5)))
    return norm(reverb(s.astype(np.float32), 0.5, 1.2), 0.6)


SFX = {"thunder": thunder, "chime": chime, "whistle": whistle, "brakes": brakes, "hiss": hiss,
       "arrive": lambda r: chugs(r, 9.0, 4.0, 0.7, 0.9, 0.4), "depart": lambda r: chugs(r, 10.0, 0.6, 4.5, 0.5, 0.9),
       "door": door_slide, "slam": slam, "boom": boom, "sting": sting, "screech": screech, "riser": riser,
       "whoosh": whoosh, "rustle": rustle, "steps": steps, "run": lambda r: steps(r, 2.0, 4.0), "bell": bell,
       "lights_off": lambda r: norm(band(r.standard_normal(int(0.4 * SR)).astype(np.float32), 50, 400) * np.exp(-np.arange(int(0.4 * SR)) / SR * 12), 0.8)}


def pa(a):
    """Old station loudspeaker: narrow band, a bit of distortion, big echo."""
    x = band(a, 350, 3400)
    x = np.tanh(norm(x, 1.0) * 2.2) * 0.8
    return reverb(x.astype(np.float32), 0.55, 1.4, echo=0.35, dly=0.38)
