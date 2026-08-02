"""Tiny JSON-backed log of past posts.

Used for two things:
  1. picking a theme that wasn't used in the last N days (variety)
  2. an audit trail of what got posted where, for debugging/reporting
"""
from __future__ import annotations

import json
import random
from dataclasses import asdict
from datetime import date

from safar_agent.config import HISTORY_PATH
from safar_agent.content.themes import THEMES
from safar_agent.models import GeneratedPost

RECENT_THEME_WINDOW = 7  # avoid repeating a theme used in the last week


def _load_raw() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    return json.loads(HISTORY_PATH.read_text())


def _save_raw(entries: list[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(entries, indent=2, default=str))


RECENT_VISUAL_NOTE_WINDOW = 10


def recent_theme_ids(window: int = RECENT_THEME_WINDOW) -> set[str]:
    entries = _load_raw()[-window:]
    return {e["theme_id"] for e in entries if "theme_id" in e}


def recent_visual_notes(window: int = RECENT_VISUAL_NOTE_WINDOW) -> list[str]:
    """Freeform notes on recent posts' visual composition/style, oldest first
    — so a human or an LLM designing today's scene can deliberately avoid
    repeating a layout/palette that was just used.
    """
    entries = _load_raw()[-window:]
    return [e["visual_note"] for e in entries if e.get("visual_note")]


def pick_theme(exclude: set[str] | None = None):
    """Pick a random theme, avoiding recently-used ones when possible."""
    exclude = exclude or recent_theme_ids()
    candidates = [t for t in THEMES if t.id not in exclude]
    if not candidates:
        candidates = THEMES  # exhausted variety window, allow repeats
    return random.choice(candidates)


def record_post(post: GeneratedPost) -> None:
    entries = _load_raw()
    entry = asdict(post)
    for key in ("image_path", "short_video_path", "weekly_video_path"):
        if entry.get(key) is not None:
            entry[key] = str(entry[key])
    entries.append(entry)
    _save_raw(entries)


def today_str() -> str:
    return date.today().isoformat()
