"""YouTube uploads via the YouTube Data API v3 (OAuth2, resumable upload).

Needs a one-time OAuth consent to obtain a refresh token — run
scripts/youtube_oauth_setup.py locally once and copy the resulting
YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN into your .env / secrets.
"""
from __future__ import annotations

from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from safar_agent.config import settings

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _require_config() -> None:
    if not (settings.yt_client_id and settings.yt_client_secret and settings.yt_refresh_token):
        raise RuntimeError(
            "YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN are not set in .env "
            "(run scripts/youtube_oauth_setup.py once to obtain them)"
        )


def _client():
    _require_config()
    creds = Credentials(
        token=None,
        refresh_token=settings.yt_refresh_token,
        client_id=settings.yt_client_id,
        client_secret=settings.yt_client_secret,
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str] | None = None,
    is_short: bool = False,
    privacy_status: str = "public",
) -> dict:
    youtube = _client()

    if is_short and "#shorts" not in title.lower() and "#shorts" not in description.lower():
        description = f"{description}\n\n#Shorts"

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags or [],
            "categoryId": "2",  # Autos & Vehicles
        },
        "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": False},
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _status, response = request.next_chunk()
    return response
