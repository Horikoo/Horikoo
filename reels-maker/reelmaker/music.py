"""Step 4 - background music.

Uses your own track if given (--music file.mp3, looped to length).
Otherwise composes a quiet, royalty-free ambient piano + pad piece so the video is never silent
and you never get a copyright strike.
"""

import subprocess
from pathlib import Path

import numpy as np

SR = 44100

# Chord progressions (MIDI note numbers). "sad" = Am - F - C - G, "warm" = C - G - Am - F
PROGRESSIONS = {
    "sad": [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]],
    "warm": [[48, 52, 55], [55, 59, 62], [57, 60, 64], [53, 57, 60]],
}


def _hz(note: float) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def _piano(freq: float, dur: float, vel: float) -> np.ndarray:
    t = np.arange(int(SR * dur)) / SR
    tone = sum(np.sin(2 * np.pi * freq * k * t) / k ** 1.6 for k in range(1, 6))
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 200))
    return tone * env * vel


def _pad(freqs: list[float], dur: float) -> np.ndarray:
    t = np.arange(int(SR * dur)) / SR
    sig = np.zeros_like(t)
    for f in freqs:
        for detune in (-0.6, 0.6):
            sig += np.sin(2 * np.pi * (f + detune) * t) + 0.3 * np.sin(2 * np.pi * 2 * (f + detune) * t)
    attack = np.minimum(1, t / 1.2)
    release = np.minimum(1, (dur - t) / 1.2)
    return sig * attack * release / (len(freqs) * 2)


def compose(duration: float, out_wav: Path, mood: str = "sad", seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    prog = PROGRESSIONS.get(mood, PROGRESSIONS["sad"])
    bar = 4.8  # seconds per chord (slow, ~50 BPM feel)
    total = int(SR * (duration + 4))
    mix = np.zeros(total)
    pos, i = 0.0, 0
    while pos < duration + 2:
        chord = prog[i % len(prog)]
        start = int(pos * SR)
        pad = _pad([_hz(n - 12) for n in chord], bar + 1.0) * 0.18
        end = min(total, start + len(pad))
        mix[start:end] += pad[: end - start]
        # gentle broken-chord arpeggio, sometimes skipping notes so it breathes
        steps = [0, 1, 2, 1, 2, 3, 1, 2]
        for s, idx in enumerate(steps):
            if rng.random() < 0.18:
                continue
            note = (chord + [chord[0] + 12])[idx] + 12
            n_start = int((pos + s * bar / len(steps)) * SR)
            p = _piano(_hz(note), 3.0, 0.22 if s == 0 else 0.13 + rng.random() * 0.05)
            n_end = min(total, n_start + len(p))
            mix[n_start:n_end] += p[: n_end - n_start]
        # occasional high melody note
        if rng.random() < 0.6:
            note = rng.choice(chord) + 24
            m_start = int((pos + bar * 0.5) * SR)
            p = _piano(_hz(note), 3.5, 0.10)
            m_end = min(total, m_start + len(p))
            mix[m_start:m_end] += p[: m_end - m_start]
        pos += bar
        i += 1

    mix = mix[: int(SR * duration)]
    mix /= max(1e-6, np.abs(mix).max()) / 0.8
    dry = out_wav.with_name("music_dry.wav")
    _write_wav(dry, mix)
    # reverb-like echoes + soft low-pass, fade in/out
    fade_out = max(0.0, duration - 4)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(dry), "-af",
         f"aecho=0.8:0.7:120|260|430:0.35|0.25|0.18,lowpass=f=5000,"
         f"afade=t=in:d=2,afade=t=out:st={fade_out:.2f}:d=4",
         "-ar", str(SR), "-ac", "2", str(out_wav)],
        check=True,
    )
    return out_wav


def loop_track(track: Path, duration: float, out_wav: Path) -> Path:
    fade_out = max(0.0, duration - 4)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(track),
         "-t", f"{duration:.3f}", "-af", f"afade=t=in:d=2,afade=t=out:st={fade_out:.2f}:d=4",
         "-ar", str(SR), "-ac", "2", str(out_wav)],
        check=True,
    )
    return out_wav


def _write_wav(path: Path, samples: np.ndarray) -> None:
    import wave

    data = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
