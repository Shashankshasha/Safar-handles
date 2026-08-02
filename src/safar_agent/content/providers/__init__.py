from __future__ import annotations

from safar_agent.content.providers import anthropic_provider, openai_provider

PROVIDERS = {
    "openai": openai_provider.generate,
    "anthropic": anthropic_provider.generate,
}
