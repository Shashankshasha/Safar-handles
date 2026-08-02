"""Instagram's Graph API (and YouTube thumbnails, etc.) need a publicly
reachable URL for media — it can't accept raw bytes. This uploads a locally
generated file to whatever public bucket you've configured and returns its URL.

Only S3 is wired up by default since it's the most common choice; swap this
module out for Cloudinary/GCS/whatever you already use if different.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from safar_agent.config import settings


def upload_public(local_path: Path) -> str:
    if settings.public_media_base_url and _s3_configured():
        return _upload_to_s3(local_path)
    raise RuntimeError(
        "No public media host configured. Set AWS_S3_BUCKET (+ credentials) and "
        "PUBLIC_MEDIA_BASE_URL in .env, or implement media_host.upload_public() "
        "for your own storage provider (Cloudinary, GCS, etc.)."
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
