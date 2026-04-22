from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


@dataclass
class PublicVenueCard:
    """
    Compact shared contract for list/map/home cards.

    `is_saved` is null when the caller is unauthenticated; boolean when
    save-state enrichment ran for an authenticated user.

    `open_now` remains null in Stage 2; centralized open-now computation
    will populate this in a single shared service (see `OPEN_NOW` integration
    in venue read services).
    """

    id: str
    name: str
    venue_type: str | None
    suburb: str
    address_short: str
    latitude: float
    longitude: float
    hero_photo_url: str | None
    open_now: bool | None = None
    distance_m: float | None = None
    open_now_uncomputed: bool = True
    feature_badges: list[str] = field(default_factory=list)
    specials_summary: list[str] = field(default_factory=list)
    events_summary: list[str] = field(default_factory=list)
    drink_highlights: list[str] = field(default_factory=list)
    is_saved: bool | None = None


def public_venue_card_to_dict(c: PublicVenueCard) -> PublicVenueCardDict:
    return {
        "id": c.id,
        "name": c.name,
        "venue_type": c.venue_type,
        "suburb": c.suburb,
        "address_short": c.address_short,
        "latitude": c.latitude,
        "longitude": c.longitude,
        "hero_photo_url": c.hero_photo_url,
        "open_now": c.open_now,
        "open_now_uncomputed": c.open_now_uncomputed,
        "distance_m": c.distance_m,
        "feature_badges": list(c.feature_badges),
        "specials_summary": list(c.specials_summary),
        "events_summary": list(c.events_summary),
        "drink_highlights": list(c.drink_highlights),
        "is_saved": c.is_saved,
    }


class PublicVenueCardDict(TypedDict, total=True):
    id: str
    name: str
    venue_type: str | None
    suburb: str
    address_short: str
    latitude: float
    longitude: float
    hero_photo_url: str | None
    open_now: bool | None
    open_now_uncomputed: bool
    distance_m: float | None
    feature_badges: list[str]
    specials_summary: list[str]
    events_summary: list[str]
    drink_highlights: list[str]
    is_saved: bool | None


def as_json_ready(obj: PublicVenueCard) -> dict[str, Any]:
    return public_venue_card_to_dict(obj)
