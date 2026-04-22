"""
Single shared discovery query for list + map. Reads published public truth only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db import connection

from apps.venues.services.published_venue_read import (
    load_published_venue_read_bundle,
    map_published_hours_uncertainty,
)
from apps.venues.services.venue_read_service import bundle_to_public_venue_card
from services.discovery.errors import DiscoveryError
from services.discovery.filters import (
    DiscoveryMvpFilters,
    DiscoveryMode,
    MEAL_STRUCT_KINDS,
)
from services.discovery.open_now import OpenNowResult, compute_open_now
from services.discovery.ranking import apply_open_now_to_card, score_rank


@dataclass(frozen=True)
class DiscoveryHit:
    """Intermediate result for shapers/serializers."""

    venue_id: str
    distance_m: float | None
    open_now: bool | None
    open_now_uncomputed: bool
    open_now_result: OpenNowResult
    rank_score: float
    rank_components: Any
    card: Any
    source_mode: str


@dataclass(frozen=True)
class DiscoveryResult:
    mode: str
    filters: DiscoveryMvpFilters
    at_utc: datetime
    hits: list[DiscoveryHit] = field(default_factory=list)
    prelimit_used: int = 0


_HAVER = """
(6371000.0 * 2.0 * asin(least(1.0, sqrt(
  greatest(0.0,
  power(sin((radians(vpm.latitude::float8) - radians(%s::float8)) / 2.0), 2.0)
  + cos(radians(%s::float8)) * cos(radians(vpm.latitude::float8))
    * power(sin((radians(vpm.longitude::float8) - radians(%s::float8)) / 2.0), 2.0)
))))) 
""".replace("\n", " ").strip()


def build_discovery_sql(
    _mode: DiscoveryMode, f: DiscoveryMvpFilters
) -> tuple[str, list[Any]]:
    p: list[Any] = []
    has_r = f.has_radius()
    if has_r:
        la, lo0 = float(f.lat or 0), float(f.lng or 0)
        dist_sel = f"{_HAVER} AS distance_m"
        p.extend([la, la, lo0])
    else:
        dist_sel = "NULL::float8 AS distance_m"

    select = f"""
SELECT
  v.id::text,
  (EXISTS (SELECT 1 FROM public.venue_published_descriptive_copy dc
           WHERE dc.venue_id = v.id)) as has_desc,
  vpp.display_name,
  l.name as suburb_name,
  vpl.country_code::text,
  vpm.latitude::float8,
  vpm.longitude::float8,
  {dist_sel}
    """

    base = """
    FROM public.venue v
    INNER JOIN public.venue_published_profile vpp
      ON vpp.venue_id = v.id
     AND vpp.discovery_eligibility_status IN ('eligible', 'limited')
    INNER JOIN public.venue_published_location vpl ON vpl.venue_id = v.id
    INNER JOIN public.locality l ON l.id = vpl.locality_id
    INNER JOIN public.venue_published_map_point vpm ON vpm.venue_id = v.id
    """

    w: list[str] = []
    if f.suburb and str(f.suburb).strip():
        w.append("lower(l.name) = lower(%s)")
        p.append(f.suburb.strip())
    if f.has_viewport():
        w.append("vpm.latitude::float8 BETWEEN %s::float8 AND %s::float8")
        w.append("vpm.longitude::float8 BETWEEN %s::float8 AND %s::float8")
        p.extend(
            [float(f.south), float(f.north), float(f.west), float(f.east)]
        )
    if has_r and f.radius_m is not None:
        la, lo = float(f.lat), float(f.lng)
        w.append(f"{_HAVER} <= %s::float8")
        p.extend([la, la, lo, float(f.radius_m)])

    for sk in f.venue_features:
        sk0 = str(sk).strip()
        w.append(
            """
            EXISTS (
              SELECT 1
              FROM public.venue_published_attribute_value pav
              INNER JOIN public.venue_attribute_definition ad
                ON ad.id = pav.attribute_definition_id
              WHERE pav.venue_id = v.id
                AND ad.stable_key = %s
            )
            """
        )
        p.append(sk0)

    m_kinds = [k for k in f.meal_specials if k in MEAL_STRUCT_KINDS]
    if m_kinds:
        w.append(
            """
            EXISTS (
              SELECT 1
              FROM public.venue_published_structured_special s
              WHERE s.venue_id = v.id
                AND s.catalog_record_status = 'active'
                AND s.structured_kind = ANY(%s::text[])
            )
            """
        )
        p.append(m_kinds)

    d_uuids = [str(x).strip() for x in f.drink_types if str(x).strip()]
    if d_uuids:
        w.append(
            """
            EXISTS (
              SELECT 1
              FROM public.venue_published_tap_offering t
              WHERE t.venue_id = v.id
                AND t.catalog_record_status = 'active'
                AND t.beverage_product_id = ANY(%s::uuid[])
            )
            """
        )
        try:
            p.append([UUID(x) for x in d_uuids])
        except (ValueError, TypeError) as e:
            raise DiscoveryError from e

    where = ("WHERE " + " AND ".join(w)) if w else ""
    if has_r:
        order = "ORDER BY distance_m ASC NULLS LAST, vpp.display_name ASC, v.id"
    else:
        order = "ORDER BY l.name, vpp.display_name, v.id"

    sql = select + base + " " + where + " " + order
    return sql, p


def run_discovery(
    mode: DiscoveryMode,
    filters: DiscoveryMvpFilters,
    *,
    at_utc: datetime | None = None,
) -> DiscoveryResult:
    filters.validate(mode)
    t0 = at_utc or datetime.now(ZoneInfo("UTC"))
    if t0.tzinfo is None:
        raise ValueError("at_utc must be tz-aware or None")

    pre = min(200, filters.limit * 5) if filters.open_now is True else min(200, filters.limit)

    sql, params = build_discovery_sql(mode, filters)
    rows: list[tuple[Any, ...]] = []
    with connection.cursor() as c:
        c.execute(f"{sql} LIMIT {pre}", params)  # noqa: S608
        rows = c.fetchall()

    uids = [str(r[0]) for r in rows] if rows else []
    umap = map_published_hours_uncertainty(uids)

    hits: list[DiscoveryHit] = []
    for r in rows:
        vid, has_desc, _dname, _sub, _c, vlat, vlng, d_m = r[0:8]
        o_lat = o_lon = None
        if filters.has_radius():
            o_lat, o_lon = float(filters.lat or 0), float(filters.lng or 0)
        bundle = load_published_venue_read_bundle(vid)
        if not bundle:
            continue
        o_res = compute_open_now(
            bundle, hours_uncertainty_level=umap.get(str(vid)), at_utc=t0
        )
        if filters.open_now is True and (
            o_res.public_open_now is not True or o_res.public_open_now_uncomputed
        ):
            continue
        card0 = bundle_to_public_venue_card(
            bundle, origin_lat=o_lat, origin_lon=o_lon
        )
        card = apply_open_now_to_card(card0, o_res)
        d_m2 = None if d_m is None else round(float(d_m), 1)
        fset = {a.stable_key for a in bundle.attributes}
        fmatch = sum(1 for x in filters.venue_features if x in fset)
        mset = set(filters.meal_specials) & MEAL_STRUCT_KINDS
        if mset:
            meal_matched = sum(
                1 for sp in bundle.specials if sp.structured_kind in mset
            )
        else:
            meal_matched = 0
        dmatch = len(
            [x for x in (filters.drink_types or []) if str(x).strip()]
        )

        rnk, rcomp = score_rank(
            mode=mode,
            filters=filters,
            distance_m_value=d_m2,
            venue_lat=float(vlat),
            venue_lon=float(vlng),
            open_result=o_res,
            meal_matched=meal_matched,
            feature_matched=fmatch,
            drink_matched=dmatch,
            has_description=bool(r[1]),
        )
        hits.append(
            DiscoveryHit(
                venue_id=str(vid),
                distance_m=card.distance_m,
                open_now=o_res.public_open_now,
                open_now_uncomputed=o_res.public_open_now_uncomputed,
                open_now_result=o_res,
                rank_score=rnk,
                rank_components=rcomp,
                card=card,
                source_mode=mode.value,
            )
        )

    hits.sort(key=lambda h: (-h.rank_score, h.venue_id))
    hits = hits[: filters.limit]

    return DiscoveryResult(
        mode=mode.value, filters=filters, at_utc=t0, hits=hits, prelimit_used=pre
    )
