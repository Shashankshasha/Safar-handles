from __future__ import annotations

import json

from safar_agent.config import settings
from safar_agent.content.occasions import Occasion
from safar_agent.content.providers.prompts import SYSTEM_PROMPT, build_user_prompt
from safar_agent.content.themes import Theme
from safar_agent.models import Fragrance


def generate(
    fragrance: Fragrance,
    theme: Theme,
    bottle_design: str,
    occasion: Occasion | None = None,
) -> dict:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env before generating content."
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_text_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(fragrance, theme, bottle_design, occasion=occasion),
            },
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
