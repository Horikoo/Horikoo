"""Shared settings. Change values here to tweak the look of every video."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".cache"
FONT_DIR = CACHE_DIR / "fonts"
OUTPUT_DIR = ROOT / "output"

# Vertical 9:16 video (Instagram Reels / YouTube Shorts / TikTok)
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Korean fonts (free, SIL Open Font License) downloaded on first run.
FONTS = {
    "NanumMyeongjo-ExtraBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/nanummyeongjo/NanumMyeongjo-ExtraBold.ttf",
    "NanumMyeongjo-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/nanummyeongjo/NanumMyeongjo-Bold.ttf",
}
FONT_FAMILY = "NanumMyeongjo"
TITLE_FONT_FILE = "NanumMyeongjo-ExtraBold.ttf"

# Microsoft Edge neural voices (free). Calm, warm voices work best for stories.
VOICES = {
    "ko-female": "ko-KR-SunHiNeural",
    "ko-male": "ko-KR-InJoonNeural",
    "ja-female": "ja-JP-NanamiNeural",
    "ja-male": "ja-JP-KeitaNeural",
    "en-female": "en-US-AriaNeural",
    "en-male": "en-US-GuyNeural",
}

# Rough speaking speed used to size the script for the requested length
# (characters per minute at the default slightly-slow narration rate).
CHARS_PER_MINUTE = {"ko": 300, "ja": 330, "en": 800}

# Background colour palettes per scene "tone" (used when no stock photo is available).
PALETTES = {
    "dawn": [(20, 24, 54), (120, 80, 120), (240, 170, 140)],
    "dusk": [(18, 14, 40), (90, 40, 80), (220, 120, 90)],
    "night": [(4, 6, 20), (16, 26, 60), (60, 80, 140)],
    "rain": [(14, 20, 28), (40, 56, 72), (110, 130, 150)],
    "warm": [(40, 20, 10), (140, 80, 40), (250, 200, 130)],
    "cold": [(8, 16, 30), (40, 70, 100), (170, 200, 220)],
    "memory": [(30, 24, 20), (110, 90, 70), (220, 200, 170)],
    "hope": [(20, 40, 60), (90, 140, 170), (250, 230, 190)],
}
