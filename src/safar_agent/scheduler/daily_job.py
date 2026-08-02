"""The daily entrypoint. Run via:

    python -m safar_agent.scheduler.daily_job            # dry run (default, safe)
    python -m safar_agent.scheduler.daily_job --publish   # actually posts

Each run:
  - picks today's fragrance-of-the-day (Mon-Fri rotate the 5 fragrances,
    weekends spotlight the diamond bottle) and an unused-recently theme
  - generates caption/hashtags/on-image text/video narration via GPT
  - composes a feed image from your uploaded product photo
  - always builds a ~15s vertical short (voiceover + captions)
  - on WEEKLY_VIDEO_WEEKDAY, also builds the long-form YouTube showcase video
  - publishes to Facebook + Instagram (image) and Instagram Reels + YouTube
    Shorts (video), plus YouTube long-form on the weekly day
  - logs everything to data/history.json
"""
from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

from safar_agent.config import OUTPUT_DIR, settings
from safar_agent.content.idea_generator import generate_post_copy
from safar_agent.content.image_generator import compose_hero_image
from safar_agent.content.product_catalog import load_catalog
from safar_agent.models import GeneratedPost
from safar_agent.publishers import facebook, instagram, youtube
from safar_agent.storage.history import pick_theme, record_post, today_str
from safar_agent.video.daily_short import generate_daily_short
from safar_agent.video.voiceover import generate_voiceover
from safar_agent.video.weekly_video import generate_weekly_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("daily_job")

BG_MUSIC = Path("assets/audio/bg_music.mp3")


def run(publish: bool) -> GeneratedPost:
    today = date.today()
    weekday = today.weekday()
    day_dir = OUTPUT_DIR / today.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    catalog = load_catalog()
    fragrance = catalog.fragrance_for_weekday(weekday)
    theme = pick_theme()
    log.info("Today's fragrance: %s | theme: %s", fragrance.name, theme.id)

    copy = generate_post_copy(fragrance, theme, catalog.bottle_design)

    image_path = compose_hero_image(fragrance, copy["on_image_text"], day_dir / "post.jpg")

    voiceover_path = None
    try:
        voiceover_path = generate_voiceover(copy["video_narration"], day_dir / "voiceover.mp3")
    except Exception:
        log.warning("Voiceover generation failed, continuing without narration", exc_info=True)

    bg_music = BG_MUSIC if BG_MUSIC.exists() else None
    short_path = generate_daily_short(
        image_path=image_path,
        caption_text=copy["on_image_text"],
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Safar daily content agent")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Actually publish to Facebook/Instagram/YouTube. Without this flag "
        "(or with DRY_RUN=true in .env) the agent only generates assets locally.",
    )
    args = parser.parse_args()

    publish = args.publish and not settings.dry_run
    if args.publish and settings.dry_run:
        log.warning("DRY_RUN=true in .env is overriding --publish; no real posts will be made.")

    run(publish=publish)


if __name__ == "__main__":
    main()
