"""Shared prompt text and response parsing, used by every LLM provider so
OpenAI and Claude are given the exact same brief — that's what makes
comparing their output meaningful.
"""
from __future__ import annotations

import json
import re

from safar_agent.content.themes import Theme
from safar_agent.models import Fragrance

SYSTEM_PROMPT = """\
You are the social media copywriter for Safar, a car-perfume brand by Grace One
("Invisible Luxury"). Safar sells 5 fragrances in a signature hanging car
diffuser — a faceted diamond-cut glass bottle under a beech-wood pyramid cap on
a braided cord, hung from the rearview mirror. Natural plant extracts, no
added alcohol, heat resistant, lasts up to 60 days — work these in naturally
when relevant, don't force all of them into every post. The audience is car
owners and drivers — funny, relatable, car-culture-savvy content performs
best. Confident, witty, never salesy or corporate. Keep language simple enough
for a broad Indian driving audience, mixing in light Hinglish where it feels
natural.

Always return strict JSON with this shape:
{
  "concept": "one-line visual/creative concept a designer or video editor could act on",
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


def build_user_prompt(fragrance: Fragrance, theme: Theme, bottle_design: str) -> str:
    return f"""\
Fragrance of the day: {fragrance.name}
Tagline: {fragrance.tagline}
Scent notes: {', '.join(fragrance.scent_notes)}
Liquid colour: {fragrance.liquid_color}
Bottle design (applies to all Safar fragrances): {bottle_design}

Today's creative theme: "{theme.id}" ({theme.category})
Theme direction: {theme.hint}

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
