"""Run this once, locally, in a browser-capable environment to obtain a
YouTube refresh token for the agent.

Prerequisites:
  1. In Google Cloud Console, create a project, enable "YouTube Data API v3".
  2. Create an OAuth 2.0 Client ID of type "Desktop app" and download its
     client_secret.json into this scripts/ folder.

Usage:
  python scripts/youtube_oauth_setup.py

It opens a browser for you to sign in with the Google account/YouTube
channel you want the agent to post as, then prints the values to put in
.env (YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN).
"""
from __future__ import annotations

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = Path(__file__).parent / "client_secret.json"


def main() -> None:
    if not CLIENT_SECRET_FILE.exists():
        raise SystemExit(
            f"Missing {CLIENT_SECRET_FILE}. Download your OAuth client's "
            "client_secret.json from Google Cloud Console and place it there."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    credentials = flow.run_local_server(port=0)

    print("\nAdd these to your .env / GitHub Actions secrets:\n")
    print(f"YT_CLIENT_ID={credentials.client_id}")
    print(f"YT_CLIENT_SECRET={credentials.client_secret}")
    print(f"YT_REFRESH_TOKEN={credentials.refresh_token}")


if __name__ == "__main__":
    main()
