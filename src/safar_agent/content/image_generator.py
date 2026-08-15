"""Turns an uploaded product photo + generated copy into a postable image.

Two paths:
  - compose_hero_image(): takes one of YOUR uploaded photos (assets/products/...)
    and overlays a branded caption banner. This is the default and doesn't need
    any image-generation API call — it just needs real photos in the asset folders.
  - generate_ai_background(): optional, calls OpenAI's image API to create a
    themed scene (e.g. "action figure diorama", "movie poster") for days you
    want a fully illustrated/stylised post rather than a photo-based one.
"""
from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image, ImageDraw

from safar_agent.config import settings
from safar_agent.fonts import bold_font
from safar_agent.models import Fragrance

FEED_SIZE = (1080, 1350)  # Instagram/Facebook portrait feed post
STORY_SIZE = (1080, 1920)  # Reels/Shorts/Stories canvas

BRAND_COLOR = (212, 175, 55)  # gold, matches "diamond bottle" positioning
BANNER_COLOR = (10, 10, 10, 190)


def _fit_cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_size = (int(src_w * scale), int(src_h * scale))
    img = img.resize(new_size, Image.LANCZOS)
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def compose_hero_image(
    fragrance: Fragrance,
    on_image_text: str,
    output_path: Path,
    size: tuple[int, int] = FEED_SIZE,
    reference_index: int = 0,
) -> Path:
    photos = fragrance.reference_images()
    if not photos:
        raise FileNotFoundError(
            f"No reference photos found in {fragrance.image_dir}. "
            "Upload at least one product/bottle photo there before generating a post."
        )
    photo_path = photos[reference_index % len(photos)]

    base = Image.open(photo_path).convert("RGB")
    canvas = _fit_cover(base, size).convert("RGBA")

    banner_height = int(size[1] * 0.28)
    banner = Image.new("RGBA", (size[0], banner_height), BANNER_COLOR)
    canvas.alpha_composite(banner, dest=(0, size[1] - banner_height))

    draw = ImageDraw.Draw(canvas)
    pad = 48
    text_y = size[1] - banner_height + pad

    draw.text((pad, text_y), "GRACE ONE", font=bold_font(34), fill=BRAND_COLOR)
    draw.text((pad, text_y + 46), fragrance.name.upper(), font=bold_font(50), fill="white")
    draw.text((pad, text_y + 110), on_image_text, font=bold_font(30), fill="white")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, quality=92)
    return output_path


def crop_to_size(input_path: Path, output_path: Path, size: tuple[int, int] = FEED_SIZE) -> Path:
    """Center-crops an image to an exact aspect ratio. Used to bring
    OpenAI-generated images (portrait 2:3, ratio 0.667) into Instagram's
    allowed feed-photo range (4:5 to 1.91:1, i.e. 0.8-1.91) — posting outside
    that range gets rejected with a 400 from the Graph API.
    """
    img = Image.open(input_path).convert("RGB")
    cropped = _fit_cover(img, size)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(output_path, quality=92)
    return output_path


def generate_ai_background(prompt: str, output_path: Path, size: str = "1024x1536") -> Path:
    """Optional: generate a fully illustrated/stylised scene via OpenAI images API.

    Useful for themes like action-figure-diorama or movie-parody where you want
    an original illustrated scene rather than a straight product photo.
    """
    from openai import OpenAI

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=settings.openai_api_key)
    result = client.images.generate(
        model=settings.openai_image_model,
        prompt=prompt,
        size=size,
    )
    image_b64 = result.data[0].b64_json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(image_b64))
    return output_path
