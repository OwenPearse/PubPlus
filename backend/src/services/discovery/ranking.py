from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from common.geo.haversine import distance_m

from services.discovery.filters import DiscoveryMvpFilters, DiscoveryMode
from services.discovery.open_now import OpenNowResult


@dataclass
class RankComponents:
    """
    Human-readable, additive ingredients for `rank_score` (0..+inf, higher is better).
    """

    geographic: float = 0.0
    viewport: float = 0.0
    open_now: float = 0.0
    special_match: float = 0.0
    feature_match: float = 0.0
    drink_match: float = 0.0
    quality_hint: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    def as_float(self) -> float:
        return float(
            self.geographic
            + self.viewport
            + self.open_now
            + self.special_match
            + self.feature_match
            + self.drink_match
            + self.quality_hint
        )


def score_rank(
    *,
    mode: DiscoveryMode,
    filters: DiscoveryMvpFilters,
    distance_m_value: float | None,
    venue_lat: float,
    venue_lon: float,
    open_result: OpenNowResult | None,
    meal_matched: int,
    feature_matched: int,
    drink_matched: int,
    has_description: bool,
) -> tuple[float, RankComponents]:
    rc = RankComponents()

    if filters.has_radius() and distance_m_value is not None:
        w = 5000.0
        rc.geographic = max(0.0, 1.0 - min(distance_m_value, w) / w)

    if mode == DiscoveryMode.MAP and filters.has_viewport():
        assert filters.south is not None and filters.north is not None
        assert filters.west is not None and filters.east is not None
        c_lat = (float(filters.south) + float(filters.north)) / 2.0
        c_lon = (float(filters.west) + float(filters.east)) / 2.0
        d = distance_m(c_lat, c_lon, float(venue_lat), float(venue_lon))
        wv = 5000.0
        rc.viewport = max(0.0, 1.0 - min(d, wv) / wv)

    if open_result and open_result.public_open_now is True and not open_result.public_open_now_uncomputed:
        rc.open_now = 0.3

    rc.special_match = min(0.25, 0.1 * max(0, int(meal_matched)))
    rc.drink_match = min(0.2, 0.05 * max(0, int(drink_matched)))
    rc.feature_match = min(0.2, 0.05 * max(0, int(feature_matched)))

    if has_description:
        rc.quality_hint = 0.02

    rc.details = {
        "distance_m": distance_m_value,
        "mode": mode.value,
    }
    return (rc.as_float(), rc)


def apply_open_now_to_card(venue_card, result: OpenNowResult):
    from apps.venues.public_read.card import PublicVenueCard

    if not isinstance(venue_card, PublicVenueCard):
        raise TypeError("expected PublicVenueCard")
    return replace(
        venue_card,
        open_now=result.public_open_now,
        open_now_uncomputed=result.public_open_now_uncomputed,
    )
