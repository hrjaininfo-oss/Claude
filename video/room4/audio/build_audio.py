#!/usr/bin/env python3
"""
Room No. 4 — sound builder.

Reads src/story.json and writes:
  public/audio/dialogue.mp3   character voices (offline Kokoro TTS, Hindi voices) placed on the timeline
  public/audio/sfx.mp3        synthesised foley + ambience (knocks, creak, rattle, footsteps, car, wind, crickets…)
  public/audio/music.mp3      synthesised horror score (drones, music box, heartbeat, risers, stingers)
  src/generated/lipsync.json  real start/end of every line + mouth-opening per video frame

Usage:  python3 audio/build_audio.py
Needs:  pip install numpy scipy soundfile kokoro-onnx ;  ffmpeg on PATH
The voice model (~350 MB) is downloaded once into audio/.models/.
"""
import hashlib, json, os, subprocess, urllib.request
import numpy as np
import soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STORY = json.load(open(os.path.join(ROOT, "src", "story.json")))
SR = 48000
FPS = STORY["fps"]
DUR = STORY["duration"]
N = int(DUR * SR)
B = STORY["beats"]
rng = np.random.default_rng(4)
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"


# ------------------------------------------------------------------ DSP helpers
def t_(dur):
    return np.arange(int(dur * SR)) / SR


def noise(dur):
    return rng.standard_normal(int(dur * SR)).astype(np.float32)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="low", fs=SR, output="sos"), x).astype(np.float32)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, btype="high", fs=SR, output="sos"), x).astype(np.float32)


def env_ad(n, a, d):
    """attack / exponential decay envelope (seconds)."""
    t = np.arange(n) / SR
    return (np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)).astype(np.float32)


def fade(x, fi=0.01, fo=0.05):
    x = x.copy()
    a, b = int(fi * SR), int(fo * SR)
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x


def reverb(x, decay, wet, seed=1, pre=0.0):
    n = int(decay * 1.6 * SR)
    t = np.arange(n) / SR
    ir = np.random.default_rng(seed).standard_normal(n) * np.exp(-t / (decay / 3))
    ir = lp(ir.astype(np.float32), 6000)
    ir /= np.sqrt((ir ** 2).sum()) + 1e-9
    if pre: ir = np.concatenate([np.zeros(int(pre * SR), np.float32), ir])
    y = signal.fftconvolve(x, ir)[: len(x) + len(ir)]
    out = np.pad(x, (0, len(y) - len(x))) * (1 - wet * 0.3) + wet * y
    return out.astype(np.float32)


SPACES = {"outdoor": (0.5, 0.18), "hall": (2.2, 0.45), "room": (0.8, 0.28)}


class Track:
    def __init__(self):
        self.L = np.zeros(N + SR * 4, np.float32)
        self.R = np.zeros(N + SR * 4, np.float32)

    def add(self, x, at, gain=1.0, pan=0.0):
        i = int(at * SR)
        if i < 0: x, i = x[-i:], 0
        x = x[: len(self.L) - i]
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.L[i:i + len(x)] += x * gain * gl * 1.414
        self.R[i:i + len(x)] += x * gain * gr * 1.414

    def stereo(self):
        return np.stack([self.L[:N], self.R[:N]], 1)


# ------------------------------------------------------------------ voices
_tts = None


def ensure_models():
    d = os.path.join(HERE, ".models"); os.makedirs(d, exist_ok=True)
    for f in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        p = os.path.join(d, f)
        if not os.path.exists(p):
            print("Downloading", f, "…"); urllib.request.urlretrieve(MODEL_URL + f, p)
    return d


def tts(text, voice, speed):
    global _tts
    cdir = os.path.join(HERE, ".cache"); os.makedirs(cdir, exist_ok=True)
    cp = os.path.join(cdir, hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16] + ".npy")
    if os.path.exists(cp): return np.load(cp)
    if _tts is None:
        from kokoro_onnx import Kokoro
        d = ensure_models()
        _tts = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
    a, sr = _tts.create(text, voice=voice, speed=speed, lang="hi")
    a = np.asarray(a, np.float32)
    a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a).astype(np.float32)
    nz = np.where(np.abs(a) > 0.02)[0]
    if len(nz): a = a[max(0, nz[0] - 1200): nz[-1] + 3600]
    np.save(cp, a)
    return a


def speak(text, prof, fit=None):
    """TTS in a character voice. Pitch shift keeps speed. Speeds up if it would overrun `fit` seconds."""
    voice, speed, st = prof["voice"], prof["speed"], prof["pitch"]
    r = 2 ** (st / 12)
    for _ in range(4):
        a = tts(text, voice, round(min(2.0, max(0.5, speed / r)), 3))
        if st:
            n = int(len(a) / r); a = np.interp(np.arange(n) * r, np.arange(len(a)), a).astype(np.float32)
        if fit is None or len(a) / SR <= fit: break
        speed *= (len(a) / SR) / fit * 1.03
    return a


def whisperize(a):
    """Turn a voice into a breathy whisper: noise shaped by the voice's own spectrum envelope."""
    f, t, Z = signal.stft(a, SR, nperseg=1024)
    mag = np.abs(Z)
    ph = np.exp(1j * rng.uniform(0, 2 * np.pi, Z.shape))
    _, w = signal.istft(mag * ph, SR, nperseg=1024)
    w = hp(w[: len(a)].astype(np.float32), 900)
    return (0.85 * w + 0.15 * hp(a, 2500)).astype(np.float32)


def mouth_env(a):
    hop = SR // FPS
    n = len(a) // hop + 1
    e = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(a) else 0 for i in range(n)])
    e = np.clip(e / (np.percentile(e, 92) + 1e-6), 0, 1)
    return np.round(e, 3).tolist()


# ------------------------------------------------------------------ SFX library
def knock(strength=1.0):
    d = 0.5
    t = t_(d)
    body = np.sin(2 * np.pi * (95 + 40 * np.exp(-t / 0.02)) * t) * env_ad(len(t), 0.001, 0.07)
    click = bp(noise(d), 300, 2500) * env_ad(len(t), 0.0005, 0.012) * 0.6
    rattle = bp(noise(d), 1500, 4000) * env_ad(len(t), 0.003, 0.05) * 0.08
    return ((body * 0.9 + click + rattle) * strength).astype(np.float32)


def footstep(surface="stone", strength=1.0):
    d = 0.35
    if surface == "wood":
        x = bp(noise(d), 120, 900) * env_ad(int(d * SR), 0.004, 0.05) * 1.2
        x += np.sin(2 * np.pi * 70 * t_(d)) * env_ad(int(d * SR), 0.002, 0.04) * 0.5
        if rng.random() < 0.35:  # creaky board
            c = creak(0.25, base=380) * 0.25
            x[: len(c)] += c
    elif surface == "dirt":
        x = bp(noise(d), 400, 5000) * env_ad(int(d * SR), 0.01, 0.06) * 0.8
    else:
        x = bp(noise(d), 200, 3000) * env_ad(int(d * SR), 0.002, 0.035) * 1.0
        x += bp(noise(d), 3000, 8000) * env_ad(int(d * SR), 0.015, 0.05) * 0.25  # scuff
    return (x * strength * (0.8 + 0.4 * rng.random())).astype(np.float32)


def creak(dur, base=520, wild=1.0):
    """Stick-slip friction: irregular pulse train through wooden resonances."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rate = 35 + 30 * np.sin(2 * np.pi * 0.7 * t) * wild + 15 * lp(rng.standard_normal(n).astype(np.float32), 8) * 40 * wild
    rate = np.clip(rate, 12, 140)
    ph = np.cumsum(rate / SR)
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(np.float32)
    pulses *= 0.6 + 0.8 * rng.random(n).astype(np.float32)
    y = np.zeros(n, np.float32)
    for f, q, g in [(base, 18, 1.0), (base * 2.13, 22, 0.6), (base * 3.4, 25, 0.35), (base * 0.55, 12, 0.5)]:
        b, a = signal.iirpeak(min(f, SR / 2 - 100), q, SR)
        y += signal.lfilter(b, a, pulses).astype(np.float32) * g
    y = fade(y, 0.05, 0.15)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def metal_clink():
    d = 0.4
    t = t_(d)
    f0 = 1700 + rng.random() * 600
    x = sum(np.sin(2 * np.pi * f0 * k * t + rng.random() * 6) * np.exp(-t / (0.08 / k ** 0.5)) / k
            for k in (1, 1.53, 2.41, 3.37))
    return (x * env_ad(len(t), 0.0005, 0.2) * 0.5 + bp(noise(d), 2000, 8000) * env_ad(len(t), 0.0005, 0.01) * 0.3).astype(np.float32)


def rattle(dur, intensity=1.0):
    n = int(dur * SR)
    y = np.zeros(n + SR, np.float32)
    tt = 0.0
    while tt < dur:
        c = metal_clink() * (0.4 + 0.6 * rng.random()) * intensity
        knk = knock(0.18) if rng.random() < 0.5 else 0
        i = int(tt * SR)
        y[i:i + len(c)] += c
        if not isinstance(knk, int): y[i:i + len(knk)] += knk
        tt += 0.035 + rng.random() * 0.06 / max(intensity, 0.3)
    return y[:n]


def boom(dur=3.0, f0=55, f1=28):
    t = t_(dur)
    f = f1 + (f0 - f1) * np.exp(-t / 0.3)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.005, dur / 3.5)
    crack = lp(noise(dur), 1800) * env_ad(len(t), 0.002, 0.25) * 0.5
    return (sub + crack).astype(np.float32)


def whoosh(dur=0.6, up=True):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    k = t if up else 1 - t
    lo, hi = bp(noise(dur), 200, 1200), bp(noise(dur), 1500, 7000)
    shape = np.sin(np.pi * t) ** 2
    return ((lo * (1 - k) + hi * k) * shape * 1.4).astype(np.float32)


def riser(dur):
    t = t_(dur)
    p = t / dur
    tone = sum(np.sin(2 * np.pi * np.cumsum(f * (1 + 0.8 * p ** 2)) / SR) for f in (220, 233, 311, 466)) * 0.15
    nz = hp(noise(dur), 2000) * 0.25
    return ((tone + nz) * p ** 2.2).astype(np.float32)


def screech(dur=2.5):
    """Dissonant high string cluster (horror 'stinger' strings)."""
    t = t_(dur)
    y = np.zeros(len(t), np.float32)
    for f in (1046, 1108, 1174, 1568, 1661):
        vib = 1 + 0.006 * np.sin(2 * np.pi * (5 + rng.random() * 2) * t)
        ph = np.cumsum(f * vib) / SR
        saw = 2 * (ph % 1) - 1
        y += saw * 0.12
    y = bp(y, 600, 7000) * env_ad(len(t), 0.01, dur / 2.2)
    return y.astype(np.float32)


def heartbeat(strength=1.0):
    d = 0.6
    t = t_(d)
    def thump(delay, g):
        tt = np.maximum(0, t - delay)
        return np.sin(2 * np.pi * 48 * tt) * np.exp(-tt / 0.06) * (t >= delay) * g
    return (lp(thump(0, 1.0) + thump(0.17, 0.7), 200) * strength * 1.6).astype(np.float32)


def clock_tick(tock=False):
    d = 0.12
    x = bp(noise(d), 2500 if not tock else 1800, 6000) * env_ad(int(d * SR), 0.0003, 0.008)
    return (x * 0.9).astype(np.float32)


def car_engine(dur, idle_from=None, stop_at=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    rpm = np.full(n, 34.0)
    if idle_from is not None:
        rpm = np.where(t < idle_from, 34.0, 34.0 - 12 * np.minimum(1, (t - idle_from) / 0.8))
    ph = np.cumsum(rpm) / SR
    eng = sum(np.sin(2 * np.pi * ph * k) / k for k in range(1, 9))
    eng = lp(eng.astype(np.float32), 420) * 0.5 + lp(noise(dur), 300) * 0.15
    gravel = bp(noise(dur), 600, 5000) * (0.5 + 0.5 * lp(np.abs(rng.standard_normal(n)).astype(np.float32), 18)) * 0.25
    road = lp(noise(dur), 120) * 0.35
    out = eng + gravel + road
    if stop_at is not None:
        k = np.clip((stop_at - t) / 0.25, 0, 1)
        out = eng * k + (gravel + road) * np.clip((idle_from - t) / 0.6 + 1, 0, 1)
    return out.astype(np.float32)


def car_door():
    d = 0.6
    t = t_(d)
    thud = np.sin(2 * np.pi * 70 * t) * env_ad(len(t), 0.002, 0.09)
    latch = bp(noise(d), 1500, 6000) * env_ad(len(t), 0.0005, 0.02) * 0.6
    return (thud + latch).astype(np.float32)


def wind(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    base = lp(noise(dur), 700) * 1.2
    gust = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + 1) * np.sin(2 * np.pi * 0.023 * t)
    whistle = bp(noise(dur), 900, 1100, 4) * 2.5 * np.clip(np.sin(2 * np.pi * 0.05 * t), 0, 1) ** 2
    return ((base * (0.4 + 0.6 * gust) + whistle * 0.3)).astype(np.float32)


def crickets(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for k, f in enumerate((4300, 4700, 5100)):
        chirp_rate = 2.2 + k * 0.7
        gate = (np.sin(2 * np.pi * chirp_rate * t + k) > 0.55).astype(np.float32)
        trill = (np.sin(2 * np.pi * 38 * t) > 0).astype(np.float32)
        y += np.sin(2 * np.pi * f * t) * lp(gate * trill, 300) * 0.05
    return y


def room_tone(dur):
    t = t_(dur)
    return (lp(noise(dur), 250) * 0.25 + np.sin(2 * np.pi * 50 * t) * 0.01).astype(np.float32)


def flicker_buzz(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    gate = (rng.random(int(dur * 30) + 1) > 0.45).astype(np.float32)
    gate = np.repeat(gate, SR // 30)[:n]
    buzz = (np.sign(np.sin(2 * np.pi * 100 * t)) * 0.2 + bp(noise(dur), 2000, 9000) * 0.4) * gate
    return buzz.astype(np.float32)


def glitch_fx(dur):
    n = int(dur * SR)
    y = np.zeros(n, np.float32)
    i = 0
    while i < n:
        seg = int(SR * (0.02 + rng.random() * 0.08))
        if rng.random() < 0.5:
            f = 200 + rng.random() * 3000
            y[i:i + seg] = (np.sign(np.sin(2 * np.pi * f * np.arange(min(seg, n - i)) / SR)) * 0.15)
        i += seg + int(SR * rng.random() * 0.15)
    return bp(y, 150, 9000)


def music_box(notes, start, track, gain=0.25, pan=0.0):
    """Detuned, slightly-wrong music box — a creepy lullaby."""
    for (t0, midi, d) in notes:
        f = 440 * 2 ** ((midi - 69) / 12) * (1 + rng.normal(0, 0.003))
        tt = t_(d + 1.5)
        x = sum(np.sin(2 * np.pi * f * k * tt) * np.exp(-tt / (0.9 / k)) / k ** 1.3 for k in (1, 2.0, 3.01, 4.2))
        x *= env_ad(len(tt), 0.002, 0.8)
        track.add(reverb(x.astype(np.float32), 2.5, 0.5, seed=9), start + t0, gain, pan)


def drone(dur, root=36.7, cutoff=400, wobble=0.1):
    t = t_(dur)
    y = np.zeros(len(t), np.float32)
    for f, g in [(root, 1.0), (root * 1.5, 0.5), (root * 2 * 1.06, 0.25), (root * 4.0 * 1.003, 0.12)]:
        for det in (-0.4, 0.4):
            ph = np.cumsum(np.full(len(t), f + det)) / SR
            y += (2 * (ph % 1) - 1) * g * 0.25
    lfo = 1 + wobble * np.sin(2 * np.pi * 0.08 * t)
    y = lp(y, cutoff) * lfo
    return fade(y.astype(np.float32), 1.5, 1.5)


def strings_cluster(dur, notes, bright=1500):
    t = t_(dur)
    y = np.zeros(len(t), np.float32)
    for m in notes:
        f = 440 * 2 ** ((m - 69) / 12)
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + rng.random() * 6)
        ph = np.cumsum(f * vib) / SR
        y += (2 * (ph % 1) - 1) * 0.1
    return fade(lp(y, bright), dur * 0.35, dur * 0.3).astype(np.float32)


# ------------------------------------------------------------------ build
def build():
    os.makedirs(os.path.join(ROOT, "public", "audio"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "src", "generated"), exist_ok=True)
    dia, sfx, mus = Track(), Track(), Track()
    lips = []

    # ---------- dialogue
    for ln in STORY["lines"]:
        prof = STORY["voices"][ln["speaker"]]
        slot = ln["end"] - ln["start"]
        a = speak(ln["tts"], prof, fit=slot - 0.15)
        env = mouth_env(a)
        style = ln.get("style", "dialogue")
        dec, wet = SPACES[ln.get("space", "room")]
        x = a
        if style == "whisper":
            x = whisperize(a) * 1.4
            x = reverb(x, 3.0, 0.8, seed=5, pre=0.03)
            for pan, dly in ((-0.8, 0.0), (0.8, 0.11)):
                dia.add(x, ln["start"] + dly, 1.0, pan)
        elif style == "aside":
            x = hp(a, 140) * 0.75 + whisperize(a) * 0.25
            dia.add(reverb(x, dec, wet * 0.6), ln["start"], 1.15)
        elif style == "glitch":
            # Vikram's twist line: pitch-dropped double + stutter + reverse-reverb swell
            dn = np.interp(np.arange(int(len(a) * 1.12)) / 1.12, np.arange(len(a)), a).astype(np.float32)
            rv = reverb(a[::-1].copy(), 2.5, 1.0, seed=8)[::-1].copy()
            dia.add(rv, ln["start"] - (len(rv) - len(a)) / SR, 0.35)
            dia.add(reverb(a, dec, wet), ln["start"], 1.0)
            dia.add(reverb(dn, 2.0, 0.6), ln["start"], 0.45)
            for k in range(3):  # stutter chops
                at = ln["start"] + 0.25 + k * 0.75
                chop = a[int(0.2 * SR):int(0.32 * SR)]
                for r in range(3): dia.add(chop * 0.5, at + r * 0.06, 0.5, (-1) ** r * 0.5)
        else:
            dia.add(reverb(hp(a, 90), dec, wet), ln["start"], 1.0)
        lips.append({"id": ln["id"], "speaker": ln["speaker"], "start": ln["start"],
                     "end": round(ln["start"] + len(a) / SR, 3), "env": env})

    # ---------- ambience beds
    sfx.add(fade(room_tone(8), 0.5, 0.5) * 0.6, 0)
    sfx.add(fade(wind(12) * 0.35 + crickets(12) * 0.6, 0.4, 0.4), 8, 0.9)
    sfx.add(fade(room_tone(12) + wind(12) * 0.12, 0.3, 0.3), 20, 0.8)
    sfx.add(fade(room_tone(16) * 0.8 + crickets(16) * 0.12 + wind(16) * 0.1, 0.3, 0.6), 32, 0.8)
    sfx.add(fade(room_tone(17) + wind(17) * 0.08, 0.3, 0.1), 48, 0.8)
    sfx.add(fade(room_tone(15) + wind(15) * 0.06, 0.05, 0.3), 65, 0.8)
    sfx.add(fade(room_tone(8) * 0.8, 0.2, 0.05), 80, 0.8)

    # ---------- hook
    for i, k in enumerate(B["hookKnocks"]):
        sfx.add(reverb(knock(1.0 - 0.1 * i), 1.2, 0.4, seed=11), k, 1.0)
    sfx.add(boom(2.5) * 0.6, 3.2, 0.9)

    # ---------- arrival
    sfx.add(fade(car_engine(5.1, idle_from=3.9, stop_at=5.0), 0.6, 0.2), 8.0, 0.8)
    sfx.add(fade(bp(noise(0.6), 800, 5000) * 0.3, 0.05, 0.3), B["carStop"] - 0.3, 0.8)  # skid
    sfx.add(bp(noise(0.08), 1000, 6000) * env_ad(int(0.08 * SR), 0.001, 0.02), B["headlightsOff"], 0.6)
    for d in B["carDoors"]:
        sfx.add(reverb(car_door(), 0.6, 0.2), d, 0.8, -0.3)
    for k in range(4):
        sfx.add(footstep("dirt", 0.6), 13.6 + k * 0.45, 0.6, -0.2)
    sfx.add(whoosh(0.5), 11.25, 0.45)
    sfx.add(whoosh(0.4), 16.3, 0.3)

    # ---------- footsteps from walk cycles
    for w in STORY["walks"]:
        t = w["from"]
        k = 0
        while t < w["to"]:
            for j in range(w["who"]):
                pan = -0.5 + j * 0.5 if w["who"] > 1 else 0
                sfx.add(reverb(footstep(w["surface"]), 1.6, 0.35, seed=3), t + j * 0.13, 0.55 if w["who"] > 1 else 0.7, pan)
            t += w["step"]; k += 1

    # ---------- warning
    sfx.add(creak(0.8, base=300) * 0.15, 24.4, 0.6)
    sfx.add(boom(2.0, 45, 25) * 0.4, 24.6, 0.6)

    # ---------- night
    for k in range(4):
        sfx.add(clock_tick(k % 2 == 1), 32.4 + k * 0.75, 0.8)
    for k in B["nightKnocks"]:
        sfx.add(reverb(knock(1.0), 1.8, 0.5, seed=12), k, 1.1, 0.25)
    sfx.add(boom(2.5, 50, 26) * 0.5, B["karanSitsUp"], 0.7)
    sfx.add(fade(bp(noise(0.5), 300, 3000) * 0.2, 0.05, 0.3), B["karanSitsUp"], 0.6)  # blanket rustle
    # Karan's frightened breathing
    for k in range(4):
        br = bp(noise(0.5), 500, 3500) * np.sin(np.pi * np.linspace(0, 1, int(0.5 * SR))) ** 2 * 0.25
        sfx.add(br.astype(np.float32), 44.35 + k * 0.62, 0.7)

    # ---------- door
    sfx.add(fade(bp(noise(0.15), 2000, 8000), 0.001, 0.05), 48.15, 0.4)  # phone torch click
    sfx.add(fade(rattle(B["silenceBeforePush"] - B["handleShakeStart"], 1.0), 0.05, 0.02),
            B["handleShakeStart"], 0.6)
    sfx.add(creak(2.6, base=480, wild=1.3), B["doorPushOpen"], 0.9, 0.1)
    sfx.add(reverb(creak(2.6, base=480, wild=1.3), 2.5, 0.7)[int(2.6 * SR):] * 0.5, B["doorPushOpen"] + 2.6, 0.6)
    sfx.add(whoosh(0.35), 58.85, 0.35)

    # ---------- reveal
    sfx.add(boom(3.5, 60, 24), B["photoFound"], 0.9)
    sfx.add(screech(3.0), B["photoFound"], 0.35)
    sfx.add(whoosh(0.3, up=True), B["yearHit"] - 0.25, 0.6)
    sfx.add(boom(2.5, 70, 30), B["yearHit"], 1.0)
    sfx.add(knock(0.4), B["yearHit"], 0.8)

    # ---------- twist
    sfx.add(creak(0.9, base=260, wild=0.6) * 0.8, B["turnAround"] + 0.1, 0.8)  # floorboard behind them
    sfx.add(boom(4.0, 40, 20), B["vikramAppears"], 1.0)
    sfx.add(screech(2.0) * 0.6, B["vikramAppears"], 0.35)
    sfx.add(glitch_fx(3.1), 83.5, 0.25)
    sfx.add(flicker_buzz(B["blackOut"] - B["torchFlickerStart"]), B["torchFlickerStart"], 0.35)
    sfx.add(boom(2.0, 80, 30), 88.1, 0.9)

    # ---------- music
    music_box([(0.0, 74, 0.6), (0.6, 77, 0.6), (1.2, 81, 0.6), (1.8, 80, 1.2), (3.6, 74, 0.6), (4.2, 77, 0.6),
               (4.8, 76, 0.6), (5.4, 73, 1.6)], 0.3, mus, 0.22, 0.2)
    mus.add(drone(8.5, 36.7, 300), 0, 0.6)
    mus.add(drone(12.5, 36.7, 380, 0.2), 8, 0.55)
    mus.add(strings_cluster(6, [50, 57, 62], 900), 13.5, 0.35)
    mus.add(drone(12.5, 38.9, 450, 0.25), 20, 0.6)
    mus.add(strings_cluster(5, [50, 51, 58], 1100), 25.5, 0.4)
    mus.add(drone(16.5, 34.6, 260, 0.1), 32, 0.55)
    mus.add(strings_cluster(6, [62, 63, 68], 1800), 40.0, 0.25)
    mus.add(drone(14.5, 36.7, 520, 0.3), 48, 0.65)
    mus.add(riser(B["silenceBeforePush"] - 55.0), 55.0, 0.5)
    # heartbeat: slow in the night, accelerating at the door, cut dead before the push
    hb, rate = 44.4, 1.0
    while hb < 47.6:
        mus.add(heartbeat(0.8), hb, 0.8); hb += 0.9
    hb, period = 50.0, 0.85
    while hb < B["silenceBeforePush"] - 0.3:
        mus.add(heartbeat(1.0), hb, 0.9); hb += period; period = max(0.36, period * 0.94)
    mus.add(drone(9.5, 34.6, 700, 0.3), B["photoFound"], 0.6)
    mus.add(strings_cluster(9, [74, 75, 80, 86], 3000), B["photoFound"], 0.35)
    mus.add(drone(B["blackOut"] - 80, 32.7, 300, 0.4), 80, 0.75)
    mus.add(strings_cluster(6.5, [62, 63, 66, 69, 70], 2200), 81.2, 0.4)
    music_box([(0.0, 74, 0.5), (0.5, 77, 0.5), (1.0, 81, 0.5), (1.5, 80, 1.5)], 88.1, mus, 0.28)

    # ---------- hard silence at the black-out, ducking under dialogue
    def apply_cut(tr, at, until, keep=0.0):
        a, b = int(at * SR), int(until * SR)
        ramp = int(0.03 * SR)
        for ch in (tr.L, tr.R):
            ch[a:a + ramp] *= np.linspace(1, keep, ramp); ch[a + ramp:b] *= keep
    apply_cut(mus, B["silenceBeforePush"], B["doorPushOpen"], 0.05)
    apply_cut(mus, B["blackOut"], 88.08)
    apply_cut(sfx, B["blackOut"] + 0.05, 88.08, 0.0)

    dl = np.abs(dia.L[:N]) + np.abs(dia.R[:N])
    sc = lp(dl.astype(np.float32), 6) * 6
    duck = 1 / (1 + np.clip(sc, 0, 4) * 0.9)
    mus.L[:N] *= duck; mus.R[:N] *= duck
    sfx.L[:N] *= (0.25 + 0.75 * duck); sfx.R[:N] *= (0.25 + 0.75 * duck)

    # ---------- normalise & export
    stems = {"dialogue": dia.stereo(), "sfx": sfx.stereo(), "music": mus.stereo()}
    targets = {"dialogue": 0.95, "sfx": 0.9, "music": 0.75}
    mix = np.zeros((N, 2), np.float32)
    for name, x in stems.items():
        x = x / (np.abs(x).max() + 1e-9) * targets[name]
        stems[name] = x
        mix += x * {"dialogue": 1.0, "sfx": 0.75, "music": 0.55}[name]
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    stems["mix"] = mix
    for name, x in stems.items():
        wav = os.path.join(HERE, ".cache", f"{name}.wav")
        sf.write(wav, x, SR)
        out = os.path.join(ROOT, "public", "audio", f"{name}.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k", out], check=True)
        print("wrote", os.path.relpath(out, ROOT))
    json.dump({"fps": FPS, "lines": lips}, open(os.path.join(ROOT, "src", "generated", "lipsync.json"), "w"))
    print("wrote src/generated/lipsync.json")


if __name__ == "__main__":
    build()
