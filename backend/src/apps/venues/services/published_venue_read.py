"""
Published-truth-only reads for public venue cards/detail.

Excludes workflow, staging, moderation, owner/commercial, and private consumer
tables except the optional `is_saved` lookup (saved_list*) which is a
separate enrichment step in `save_enrichment.py`.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, time
from uuid import UUID

from django.db import connection


@dataclass
class PublishedCoreRow:
    venue_id: str
    display_name: str
    slug: str | None
    operational_status: str | None
    suburb_name: str
    address_line_1: str | None
    address_line_2: str | None
    postal_code: str | None
    country_code: str
    latitude: float
    longitude: float


@dataclass
class PublishedAttributeRow:
    stable_key: str
    definition_label: str
    is_discovery_driving: bool
    value_code: str | None
    value_label: str | None
    value_boolean: bool | None


@dataclass
class PublishedDescriptiveRow:
    short_description: str | None
    long_description: str | None


@dataclass
class PublishedRegularHoursRow:
    day_of_week: int
    opens_at: str
    closes_at: str
    crosses_midnight: bool
    sort_order: int


@dataclass
class PublishedExceptionHoursRow:
    start_date: str
    end_date: str
    exception_kind: str
    opens_at: str | None
    closes_at: str | None
    crosses_midnight: bool
    note: str | None


@dataclass
class PublishedSpecialRow:
    id: str
    structured_kind: str
    short_label: str
    headline: str | None


@dataclass
class PublishedTapRow:
    id: str
    unstructured_line_label: str | None
    product_name: str | None
    is_rotating: bool
    is_guest_tap: bool
    sort_order: int | None


@dataclass
class PublishedMediaRef:
    """
    Future: rows from a `venue_published_media` (or similar) table.
    Stage 2: always empty; hero/gallery resolution hooks read these keys.
    """

    storage_object_path: str
    sort_order: int | None
    is_hero: bool


@dataclass
class PublishedVenueReadBundle:
    core: PublishedCoreRow
    descriptive: PublishedDescriptiveRow | None
    attributes: list[PublishedAttributeRow] = field(default_factory=list)
    hours_regular: list[PublishedRegularHoursRow] = field(default_factory=list)
    hours_exceptions: list[PublishedExceptionHoursRow] = field(default_factory=list)
    specials: list[PublishedSpecialRow] = field(default_factory=list)
    taps: list[PublishedTapRow] = field(default_factory=list)
    media_refs: list[PublishedMediaRef] = field(default_factory=list)


def _time_to_hhmm(value: time | str) -> str:
    if isinstance(value, str):
        return value[:5] if len(value) >= 5 else value
    return value.strftime("%H:%M")


def _date_to_iso(value: date) -> str:
    return value.isoformat()


def _dedupe_venue_ids(venue_ids: list[UUID | str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in venue_ids:
        vid = str(raw)
        if not vid or vid in seen:
            continue
        seen.add(vid)
        out.append(vid)
    return out


def _in_clause(ids: list[str]) -> tuple[str, list[str]]:
    placeholders = ",".join(["%s"] * len(ids))
    return placeholders, ids


def get_published_hours_uncertainty(venue_id: UUID | str) -> str | None:
    """
    `venue_hours_uncertainty` row, if any. Used by centralized open-now logic.
    """
    vid = str(venue_id)
    with connection.cursor() as c:
        c.execute(
            """
            SELECT uncertainty_level
            FROM public.venue_hours_uncertainty
            WHERE venue_id = %s
            """,
            [vid],
        )
        row = c.fetchone()
        return str(row[0]) if row else None


def map_published_hours_uncertainty(venue_ids: list[UUID | str]) -> dict[str, str | None]:
    if not venue_ids:
        return {}
    ids = [str(v) for v in venue_ids]
    with connection.cursor() as c:
        placeholders, params = _in_clause(ids)
        c.execute(
            f"""
            SELECT venue_id::text, uncertainty_level
            FROM public.venue_hours_uncertainty
            WHERE venue_id IN ({placeholders})
            """,
            params,
        )
        out: dict[str, str | None] = {i: None for i in ids}
        for row in c.fetchall():
            out[str(row[0])] = str(row[1])
    return out


def _load_core_rows(venue_ids: list[str]) -> dict[str, PublishedCoreRow]:
    if not venue_ids:
        return {}
    placeholders, params = _in_clause(venue_ids)
    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT
              v.id,
              vpp.display_name,
              vpp.slug,
              vpp.operational_status,
              l.name,
              vpl.address_line_1,
              vpl.address_line_2,
              vpl.postal_code,
              vpl.country_code,
              vpm.latitude,
              vpm.longitude
            FROM public.venue v
            INNER JOIN public.venue_published_profile vpp
              ON vpp.venue_id = v.id
            INNER JOIN public.venue_published_location vpl
              ON vpl.venue_id = v.id
            INNER JOIN public.locality l
              ON l.id = vpl.locality_id
            INNER JOIN public.venue_published_map_point vpm
              ON vpm.venue_id = v.id
            WHERE v.id IN ({placeholders})
              AND vpp.discovery_eligibility_status IN ('eligible', 'limited')
            """,
            params,
        )
        out: dict[str, PublishedCoreRow] = {}
        for row in c.fetchall():
            out[str(row[0])] = PublishedCoreRow(
                venue_id=str(row[0]),
                display_name=row[1],
                slug=row[2],
                operational_status=row[3],
                suburb_name=row[4],
                address_line_1=row[5],
                address_line_2=row[6],
                postal_code=row[7],
                country_code=row[8],
                latitude=float(row[9]),
                longitude=float(row[10]),
            )
    return out


def _load_descriptive_rows(venue_ids: list[str]) -> dict[str, PublishedDescriptiveRow]:
    if not venue_ids:
        return {}
    placeholders, params = _in_clause(venue_ids)
    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT venue_id::text, short_description, long_description
            FROM public.venue_published_descriptive_copy
            WHERE venue_id IN ({placeholders})
            """,
            params,
        )
        return {
            str(row[0]): PublishedDescriptiveRow(
                short_description=row[1], long_description=row[2]
            )
            for row in c.fetchall()
        }


def _load_attribute_rows(venue_ids: list[str]) -> dict[str, list[PublishedAttributeRow]]:
    if not venue_ids:
        return {}
    placeholders, params = _in_clause(venue_ids)
    grouped: dict[str, list[PublishedAttributeRow]] = defaultdict(list)
    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT
              pav.venue_id::text,
              ad.stable_key,
              ad.display_label,
              ad.is_discovery_driving,
              aav.code,
              aav.display_label,
              pav.value_boolean
            FROM public.venue_published_attribute_value pav
            INNER JOIN public.venue_attribute_definition ad
              ON ad.id = pav.attribute_definition_id
            LEFT JOIN public.venue_attribute_allowed_value aav
              ON aav.id = pav.allowed_value_id
            WHERE pav.venue_id IN ({placeholders})
            ORDER BY pav.venue_id, ad.stable_key
            """,
            params,
        )
        for row in c.fetchall():
            grouped[str(row[0])].append(
                PublishedAttributeRow(
                    stable_key=row[1],
                    definition_label=row[2],
                    is_discovery_driving=bool(row[3]),
                    value_code=row[4],
                    value_label=row[5],
                    value_boolean=row[6],
                )
            )
    return dict(grouped)


def _load_regular_hours_rows(venue_ids: list[str]) -> dict[str, list[PublishedRegularHoursRow]]:
    if not venue_ids:
        return {}
    placeholders, params = _in_clause(venue_ids)
    grouped: dict[str, list[PublishedRegularHoursRow]] = defaultdict(list)
    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT
              venue_id::text,
              day_of_week,
              opens_at,
              closes_at,
              crosses_midnight,
              sort_order
            FROM public.venue_hours_regular
            WHERE venue_id IN ({placeholders})
            ORDER BY venue_id, day_of_week, sort_order, opens_at
            """,
            params,
        )
        for row in c.fetchall():
            grouped[str(row[0])].append(
                PublishedRegularHoursRow(
                    day_of_week=int(row[1]),
                    opens_at=_time_to_hhmm(row[2]),
                    closes_at=_time_to_hhmm(row[3]),
                    crosses_midnight=bool(row[4]),
                    sort_order=int(row[5]),
                )
            )
    return dict(grouped)


def _load_exception_hours_rows(
    venue_ids: list[str],
) -> dict[str, list[PublishedExceptionHoursRow]]:
    if not venue_ids:
        return {}
    placeholders, params = _in_clause(venue_ids)
    grouped: dict[str, list[PublishedExceptionHoursRow]] = defaultdict(list)
    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT
              venue_id::text,
              start_date,
              end_date,
              exception_kind,
              opens_at,
              closes_at,
              crosses_midnight,
              note
            FROM public.venue_hours_exception
            WHERE venue_id IN ({placeholders})
            ORDER BY venue_id, start_date
            """,
            params,
        )
        for row in c.fetchall():
            grouped[str(row[0])].append(
                PublishedExceptionHoursRow(
                    start_date=_date_to_iso(row[1])
                    if hasattr(row[1], "isoformat")
                    else str(row[1]),
                    end_date=_date_to_iso(row[2])
                    if hasattr(row[2], "isoformat")
                    else str(row[2]),
                    exception_kind=row[3],
                    opens_at=_time_to_hhmm(row[4]) if row[4] is not None else None,
                    closes_at=_time_to_hhmm(row[5]) if row[5] is not None else None,
                    crosses_midnight=bool(row[6]),
                    note=row[7],
                )
            )
    return dict(grouped)


def _load_special_rows(
    venue_ids: list[str], *, limit_per_venue: int = 12
) -> dict[str, list[PublishedSpecialRow]]:
    if not venue_ids:
        return {}
    placeholders, params = _in_clause(venue_ids)
    grouped: dict[str, list[PublishedSpecialRow]] = defaultdict(list)
    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT
              s.venue_id::text,
              s.id,
              s.structured_kind,
              s.short_label,
              m.headline
            FROM public.venue_published_structured_special s
            LEFT JOIN public.venue_published_structured_special_marketing_copy m
              ON m.structured_special_id = s.id
            WHERE s.venue_id IN ({placeholders})
              AND s.catalog_record_status = 'active'
            ORDER BY s.venue_id, s.updated_at DESC
            """,
            params,
        )
        for row in c.fetchall():
            vid = str(row[0])
            if len(grouped[vid]) >= limit_per_venue:
                continue
            grouped[vid].append(
                PublishedSpecialRow(
                    id=str(row[1]),
                    structured_kind=row[2],
                    short_label=row[3],
                    headline=row[4],
                )
            )
    return dict(grouped)


def _load_tap_rows(
    venue_ids: list[str], *, limit_per_venue: int = 24
) -> dict[str, list[PublishedTapRow]]:
    if not venue_ids:
        return {}
    placeholders, params = _in_clause(venue_ids)
    grouped: dict[str, list[PublishedTapRow]] = defaultdict(list)
    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT
              t.venue_id::text,
              t.id,
              t.unstructured_line_label,
              p.display_name,
              t.is_rotating,
              t.is_guest_tap,
              t.sort_order
            FROM public.venue_published_tap_offering t
            LEFT JOIN public.beverage_product p
              ON p.id = t.beverage_product_id
            WHERE t.venue_id IN ({placeholders})
              AND t.catalog_record_status = 'active'
            ORDER BY t.venue_id, t.sort_order NULLS LAST, t.created_at
            """,
            params,
        )
        for row in c.fetchall():
            vid = str(row[0])
            if len(grouped[vid]) >= limit_per_venue:
                continue
            grouped[vid].append(
                PublishedTapRow(
                    id=str(row[1]),
                    unstructured_line_label=row[2],
                    product_name=row[3],
                    is_rotating=bool(row[4]),
                    is_guest_tap=bool(row[5]),
                    sort_order=int(row[6]) if row[6] is not None else None,
                )
            )
    return dict(grouped)


def _assemble_bundle(
    core: PublishedCoreRow,
    *,
    descriptive: PublishedDescriptiveRow | None,
    attributes: list[PublishedAttributeRow],
    hours_regular: list[PublishedRegularHoursRow],
    hours_exceptions: list[PublishedExceptionHoursRow],
    specials: list[PublishedSpecialRow],
    taps: list[PublishedTapRow],
) -> PublishedVenueReadBundle:
    return PublishedVenueReadBundle(
        core=core,
        descriptive=descriptive,
        attributes=attributes,
        hours_regular=hours_regular,
        hours_exceptions=hours_exceptions,
        specials=specials,
        taps=taps,
        media_refs=[],
    )


def load_published_venue_read_bundles(
    venue_ids: list[UUID | str],
) -> dict[str, PublishedVenueReadBundle]:
    """
    Batch-load published venue bundles for card/detail shaping.

    Uses a fixed small number of SQL queries (one per published table) instead of
    ~8 round-trips per venue. Missing or ineligible venues are omitted.
    """
    ids = _dedupe_venue_ids(venue_ids)
    if not ids:
        return {}

    cores = _load_core_rows(ids)
    if not cores:
        return {}

    valid_ids = list(cores.keys())
    descriptive = _load_descriptive_rows(valid_ids)
    attributes = _load_attribute_rows(valid_ids)
    hours_regular = _load_regular_hours_rows(valid_ids)
    hours_exceptions = _load_exception_hours_rows(valid_ids)
    specials = _load_special_rows(valid_ids)
    taps = _load_tap_rows(valid_ids)

    out: dict[str, PublishedVenueReadBundle] = {}
    for vid, core in cores.items():
        out[vid] = _assemble_bundle(
            core,
            descriptive=descriptive.get(vid),
            attributes=attributes.get(vid, []),
            hours_regular=hours_regular.get(vid, []),
            hours_exceptions=hours_exceptions.get(vid, []),
            specials=specials.get(vid, []),
            taps=taps.get(vid, []),
        )
    return out


def load_published_venue_read_bundle(venue_id: UUID | str) -> PublishedVenueReadBundle | None:
    return load_published_venue_read_bundles([venue_id]).get(str(venue_id))
