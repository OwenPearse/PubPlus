from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, replace

from apps.venues.public_read.card import PublicVenueCard, public_venue_card_to_dict
from common.auth.context import AuthContext
from services.discovery import (
    MEAL_STRUCT_KINDS,
    DiscoveryMode,
    DiscoveryMvpFilters,
    run_discovery,
)

logger = logging.getLogger(__name__)

# Default per section — see api.v1.home.views.HOME_FEED_DEFAULT_LIMIT (kept in sync).
HOME_FEED_DEFAULT_LIMIT = 3


@dataclass(frozen=True)
class HomeFeedQuery:
    lat: float | None = None
    lng: float | None = None
    suburb: str | None = None
    radius_m: float = 5000.0
    limit: int = HOME_FEED_DEFAULT_LIMIT


@dataclass(frozen=True)
class HomeFeedSection:
    id: str
    title: str
    items: list[PublicVenueCard] = field(default_factory=list)


@dataclass(frozen=True)
class HomeFeedResult:
    sections: list[HomeFeedSection]


def _base_filters(q: HomeFeedQuery) -> DiscoveryMvpFilters:
    return DiscoveryMvpFilters(
        suburb=q.suburb,
        lat=q.lat,
        lng=q.lng,
        radius_m=q.radius_m if q.lat is not None and q.lng is not None else None,
        limit=q.limit,
    )


def _run_section(filters: DiscoveryMvpFilters) -> list[PublicVenueCard]:
    result = run_discovery(DiscoveryMode.LIST, filters)
    return [hit.card for hit in result.hits]


def _with_save_state(
    cards: list[PublicVenueCard], *, auth: AuthContext | None
) -> list[PublicVenueCard]:
    if auth is None:
        return cards
    from apps.venues.services.save_enrichment import apply_save_to_card

    return [
        apply_save_to_card(card, auth=auth, venue_id=card.id)
        for card in cards
    ]


def run_home_feed(
    query: HomeFeedQuery, *, auth: AuthContext | None = None
) -> HomeFeedResult:
    started = time.perf_counter()
    logger.info(
        "home_feed start limit=%s suburb=%s has_coords=%s",
        query.limit,
        query.suburb,
        query.lat is not None and query.lng is not None,
    )

    section_specs: list[tuple[str, str, DiscoveryMvpFilters]] = [
        ("nearby", "Nearby", _base_filters(query)),
        ("open_now", "Open now", replace(_base_filters(query), open_now=True)),
        (
            "specials_tonight",
            "Specials tonight",
            replace(_base_filters(query), meal_specials=sorted(MEAL_STRUCT_KINDS)),
        ),
    ]

    sections: list[HomeFeedSection] = []
    for section_id, title, filters in section_specs:
        section_started = time.perf_counter()
        items = _with_save_state(_run_section(filters), auth=auth)
        elapsed_ms = (time.perf_counter() - section_started) * 1000
        logger.info(
            "home_feed section=%s venues=%s elapsed_ms=%.0f",
            section_id,
            len(items),
            elapsed_ms,
        )
        sections.append(HomeFeedSection(id=section_id, title=title, items=items))

    logger.info(
        "home_feed done sections=%s elapsed_ms=%.0f",
        len(sections),
        (time.perf_counter() - started) * 1000,
    )
    return HomeFeedResult(sections=sections)


def home_feed_to_dict(home_feed: HomeFeedResult) -> dict:
    return {
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "venues": [public_venue_card_to_dict(card) for card in s.items],
            }
            for s in home_feed.sections
        ]
    }
