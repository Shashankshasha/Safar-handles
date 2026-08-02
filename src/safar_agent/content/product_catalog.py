from __future__ import annotations

from pathlib import Path

import yaml

from safar_agent.config import PRODUCTS_YAML, REPO_ROOT
from safar_agent.models import Fragrance, ProductCatalog


def _fragrance_from_dict(d: dict) -> Fragrance:
    return Fragrance(
        id=d["id"],
        name=d["name"],
        tagline=d["tagline"],
        scent_notes=list(d.get("scent_notes", [])),
        liquid_color=d.get("liquid_color", ""),
        image_dir=REPO_ROOT / d["image_dir"],
        weekday=d.get("weekday"),
    )


def load_catalog(path: Path = PRODUCTS_YAML) -> ProductCatalog:
    raw = yaml.safe_load(path.read_text())

    weekday_fragrances: dict[int, Fragrance] = {}
    for entry in raw["fragrances"]:
        fragrance = _fragrance_from_dict(entry)
        if fragrance.weekday is None:
            raise ValueError(f"Fragrance {fragrance.id!r} is missing a weekday assignment")
        weekday_fragrances[fragrance.weekday] = fragrance

    weekend_spotlight = _fragrance_from_dict(raw["weekend_spotlight"])

    return ProductCatalog(
        brand=raw["brand"],
        maker=raw.get("maker", raw["brand"]),
        tagline=raw.get("tagline", ""),
        bottle_design=raw["bottle_design"].strip(),
        weekday_fragrances=weekday_fragrances,
        weekend_spotlight=weekend_spotlight,
    )
