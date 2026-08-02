"""Theme bank the idea generator rotates through so posts don't feel repetitive.

Each theme is a creative angle, not a finished caption — idea_generator.py
feeds the theme + the fragrance-of-the-day into GPT to write the actual copy.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    id: str
    category: str
    hint: str


THEMES: list[Theme] = [
    Theme(
        "action-figure-diorama",
        "comedy",
        "Stage the Safar bottle like a collectible action figure in a tiny diorama "
        "next to a toy/model car — dramatic hero lighting, blister-pack-style caption "
        "('Safar Oud Voyage, Series 1 — Every Drive Included').",
    ),
    Theme(
        "movie-parody",
        "comedy",
        "Parody a famous movie poster or scene using the bottle as the 'star' "
        "(spy thriller, western showdown, superhero origin) themed around car culture.",
    ),
    Theme(
        "before-after-smell",
        "relatable",
        "Split-panel 'before Safar / after Safar' gag about a smelly car (gym bag, "
        "fast food, wet dog) getting rescued.",
    ),
    Theme(
        "pov-driver",
        "relatable",
        "POV caption from the driver's seat — a funny inner monologue about traffic, "
        "red lights, or road rage that Safar's scent calms down.",
    ),
    Theme(
        "asmr-unboxing",
        "aesthetic",
        "Slow, satisfying unboxing / close-up facets-catching-light moment on the "
        "diamond-cut bottle — minimal caption, let the visual do the work.",
    ),
    Theme(
        "road-trip-story",
        "storytelling",
        "Mini story format: 'Day 1 of our road trip...' with the bottle as a travel "
        "companion character.",
    ),
    Theme(
        "meme-format",
        "comedy",
        "Use a well-known meme template/format (drake, two buttons, expanding brain) "
        "reframed around choosing Safar over a generic tree air freshener.",
    ),
    Theme(
        "festival-seasonal",
        "seasonal",
        "Tie the fragrance to the current season/festival/long-weekend driving "
        "occasion in India (monsoon road trips, festive homecoming drives, etc).",
    ),
    Theme(
        "car-guy-humor",
        "comedy",
        "In-jokes for car enthusiasts — detailing culture, 'new car smell' obsession, "
        "modding community banter — with Safar as the punchline upgrade.",
    ),
    Theme(
        "diamond-bottle-glamour",
        "aesthetic",
        "Pure product glamour shot celebrating the diamond-cut bottle design itself, "
        "like a jewellery ad, luxury tone.",
    ),
    Theme(
        "scent-notes-explainer",
        "educational",
        "Quick, punchy breakdown of the fragrance's top/mid/base notes and who it "
        "suits, styled like a perfumer's tasting note card.",
    ),
    Theme(
        "customer-review-style",
        "social-proof",
        "Written like a 5-star review or testimonial quote card from a happy driver.",
    ),
    Theme(
        "day-in-life-of-bottle",
        "comedy",
        "A cheeky 'day in the life' narrated by the bottle itself, riding along on "
        "the dashboard through a normal day.",
    ),
    Theme(
        "car-detailing-combo",
        "lifestyle",
        "Pair the fragrance with a full car-detailing/clean-car aesthetic — the "
        "'finishing touch' after a wash and vacuum.",
    ),
    Theme(
        "traffic-jam-relief",
        "relatable",
        "Comedic take on surviving a brutal traffic jam, with Safar as the one thing "
        "keeping sanity intact.",
    ),
    Theme(
        "gift-idea",
        "seasonal",
        "Position the bottle as a thoughtful gift for a new car owner, dad, or "
        "car-loving friend.",
    ),
    Theme(
        "monsoon-freshness",
        "seasonal",
        "Damp-weather musty-car problem solved by Safar — relatable monsoon humor.",
    ),
    Theme(
        "night-drive-vibes",
        "aesthetic",
        "Moody night-drive aesthetic — city lights, dashboard glow, bottle silhouette, "
        "chill/cinematic caption.",
    ),
    Theme(
        "dashcam-vlog",
        "storytelling",
        "Framed like a dashcam/vlog clip caption — 'caught on cam: the moment my car "
        "started smelling amazing'.",
    ),
    Theme(
        "guess-the-scent-challenge",
        "engagement",
        "Interactive challenge inviting followers to guess the scent notes or vote "
        "for their favourite fragrance in the comments.",
    ),
]


def theme_by_id(theme_id: str) -> Theme:
    for theme in THEMES:
        if theme.id == theme_id:
            return theme
    raise KeyError(f"Unknown theme id: {theme_id}")
