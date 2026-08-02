#!/usr/bin/env python3
"""Prints today's fragrance + theme + bottle design as JSON.

Used by the safar-daily-post Claude Code skill so Claude can write copy
without needing an LLM API key — it reads this brief instead of calling
OpenAI/Anthropic itself. Run once per day, BEFORE writing copy: theme
selection is random, so whatever theme_id this prints must be echoed back
verbatim in the copy JSON's "_meta.theme_id" field (see the skill
instructions) — otherwise the actual publishing run would re-roll a
different theme than the one the copy was written for.
"""
from __future__ import annotations

import json
from datetime import date

from safar_agent.content.product_catalog import load_catalog
from safar_agent.storage.history import pick_theme, recent_visual_notes


def main() -> None:
    today = date.today()
    catalog = load_catalog()
    fragrance = catalog.fragrance_for_weekday(today.weekday())
    theme = pick_theme()

    print(
        json.dumps(
            {
                "date": today.isoformat(),
                "fragrance_id": fragrance.id,
                "fragrance_name": fragrance.name,
                "fragrance_tagline": fragrance.tagline,
                "scent_notes": fragrance.scent_notes,
                "liquid_color": fragrance.liquid_color,
                "reference_photos": [str(p) for p in fragrance.reference_images()],
                "theme_id": theme.id,
                "theme_category": theme.category,
                "theme_hint": theme.hint,
                "bottle_design": catalog.bottle_design,
                "recent_visual_notes": recent_visual_notes(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
