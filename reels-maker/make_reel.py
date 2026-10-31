#!/usr/bin/env python3
"""
Automatic story reel maker.

Examples
--------
  # Claude writes a ~5 minute sad & beautiful true story, then the video is built automatically
  python make_reel.py --topic "슬프고 아름다운 실화" --minutes 5

  # Use the included sample story (no Claude API key needed)
  python make_reel.py --story samples/hachiko_ko.json

  # Also cut into parts of max 90 seconds for Instagram Reels
  python make_reel.py --topic "감동적인 가족 실화" --minutes 5 --split 90

Output (in output/<date>_<title>/):
  reel.mp4        the finished vertical video (1080x1920)
  reel_partN.mp4  parts, if --split was used
  cover.jpg       cover/thumbnail image
  caption.txt     ready-to-paste caption + hashtags + sources
  story.json      the script (edit it and re-run with --story to rebuild)
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from reelmaker import music, render, story as story_mod, visuals, voice
from reelmaker.config import OUTPUT_DIR, VOICES


def slug(text: str) -> str:
    s = re.sub(r"[^\w가-힣ぁ-んァ-ン一-龥]+", "_", text).strip("_")
    return s[:40] or "reel"


def main() -> int:
    p = argparse.ArgumentParser(description="Make a narrated, subtitled story reel automatically.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--topic", help='What the story should be about, e.g. "슬프고 아름다운 실화"')
    src.add_argument("--story", type=Path, help="Use an existing story JSON instead of asking Claude")
    p.add_argument("--minutes", type=float, default=5, help="Target length in minutes (default 5)")
    p.add_argument("--lang", default="ko", choices=["ko", "ja", "en"], help="Narration language")
    p.add_argument("--voice", default=None,
                   help=f"Voice preset ({', '.join(VOICES)}) or any Edge voice name. Default: <lang>-female")
    p.add_argument("--rate", default="-8%", help="Speaking speed, e.g. -15%% (slower) or +5%% (faster)")
    p.add_argument("--images", type=Path, help="Folder of your own photos to use as backgrounds")
    p.add_argument("--music", type=Path, help="Your own background music file (mp3/wav)")
    p.add_argument("--music-mood", default="sad", choices=["sad", "warm"], help="Mood of generated music")
    p.add_argument("--music-volume", type=float, default=0.22, help="Background music volume (0-1)")
    p.add_argument("--split", type=float, default=0, help="Also cut into parts of at most N seconds")
    p.add_argument("--tts", default="edge", choices=["edge", "none"],
                   help="'none' = silent preview (no internet needed) to check the visuals quickly")
    p.add_argument("--out", type=Path, default=OUTPUT_DIR, help="Output folder")
    args = p.parse_args()

    voice_name = VOICES.get(args.voice or f"{args.lang}-female", args.voice)

    print("1/5  Story script")
    if args.story:
        data = story_mod.load_story(args.story)
    else:
        data = story_mod.generate_story(args.topic, args.minutes, args.lang)
    data = story_mod.validate_story(data)
    print(f"  Title: {data['title']}  ({len(data['scenes'])} scenes)")

    folder = args.out / f"{datetime.now():%Y%m%d_%H%M}_{slug(data['title'])}"
    work = folder / "_work"
    work.mkdir(parents=True, exist_ok=True)
    (folder / "story.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"2/5  Narration ({voice_name if args.tts == 'edge' else 'silent preview'})")
    lines = voice.synthesize(data, work / "voice", voice_name, args.lang, rate=args.rate, engine=args.tts)
    starts, scene_starts, total = render.build_timeline(lines, len(data["scenes"]))
    print(f"  Video length: {int(total // 60)}m {int(total % 60)}s")

    print("3/5  Backgrounds")
    bgs = visuals.make_backgrounds(data, work / "bg", args.images)

    print("4/5  Music")
    narration = render.mix_narration(lines, starts, total, work / "narration.wav")
    if args.music:
        bgm = music.loop_track(args.music, total, work / "music.wav")
    else:
        bgm = music.compose(total, work / "music.wav", mood=args.music_mood)

    print("5/5  Video")
    subs = render.write_ass(data, lines, starts, total, work / "subs.ass", args.lang)
    final = render.render_video(bgs, scene_starts, total, narration, bgm, subs, work,
                                folder / "reel.mp4", music_volume=args.music_volume)
    render.make_cover(bgs[0], data["title"], folder / "cover.jpg")

    parts = []
    if args.split and total > args.split:
        parts = render.split_video(final, scene_starts, total, args.split)

    tags = " ".join("#" + t.lstrip("#").replace(" ", "") for t in data.get("hashtags", []))
    caption = f"{data['caption']}\n\n{tags}\n"
    if data.get("sources"):
        caption += "\n출처 / Sources:\n" + "\n".join(f"- {s}" for s in data["sources"]) + "\n"
    (folder / "caption.txt").write_text(caption, encoding="utf-8")

    shutil.rmtree(work, ignore_errors=True)
    print(f"\nDone!  {final}")
    for part in parts:
        print(f"       {part}")
    print(f"       {folder / 'cover.jpg'}\n       {folder / 'caption.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
