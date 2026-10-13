"""Synthesize a royalty-free lo-fi background track and UI sound effects (numpy only)."""
import subprocess
import wave
from pathlib import Path
import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "public"
rng = np.random.default_rng(7)


def save(path, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc; y[i] = acc
    return y


def epiano(freq, dur):
    t = np.arange(int(dur * SR)) / SR
    env = np.exp(-t * 1.6) * (1 - np.exp(-t * 200))
    tone = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2 * freq * t) * np.exp(-t * 4)
            + 0.12 * np.sin(2 * np.pi * 3 * freq * t) * np.exp(-t * 7))
    trem = 1 + 0.08 * np.sin(2 * np.pi * 4.5 * t)
    return tone * env * trem


# ---------------- music ----------------
BPM = 88
beat = 60 / BPM
bar = 4 * beat
LENGTH = 66.0
N = int(LENGTH * SR)
L = np.zeros(N); R = np.zeros(N)

chords = [  # Fmaj9, Em7, Dm9, Cmaj7(add 9)
    [53, 57, 60, 64, 67], [52, 55, 59, 62, 67], [50, 53, 57, 60, 64], [48, 55, 59, 62, 64],
]
basses = [41, 40, 38, 36]


def add(buf, sig, start, gain=1.0):
    s = int(start * SR)
    if s >= N: return
    e = min(N, s + len(sig)); buf[s:e] += sig[: e - s] * gain


nbars = int(LENGTH / bar) + 1
for b in range(nbars):
    t0 = b * bar
    ch = chords[b % 4]
    for k, n in enumerate(ch):  # slightly strummed chord, twice per bar
        for hit in (0, 2.5):
            sig = epiano(midi(n), bar)
            pan = 0.35 + 0.3 * (k / len(ch))
            add(L, sig, t0 + hit * beat + k * 0.012, 0.11 * (1 - pan) * 2)
            add(R, sig, t0 + hit * beat + k * 0.012, 0.11 * pan * 2)
    # sub bass
    t = np.arange(int(bar * SR)) / SR
    bs = np.sin(2 * np.pi * midi(basses[b % 4]) * t) * np.exp(-t * 0.9) * (1 - np.exp(-t * 80))
    add(L, bs, t0, 0.32); add(R, bs, t0, 0.32)
    intro = b < 1  # drums enter after the first bar
    if intro: continue
    for q in range(4):
        tq = t0 + q * beat
        if q in (0, 2) or (q == 3 and b % 2):  # kick
            tk = np.arange(int(0.35 * SR)) / SR
            f = 50 + 90 * np.exp(-tk * 30)
            kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tk * 9)
            add(L, kick, tq + (0.5 * beat if q == 3 else 0), 0.55); add(R, kick, tq + (0.5 * beat if q == 3 else 0), 0.55)
        if q in (1, 3):  # soft snare / clap
            ts = np.arange(int(0.25 * SR)) / SR
            sn = rng.standard_normal(len(ts)) * np.exp(-ts * 22)
            sn = sn - lowpass(sn, 900)
            add(L, sn, tq, 0.16); add(R, sn, tq + 0.004, 0.16)
        for h in (0, 0.5):  # swung hats
            th = np.arange(int(0.06 * SR)) / SR
            hat = rng.standard_normal(len(th)) * np.exp(-th * 90)
            hat = hat - lowpass(hat, 6000)
            add(R, hat, tq + h * beat * (1.12 if h else 1), 0.07); add(L, hat, tq + h * beat * (1.12 if h else 1), 0.05)

# vinyl crackle
crackle = (rng.random(N) > 0.9993) * rng.standard_normal(N) * 0.25
L += crackle; R += crackle * 0.8
mix = np.stack([lowpass(L, 7000), lowpass(R, 7000)], axis=1)
fade = np.ones(N); fl = int(2.5 * SR); fade[-fl:] = np.linspace(1, 0, fl); fade[: int(0.4 * SR)] = np.linspace(0, 1, int(0.4 * SR))
save(OUT / "music.wav", mix * fade[:, None])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "music.wav"), "-b:a", "192k", str(OUT / "music.mp3")], check=True)
(OUT / "music.wav").unlink()

# ---------------- sfx ----------------
t = np.arange(int(0.6 * SR)) / SR
noise = rng.standard_normal(len(t))
sweep = np.zeros_like(noise); acc = 0.0
for i, v in enumerate(noise):  # sweeping low-pass = whoosh
    c = 300 + 5000 * np.sin(np.pi * t[i] / t[-1]) ** 2
    a = np.exp(-2 * np.pi * c / SR); acc = (1 - a) * v + a * acc; sweep[i] = acc
save(OUT / "sfx" / "whoosh.wav", sweep * np.sin(np.pi * t / t[-1]) ** 1.5)

t = np.arange(int(0.9 * SR)) / SR
ding = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) * g for f, d, g in [(1318.5, 4, 1), (1975.5, 6, 0.5), (2637, 9, 0.25)])
ding2 = np.concatenate([np.zeros(int(0.09 * SR)), sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) * g for f, d, g in [(1760, 4, 1), (2637, 7, 0.4)])])[: len(t)]
save(OUT / "sfx" / "success.wav", (ding + ding2) * (1 - np.exp(-t * 400)))

t = np.arange(int(0.35 * SR)) / SR
coin = (np.sin(2 * np.pi * 1975.5 * t) * (t < 0.07) + np.sin(2 * np.pi * 2637 * t) * (t >= 0.07)) * np.exp(-t * 9)
save(OUT / "sfx" / "coin.wav", coin)

t = np.arange(int(0.12 * SR)) / SR
pop = np.sin(2 * np.pi * (900 - 600 * t / t[-1]) * t) * np.exp(-t * 40)
save(OUT / "sfx" / "pop.wav", pop)
print("ok")
