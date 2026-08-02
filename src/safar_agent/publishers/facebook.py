"""Facebook Page publishing via the Graph API.

Requires a Page Access Token with pages_manage_posts + pages_read_engagement
scopes for FB_PAGE_ID. Create one via a Meta developer app -> Graph API
Explorer (short-lived) then exchange for a long-lived token; see README.
"""
from __future__ import annotations

from pathlib import Path

import requests

from safar_agent.config import settings

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def _require_config() -> None:
    if not (settings.fb_page_id and settings.fb_page_access_token):
        raise RuntimeError("FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN are not set in .env")


def publish_photo(image_path: Path, caption: str) -> dict:
    _require_config()
    url = f"{GRAPH_API_BASE}/{settings.fb_page_id}/photos"
    with open(image_path, "rb") as fh:
        response = requests.post(
            url,
            data={"caption": caption, "access_token": settings.fb_page_access_token},
            files={"source": fh},
            timeout=120,
        )
    response.raise_for_status()
    return response.json()


def publish_video(video_path: Path, description: str, title: str | None = None) -> dict:
    """Uploads a native video to the Page feed. Short vertical videos posted
    this way are generally eligible for Meta's own Reels distribution, but for
    guaranteed Reels placement use the dedicated /video_reels resumable-upload
    endpoint (Meta docs: 'Publishing Reels via the Graph API') if this isn't
    enough for your use case.
    """
    _require_config()
    url = f"{GRAPH_API_BASE}/{settings.fb_page_id}/videos"
    data = {"description": description, "access_token": settings.fb_page_access_token}
    if title:
        data["title"] = title
    with open(video_path, "rb") as fh:
        response = requests.post(url, data=data, files={"source": fh}, timeout=600)
    response.raise_for_status()
    return response.json()
