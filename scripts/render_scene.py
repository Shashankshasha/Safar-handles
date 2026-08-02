#!/usr/bin/env python3
"""Renders an HTML file to a PNG via headless Chromium (Playwright).

Used by the safar-daily-post skill so Claude can design a cartoon/illustrated
scene as HTML+CSS and turn it into a postable image for free — no
image-generation API call needed.

One-time setup (in addition to `pip install -e .`):
    playwright install chromium
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def render_html(
    html_path: Path,
    output_path: Path,
    width: int = 1080,
    height: int = 1350,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    launch_kwargs: dict = {}
    # Escape hatch for environments where Chromium lives at a fixed,
    # non-standard path (e.g. a pre-baked container image) instead of
    # wherever `playwright install` put it.
    executable = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if executable:
        launch_kwargs["executable_path"] = executable
        launch_kwargs["args"] = ["--no-sandbox"]

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"file://{html_path.resolve()}")
        page.screenshot(path=str(output_path))
        browser.close()

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an HTML scene to a PNG image")
    parser.add_argument("html_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1350)
    args = parser.parse_args()

    render_html(args.html_path, args.output_path, args.width, args.height)
    print(f"Rendered {args.output_path}")


if __name__ == "__main__":
    main()
