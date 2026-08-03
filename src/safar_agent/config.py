from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
ASSETS_DIR = REPO_ROOT / "assets"
OUTPUT_DIR = REPO_ROOT / "output"
HISTORY_PATH = DATA_DIR / "history.json"
PRODUCTS_YAML = DATA_DIR / "products.yaml"


def _bool_env(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Which LLM writes captions/scripts by default: "openai" or "anthropic".
    # Only image generation is OpenAI-only (image_generator.generate_ai_background).
    text_provider: str = os.getenv("TEXT_PROVIDER", "openai")

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_text_model: str = os.getenv("OPENAI_TEXT_MODEL", "gpt-5")
    openai_image_model: str = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_text_model: str = os.getenv("ANTHROPIC_TEXT_MODEL", "claude-sonnet-5")

    # Daily hero image style: "anime" (AI-generated anime-character scene via
    # OpenAI, a few cents/day) or "photo" (free — composites your uploaded
    # product photo with a text banner, no image-generation API call).
    # Falls back to "photo" automatically if OPENAI_API_KEY isn't set or a
    # generation call fails.
    hero_image_style: str = os.getenv("HERO_IMAGE_STYLE", "anime")

    fb_page_id: str | None = os.getenv("FB_PAGE_ID")
    fb_page_access_token: str | None = os.getenv("FB_PAGE_ACCESS_TOKEN")

    ig_business_account_id: str | None = os.getenv("IG_BUSINESS_ACCOUNT_ID")

    # Instagram's API needs a public URL for any image/video it posts.
    # MEDIA_HOST_PROVIDER: "github" (free, commits media to a branch of this
    # repo and serves it via raw.githubusercontent.com — repo must be public)
    # or "s3" (near-free, needs an AWS account).
    media_host_provider: str = os.getenv("MEDIA_HOST_PROVIDER", "s3")
    public_media_base_url: str | None = os.getenv("PUBLIC_MEDIA_BASE_URL")

    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_repo: str | None = os.getenv("GITHUB_REPO")
    github_media_branch: str = os.getenv("GITHUB_MEDIA_BRANCH", "media")

    yt_client_id: str | None = os.getenv("YT_CLIENT_ID")
    yt_client_secret: str | None = os.getenv("YT_CLIENT_SECRET")
    yt_refresh_token: str | None = os.getenv("YT_REFRESH_TOKEN")

    weekly_video_weekday: int = int(os.getenv("WEEKLY_VIDEO_WEEKDAY", "6"))
    dry_run: bool = _bool_env("DRY_RUN", True)


settings = Settings()
