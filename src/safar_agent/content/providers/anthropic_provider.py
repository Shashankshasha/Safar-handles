from __future__ import annotations

from safar_agent.config import settings
from safar_agent.content.providers.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    parse_json_response,
)
from safar_agent.content.themes import Theme
from safar_agent.models import Fragrance


def generate(fragrance: Fragrance, theme: Theme, bottle_design: str) -> dict:
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env before generating content."
        )

    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_text_model,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_user_prompt(fragrance, theme, bottle_design)},
        ],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return parse_json_response(text)
