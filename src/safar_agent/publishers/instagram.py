"""Instagram publishing via the Instagram Graph API (Business account linked
to your Facebook Page). Two-step "container" flow for both images and Reels:
create a media container, poll until it's ready, then publish it.
"""
from __future__ import annotations

import time
from pathlib import Path

import requests

from safar_agent.config import settings
from safar_agent.publishers.media_host import upload_public

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"


def _require_config() -> None:
    if not (settings.ig_business_account_id and settings.fb_page_access_token):
        raise RuntimeError(
            "IG_BUSINESS_ACCOUNT_ID / FB_PAGE_ACCESS_TOKEN are not set in .env"
        )


def _check(response: requests.Response) -> requests.Response:
    """requests' raise_for_status() only says "400 Bad Request" — Meta's
    actual reason (bad aspect ratio, expired token, etc.) is in the response
    body, so surface that instead of forcing a re-run just to see it.
    """
    if not response.ok:
        raise RuntimeError(
            f"Instagram Graph API error ({response.status_code}) for {response.url}: "
            f"{response.text}"
        )
    return response


def _create_container(**fields) -> str:
    url = f"{GRAPH_API_BASE}/{settings.ig_business_account_id}/media"
    fields["access_token"] = settings.fb_page_access_token
    response = _check(requests.post(url, data=fields, timeout=120))
    return response.json()["id"]


def _wait_until_ready(creation_id: str, timeout_s: int = 300, poll_every_s: int = 5) -> None:
    url = f"{GRAPH_API_BASE}/{creation_id}"
    waited = 0
    while waited < timeout_s:
        response = _check(
            requests.get(
                url,
                params={"fields": "status_code", "access_token": settings.fb_page_access_token},
                timeout=30,
            )
        )
        status = response.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Instagram media container {creation_id} failed processing")
        time.sleep(poll_every_s)
        waited += poll_every_s
    raise TimeoutError(f"Instagram media container {creation_id} did not finish processing in time")


def _publish(creation_id: str) -> dict:
    url = f"{GRAPH_API_BASE}/{settings.ig_business_account_id}/media_publish"
    response = _check(
        requests.post(
            url,
            data={"creation_id": creation_id, "access_token": settings.fb_page_access_token},
            timeout=60,
        )
    )
    return response.json()


def publish_image(image_path: Path, caption: str) -> dict:
    _require_config()
    image_url = upload_public(image_path)
    creation_id = _create_container(image_url=image_url, caption=caption)
    return _publish(creation_id)


def publish_reel(video_path: Path, caption: str) -> dict:
    _require_config()
    video_url = upload_public(video_path)
    creation_id = _create_container(
        media_type="REELS", video_url=video_url, caption=caption
    )
    _wait_until_ready(creation_id)
    return _publish(creation_id)
