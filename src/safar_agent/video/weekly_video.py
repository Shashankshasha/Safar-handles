"""Builds the once-a-week long-form YouTube video: a landscape showcase
slideshow across all 5 fragrances (+ the diamond bottle hero), with narration.
"""
from __future__ import annotations

from pathlib import Path

from safar_agent.video.ffmpeg_utils import build_audio_track, run_ffmpeg, write_drawtext_file

WEEKLY_SIZE = (1920, 1080)
SEGMENT_DURATION = 8  # seconds per fragrance


def generate_weekly_video(
    segments: list[tuple[Path, str]],  # (image_path, lower_third_text) per fragrance
    output_path: Path,
    narration_path: Path | None = None,
    bg_music_path: Path | None = None,
    segment_duration: int = SEGMENT_DURATION,
) -> Path:
    if not segments:
        raise ValueError("Need at least one (image, text) segment for the weekly video.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = WEEKLY_SIZE

    inputs: list[str] = []
    filter_parts: list[str] = []
    textfiles: list[Path] = []
    concat_labels: list[str] = []

    for idx, (image_path, text) in enumerate(segments):
        inputs += ["-loop", "1", "-t", str(segment_duration), "-i", str(image_path)]
        textfile = write_drawtext_file(text)
        textfiles.append(textfile)
        filter_parts.append(
            f"[{idx}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"drawtext=textfile='{textfile}':fontsize=48:fontcolor=white:"
            f"box=1:boxcolor=black@0.5:boxborderw=20:x=(w-text_w)/2:y=h-160,"
            f"format=yuv420p[v{idx}]"
        )
        concat_labels.append(f"[v{idx}]")

    filter_parts.append(f"{''.join(concat_labels)}concat=n={len(segments)}:v=1:a=0[vout]")

    total_duration = segment_duration * len(segments)
    extra_inputs, audio_filter, audio_map = build_audio_track(
        narration_path, bg_music_path, first_input_index=len(segments)
    )
    inputs += extra_inputs
    if audio_filter:
        filter_parts.append(audio_filter)

    try:
        args = [
            *inputs,
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[vout]",
            "-map",
            audio_map,
            "-t",
            str(total_duration),
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
        for tf in textfiles:
            tf.unlink(missing_ok=True)

    return output_path
