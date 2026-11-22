"""Step 1 - write the story script with Claude (or load one from a JSON file)."""

import json
from pathlib import Path

from .config import CHARS_PER_MINUTE, PALETTES

MODEL = "claude-opus-5-5"

TONES = list(PALETTES.keys())

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Short on-screen title, max ~16 characters"},
        "hook": {"type": "string", "description": "First spoken line (1 sentence) that makes viewers stay"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string"},
                    "image_keywords": {"type": "string", "description": "2-5 English words for a stock photo search"},
                    "tone": {"type": "string", "enum": TONES},
                },
                "required": ["narration", "image_keywords", "tone"],
                "additionalProperties": False,
            },
        },
        "ending": {"type": "string", "description": "Closing line + soft call to follow/save"},
        "caption": {"type": "string", "description": "Post caption for Instagram, 2-4 lines"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "sources": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Where the true story is documented (books, news outlets, museums, etc.)",
        },
    },
    "required": ["title", "hook", "scenes", "ending", "caption", "hashtags", "sources"],
    "additionalProperties": False,
}

LANG_NAMES = {"ko": "Korean", "ja": "Japanese", "en": "English"}

SYSTEM = """You write narration scripts for short vertical story videos (Instagram Reels, YouTube Shorts).
The style: slow, emotional, cinematic voice-over, like a late-night radio storyteller.

Rules for "true story" requests:
- Only use stories that are genuinely real AND widely documented (well-known news stories, historical
  events, published biographies). Never invent a story and call it true.
- Keep the core facts (names, places, years, what happened) accurate. You may add atmosphere and feeling,
  but do not invent specific facts, quotes, or numbers. If a detail is uncertain, leave it out.
- List where the story is documented in "sources".
- Avoid stories centred on graphic violence, suicide, or abuse of children; prefer love, loyalty,
  sacrifice, farewell, kindness of strangers, reunions.

Writing rules:
- Short sentences (each under ~45 characters in Korean/Japanese, ~18 words in English) so the subtitles fit.
- Every scene is 2-5 sentences. Each scene has an English stock-photo search phrase that matches the mood
  without showing identifiable real people's faces (e.g. "empty train station dusk", "old letter hands").
- Open with a hook that creates curiosity in the first 3 seconds. End with a line that lingers.
- No emojis or hashtags inside the narration."""


def target_chars(minutes: float, lang: str) -> int:
    return int(minutes * CHARS_PER_MINUTE.get(lang, 300))


def generate_story(topic: str, minutes: float, lang: str = "ko") -> dict:
    import anthropic

    client = anthropic.Anthropic()
    chars = target_chars(minutes, lang)
    unit = "words" if lang == "en" else "characters"
    if lang == "en":
        chars = int(minutes * 140)  # words per minute
    scene_count = max(4, round(minutes * 3))

    prompt = (
        f"Topic / request: {topic}\n\n"
        f"Language of all narration, title, caption: {LANG_NAMES.get(lang, lang)}\n"
        f"Target video length: {minutes} minutes of narration, so the hook + all scenes + ending together "
        f"should be about {chars} {unit} long (this matters - do not write much shorter).\n"
        f"Use about {scene_count} scenes.\n"
        f"Hashtags: 8-15, without the # sign, mixing {LANG_NAMES.get(lang, lang)} and English."
    )

    print(f"  Asking Claude ({MODEL}) for a ~{minutes} min script...")
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
        # If Claude's safety filter declines, the API automatically retries on a fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined this topic. Try wording it differently.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("The script was cut off (too long). Try a shorter --minutes value.")

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def load_story(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_story(story: dict) -> dict:
    for key in ("title", "hook", "scenes", "ending"):
        if key not in story:
            raise ValueError(f"Story JSON is missing '{key}'")
    for scene in story["scenes"]:
        scene.setdefault("image_keywords", "cinematic moody landscape")
        if scene.get("tone") not in PALETTES:
            scene["tone"] = "dusk"
    story.setdefault("caption", story["title"])
    story.setdefault("hashtags", [])
    story.setdefault("sources", [])
    return story


# ------------------------------------------------------------------ 15-second YouTube Shorts
# Different kinds of true stories, rotated so the channel doesn't feel repetitive.
SHORT_CATEGORIES = [
    "a loyal animal (dog, cat, horse, dolphin, bird...) and the people it loved",
    "a stranger's unexpected kindness that changed someone's life",
    "a parent's or grandparent's sacrifice for their child",
    "a long-lost family reunion after many years",
    "an ordinary person who saved lives (rescue, firefighter, nurse, passer-by)",
    "an athlete's moment of sportsmanship or comeback",
    "a teacher and a student",
    "love that lasted a lifetime (old couples, promises kept)",
    "a child's act of kindness that moved a whole town or country",
    "humanity and compassion during war or disaster",
    "a doctor, scientist or inventor who helped people without seeking money or fame",
    "a famous person's little-known kind act (only if well documented)",
]

SHORT_SYSTEM = SYSTEM + """

THIS IS A 15-SECOND YOUTUBE SHORT. Extreme brevity:
- hook: exactly 1 short sentence that grabs attention in the first 2 seconds.
- scenes: exactly 3 scenes, each exactly 1 short sentence.
- ending: 1 short sentence that gives the emotional payoff (the twist / the touching truth).
- The whole narration (hook + scenes + ending) must be about {chars} {unit} in total. Never longer.
- title: max 14 characters, curiosity-driven (it is shown on screen the whole time).
- youtube_title: max 60 characters, emotional, makes people tap. Do not add #shorts (added automatically).
- story_id: a short English identifier of the real story, e.g. "Hachiko the Akita, Shibuya 1925".
- Pick a DIFFERENT real story from every story_id listed as already used."""

SHORT_SCHEMA = json.loads(json.dumps(SCHEMA))
SHORT_SCHEMA["properties"]["story_id"] = {"type": "string"}
SHORT_SCHEMA["properties"]["youtube_title"] = {"type": "string"}
SHORT_SCHEMA["required"] += ["story_id", "youtube_title"]

# total narration length for 15 seconds (speech ~12s + short pauses + music tail)
SHORT_CHARS = {"ko": 75, "ja": 85, "en": 38}


def _ask_claude(system: str, prompt: str, schema: dict, max_tokens: int) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        response = stream.get_final_message()
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined this request. Try again or change the category.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("The script was cut off.")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def generate_short(lang: str, used_ids: list[str], category: str, topic: str = "") -> dict:
    unit = "words" if lang == "en" else "characters (including spaces)"
    chars = SHORT_CHARS.get(lang, 62)
    used = "\n".join(f"- {u}" for u in used_ids[-400:]) or "(none yet)"
    prompt = (
        f"Write one 15-second touching TRUE story Short.\n"
        f"Story type for today: {topic or category}\n"
        f"Language of narration, title, youtube_title, caption: {LANG_NAMES.get(lang, lang)}\n"
        f"Hashtags: 5-8, without the # sign, mixing {LANG_NAMES.get(lang, lang)} and English.\n\n"
        f"Stories already used on this channel (do NOT repeat any of them):\n{used}"
    )
    print(f"  Asking Claude ({MODEL}) for a 15-second story: {topic or category}")
    return _ask_claude(SHORT_SYSTEM.format(chars=chars, unit=unit), prompt, SHORT_SCHEMA, 16000)
