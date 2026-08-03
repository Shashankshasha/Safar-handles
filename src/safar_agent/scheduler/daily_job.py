"""The daily entrypoint. Run via:

    python -m safar_agent.scheduler.daily_job                     # dry run (default, safe)
    python -m safar_agent.scheduler.daily_job --publish            # actually posts
    python -m safar_agent.scheduler.daily_job --provider anthropic # use Claude instead of GPT
    python -m safar_agent.scheduler.daily_job --compare-providers  # caption-only, both providers
    python -m safar_agent.scheduler.daily_job --copy-file out.json # use pre-written copy, no LLM API call
    python -m safar_agent.scheduler.daily_job --image-file scene.png # use a pre-rendered hero image

Each run:
  - picks today's fragrance-of-the-day (Mon-Fri rotate the 5 fragrances,
    weekends spotlight the diamond bottle) and an unused-recently theme
  - generates caption/hashtags/on-image text/video narration via whichever
    LLM TEXT_PROVIDER (or --provider) selects
  - composes a feed image from your uploaded product photo
  - always builds a ~15s vertical short (voiceover + captions)
  - on WEEKLY_VIDEO_WEEKDAY, also builds the long-form YouTube showcase video
  - publishes to Facebook + Instagram (image) and Instagram Reels + YouTube
    Shorts (video), plus YouTube long-form on the weekly day
  - logs everything to data/history.json
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from safar_agent.config import OUTPUT_DIR, settings
from safar_agent.content.idea_generator import generate_post_copy, generate_post_copy_all
from safar_agent.content.image_generator import compose_hero_image, generate_ai_background
from safar_agent.content.product_catalog import load_catalog
from safar_agent.content.providers import PROVIDERS
from safar_agent.content.themes import theme_by_id
from safar_agent.models import GeneratedPost
from safar_agent.publishers import facebook, instagram, youtube
from safar_agent.storage.history import pick_theme, record_post, today_str
from safar_agent.video.daily_short import generate_daily_short
from safar_agent.video.voiceover import generate_voiceover
from safar_agent.video.weekly_video import generate_weekly_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("daily_job")

BG_MUSIC = Path("assets/audio/bg_music.mp3")


def run(
    publish: bool,
    provider: str | None = None,
    copy_override: dict | None = None,
    image_override: Path | None = None,
) -> GeneratedPost:
    """If copy_override is given (e.g. written by the safar-daily-post Claude
    Code skill instead of an LLM API call), it must include a "_meta.theme_id"
    matching a theme id from content/themes.py — that pins which theme was
    actually written for, since theme selection is otherwise random. No LLM
    provider is called in that case. copy_override may also include an
    optional "_meta.visual_note" describing the visual composition used, so
    future runs can deliberately pick something different.

    image_override, if given, is used as the hero image as-is (e.g. a
    Claude-designed cartoon scene rendered via scripts/render_scene.py)
    instead of compositing one from your uploaded product photo.
    """
    today = date.today()
    weekday = today.weekday()
    day_dir = OUTPUT_DIR / today.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    catalog = load_catalog()
    fragrance = catalog.fragrance_for_weekday(weekday)
    visual_note = None

    if copy_override is not None:
        meta = copy_override.get("_meta", {})
        theme_id = meta.get("theme_id")
        if not theme_id:
            raise ValueError('copy_override is missing required "_meta.theme_id"')
        theme = theme_by_id(theme_id)
        visual_note = meta.get("visual_note")
        copy = copy_override
        log.info("Today's fragrance: %s | theme: %s | copy: pre-written", fragrance.name, theme.id)
    else:
        theme = pick_theme()
        log.info(
            "Today's fragrance: %s | theme: %s | text provider: %s",
            fragrance.name,
            theme.id,
            provider or settings.text_provider,
        )
        copy = generate_post_copy(fragrance, theme, catalog.bottle_design, provider=provider)

    # The video always gets its own caption overlay burned in (see
    # video/text_overlay.py), so its background must be a *clean* image —
    # reusing an image that already has on_image_text baked into it would
    # show the caption twice. A Claude-designed scene (image_override) is
    # trusted to already convey whatever text it needs, so no overlay is
    # added on top of it there.
    if image_override is not None:
        if not image_override.exists():
            raise FileNotFoundError(f"--image-file path does not exist: {image_override}")
        image_path = image_override
        video_background = image_override
        video_caption = ""
    else:
        image_path = compose_hero_image(fragrance, copy["on_image_text"], day_dir / "post.jpg")
        raw_photos = fragrance.reference_images()
        video_background = raw_photos[0] if raw_photos else image_path
        video_caption = copy["on_image_text"]

    voiceover_path = None
    try:
        voiceover_path = generate_voiceover(copy["video_narration"], day_dir / "voiceover.mp3")
    except Exception:
        log.warning("Voiceover generation failed, continuing without narration", exc_info=True)

    bg_music = BG_MUSIC if BG_MUSIC.exists() else None
    short_path = generate_daily_short(
        image_path=video_background,
        caption_text=video_caption,
        output_path=day_dir / "short.mp4",
        voiceover_path=voiceover_path,
        bg_music_path=bg_music,
    )

    weekly_video_path = None
    if weekday == settings.weekly_video_weekday:
        weekly_video_path = _build_weekly_video(catalog, day_dir, bg_music)

    post = GeneratedPost(
        date=today_str(),
        fragrance_id=fragrance.id,
        theme_id=theme.id,
        caption=copy["instagram_caption"],
        hashtags=copy.get("hashtags", []),
        image_path=image_path,
        short_video_path=short_path,
        weekly_video_path=weekly_video_path,
        visual_note=visual_note,
    )

    if publish:
        _publish_everywhere(post, copy)
    else:
        log.info("Dry run: skipping real publishing. Generated assets are in %s", day_dir)

    record_post(post)
    return post


def _build_weekly_video(catalog, day_dir: Path, bg_music: Path | None) -> Path:
    log.info("Today is the weekly video day — building the showcase video")
    segments = []

    cover_path = _try_generate_weekly_cover_art(catalog, day_dir)
    if cover_path:
        segments.append((cover_path, f"This Week on {catalog.brand}\n{catalog.tagline}"))

    for fragrance in catalog.all_fragrances():
        photos = fragrance.reference_images()
        if not photos:
            log.warning("Skipping %s in weekly video: no reference photos", fragrance.id)
            continue
        segments.append((photos[0], f"{fragrance.name}\n{fragrance.tagline}"))

    narration_text = " ".join(f"{f.name}. {f.tagline}." for f in catalog.all_fragrances())
    narration_path = None
    try:
        narration_path = generate_voiceover(narration_text, day_dir / "weekly_voiceover.mp3")
    except Exception:
        log.warning("Weekly narration generation failed, continuing without it", exc_info=True)

    return generate_weekly_video(
        segments=segments,
        output_path=day_dir / "weekly.mp4",
        narration_path=narration_path,
        bg_music_path=bg_music,
    )


def _try_generate_weekly_cover_art(catalog, day_dir: Path) -> Path | None:
    """The weekly showcase is the flagship piece of content, so it's worth
    spending a few cents on a real AI-illustrated cover — daily posts instead
    default to the free Claude-coded cartoon scene (see the safar-daily-post
    skill) or the plain photo composite. Skipped gracefully if no OpenAI key.
    """
    if not settings.openai_api_key:
        log.info("OPENAI_API_KEY not set — skipping AI-generated weekly cover art")
        return None
    try:
        prompt = (
            f"Vibrant, playful illustrated poster art for '{catalog.brand}' car "
            f"perfume by {catalog.maker}. A hanging diamond-cut glass bottle "
            "diffuser under a beech-wood pyramid cap, hanging from a car's "
            "rearview mirror. Warm, inviting cartoon/illustration style. "
            "No text, letters, or logos rendered in the image."
        )
        return generate_ai_background(prompt, day_dir / "weekly_cover.png", size="1536x1024")
    except Exception:
        log.warning("AI weekly cover art generation failed, continuing without it", exc_info=True)
        return None


def _publish_everywhere(post: GeneratedPost, copy: dict) -> None:
    hashtag_str = " ".join(post.hashtags)

    log.info("Publishing image post to Facebook")
    facebook.publish_photo(post.image_path, f"{copy['facebook_caption']}\n\n{hashtag_str}")

    log.info("Publishing image post to Instagram")
    instagram.publish_image(post.image_path, f"{post.caption}\n\n{hashtag_str}")

    log.info("Publishing daily short to Instagram Reels")
    instagram.publish_reel(post.short_video_path, f"{post.caption}\n\n{hashtag_str}")

    log.info("Publishing daily short to YouTube Shorts")
    youtube.upload_video(
        post.short_video_path,
        title=copy["youtube_short_title"],
        description=f"{copy['youtube_short_description']}\n\n{hashtag_str}",
        tags=[h.lstrip("#") for h in post.hashtags],
        is_short=True,
    )

    if post.weekly_video_path:
        log.info("Publishing weekly showcase video to YouTube")
        youtube.upload_video(
            post.weekly_video_path,
            title="Safar Car Perfumes — Weekly Fragrance Showcase",
            description=(
                "This week's tour through all 5 Safar fragrances and the "
                f"signature diamond-cut bottle.\n\n{hashtag_str}"
            ),
            tags=[h.lstrip("#") for h in post.hashtags],
            is_short=False,
        )


def compare_providers() -> Path:
    """Generates today's caption from every configured provider (OpenAI,
    Anthropic) without touching images/video/publishing, so you can eyeball
    quality and cost before picking a default. Nothing here posts anywhere.
    """
    today = date.today()
    day_dir = OUTPUT_DIR / today.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    catalog = load_catalog()
    fragrance = catalog.fragrance_for_weekday(today.weekday())
    theme = pick_theme()
    log.info("Comparing providers for %s | theme: %s", fragrance.name, theme.id)

    results = generate_post_copy_all(fragrance, theme, catalog.bottle_design)

    out_path = day_dir / "compare_providers.json"
    out_path.write_text(json.dumps(results, indent=2))

    for name, result in results.items():
        print(f"\n{'=' * 20} {name} {'=' * 20}")
        print(json.dumps(result, indent=2))

    print(f"\nSaved comparison to {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Safar daily content agent")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Actually publish to Facebook/Instagram/YouTube. Without this flag "
        "(or with DRY_RUN=true in .env) the agent only generates assets locally.",
    )
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS),
        default=None,
        help="Override TEXT_PROVIDER from .env for this run (openai or anthropic).",
    )
    parser.add_argument(
        "--compare-providers",
        action="store_true",
        help="Generate today's caption from every provider and print/save them "
        "side by side. Skips image/video generation and never publishes.",
    )
    parser.add_argument(
        "--copy-file",
        type=Path,
        default=None,
        help="Path to pre-written copy JSON (see scripts/print_today_brief.py "
        "and the safar-daily-post skill) instead of calling an LLM provider. "
        "Must include a top-level \"_meta\": {\"theme_id\": \"...\"}.",
    )
    parser.add_argument(
        "--image-file",
        type=Path,
        default=None,
        help="Path to a pre-rendered hero image (e.g. a Claude-designed cartoon "
        "scene from scripts/render_scene.py) instead of compositing one from "
        "your uploaded product photo.",
    )
    args = parser.parse_args()

    if args.compare_providers:
        compare_providers()
        return

    publish = args.publish and not settings.dry_run
    if args.publish and settings.dry_run:
        log.warning("DRY_RUN=true in .env is overriding --publish; no real posts will be made.")

    copy_override = json.loads(args.copy_file.read_text()) if args.copy_file else None
    run(
        publish=publish,
        provider=args.provider,
        copy_override=copy_override,
        image_override=args.image_file,
    )


if __name__ == "__main__":
    main()
