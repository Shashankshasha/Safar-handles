"""Builds the daily vertical short (Instagram Reels / YouTube Shorts).

A slow Ken-Burns zoom on the product hero image, a caption composited near
the bottom via a Pillow-rendered overlay (see text_overlay.py — deliberately
not ffmpeg's drawtext filter, which needs a font-rendering build many ffmpeg
installs don't have), and an audio bed (voiceover and/or background music,
or silence).
"""
from __future__ import annotations

from pathlib import Path

from safar_agent.video.ffmpeg_utils import build_audio_track, run_ffmpeg
from safar_agent.video.text_overlay import render_caption_overlay

SHORT_SIZE = (1080, 1920)
DEFAULT_DURATION = 15
DEFAULT_FPS = 30


def generate_daily_short(
    image_path: Path,
    caption_text: str,
    output_path: Path,
    voiceover_path: Path | None = None,
    bg_music_path: Path | None = None,
    duration: int = DEFAULT_DURATION,
    fps: int = DEFAULT_FPS,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = SHORT_SIZE

    overlay_path = output_path.parent / f"{output_path.stem}_caption_overlay.png"
    render_caption_overlay(caption_text, SHORT_SIZE, overlay_path)

    video_filter = (
        f"[0:v]scale=-2:{height * 2},"
        f"zoompan=z='min(zoom+0.0012,1.4)':d={duration * fps}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps},"
        f"format=yuv420p[bg];"
        f"[bg][1:v]overlay=0:0[v]"
    )

    inputs = ["-loop", "1", "-i", str(image_path), "-loop", "1", "-i", str(overlay_path)]
    filter_complex_parts = [video_filter]

    extra_inputs, audio_filter, audio_map = build_audio_track(
        voiceover_path, bg_music_path, first_input_index=2
    )
    inputs += extra_inputs
    if audio_filter:
        filter_complex_parts.append(audio_filter)

    try:
        args = [
            *inputs,
            "-filter_complex",
            ";".join(filter_complex_parts),
            "-map",
            "[v]",
            "-map",
            audio_map,
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
        run_ffmpeg(args)
    finally:
        overlay_path.unlink(missing_ok=True)

    return output_path
