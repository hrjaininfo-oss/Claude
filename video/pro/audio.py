#!/usr/bin/env python3
"""Original score + sound design for the pro cut, synthesised with numpy.
96 BPM, A minor (Am-F-C-G), cut points land on bar lines (2.5 s).
Writes build/music.wav and build/sfx.wav; mix.sh masters them."""
import numpy as np, wave, os, json

SR = 48000
DUR = 64.0
BPM = 96; BEAT = 60 / BPM; BAR = 4 * BEAT
N = int(DUR * SR)
rng = np.random.default_rng(7)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
os.makedirs(OUT, exist_ok=True)

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def buf(): return np.zeros((2, N))
def place(dst, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    sig = sig[: N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    dst[0, i:i + len(sig)] += sig * gain * l * 1.414
    dst[1, i:i + len(sig)] += sig * gain * r * 1.414
def tt(d): return np.arange(int(d * SR)) / SR

def noise_band(d, fc, width=0.6, amp=None):
    """STFT-shaped noise; fc(t) and amp(t) are functions of time in seconds."""
    n, hop = 2048, 512
    L = int(d * SR) + n
    out = np.zeros(L); win = np.hanning(n)
    f = np.fft.rfftfreq(n, 1 / SR); f[0] = 1
    for s in range(0, L - n, hop):
        tc = (s + n / 2) / SR
        g = np.exp(-0.5 * (np.log2(f / max(fc(tc), 20)) / width) ** 2)
        spec = (rng.standard_normal(len(f)) + 1j * rng.standard_normal(len(f))) * g
        out[s:s + n] += np.fft.irfft(spec, n) * win
    out = out[: int(d * SR)]
    out /= np.max(np.abs(out)) + 1e-9
    if amp: out *= amp(tt(d))
    return out

def env_adsr(d, a, r):
    t = tt(d); e = np.minimum(1, t / max(a, 1e-4)); e *= np.clip((d - t) / max(r, 1e-4), 0, 1); return e

# ---------------------------------------------------------------- music
CHORDS = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]  # Am F C G (root, triad)
def section(t):
    if t < 5: return "intro"
    if t < 27.5: return "full"
    if t < 40: return "break"
    if t < 57.5: return "full2"
    return "outro"

music = buf()
bars = int(np.ceil(62.5 / BAR))
for b in range(bars):
    t0 = b * BAR; root, triad = CHORDS[b % 4]; sec = section(t0 + 0.01)
    if sec == "outro":
        root, triad = CHORDS[0]
    # pad: detuned soft-saw stack, one chord per bar with overlap
    d = BAR + 0.8 if sec != "outro" else 6.5
    t = tt(d); pad = np.zeros((2, len(t)))
    for m in triad + [triad[0] + 12, root - 12]:
        for ch, det in ((0, -0.07), (1, 0.07)):
            f = hz(m) * 2 ** (det / 12)
            v = sum(np.sin(2 * np.pi * f * k * t + k) / k ** 1.7 for k in range(1, 7))
            pad[ch] += v
    e = env_adsr(d, 0.5 if sec != "intro" else 1.2, 0.8 if sec != "outro" else 4.0)
    lvl = {"intro": .05, "full": .055, "break": .065, "full2": .06, "outro": .07}[sec]
    i = int(t0 * SR); n = min(len(t), N - i)
    music[:, i:i + n] += (pad * e * lvl)[:, :n]

    # plucked arpeggio (8ths) except intro
    if sec in ("full", "break", "full2"):
        pat = [0, 1, 2, 3, 2, 1, 2, 3]
        notes = triad + [triad[0] + 12]
        for k in range(8):
            m = notes[pat[k]] + 12
            d2 = 0.6; t2 = tt(d2); f = hz(m)
            s = (np.sin(2 * np.pi * f * t2) + .3 * np.sin(4 * np.pi * f * t2) + .1 * np.sin(6 * np.pi * f * t2)) * np.exp(-t2 / 0.16)
            s *= np.minimum(1, t2 / 0.003)
            g = .09 if sec != "break" else .075
            place(music, s, t0 + k * BEAT / 2, g * (1 if k % 2 == 0 else .7), pan=(-.35 if k % 2 else .35))

    # bass + drums in full sections
    if sec in ("full", "full2"):
        for k in range(8):
            d3 = BEAT / 2 * .95; t3 = tt(d3); f = hz(root - 24 + (12 if k in (3, 7) else 0))
            s = np.tanh(1.6 * (np.sin(2 * np.pi * f * t3) + .25 * np.sin(4 * np.pi * f * t3))) * np.exp(-t3 / 0.22) * np.minimum(1, t3 / .004)
            place(music, s, t0 + k * BEAT / 2, .2)
        for k in range(4):
            tb = t0 + k * BEAT
            t4 = tt(.45); ph = 2 * np.pi * np.cumsum(45 + 95 * np.exp(-t4 * 32)) / SR
            kick = np.sin(ph) * np.exp(-t4 * 7.5); kick[:60] += np.linspace(.6, 0, 60)
            place(music, kick, tb, .55)
            hat = np.diff(np.diff(rng.standard_normal(int(.06 * SR) + 2))) * np.exp(-tt(.06) / .012)
            place(music, hat / 4, tb + BEAT / 2, .22, pan=.3)
            if k in (1, 3):
                t5 = tt(.25); sn = noise_band(.25, lambda x: 1800, .9) * np.exp(-t5 / .07) + .4 * np.sin(2 * np.pi * 190 * t5) * np.exp(-t5 / .05)
                place(music, sn, tb, .12, pan=-.1)
    if sec == "break":  # soft pulse to keep time under the demo
        for k in range(4):
            t6 = tt(.5); f = hz(root - 24)
            place(music, np.sin(2 * np.pi * f * t6) * np.exp(-t6 / .35) * np.minimum(1, t6 / .01), t0 + k * BEAT, .14)

# sidechain-style pump on full sections (duck pad/arp on each beat)
tg = np.arange(N) / SR
pump = np.ones(N)
for b in range(bars):
    if section(b * BAR + .01) in ("full", "full2"):
        for k in range(4):
            tb = b * BAR + k * BEAT; i = int(tb * SR); n = int(BEAT * SR)
            pump[i:i + n] = np.minimum(pump[i:i + n], 1 - .35 * np.exp(-np.arange(n) / SR / .11))
music *= pump
# master fade
music *= np.clip((62.6 - tg) / 2.2, 0, 1)
music *= np.clip(tg / .3, 0, 1)

# ---------------------------------------------------------------- sound design
sfx = buf()
def thud(t, g=1.0):
    d = .5; x = tt(d); s = np.sin(2 * np.pi * np.cumsum(55 + 60 * np.exp(-x * 25)) / SR) * np.exp(-x * 6)
    s += .25 * noise_band(d, lambda q: 900, .8) * np.exp(-x * 30)
    place(sfx, s, t, .5 * g)
def pop(t, g=1.0, pan=0.0, f0=1300):
    d = .12; x = tt(d); s = np.sin(2 * np.pi * np.cumsum(f0 * np.exp(-x * 9)) / SR) * np.exp(-x * 40) * np.minimum(1, x / .002)
    place(sfx, s, t, .16 * g, pan)
def whoosh(tc, d=.8, g=1.0, up=False):
    def fc(q):
        p = min(max(q / d, 0), 1)
        return 300 * 2 ** (4.2 * p) if up else 350 + 2600 * max(np.sin(np.pi * p), 0) ** 1.5
    a = lambda q: np.sin(np.pi * np.clip(q / d, 0, 1)) ** 2
    place(sfx, noise_band(d, fc, .55, a), tc - d * .55, .32 * g, pan=0)
def impact(t, g=1.0):
    thud(t, 1.6 * g)
    d = 2.2; x = tt(d)
    place(sfx, noise_band(d, lambda q: 500 * np.exp(-q * 1.5) + 120, 1.2) * np.exp(-x * 2.2), t, .22 * g)
    place(sfx, np.sin(2 * np.pi * np.cumsum(70 * np.exp(-x * .8) + 25) / SR) * np.exp(-x * 1.8), t, .35 * g)

# cold open hits on the words (beats 1-4)
for k in range(1, 5): thud(k * BEAT, .8 + .1 * k)
# riser into the drop
d = 1.9; place(sfx, noise_band(d, lambda q: 300 * 2 ** (4.5 * q / d), .5, lambda q: (q / d) ** 2.2), 5.0 - d, .3)
x = tt(d); place(sfx, np.sin(2 * np.pi * np.cumsum(180 * 2 ** (2 * x / d)) / SR) * (x / d) ** 3, 5.0 - d, .06)
impact(5.0)
for tc in (10.0, 17.5, 27.5, 40.0, 47.5): whoosh(tc)
whoosh(52.5, 1.0, .5)
for i in range(3): pop(13.1 + i * BEAT / 2, 1, .4)
for i in range(5): pop(18.75 + i * BEAT / 2, 1, -.4 + .2 * i, 1100 + 80 * i)
for i in range(5): pop(22.5 + i * BEAT, .45, -.4 + .2 * i, 1700)
# typing
UTEXT = "Summarise this GST show-cause notice and list each allegation with the documents I need."
for k, ch in enumerate(UTEXT):
    tk = 28.45 + k * (2.45 / len(UTEXT)) + rng.uniform(-.008, .008)
    dk = .03; xk = tt(dk)
    c = noise_band(dk, lambda q: 3500 if ch != " " else 1400, .7) * np.exp(-xk / .006)
    place(sfx, c, tk, (.05 if ch != " " else .07) * rng.uniform(.6, 1), pan=rng.uniform(-.2, .2))
whoosh(31.05, .35, .5, up=True); pop(31.1, .8, 0, 900)
for i in range(4): pop(40.85 + i * .16, .8, -.3 + .2 * i, 1000)
pop(43.0 + .12, 1.3, .3, 1600)
for i in range(3): pop(48.4 + i * BEAT, 1, -.4 + .4 * i, 1200)
for i in range(3): pop(52.8 + i * BEAT, 1, -.4 + .4 * i, 1000 + 100 * i)
impact(57.5, .8)
x = tt(3.5); bell = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * (1.2 + j)) / (j + 1) for j, f in enumerate((880, 1318.5, 1760, 2637)))
place(sfx, bell, 57.6, .05)
sfx *= np.clip((62.8 - tg) / 1.5, 0, 1)

def write(path, a):
    a = a / max(1e-9, np.max(np.abs(a))) * 0.9
    pcm = (np.clip(a.T, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
peak = max(np.max(np.abs(music)), np.max(np.abs(sfx)))
write(os.path.join(OUT, "music.wav"), music / peak)
write(os.path.join(OUT, "sfx.wav"), sfx / peak)
json.dump({"music_peak": float(np.max(np.abs(music))), "sfx_peak": float(np.max(np.abs(sfx)))}, open(os.path.join(OUT, "levels.json"), "w"))
print("audio written")
