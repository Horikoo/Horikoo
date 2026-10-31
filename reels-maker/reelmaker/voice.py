"""Step 2 - turn every sentence into narration audio (free Microsoft Edge neural voices)."""

import asyncio
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .config import CHARS_PER_MINUTE


@dataclass
class Line:
    text: str
    wav: Path
    duration: float
    scene: int  # -1 = hook, len(scenes) = ending


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？…])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def audio_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def _to_wav(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", "44100", "-ac", "1", str(dst)],
        check=True,
    )


def _edge_tts(text: str, voice: str, rate: str, pitch: str, out_mp3: Path) -> None:
    import edge_tts

    async def run():
        await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(out_mp3))

    for attempt in range(4):
        try:
            asyncio.run(run())
            if out_mp3.exists() and out_mp3.stat().st_size > 0:
                return
        except Exception as exc:  # network hiccups happen; retry with backoff
            if attempt == 3:
                raise RuntimeError(f"Text-to-speech failed for: {text[:30]}... ({exc})") from exc
        time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"Text-to-speech produced no audio for: {text[:30]}...")


def _silence(seconds: float, out_wav: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{seconds:.3f}", str(out_wav)],
        check=True,
    )


def synthesize(story: dict, workdir: Path, voice: str, lang: str, rate: str = "-8%",
               pitch: str = "-2Hz", engine: str = "edge") -> list[Line]:
    """engine='edge' uses real voices; engine='none' makes silent placeholders (for quick previews)."""
    workdir.mkdir(parents=True, exist_ok=True)
    chunks: list[tuple[str, int]] = [(s, -1) for s in split_sentences(story["hook"])]
    for i, scene in enumerate(story["scenes"]):
        chunks += [(s, i) for s in split_sentences(scene["narration"])]
    chunks += [(s, len(story["scenes"])) for s in split_sentences(story["ending"])]

    chars_per_sec = CHARS_PER_MINUTE.get(lang, 300) / 60
    lines: list[Line] = []
    for n, (text, scene) in enumerate(chunks):
        wav = workdir / f"line_{n:03d}.wav"
        if engine == "none":
            _silence(max(1.2, len(text) / chars_per_sec), wav)
        else:
            mp3 = workdir / f"line_{n:03d}.mp3"
            _edge_tts(text, voice, rate, pitch, mp3)
            _to_wav(mp3, wav)
        lines.append(Line(text, wav, audio_duration(wav), scene))
        print(f"\r  Voice: {n + 1}/{len(chunks)} sentences", end="", flush=True)
    print()
    return lines
