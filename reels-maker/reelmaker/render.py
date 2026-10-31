"""Step 5 - put it all together: timeline, subtitles, slow-zoom scenes, audio mix, final MP4."""

import os
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .config import FONT_DIR, FONT_FAMILY, FONTS, FPS, HEIGHT, TITLE_FONT_FILE, WIDTH
from .voice import Line

LEAD_IN = 0.6        # silence before the first word
GAP = 0.35           # pause between sentences
SCENE_GAP = 0.9      # longer pause when the picture changes
TAIL = 2.8           # music-only ending


def ensure_fonts() -> Path:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in FONTS.items():
        path = FONT_DIR / name
        if not path.exists() or path.stat().st_size < 10000:
            print(f"  Downloading font {name} ...")
            urllib.request.urlretrieve(url, path)
    return FONT_DIR


# ---------------------------------------------------------------- timeline
def build_timeline(lines: list[Line], n_scenes: int) -> tuple[list[float], list[float], float]:
    """Returns (start time of each line, start time of each visual scene, total length)."""
    starts, t = [], LEAD_IN
    prev_visual = 0
    for line in lines:
        visual = min(max(line.scene, 0), n_scenes - 1)
        if starts and visual != prev_visual:
            t += SCENE_GAP - GAP
        starts.append(t)
        t += line.duration + GAP
        prev_visual = visual
    total = t - GAP + TAIL

    scene_starts = [0.0]
    for k in range(1, n_scenes):
        first = next(i for i, ln in enumerate(lines) if min(max(ln.scene, 0), n_scenes - 1) == k)
        scene_starts.append(max(scene_starts[-1] + 1.0, starts[first] - SCENE_GAP / 2))
    return starts, scene_starts, total


def mix_narration(lines: list[Line], starts: list[float], total: float, out: Path) -> Path:
    sr = 44100
    track = np.zeros(int(total * sr) + sr, dtype=np.float32)
    for line, start in zip(lines, starts):
        with wave.open(str(line.wav)) as w:
            data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        i = int(start * sr)
        track[i:i + len(data)] += data[: len(track) - i]
    track = track[: int(total * sr)]
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
    return out


# ---------------------------------------------------------------- subtitles
def wrap(text: str, max_chars: int) -> str:
    """Break a sentence into balanced lines at spaces (ASS line break = \\N)."""
    if len(text) <= max_chars:
        return text
    words, lines, cur = text.split(" "), [], ""
    if len(words) == 1:  # no spaces (Japanese): hard wrap
        return r"\N".join(text[i:i + max_chars] for i in range(0, len(text), max_chars))
    n_lines = -(-len(text) // max_chars)
    target = len(text) / n_lines
    for word in words:
        if cur and len(cur) + 1 + len(word) > max(target, len(word)) + 2:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    lines.append(cur)
    return r"\N".join(lines)


def _ts(sec: float) -> str:
    cs = int(round(sec * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def write_ass(story: dict, lines: list[Line], starts: list[float], total: float, out: Path, lang: str) -> Path:
    max_chars = 30 if lang == "en" else 15
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FONT_FAMILY},76,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,-1,0,0,0,100,100,1,0,1,4,3,2,110,110,560,1
Style: Hook,{FONT_FAMILY},84,&H00E8F4FF,&H00FFFFFF,&H00101010,&H96000000,-1,0,0,0,100,100,2,0,1,5,4,5,90,90,0,1
Style: Title,{FONT_FAMILY},60,&H00D9ECFF,&H00FFFFFF,&H00202020,&H64000000,-1,0,0,0,100,100,3,0,1,3,2,8,80,80,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = [f"Dialogue: 1,{_ts(0.3)},{_ts(total - 0.3)},Title,,0,0,0,,{{\\fad(800,800)}}{story['title']}"]
    for i, (line, start) in enumerate(zip(lines, starts)):
        end = starts[i + 1] - 0.05 if i + 1 < len(starts) else start + line.duration + 1.5
        style = "Hook" if line.scene == -1 else "Sub"
        text = wrap(line.text.replace("{", "(").replace("}", ")"), 11 if style == "Hook" and lang != "en" else max_chars)
        events.append(f"Dialogue: 0,{_ts(start - 0.1)},{_ts(end)},{style},,0,0,0,,{{\\fad(250,200)}}{text}")
    out.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return out


# ---------------------------------------------------------------- video
def render_scene(bg: Path, duration: float, index: int, out: Path) -> Path:
    frames = max(1, round(duration * FPS))
    zoom = f"1+0.12*on/{frames}" if index % 2 == 0 else f"1.12-0.12*on/{frames}"
    # gentle drift left/right so consecutive scenes feel different
    drift = "0.25" if index % 3 == 0 else ("0.75" if index % 3 == 1 else "0.5")
    vf = (
        f"zoompan=z='{zoom}':x='(iw-iw/zoom)*{drift}':y='(ih-ih/zoom)/2':d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
        f"fade=t=in:st=0:d=0.45,fade=t=out:st={max(0, duration - 0.45):.3f}:d=0.45,format=yuv420p"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(bg),
         "-frames:v", str(frames), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
         "-r", str(FPS), str(out)],
        check=True,
    )
    return out


def render_video(backgrounds: list[Path], scene_starts: list[float], total: float, narration: Path,
                 music: Path, subs: Path, workdir: Path, out: Path, music_volume: float = 0.22) -> Path:
    bounds = scene_starts + [total]
    clips = [workdir / f"scene_{i:02d}.mp4" for i in range(len(backgrounds))]
    # Scenes are independent, so render several at once (zoompan itself is single-threaded).
    workers = max(1, min(len(clips), os.cpu_count() or 2))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [pool.submit(render_scene, bg, bounds[i + 1] - bounds[i], i, clips[i])
                for i, bg in enumerate(backgrounds)]
        for done, job in enumerate(as_completed(jobs), 1):
            job.result()
            print(f"\r  Rendering scenes: {done}/{len(clips)}", end="", flush=True)
    print()
    concat = workdir / "scenes.txt"
    concat.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))

    fonts = ensure_fonts()
    subs_arg = str(subs.resolve()).replace(":", r"\:")
    fonts_arg = str(fonts.resolve()).replace(":", r"\:")
    audio = (
        f"[1:a]aformat=channel_layouts=stereo,asplit=2[voice][key];"
        f"[2:a]volume={music_volume}[bgm];"
        # music ducks automatically while the narrator speaks
        f"[bgm][key]sidechaincompress=threshold=0.04:ratio=5:attack=80:release=900[ducked];"
        f"[voice][ducked]amix=inputs=2:normalize=0,alimiter=limit=0.95[aout]"
    )
    print("  Final encode (subtitles + audio mix)...")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(narration), "-i", str(music),
         "-filter_complex", audio + f";[0:v]ass='{subs_arg}':fontsdir='{fonts_arg}'[vout]",
         "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
        check=True,
    )
    return out


def split_video(video: Path, scene_starts: list[float], total: float, max_seconds: float) -> list[Path]:
    """Cut a long video into parts (at scene changes) for platforms with a length limit."""
    cuts, part_start, last_ok = [], 0.0, None
    for t in scene_starts[1:] + [total]:
        if t - part_start <= max_seconds:
            last_ok = t
            continue
        cut = last_ok if last_ok and last_ok > part_start else t
        if cut >= total:
            break
        cuts.append(cut)
        part_start, last_ok = cut, (t if t - cut <= max_seconds else None)
    edges = [0.0] + cuts + [total]
    parts = []
    for n in range(len(edges) - 1):
        out = video.with_name(f"{video.stem}_part{n + 1}.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{edges[n]:.3f}", "-i", str(video),
             "-t", f"{edges[n + 1] - edges[n]:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
            check=True,
        )
        parts.append(out)
    return parts


def make_cover(bg: Path, title: str, out: Path) -> Path:
    """Reels cover image (1080x1920) with the title in the middle."""
    img = Image.open(bg).convert("RGB")
    img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
    font = ImageFont.truetype(str(ensure_fonts() / TITLE_FONT_FILE), 96)
    draw = ImageDraw.Draw(img)
    wrapped = wrap(title, 9).split(r"\N")
    y = HEIGHT // 2 - len(wrapped) * 60
    for line in wrapped:
        w = draw.textlength(line, font=font)
        draw.text(((WIDTH - w) / 2, y), line, font=font, fill=(255, 245, 230),
                  stroke_width=5, stroke_fill=(15, 15, 15))
        y += 125
    img.save(out, quality=92)
    return out
