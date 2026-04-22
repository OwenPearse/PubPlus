from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from services.discovery.errors import DiscoveryFilterError


class DiscoveryMode(str, Enum):
    """
    - `list`: list/search (radius, suburb) constraints
    - `map`: viewport (north/south/east/west) is primary; still uses shared filter semantics
    """

    LIST = "list"
    MAP = "map"


# Allowed structured special kinds (migration 0021) for `meal_specials` filter
MEAL_STRUCT_KINDS = frozenset(
    {
        "meal_special",
    }
)


@dataclass(frozen=True)
class DiscoveryMvpFilters:
    """
    All optional at construction; `validate` enforces inter-field rules and mode.
    """

    suburb: str | None = None
    lat: float | None = None
    lng: float | None = None
    radius_m: float | None = None
    north: float | None = None
    south: float | None = None
    east: float | None = None
    west: float | None = None
    open_now: bool | None = None
    meal_specials: list[str] = field(default_factory=list)
    drink_types: list[str] = field(
        default_factory=list
    )  # `beverage_product_id` (uuid string)
    venue_features: list[str] = field(default_factory=list)  # attribute `stable_key`
    require_published_events: bool = False
    q: str | None = None
    # optional query hook — disabled until FTS exists (rejects if set)
    limit: int = 50

    def validate(self, mode: DiscoveryMode) -> None:
        v = (self.south, self.north, self.west, self.east)
        v_count = sum(1 for x in v if x is not None)
        if v_count not in (0, 4):
            raise DiscoveryFilterError(
                "viewport_incomplete",
                "viewport requires all of north, south, east, and west, or none",
            )
        if v_count == 4:
            s, n, w, e = (self.south, self.north, self.west, self.east)  # type: ignore[assignment]
            if s is None or n is None or w is None or e is None:  # pragma: no cover
                raise DiscoveryFilterError("viewport_incomplete", "viewport incomplete")
            if s >= n:
                raise DiscoveryFilterError(
                    "invalid_viewport", "south must be < north in this MVP implementation"
                )
            if w >= e:
                raise DiscoveryFilterError(
                    "invalid_viewport", "west must be < east (no dateline / wrap in MVP)"
                )
            if s < -90 or n > 90 or w < -180 or e > 180:
                raise DiscoveryFilterError("invalid_viewport", "lat/lon out of WGS84 range")

        loc = (self.lat, self.lng, self.radius_m)
        loc_count = sum(1 for x in loc if x is not None)
        if loc_count not in (0, 3):
            raise DiscoveryFilterError(
                "location_incomplete",
                "location filters require all of lat, lng, and radius_m, or none",
            )
        if v_count == 4 and loc_count == 3:
            raise DiscoveryFilterError(
                "location_with_viewport",
                "do not combine radius-based search with a viewport; choose one",
            )
        if self.q is not None and self.q.strip() != "":
            raise DiscoveryFilterError(
                "q_unsupported",
                "text query (q) is not wired to published content search in this tranche; omit q",
            )
        if self.require_published_events:
            raise DiscoveryFilterError(
                "events_unavailable",
                "no published public event catalog is available for this filter in the current schema",
            )
        if self.open_now is not None and self.open_now is False:
            raise DiscoveryFilterError(
                "open_now_false_unsupported",
                "open_now filter supports true or omit; false is not implemented for MVP",
            )
        for k in self.meal_specials:
            if k not in MEAL_STRUCT_KINDS:
                raise DiscoveryFilterError(
                    "invalid_meal_specials_kind",
                    f"unknown meal_specials kind {k!r} (MVP: {sorted(MEAL_STRUCT_KINDS)})",
                )
        for uid in self.drink_types:
            try:
                UUID(str(uid).strip())
            except (ValueError, TypeError) as e:
                raise DiscoveryFilterError(
                    "invalid_drink_type_id",
                    f"drink_types entries must be UUID beverage_product_id values, got {uid!r}",
                ) from e
        for fk in self.venue_features:
            if not fk or not str(fk).strip():
                raise DiscoveryFilterError("empty_feature", "empty venue feature stable_key")
        if self.limit < 1 or self.limit > 200:
            raise DiscoveryFilterError("invalid_limit", "limit must be between 1 and 200")

        if mode == DiscoveryMode.MAP and v_count != 4:
            raise DiscoveryFilterError("map_needs_viewport", "map mode requires a full viewport (north, south, east, west)")

        if mode == DiscoveryMode.LIST and v_count == 4:
            raise DiscoveryFilterError("list_uses_not_viewport", "use DiscoveryMode.MAP for viewport-bounded results")

    def has_viewport(self) -> bool:
        return all(x is not None for x in (self.south, self.north, self.west, self.east))

    def has_radius(self) -> bool:
        return all(x is not None for x in (self.lat, self.lng, self.radius_m))
