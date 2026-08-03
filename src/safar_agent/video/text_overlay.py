"""Renders caption text as a transparent PNG, composited onto video via
ffmpeg's `overlay` filter — deliberately avoids ffmpeg's `drawtext` filter,
which needs a libfreetype/fontconfig-enabled build that many common ffmpeg
installs (including Homebrew's default `ffmpeg` formula) don't include.
`overlay` is a core filter present in every standard ffmpeg build.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from safar_agent.fonts import bold_font


def render_caption_overlay(
    text: str,
    size: tuple[int, int],
    output_path: Path,
    font_size: int = 54,
    box_y_from_bottom: int = 340,
) -> Path:
    width, height = size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    if not text.strip():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        overlay.save(output_path)
        return output_path

    draw = ImageDraw.Draw(overlay)
    font = bold_font(font_size)

    lines = text.split("\n")
    line_heights = []
    line_widths = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])

    line_gap = 10
    text_block_h = sum(line_heights) + line_gap * (len(lines) - 1)
    pad_x, pad_y = 24, 16

    box_bottom = height - box_y_from_bottom + text_block_h // 2 + pad_y
    box_top = box_bottom - text_block_h - pad_y * 2
    draw.rectangle([0, box_top, width, box_bottom], fill=(0, 0, 0, 140))

    y = box_top + pad_y
    for line, lw, lh in zip(lines, line_widths, line_heights):
        x = (width - lw) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += lh + line_gap

    output_path.parent.mkdir(parents=True, exist_ok=True)
    overlay.save(output_path)
    return output_path
