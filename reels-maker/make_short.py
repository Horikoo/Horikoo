#!/usr/bin/env python3
"""
Make ONE 15-second touching true-story YouTube Short and (optionally) upload it.

  # make + upload (needs ANTHROPIC_API_KEY and the YT_* secrets)
  python make_short.py

  # make only, no upload (check the video first)
  python make_short.py --no-upload

  # test without any API key, using a ready-made 15-second script
  python make_short.py --story samples/short_hachiko_ko.json --no-upload

Every story used is remembered in shorts_history.json so the channel never repeats a story.
"""

import argparse
import json
import random
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from make_reel import slug
from reelmaker import music, render, story as story_mod, visuals, voice, youtube
from reelmaker.config import OUTPUT_DIR, ROOT, VOICES

HISTORY = ROOT / "shorts_history.json"
MAX_SECONDS = 17.0   # aim for ~15s; if the voice runs long we speed it up a little
RATES = ["+0%", "+10%", "+20%", "+28%"]
AI_NOTE = {
    "ko": "※ 실제 있었던 이야기를 바탕으로 AI 내레이션으로 제작했습니다.",
    "ja": "※ 実話をもとに、AIナレーションで制作しています。",
    "en": "※ Based on a true story, narrated with an AI voice.",
}


def load_history() -> list[dict]:
    if HISTORY.exists():
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    return []


def main() -> int:
    p = argparse.ArgumentParser(description="Make a 15-second true-story YouTube Short.")
    p.add_argument("--story", type=Path, help="Use an existing short story JSON instead of asking Claude")
    p.add_argument("--topic", default="", help="Optional: force a story type (otherwise rotates automatically)")
    p.add_argument("--lang", default="ko", choices=["ko", "ja", "en"])
    p.add_argument("--voice", default=None, help=f"Voice preset ({', '.join(VOICES)})")
    p.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    p.add_argument("--no-upload", action="store_true", help="Only make the video")
    p.add_argument("--tts", default="edge", choices=["edge", "none"])
    p.add_argument("--out", type=Path, default=OUTPUT_DIR)
    args = p.parse_args()

    voice_name = VOICES.get(args.voice or f"{args.lang}-female", args.voice)
    history = load_history()
    render.use_short_pace()

    print("1/6  Story script")
    if args.story:
        data = story_mod.load_story(args.story)
    else:
        category = story_mod.SHORT_CATEGORIES[len(history) % len(story_mod.SHORT_CATEGORIES)]
        data = story_mod.generate_short(args.lang, [h["story_id"] for h in history], category, args.topic)
    data = story_mod.validate_story(data)
    data.setdefault("story_id", data["title"])
    data.setdefault("youtube_title", data["title"])
    if any(h["story_id"].lower() == data["story_id"].lower() for h in history) and not args.story:
        print(f"  Warning: '{data['story_id']}' was used before.")
    print(f"  Story: {data['story_id']}\n  Title: {data['youtube_title']}")

    folder = args.out / f"{datetime.now():%Y%m%d_%H%M}_{slug(data['title'])}"
    work = folder / "_work"
    work.mkdir(parents=True, exist_ok=True)
    (folder / "story.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("2/6  Narration")
    for rate in RATES:
        lines = voice.synthesize(data, work / "voice", voice_name, args.lang, rate=rate, engine=args.tts)
        starts, scene_starts, total = render.build_timeline(lines, len(data["scenes"]))
        print(f"  Speed {rate}: {total:.1f} seconds")
        if total <= MAX_SECONDS or args.tts == "none":
            break

    print("3/6  Backgrounds")
    bgs = visuals.make_backgrounds(data, work / "bg")

    print("4/6  Music")
    narration = render.mix_narration(lines, starts, total, work / "narration.wav")
    bgm = music.compose(total, work / "music.wav", mood=random.choice(["sad", "warm"]),
                        seed=random.randint(1, 10_000))

    print("5/6  Video")
    subs = render.write_ass(data, lines, starts, total, work / "subs.ass", args.lang)
    final = render.render_video(bgs, scene_starts, total, narration, bgm, subs, work,
                                folder / "short.mp4", music_volume=0.25)

    tags = [re.sub(r"\s+", "", t.lstrip("#")) for t in data.get("hashtags", [])]
    hashtag_line = " ".join(f"#{t}" for t in ["shorts"] + tags)
    description = f"{data['caption']}\n\n"
    if data.get("sources"):
        description += "📚 출처 / Sources:\n" + "\n".join(f"- {s}" for s in data["sources"]) + "\n\n"
    description += f"{AI_NOTE.get(args.lang, AI_NOTE['en'])}\n\n{hashtag_line}\n"
    title = f"{data['youtube_title']} #shorts"
    (folder / "youtube.txt").write_text(f"{title}\n\n{description}", encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    print(f"  {final}  ({total:.1f}s)")

    print("6/6  YouTube upload")
    url = ""
    if args.no_upload:
        print("  Skipped (--no-upload).")
    elif not youtube.credentials_available():
        print("  Skipped: YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN are not set.")
    else:
        url = youtube.upload(final, title, description, ["shorts"] + tags, args.lang, args.privacy)
        print(f"  Uploaded: {url}")

    if not args.story:
        history.append({
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "story_id": data["story_id"],
            "title": data["youtube_title"],
            "url": url,
            "sources": data.get("sources", []),
        })
        HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
