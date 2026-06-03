"""
Public reference payload for Search filter chips.

Values must match what ``DiscoveryMvpFilters`` accepts on ``/api/v1/search/venues``.
"""

from __future__ import annotations

from typing import Any

from django.db import connection

from services.discovery.filters import MEAL_STRUCT_KINDS

# Optional UI grouping for boolean venue features (not stored in schema).
_VENUE_FEATURE_GROUPS: dict[str, str] = {
    "beer_garden": "spaces",
    "rooftop": "spaces",
    "live_music": "entertainment",
    "dog_friendly": "accessibility",
    "sports_screens": "entertainment",
    "pool_table": "entertainment",
    "late_night": "hours",
    "vegan_options": "food",
    "serves_food": "food",
}

_MEAL_SPECIAL_LABELS: dict[str, str] = {
    "meal_special": "Meal specials tonight",
}


def _load_venue_features() -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT stable_key, display_label
            FROM public.venue_attribute_definition
            WHERE is_discovery_driving = true
              AND value_shape = 'boolean'
            ORDER BY display_label ASC, stable_key ASC
            """
        )
        rows = cursor.fetchall()
    return [
        {
            "key": stable_key,
            "label": display_label,
            "group": _VENUE_FEATURE_GROUPS.get(stable_key),
        }
        for stable_key, display_label in rows
    ]


def _load_drink_types() -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id::text, display_name
            FROM public.beverage_product
            ORDER BY display_name ASC, id ASC
            """
        )
        rows = cursor.fetchall()
    return [{"id": product_id, "label": display_name} for product_id, display_name in rows]


def _load_meal_specials() -> list[dict[str, Any]]:
    return [
        {
            "key": kind,
            "label": _MEAL_SPECIAL_LABELS.get(kind, kind.replace("_", " ").title()),
        }
        for kind in sorted(MEAL_STRUCT_KINDS)
    ]


def build_search_filter_reference() -> dict[str, Any]:
    return {
        "venue_features": _load_venue_features(),
        "drink_types": _load_drink_types(),
        "meal_specials": _load_meal_specials(),
        "event_filters": [],
    }
