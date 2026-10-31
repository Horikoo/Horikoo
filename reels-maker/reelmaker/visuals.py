"""Step 3 - one background picture per scene.

Priority:
  1. Your own photos (--images folder), used in file-name order
  2. Free stock photos from Pexels (if PEXELS_API_KEY is set)
  3. Generated cinematic backgrounds (soft gradients + bokeh light), no internet needed
"""

import json
import os
import random
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from .config import HEIGHT, PALETTES, WIDTH

# Render backgrounds bigger than the video so the slow zoom stays sharp.
BG_SCALE = 1.5
BG_W, BG_H = int(WIDTH * BG_SCALE), int(HEIGHT * BG_SCALE)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Resize + centre-crop to exactly w x h (like CSS object-fit: cover)."""
    img = img.convert("RGB")
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def _vignette(img: Image.Image, strength: float = 0.55) -> Image.Image:
    w, h = img.size
    y, x = np.ogrid[-1:1:complex(0, h), -1:1:complex(0, w)]
    mask = 1 - strength * np.clip((x ** 2 + y ** 2) / 1.6, 0, 1)
    arr = np.asarray(img).astype(np.float32) * mask[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def _grade(img: Image.Image, tone: str) -> Image.Image:
    """Cinematic look: a little darker, softer colours, tinted by the scene tone, darker bottom for subtitles."""
    img = ImageEnhance.Color(img).enhance(0.75)
    img = ImageEnhance.Brightness(img).enhance(0.72)
    tint = Image.new("RGB", img.size, PALETTES.get(tone, PALETTES["dusk"])[1])
    img = Image.blend(img, tint, 0.18)
    arr = np.asarray(img).astype(np.float32)
    ramp = np.linspace(1.0, 0.55, img.height)[:, None, None]
    ramp[: int(img.height * 0.55)] = 1.0
    return _vignette(Image.fromarray((arr * ramp).clip(0, 255).astype(np.uint8)))


def generated_background(tone: str, seed: int) -> Image.Image:
    rng = random.Random(seed)
    c1, c2, c3 = PALETTES.get(tone, PALETTES["dusk"])
    t = np.linspace(0, 1, BG_H)[:, None]
    top = np.array(c1, np.float32)
    mid = np.array(c2, np.float32)
    bot = np.array(c3, np.float32)
    # sky-like gradient: dark top -> mid -> bright horizon around 70% height -> darker ground
    up = (t / 0.7).clip(0, 1)[..., None]
    down = ((t - 0.7) / 0.3).clip(0, 1)[..., None]
    col = np.where(t[..., None] < 0.7, top * (1 - up) + mid * up, mid * (1 - down) + top * down)
    glow = np.exp(-((t - 0.68) ** 2) / 0.004)[..., None]
    col = col + (bot - col) * glow * 0.8
    arr = np.repeat(col, BG_W, axis=1)
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))

    # soft bokeh lights
    layer = Image.new("RGB", img.size, (0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for _ in range(rng.randint(18, 32)):
        r = rng.randint(20, 140)
        x, y = rng.randint(0, BG_W), rng.randint(0, int(BG_H * 0.85))
        b = rng.randint(40, 110)
        tint = tuple(min(255, int(v * 0.5 + b)) for v in c3)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=tint)
    layer = layer.filter(ImageFilter.GaussianBlur(28))
    img = Image.fromarray(
        np.clip(np.asarray(img, np.float32) + np.asarray(layer, np.float32) * 0.55, 0, 255).astype(np.uint8)
    )

    # film grain
    noise = np.random.default_rng(seed).normal(0, 4, (BG_H, BG_W, 1))
    img = Image.fromarray(np.clip(np.asarray(img, np.float32) + noise, 0, 255).astype(np.uint8))
    return _vignette(img, 0.6)


def _pexels_search(query: str, key: str) -> list[str]:
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": query, "orientation": "portrait", "per_page": 15}
    )
    req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": "reels-maker"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    return [p["src"].get("large2x") or p["src"]["original"] for p in data.get("photos", [])]


def _download(url: str, dst: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "reels-maker"})
    with urllib.request.urlopen(req, timeout=60) as r:
        dst.write_bytes(r.read())


def make_backgrounds(story: dict, workdir: Path, images_dir: Path | None = None) -> list[Path]:
    workdir.mkdir(parents=True, exist_ok=True)
    scenes = story["scenes"]
    own = []
    if images_dir:
        own = sorted(p for p in Path(images_dir).iterdir() if p.suffix.lower() in IMAGE_EXTS)
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    used: set[str] = set()
    paths = []

    for i, scene in enumerate(scenes):
        out = workdir / f"bg_{i:02d}.jpg"
        img = None
        source = "generated"
        if own:
            img = Image.open(own[i % len(own)])
            source = f"your photo {own[i % len(own)].name}"
        elif key:
            try:
                for url in _pexels_search(scene["image_keywords"], key):
                    if url not in used:
                        used.add(url)
                        raw = workdir / f"raw_{i:02d}.jpg"
                        _download(url, raw)
                        img = Image.open(raw)
                        source = "Pexels"
                        break
            except Exception as exc:
                print(f"  (Pexels search failed for scene {i + 1}: {exc}; using generated background)")
        if img is not None:
            img = _grade(_cover(img, BG_W, BG_H), scene["tone"])
        else:
            img = generated_background(scene["tone"], seed=i * 7919 + len(scene["narration"]))
        img.save(out, quality=92)
        paths.append(out)
        print(f"  Scene {i + 1}/{len(scenes)} background: {source}")
    return paths
