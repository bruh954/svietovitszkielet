"""Efekty dźwiękowe generowane w kodzie (bez plików).

"""
import math
import os
import struct
import wave


RATE = 22050

# Pitch contours on the 1-5 Chao scale, as (time 0-1, level) points.
CONTOURS = {
    1: [(0, 5), (1, 5)],
    2: [(0, 3), (1, 5)],
    3: [(0, 2), (0.5, 1), (1, 4)],
    4: [(0, 5), (1, 1)],
}


def contour_level(tone, x):
    pts = CONTOURS[tone]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            f = (x - x0) / (x1 - x0)
            f = f * f * (3 - 2 * f)  # smooth
            return y0 + (y1 - y0) * f
    return pts[-1][1]


def _write(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 30000)) for s in samples))


def _env(i, n, attack=0.02, release=0.08):
    t = i / RATE
    total = n / RATE
    a = min(1.0, t / attack) if attack else 1
    r = min(1.0, (total - t) / release) if release else 1
    return max(0.0, min(a, r))


def _hum(tone):
    """A voice-like hum that follows the tone's pitch contour."""
    dur = 0.65 if tone == 3 else 0.5
    n = int(dur * RATE)
    out, phase = [], 0.0
    for i in range(n):
        level = contour_level(tone, i / n)
        freq = 130 * 2 ** ((level - 1) / 4 * 0.9)  # level 1..5 spans about 11 semitones
        phase += 2 * math.pi * freq / RATE
        s = sum(math.sin(phase * h) / h ** 1.3 for h in range(1, 7))
        out.append(0.45 * s * _env(i, n, 0.03, 0.12))
    return out


def _notes(notes, wave_kind="sine", vol=0.35):
    out = []
    for freq, dur in notes:
        n = int(dur * RATE)
        for i in range(n):
            t = i / RATE
            p = 2 * math.pi * freq * t
            if wave_kind == "buzz":
                s = 0.6 * math.sin(p) + 0.3 * math.sin(2 * p) + 0.2 * math.sin(3 * p)
            else:
                s = math.sin(p) + 0.3 * math.sin(2 * p) * math.exp(-t * 8)
            out.append(vol * s * _env(i, n, 0.005, min(0.08, dur / 2)))
    return out


def generate_sounds(folder):
    """Create the sound files once. Returns {name: path}."""
    os.makedirs(folder, exist_ok=True)
    makers = {
        "correct": lambda: _notes([(784, 0.09), (1175, 0.22)]),
        "wrong": lambda: _notes([(220, 0.12), (185, 0.25)], "buzz", 0.3),
        "complete": lambda: _notes([(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.35)]),
        "streak": lambda: _notes([(659, 0.08), (880, 0.08), (1319, 0.3)]),
        "tap": lambda: _notes([(1200, 0.03)], vol=0.15),
    }
    for t in (1, 2, 3, 4):
        makers["tone%d" % t] = (lambda t=t: _hum(t))
    paths = {}
    for name, make in makers.items():
        p = os.path.join(folder, name + "_v2.wav")
        if not os.path.exists(p):
            _write(p, make())
        paths[name] = p
    return paths
