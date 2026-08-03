"""Instagram's Graph API (and YouTube thumbnails, etc.) need a publicly
reachable URL for media — it can't accept raw bytes. This uploads a locally
generated file to whichever public host you've configured and returns its URL.

Two providers are wired up:
  - "github" (MEDIA_HOST_PROVIDER=github): free, no cloud account needed.
    Commits the file to a dedicated branch of this repo via the GitHub
    Contents API and serves it via raw.githubusercontent.com. Requires the
    repo to be public (raw URLs on a private repo aren't fetchable by
    Instagram's servers) and permanently keeps every posted file in git
    history on that branch.
  - "s3" (MEDIA_HOST_PROVIDER=s3, the default): near-free, needs an AWS
    account, bucket, and credentials.

Swap in Cloudinary/GCS/whatever else by adding another branch here if you'd
rather use a different provider.
"""
from __future__ import annotations

import base64
import os
import uuid
from pathlib import Path

import requests

from safar_agent.config import settings

GITHUB_API = "https://api.github.com"


def upload_public(local_path: Path) -> str:
    if settings.media_host_provider == "github":
        return _upload_to_github(local_path)
    if settings.public_media_base_url and _s3_configured():
        return _upload_to_s3(local_path)
    raise RuntimeError(
        "No public media host configured. Set MEDIA_HOST_PROVIDER=github "
        "(+ GITHUB_TOKEN, GITHUB_REPO) for the free option, or "
        "MEDIA_HOST_PROVIDER=s3 (+ AWS_S3_BUCKET, AWS credentials, "
        "PUBLIC_MEDIA_BASE_URL) in .env."
    )


def _s3_configured() -> bool:
    return bool(os.getenv("AWS_S3_BUCKET") and os.getenv("AWS_ACCESS_KEY_ID"))


def _upload_to_s3(local_path: Path) -> str:
    import boto3  # optional dependency, only needed if you use S3 hosting

    bucket = os.environ["AWS_S3_BUCKET"]
    region = os.getenv("AWS_S3_REGION", "us-east-1")
    key = f"safar-posts/{uuid.uuid4().hex}{local_path.suffix}"

    client = boto3.client("s3", region_name=region)
    client.upload_file(str(local_path), bucket, key, ExtraArgs={"ACL": "public-read"})

    base = settings.public_media_base_url.rstrip("/")
    return f"{base}/{key}"


def _upload_to_github(local_path: Path) -> str:
    if not (settings.github_token and settings.github_repo):
        raise RuntimeError(
            "MEDIA_HOST_PROVIDER=github requires GITHUB_TOKEN (a personal "
            "access token with contents write access) and GITHUB_REPO "
            "(e.g. 'youruser/yourrepo') in .env."
        )

    repo = settings.github_repo
    branch = settings.github_media_branch
    headers = {
        "Authorization": f"token {settings.github_token}",
        "Accept": "application/vnd.github+json",
    }

    _ensure_branch_exists(repo, branch, headers)

    remote_path = f"media/{uuid.uuid4().hex}{local_path.suffix}"
    content_b64 = base64.b64encode(local_path.read_bytes()).decode()

    response = requests.put(
        f"{GITHUB_API}/repos/{repo}/contents/{remote_path}",
        headers=headers,
        json={
            "message": f"Add generated media {remote_path}",
            "content": content_b64,
            "branch": branch,
        },
        timeout=60,
    )
    response.raise_for_status()

    return f"https://raw.githubusercontent.com/{repo}/{branch}/{remote_path}"


def _ensure_branch_exists(repo: str, branch: str, headers: dict) -> None:
    check = requests.get(
        f"{GITHUB_API}/repos/{repo}/branches/{branch}", headers=headers, timeout=30
    )
    if check.status_code == 200:
        return

    repo_info = requests.get(f"{GITHUB_API}/repos/{repo}", headers=headers, timeout=30)
    repo_info.raise_for_status()
    default_branch = repo_info.json()["default_branch"]

    ref = requests.get(
        f"{GITHUB_API}/repos/{repo}/git/ref/heads/{default_branch}",
        headers=headers,
        timeout=30,
    )
    ref.raise_for_status()
    sha = ref.json()["object"]["sha"]

    create = requests.post(
        f"{GITHUB_API}/repos/{repo}/git/refs",
        headers=headers,
        json={"ref": f"refs/heads/{branch}", "sha": sha},
        timeout=30,
    )
    create.raise_for_status()
