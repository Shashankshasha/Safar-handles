"""Cross-platform bold font lookup for Pillow text rendering.

PIL.ImageFont.load_default() is a tiny bitmap font — fine for nothing we
generate here. This checks a handful of paths bold fonts commonly live at on
Linux (CI/servers), macOS, and Windows, so generated images/video captions
look the same regardless of which machine renders them.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

_CANDIDATE_BOLD_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux (most distros/CI)
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
    "/Library/Fonts/Arial Bold.ttf",  # macOS (older/manual installs)
    "/System/Library/Fonts/Helvetica.ttc",  # macOS fallback (not bold, but present)
    "C:\\Windows\\Fonts\\arialbd.ttf",  # Windows
]


def bold_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _CANDIDATE_BOLD_FONTS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()
