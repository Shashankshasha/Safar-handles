from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Fragrance:
    id: str
    name: str
    tagline: str
    scent_notes: list[str]
    liquid_color: str
    image_dir: Path
    weekday: int | None = None  # 0=Mon ... 6=Sun; None for the weekend spotlight product

    def reference_images(self) -> list[Path]:
        if not self.image_dir.exists():
            return []
        exts = {".jpg", ".jpeg", ".png", ".webp"}
        return sorted(p for p in self.image_dir.iterdir() if p.suffix.lower() in exts)


@dataclass(frozen=True)
class ProductCatalog:
    brand: str
    bottle_design: str
    weekday_fragrances: dict[int, Fragrance]  # keyed 0-4, Mon-Fri
    weekend_spotlight: Fragrance

    def fragrance_for_weekday(self, weekday: int) -> Fragrance:
        """weekday: 0=Mon ... 6=Sun (Python's date.weekday())."""
        if weekday in self.weekday_fragrances:
            return self.weekday_fragrances[weekday]
        return self.weekend_spotlight

    def all_fragrances(self) -> list[Fragrance]:
        return [*self.weekday_fragrances.values(), self.weekend_spotlight]


@dataclass
class GeneratedPost:
    date: str
    fragrance_id: str
    theme_id: str
    caption: str
    hashtags: list[str] = field(default_factory=list)
    image_path: Path | None = None
    short_video_path: Path | None = None
    weekly_video_path: Path | None = None
