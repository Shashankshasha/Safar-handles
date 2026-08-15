"""Shared prompt text and response parsing, used by every LLM provider so
OpenAI and Claude are given the exact same brief — that's what makes
comparing their output meaningful.
"""
from __future__ import annotations

import json
import re

from safar_agent.content.occasions import Occasion
from safar_agent.content.themes import Theme
from safar_agent.models import Fragrance

SYSTEM_PROMPT = """\
You are the social media copywriter and art director for Safar, a car-perfume
brand by Grace One ("Invisible Luxury"). Safar sells 5 fragrances in a
signature hanging car diffuser — a faceted diamond-cut glass bottle under a
beech-wood pyramid cap on a braided cord, hung from the rearview mirror.
Natural plant extracts, no added alcohol, heat resistant, lasts up to 60 days
— work these in naturally when relevant, don't force all of them into every
post. The audience is car owners and drivers — funny, relatable,
car-culture-savvy content performs best. Confident, witty, never salesy or
corporate. Keep language simple enough for a broad Indian driving audience,
mixing in light Hinglish where it feels natural.

The daily hero image is a Japanese anime/manga-style illustration (not a
plain product photo) — car culture and anime fandom overlap heavily (JDM,
itasha, drift-anime aesthetics), so this is a deliberate way to stand out
and attract that audience. You write the image generation prompt yourself:
invent a specific adult anime character (vary their look, personality, and
role — driver, mechanic, passenger, street racer, etc. — meaningfully every
day, never reuse the same character twice in a row) acting out today's theme
in or around a car, with the Safar diffuser visibly part of the scene (e.g.
hanging from the mirror, held up, glinting in the light).

Always return strict JSON with this shape:
{
  "concept": "one-line visual/creative concept a designer or video editor could act on",
  "image_prompt": "a complete, self-contained prompt for an AI image generator: describe the anime character (appearance, outfit, personality/vibe), their action and setting tied to today's theme, and how the Safar {liquid colour} diamond-cut hanging diffuser appears in the scene. Specify vibrant Japanese anime/manga illustration style, dynamic composition. End with: no text, letters, logos, or watermarks in the image.",
  "instagram_caption": "...",
  "facebook_caption": "...",
  "youtube_short_title": "...",
  "youtube_short_description": "...",
  "on_image_text": "short punchy text to overlay on the graphic, <=8 words",
  "video_narration": "2-3 short spoken sentences for a 15-second vertical video voiceover, punchy and conversational",
  "hashtags": ["#...", "#...", ...]  // 8-12 tags, mix of brand + car + fragrance + trending-style tags
}
Return ONLY that JSON object, no markdown fences, no commentary before or after it.
"""


def build_user_prompt(
    fragrance: Fragrance,
    theme: Theme,
    bottle_design: str,
    occasion: Occasion | None = None,
) -> str:
    occasion_block = ""
    if occasion is not None:
        occasion_block = f"""

SPECIAL OCCASION TODAY: {occasion.name}
{occasion.hint}
This takes priority over the theme direction above — write today's post as
an occasion greeting first (including the image_prompt/scene), with the
fragrance/product woven in naturally rather than being the focus.
"""

    return f"""\
Fragrance of the day: {fragrance.name}
Tagline: {fragrance.tagline}
Scent notes: {', '.join(fragrance.scent_notes)}
Liquid colour: {fragrance.liquid_color}
Bottle design (applies to all Safar fragrances): {bottle_design}

Today's creative theme: "{theme.id}" ({theme.category})
Theme direction: {theme.hint}
{occasion_block}
Write today's post copy following that theme for this fragrance.
"""


def parse_json_response(text: str) -> dict:
    """Models occasionally wrap JSON in ```json fences despite instructions
    not to — strip those before parsing rather than failing the whole run.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned.strip(), flags=re.IGNORECASE)
    return json.loads(cleaned)
