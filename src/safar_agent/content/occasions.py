"""Special-occasion calendar (data/occasions.yaml) — festival/national-day
posts that override the normal random theme rotation for that one day, so
daily automation naturally does the right thing on Independence Day, Diwali,
etc. without anyone needing to remember and intervene manually.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from safar_agent.config import DATA_DIR

OCCASIONS_YAML = DATA_DIR / "occasions.yaml"


@dataclass(frozen=True)
class Occasion:
    name: str
    hint: str


def load_occasions(path: Path = OCCASIONS_YAML) -> dict[str, Occasion]:
    """Keyed by MM-DD."""
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text()) or {}
    return {
        entry["date"]: Occasion(name=entry["name"], hint=entry["hint"].strip())
        for entry in raw.get("occasions", [])
    }


def occasion_for_date(day: date) -> Occasion | None:
    return load_occasions().get(day.strftime("%m-%d"))
