from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, replace

from apps.venues.public_read.card import PublicVenueCard, public_venue_card_to_dict
from apps.venues.services.published_venue_read import PublishedVenueReadBundle
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


def _run_section(
    filters: DiscoveryMvpFilters,
    *,
    bundle_cache: dict[str, PublishedVenueReadBundle],
) -> list[PublicVenueCard]:
    result = run_discovery(DiscoveryMode.LIST, filters, bundle_cache=bundle_cache)
    return [hit.card for hit in result.hits]


def _apply_save_state_to_sections(
    section_items: list[tuple[str, str, list[PublicVenueCard]]],
    *,
    auth: AuthContext | None,
) -> list[HomeFeedSection]:
    if auth is None:
        return [
            HomeFeedSection(id=section_id, title=title, items=items)
            for section_id, title, items in section_items
        ]

    from apps.venues.services.save_enrichment import apply_save_to_cards

    all_cards = [card for _, _, items in section_items for card in items]
    enriched = apply_save_to_cards(all_cards, auth=auth)
    cursor = 0
    sections: list[HomeFeedSection] = []
    for section_id, title, items in section_items:
        count = len(items)
        sections.append(
            HomeFeedSection(
                id=section_id,
                title=title,
                items=enriched[cursor : cursor + count],
            )
        )
        cursor += count
    return sections


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

    bundle_cache: dict[str, PublishedVenueReadBundle] = {}
    section_items: list[tuple[str, str, list[PublicVenueCard]]] = []
    for section_id, title, filters in section_specs:
        section_started = time.perf_counter()
        items = _run_section(filters, bundle_cache=bundle_cache)
        elapsed_ms = (time.perf_counter() - section_started) * 1000
        logger.info(
            "home_feed section=%s venues=%s bundle_cache=%s elapsed_ms=%.0f",
            section_id,
            len(items),
            len(bundle_cache),
            elapsed_ms,
        )
        section_items.append((section_id, title, items))

    sections = _apply_save_state_to_sections(section_items, auth=auth)

    logger.info(
        "home_feed done sections=%s unique_bundles=%s elapsed_ms=%.0f",
        len(sections),
        len(bundle_cache),
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
