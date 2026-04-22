"""
Published-truth-only reads for public venue cards/detail.

Excludes workflow, staging, moderation, owner/commercial, and private consumer
tables except the optional `is_saved` lookup (saved_list*) which is a
separate enrichment step in `save_enrichment.py`.
"""

from __future__ import annotations

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


def load_published_venue_read_bundle(venue_id: UUID | str) -> PublishedVenueReadBundle | None:
    vid = str(venue_id)
    with connection.cursor() as c:
        c.execute(
            """
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
            WHERE v.id = %s
              AND vpp.discovery_eligibility_status IN ('eligible', 'limited')
            """,
            [vid],
        )
        row = c.fetchone()
        if not row:
            return None
        core = PublishedCoreRow(
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

        c.execute(
            """
            SELECT short_description, long_description
            FROM public.venue_published_descriptive_copy
            WHERE venue_id = %s
            """,
            [vid],
        )
        dr = c.fetchone()
        descriptive = (
            PublishedDescriptiveRow(
                short_description=dr[0], long_description=dr[1]
            )
            if dr
            else None
        )

        c.execute(
            """
            SELECT
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
            WHERE pav.venue_id = %s
            """,
            [vid],
        )
        attr_rows: list[PublishedAttributeRow] = []
        for r in c.fetchall():
            attr_rows.append(
                PublishedAttributeRow(
                    stable_key=r[0],
                    definition_label=r[1],
                    is_discovery_driving=bool(r[2]),
                    value_code=r[3],
                    value_label=r[4],
                    value_boolean=r[5],
                )
            )

        c.execute(
            """
            SELECT
              day_of_week,
              opens_at,
              closes_at,
              crosses_midnight,
              sort_order
            FROM public.venue_hours_regular
            WHERE venue_id = %s
            ORDER BY day_of_week, sort_order, opens_at
            """,
            [vid],
        )
        reg: list[PublishedRegularHoursRow] = []
        for r in c.fetchall():
            reg.append(
                PublishedRegularHoursRow(
                    day_of_week=int(r[0]),
                    opens_at=_time_to_hhmm(r[1]),
                    closes_at=_time_to_hhmm(r[2]),
                    crosses_midnight=bool(r[3]),
                    sort_order=int(r[4]),
                )
            )

        c.execute(
            """
            SELECT
              start_date,
              end_date,
              exception_kind,
              opens_at,
              closes_at,
              crosses_midnight,
              note
            FROM public.venue_hours_exception
            WHERE venue_id = %s
            ORDER BY start_date
            """,
            [vid],
        )
        ex: list[PublishedExceptionHoursRow] = []
        for r in c.fetchall():
            ex.append(
                PublishedExceptionHoursRow(
                    start_date=_date_to_iso(r[0])
                    if hasattr(r[0], "isoformat")
                    else str(r[0]),
                    end_date=_date_to_iso(r[1])
                    if hasattr(r[1], "isoformat")
                    else str(r[1]),
                    exception_kind=r[2],
                    opens_at=_time_to_hhmm(r[3]) if r[3] is not None else None,
                    closes_at=_time_to_hhmm(r[4]) if r[4] is not None else None,
                    crosses_midnight=bool(r[5]),
                    note=r[6],
                )
            )

        c.execute(
            """
            SELECT
              s.id,
              s.structured_kind,
              s.short_label,
              m.headline
            FROM public.venue_published_structured_special s
            LEFT JOIN public.venue_published_structured_special_marketing_copy m
              ON m.structured_special_id = s.id
            WHERE s.venue_id = %s
              AND s.catalog_record_status = 'active'
            ORDER BY s.updated_at DESC
            LIMIT 12
            """,
            [vid],
        )
        sp: list[PublishedSpecialRow] = []
        for r in c.fetchall():
            sp.append(
                PublishedSpecialRow(
                    id=str(r[0]),
                    structured_kind=r[1],
                    short_label=r[2],
                    headline=r[3],
                )
            )

        c.execute(
            """
            SELECT
              t.id,
              t.unstructured_line_label,
              p.display_name,
              t.is_rotating,
              t.is_guest_tap,
              t.sort_order
            FROM public.venue_published_tap_offering t
            LEFT JOIN public.beverage_product p
              ON p.id = t.beverage_product_id
            WHERE t.venue_id = %s
              AND t.catalog_record_status = 'active'
            ORDER BY t.sort_order NULLS LAST, t.created_at
            LIMIT 24
            """,
            [vid],
        )
        taps: list[PublishedTapRow] = []
        for r in c.fetchall():
            taps.append(
                PublishedTapRow(
                    id=str(r[0]),
                    unstructured_line_label=r[1],
                    product_name=r[2],
                    is_rotating=bool(r[3]),
                    is_guest_tap=bool(r[4]),
                    sort_order=int(r[5]) if r[5] is not None else None,
                )
            )

    return PublishedVenueReadBundle(
        core=core,
        descriptive=descriptive,
        attributes=attr_rows,
        hours_regular=reg,
        hours_exceptions=ex,
        specials=sp,
        taps=taps,
        media_refs=[],
    )
