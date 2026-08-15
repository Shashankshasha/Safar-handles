"""Turns a (fragrance, theme) pair into ready-to-post copy.

Provider-agnostic: TEXT_PROVIDER in .env picks "openai" or "anthropic" by
default, either can be forced per call, and generate_post_copy_all() runs
both so you can compare quality/cost side by side.
"""
from __future__ import annotations

from safar_agent.config import settings
from safar_agent.content.occasions import Occasion
from safar_agent.content.providers import PROVIDERS
from safar_agent.content.themes import Theme
from safar_agent.models import Fragrance


def generate_post_copy(
    fragrance: Fragrance,
    theme: Theme,
    bottle_design: str,
    provider: str | None = None,
    occasion: Occasion | None = None,
) -> dict:
    provider = provider or settings.text_provider
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown text provider {provider!r}. Choose from: {list(PROVIDERS)}")
    return PROVIDERS[provider](fragrance, theme, bottle_design, occasion=occasion)


def generate_post_copy_all(
    fragrance: Fragrance,
    theme: Theme,
    bottle_design: str,
    occasion: Occasion | None = None,
) -> dict:
    """Runs every configured provider and returns {provider_name: result_or_error}."""
    results: dict[str, dict] = {}
    for name, generate in PROVIDERS.items():
        try:
            results[name] = generate(fragrance, theme, bottle_design, occasion=occasion)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user, not swallowed
            results[name] = {"error": str(exc)}
    return results
