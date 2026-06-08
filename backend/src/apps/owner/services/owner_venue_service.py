"""
Owner portal venue list, detail, core_details proposal intake (Phase A),
and direct operational edits (Stage 4.1).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from django.db import connection, transaction

from apps.venues.services.published_venue_read import (
    _time_to_hhmm,
    get_published_hours_uncertainty,
)
from common.auth.context import AuthContext
from common.owner_account import admin_account_exists_for_auth, get_owner_account_id

logger = logging.getLogger(__name__)

_TERMINAL_PROPOSAL_STATUSES = frozenset(
    {"approved", "rejected", "withdrawn", "superseded"}
)
_UNCERTAINTY = frozenset(
    {"unknown", "partial", "weak_stale", "disputed", "resolved_confident"}
)
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_POSTAL_RE = re.compile(r"^[A-Za-z0-9 \-]+$")
_UNSUPPORTED_PAYLOAD_KEYS = frozenset(
    {
        "phone",
        "email",
        "website",
        "contact_person_name",
        "contact_person_role",
        "google_place_id",
    }
)
_CORE_TARGETS = ("profile", "geo", "hours")
_DIRECT_EDIT_CAPABILITY = "manage_published_venue_operations"
_RESTRICTED_SUBMIT_CAPABILITY = "submit_restricted_changes_for_review"
_RESTRICTED_IDENTITY_TARGETS = ("profile", "geo")
_RESTRICTED_FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {
        "short_description",
        "long_description",
        "opening_hours",
        "phone",
        "email",
        "website",
        "contact_person_name",
        "contact_person_role",
        "google_place_id",
        "owner_confirms_management",
    }
)
_HOURS_NOTES_MAX_LEN = 1000
_MVP_OWNER_EDITABLE_FEATURE_KEYS = frozenset(
    {
        "beer_garden",
        "rooftop",
        "live_music",
        "dog_friendly",
        "sports_screens",
        "pool_table",
        "late_night",
        "vegan_options",
    }
)
_FEATURE_UI_GROUPS: dict[str, str] = {
    "beer_garden": "spaces",
    "rooftop": "spaces",
    "live_music": "entertainment",
    "dog_friendly": "pets",
    "sports_screens": "entertainment",
    "pool_table": "entertainment",
    "late_night": "food",
    "vegan_options": "food",
}
_OPERATIONAL_PROFILE_ALLOWED_KEYS = frozenset(
    {"short_description", "long_description"}
)
_OPERATIONAL_PROFILE_FORBIDDEN_KEYS = frozenset(
    {
        "display_name",
        "address_line_1",
        "address_line_2",
        "postal_code",
        "locality_id",
        "country_code",
        "latitude",
        "longitude",
        "phone",
        "email",
        "website",
        "contact_person_name",
        "contact_person_role",
        "google_place_id",
        "opening_hours",
        "operational_status",
        "discovery_eligibility_status",
        "owner_confirms_management",
    }
)
_MEAL_SPECIAL_STRUCTURED_KIND = "meal_special"
_MEAL_SPECIAL_DEFAULT_TIMEZONE = "Australia/Melbourne"
_MEAL_SPECIAL_TITLE_MIN = 2
_MEAL_SPECIAL_TITLE_MAX = 120
_MEAL_SPECIAL_DESCRIPTION_MAX = 500
_MEAL_SPECIAL_PRICE_TEXT_MAX = 80
_MEAL_SPECIAL_CONDITIONS_MAX = 300
_MEAL_SPECIAL_SORT_ORDER_MIN = 0
_MEAL_SPECIAL_SORT_ORDER_MAX = 999
_MEAL_SPECIAL_INPUT_ALLOWED_KEYS = frozenset(
    {
        "title",
        "description",
        "days_available",
        "start_time",
        "end_time",
        "price_text",
        "conditions",
        "active",
        "sort_order",
    }
)
_SORT_ORDER_TIER_NOTES_PREFIX = "owner_sort_order="
_TAP_LIST_DRINK_NAME_MIN = 2
_TAP_LIST_DRINK_NAME_MAX = 120
_TAP_LIST_BREWERY_MAX = 120
_TAP_LIST_TYPE_MAX = 80
_TAP_LIST_ABV_MAX = 20
_TAP_LIST_PRICE_TEXT_MAX = 80
_TAP_LIST_NOTES_MAX = 300
_TAP_LIST_SORT_ORDER_MIN = 0
_TAP_LIST_SORT_ORDER_MAX = 999
_TAP_LIST_AVAILABILITY = frozenset({"permanent", "rotating", "seasonal", "limited"})
_TAP_LIST_INPUT_ALLOWED_KEYS = frozenset(
    {
        "drink_name",
        "brewery_or_brand",
        "drink_type",
        "abv",
        "price_text",
        "availability",
        "notes",
        "active",
        "sort_order",
    }
)
_TAP_OWNER_META_PREFIX = "owner_meta="
_MARKUP_RE = re.compile(r"<\s*(script|iframe|object|embed|svg|/script)", re.I)
_HOURS_PATCH_FORBIDDEN_KEYS = frozenset(
    {
        "display_name",
        "address_line_1",
        "address_line_2",
        "postal_code",
        "locality_id",
        "country_code",
        "latitude",
        "longitude",
        "short_description",
        "long_description",
        "phone",
        "email",
        "website",
        "google_place_id",
        "operational_status",
        "discovery_eligibility_status",
        "owner_confirms_management",
    }
)


@dataclass(frozen=True)
class ResolvedVenueAccess:
    owner_account_id: UUID
    business_id: UUID
    relationship_id: UUID
    venue_id: UUID


def _bad_uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    try:
        UUID(value)
    except (ValueError, TypeError):
        return True
    return False


def _parse_venue_uuid(venue_id: str) -> UUID | None:
    if _bad_uuid(venue_id):
        return None
    return UUID(venue_id)


def _locality_exists(locality_id: str) -> bool:
    with connection.cursor() as c:
        c.execute(
            "SELECT 1 FROM public.locality WHERE id = %s::uuid",
            [locality_id],
        )
        return c.fetchone() is not None


def _venue_row_exists(venue_id: str) -> bool:
    with connection.cursor() as c:
        c.execute("SELECT 1 FROM public.venue WHERE id = %s::uuid", [venue_id])
        return c.fetchone() is not None


def _resolve_venue_access(
    owner_account_id: UUID, venue_id: str
) -> ResolvedVenueAccess | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              b.id::text,
              bvmr.id::text
            FROM public.owner_business_membership obm
            INNER JOIN public.business_venue_management_relationship bvmr
              ON bvmr.business_id = obm.business_id
            INNER JOIN public.business b
              ON b.id = obm.business_id
            WHERE obm.owner_account_id = %s::uuid
              AND obm.membership_status = 'active'
              AND bvmr.venue_id = %s::uuid
              AND bvmr.relationship_lifecycle = 'approved'
            LIMIT 1
            """,
            [str(owner_account_id), venue_id],
        )
        row = c.fetchone()
    if not row:
        return None
    return ResolvedVenueAccess(
        owner_account_id=owner_account_id,
        business_id=UUID(row[0]),
        relationship_id=UUID(row[1]),
        venue_id=UUID(venue_id),
    )


def assert_owner_manages_venue(
    auth: AuthContext, venue_id: str
) -> tuple[ResolvedVenueAccess | None, str]:
    """
    Return (access, error_code).

    error_code: forbidden | not_found | admin_forbidden
    """
    if admin_account_exists_for_auth(auth):
        return None, "admin_forbidden"

    owner_id = get_owner_account_id(auth)
    if owner_id is None:
        return None, "forbidden"

    vid = _parse_venue_uuid(venue_id)
    if vid is None:
        return None, "not_found"

    access = _resolve_venue_access(owner_id, str(vid))
    if access is not None:
        return access, "ok"

    if not _venue_row_exists(str(vid)):
        return None, "not_found"
    return None, "forbidden"


def _has_active_capability(
    relationship_id: UUID, owner_account_id: UUID, capability_code: str
) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1
            FROM public.venue_capability_grant
            WHERE business_venue_management_relationship_id = %s::uuid
              AND owner_account_id = %s::uuid
              AND capability_code = %s
              AND grant_status = 'active'
            LIMIT 1
            """,
            [str(relationship_id), str(owner_account_id), capability_code],
        )
        return c.fetchone() is not None


def assert_owner_can_submit_restricted_change(
    auth: AuthContext, venue_id: str
) -> tuple[ResolvedVenueAccess | None, str]:
    access, err = assert_owner_manages_venue(auth, venue_id)
    if access is None:
        return None, err
    if not _has_active_capability(
        access.relationship_id,
        access.owner_account_id,
        _RESTRICTED_SUBMIT_CAPABILITY,
    ):
        return None, "missing_restricted_capability"
    return access, "ok"


def assert_owner_can_direct_edit(
    auth: AuthContext, venue_id: str
) -> tuple[ResolvedVenueAccess | None, str]:
    """
    Approved relationship plus manage_published_venue_operations grant.

    error_code: forbidden | not_found | admin_forbidden | missing_capability
    """
    access, err = assert_owner_manages_venue(auth, venue_id)
    if access is None:
        return None, err
    if not _has_active_capability(
        access.relationship_id,
        access.owner_account_id,
        _DIRECT_EDIT_CAPABILITY,
    ):
        return None, "missing_capability"
    return access, "ok"


def _load_capabilities(relationship_id: UUID, owner_account_id: UUID) -> list[str]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT capability_code
            FROM public.venue_capability_grant
            WHERE business_venue_management_relationship_id = %s::uuid
              AND owner_account_id = %s::uuid
              AND grant_status = 'active'
            ORDER BY capability_code
            """,
            [str(relationship_id), str(owner_account_id)],
        )
        caps = [str(r[0]) for r in c.fetchall()]
    if "submit_restricted_changes_for_review" not in caps:
        logger.warning(
            "Owner %s lacks submit_restricted_changes_for_review on relationship %s",
            owner_account_id,
            relationship_id,
        )
    return caps


def _merge_basics_sources(
    *,
    published: dict[str, Any],
    staged: dict[str, Any] | None,
) -> dict[str, Any]:
    staged = staged or {}
    return {
        "display_name": staged.get("display_name") or published.get("display_name"),
        "address_line_1": staged.get("address_line_1")
        or published.get("address_line_1"),
        "locality_id": staged.get("locality_id") or published.get("locality_id"),
        "short_description": staged.get("short_description")
        or published.get("short_description"),
        "hours_ok": bool(staged.get("hours_ok") or published.get("hours_ok")),
    }


def _hours_satisfied(
    *,
    regular: list[Any],
    exceptions: list[Any],
    uncertainty: str | None,
    notes: str | None,
) -> bool:
    if regular or exceptions:
        return True
    if uncertainty and uncertainty != "resolved_confident":
        return True
    if notes and len(notes.strip()) >= 10:
        return True
    return False


def _compute_required_basics(basics: dict[str, Any]) -> bool:
    return bool(
        basics.get("display_name")
        and basics.get("address_line_1")
        and basics.get("locality_id")
        and basics.get("short_description")
        and basics.get("hours_ok")
    )


def _core_section_status(basics: dict[str, Any]) -> str:
    if _compute_required_basics(basics):
        return "complete"
    if any(
        (
            basics.get("display_name"),
            basics.get("address_line_1"),
            basics.get("locality_id"),
            basics.get("short_description"),
            basics.get("hours_ok"),
        )
    ):
        return "partial"
    return "missing"


def _is_restricted_pending_review(pending: dict[str, Any]) -> bool:
    return bool(
        pending.get("proposal_id")
        and pending.get("lifecycle_status") == "in_review"
        and pending.get("submitted_at")
        and pending.get("review_outcome") not in ("rejected", "changes_requested")
    )


def _core_details_completeness_points(basics: dict[str, Any]) -> int:
    core_status = _core_section_status(basics)
    if core_status == "complete":
        return 30
    if core_status == "partial":
        checks = [
            bool(
                basics.get("display_name")
                and basics.get("address_line_1")
                and basics.get("locality_id")
            ),
            bool(basics.get("short_description")),
            bool(basics.get("hours_ok")),
        ]
        return int(30 * sum(1 for x in checks if x) / 3)
    return 0


def _completeness_percent(
    basics: dict[str, Any],
    *,
    features_status: str = "missing",
    meal_specials_status: str = "missing",
    tap_list_status: str = "missing",
    photos_status: str = "deferred",
    photos_available: bool = False,
    restricted_pending: bool = False,
) -> int:
    score = _core_details_completeness_points(basics)
    if features_status == "complete":
        score += 15
    if meal_specials_status == "complete":
        score += 15
    if tap_list_status == "complete":
        score += 15
    if photos_available and photos_status == "complete":
        score += 20
    if not restricted_pending:
        score += 5
    return min(100, score)


def _parse_owner_sort_order_from_tier_notes(tier_notes: str | None) -> int:
    if not tier_notes:
        return _MEAL_SPECIAL_SORT_ORDER_MAX
    for part in str(tier_notes).split("|"):
        part = part.strip()
        if part.startswith(_SORT_ORDER_TIER_NOTES_PREFIX):
            try:
                return int(part[len(_SORT_ORDER_TIER_NOTES_PREFIX) :])
            except ValueError:
                return _MEAL_SPECIAL_SORT_ORDER_MAX
    return _MEAL_SPECIAL_SORT_ORDER_MAX


def _format_owner_sort_order_tier_notes(
    sort_order: int, existing_notes: str | None
) -> str:
    prefix = f"{_SORT_ORDER_TIER_NOTES_PREFIX}{sort_order}"
    if not existing_notes:
        return prefix
    remainder = existing_notes
    if _SORT_ORDER_TIER_NOTES_PREFIX in remainder:
        parts = [p.strip() for p in remainder.split("|") if p.strip()]
        parts = [
            p for p in parts if not p.startswith(_SORT_ORDER_TIER_NOTES_PREFIX)
        ]
        if parts:
            return f"{prefix}|{'|'.join(parts)}"
    return f"{prefix}|{remainder}" if remainder else prefix


def _meal_specials_section_status(venue_id: str) -> str:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.venue_published_structured_special
            WHERE venue_id = %s::uuid
              AND structured_kind = %s
              AND catalog_record_status = 'active'
            """,
            [venue_id, _MEAL_SPECIAL_STRUCTURED_KIND],
        )
        row = c.fetchone()
    return "complete" if row and int(row[0]) > 0 else "missing"


def _contains_markup(value: str) -> bool:
    return bool(_MARKUP_RE.search(value))


def _tap_list_section_status(venue_id: str) -> str:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.venue_published_tap_offering
            WHERE venue_id = %s::uuid
              AND catalog_record_status = 'active'
            """,
            [venue_id],
        )
        row = c.fetchone()
    return "complete" if row and int(row[0]) > 0 else "missing"


def _features_section_status(venue_id: str) -> str:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.venue_published_attribute_value pav
            INNER JOIN public.venue_attribute_definition ad
              ON ad.id = pav.attribute_definition_id
            WHERE pav.venue_id = %s::uuid
              AND ad.stable_key = ANY(%s::text[])
              AND ad.value_shape = 'boolean'
              AND pav.value_boolean IS TRUE
            """,
            [venue_id, list(_MVP_OWNER_EDITABLE_FEATURE_KEYS)],
        )
        row = c.fetchone()
    return "complete" if row and int(row[0]) > 0 else "missing"


def _photos_section_status(venue_id: str) -> str:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'venue_published_media'
            """
        )
        if not c.fetchone():
            return "deferred"
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.venue_published_media
            WHERE venue_id = %s::uuid
              AND catalog_record_status = 'active'
            """,
            [venue_id],
        )
        row = c.fetchone()
    return "complete" if row and int(row[0]) > 0 else "missing"


def _photos_section_available(venue_id: str) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'venue_published_media'
            """
        )
        return c.fetchone() is not None


def _load_section_statuses(
    venue_id: str,
) -> tuple[str, str, str, str, bool]:
    features_status = _features_section_status(venue_id)
    meal_specials_status = _meal_specials_section_status(venue_id)
    tap_list_status = _tap_list_section_status(venue_id)
    photos_available = _photos_section_available(venue_id)
    photos_status = (
        _photos_section_status(venue_id) if photos_available else "deferred"
    )
    return (
        features_status,
        meal_specials_status,
        tap_list_status,
        photos_status,
        photos_available,
    )


def _compute_venue_completeness(
    venue_id: str,
    basics: dict[str, Any],
    pending: dict[str, Any],
) -> dict[str, Any]:
    (
        features_status,
        meal_specials_status,
        tap_list_status,
        photos_status,
        photos_available,
    ) = _load_section_statuses(venue_id)
    restricted_pending = _is_restricted_pending_review(pending)
    return {
        "percent": _completeness_percent(
            basics,
            features_status=features_status,
            meal_specials_status=meal_specials_status,
            tap_list_status=tap_list_status,
            photos_status=photos_status,
            photos_available=photos_available,
            restricted_pending=restricted_pending,
        ),
        "required_basics_complete": _compute_required_basics(basics),
        "sections": _completeness_sections(
            basics,
            features_status=features_status,
            meal_specials_status=meal_specials_status,
            tap_list_status=tap_list_status,
            photos_status=photos_status,
            photos_available=photos_available,
        ),
        "restricted_pending_review": restricted_pending,
    }


def _completeness_sections(
    basics: dict[str, Any],
    *,
    features_status: str = "missing",
    meal_specials_status: str = "missing",
    tap_list_status: str = "missing",
    photos_status: str = "deferred",
    photos_available: bool = False,
) -> list[dict[str, Any]]:
    core_status = _core_section_status(basics)
    return [
        {
            "key": "core_details",
            "label": "Pub details",
            "status": core_status,
            "required": True,
            "available": True,
        },
        {
            "key": "features",
            "label": "Features",
            "status": features_status,
            "required": False,
            "available": True,
        },
        {
            "key": "meal_specials",
            "label": "Meal specials",
            "status": meal_specials_status,
            "required": False,
            "available": True,
        },
        {
            "key": "tap_list",
            "label": "Tap list & drinks",
            "status": tap_list_status,
            "required": False,
            "available": True,
        },
        {
            "key": "photos",
            "label": "Photos",
            "status": photos_status if photos_available else "deferred",
            "required": False,
            "available": photos_available,
        },
        {
            "key": "events",
            "label": "Events",
            "status": "deferred",
            "required": False,
            "available": False,
        },
        {
            "key": "menus",
            "label": "Menus",
            "status": "deferred",
            "required": False,
            "available": False,
        },
    ]


def _load_published_snapshot(venue_id: str) -> dict[str, Any]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              vpp.display_name,
              vpp.slug,
              vpp.operational_status,
              vpp.discovery_eligibility_status,
              vpl.locality_id::text,
              l.name,
              COALESCE(
                CASE WHEN gr.region_level = 'state' THEN gr.region_code END,
                pgr.region_code
              ),
              vpl.address_line_1,
              vpl.address_line_2,
              vpl.postal_code,
              vpl.country_code,
              vpm.latitude,
              vpm.longitude
            FROM public.venue v
            LEFT JOIN public.venue_published_profile vpp ON vpp.venue_id = v.id
            LEFT JOIN public.venue_published_location vpl ON vpl.venue_id = v.id
            LEFT JOIN public.locality l ON l.id = vpl.locality_id
            LEFT JOIN public.geographic_region gr ON gr.id = l.geographic_region_id
            LEFT JOIN public.geographic_region pgr ON pgr.id = gr.parent_region_id
            LEFT JOIN public.venue_published_map_point vpm ON vpm.venue_id = v.id
            WHERE v.id = %s::uuid
            """,
            [venue_id],
        )
        row = c.fetchone()

    profile = {
        "display_name": None,
        "slug": None,
        "operational_status": None,
    }
    location = {
        "locality_id": None,
        "locality_name": None,
        "state_code": None,
        "address_line_1": None,
        "address_line_2": None,
        "postal_code": None,
        "country_code": None,
        "latitude": None,
        "longitude": None,
    }
    listing = {
        "discovery_eligibility_status": "unknown",
        "operational_status": "unknown",
    }
    descriptions = {"short_description": None, "long_description": None}
    hours_ok = False

    if row:
        profile = {
            "display_name": row[0],
            "slug": row[1],
            "operational_status": row[2],
        }
        listing = {
            "discovery_eligibility_status": row[3] or "unknown",
            "operational_status": row[2] or "unknown",
        }
        location = {
            "locality_id": row[4],
            "locality_name": row[5],
            "state_code": row[6],
            "address_line_1": row[7],
            "address_line_2": row[8],
            "postal_code": row[9],
            "country_code": row[10],
            "latitude": float(row[11]) if row[11] is not None else None,
            "longitude": float(row[12]) if row[12] is not None else None,
        }

    with connection.cursor() as c:
        c.execute(
            """
            SELECT short_description, long_description
            FROM public.venue_published_descriptive_copy
            WHERE venue_id = %s::uuid
            """,
            [venue_id],
        )
        desc = c.fetchone()
    if desc:
        descriptions = {
            "short_description": desc[0],
            "long_description": desc[1],
        }

    uncertainty = get_published_hours_uncertainty(venue_id) or "resolved_confident"
    regular: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    with connection.cursor() as c:
        c.execute(
            """
            SELECT day_of_week, opens_at, closes_at, crosses_midnight
            FROM public.venue_hours_regular
            WHERE venue_id = %s::uuid
            ORDER BY day_of_week, sort_order, opens_at
            """,
            [venue_id],
        )
        for r in c.fetchall():
            regular.append(
                {
                    "day_of_week": int(r[0]),
                    "opens_at": _time_to_hhmm(r[1]),
                    "closes_at": _time_to_hhmm(r[2]),
                    "crosses_midnight": bool(r[3]),
                }
            )
        c.execute(
            """
            SELECT start_date, end_date, exception_kind, opens_at, closes_at,
                   crosses_midnight, note
            FROM public.venue_hours_exception
            WHERE venue_id = %s::uuid
            ORDER BY start_date
            """,
            [venue_id],
        )
        for r in c.fetchall():
            exceptions.append(
                {
                    "start_date": r[0].isoformat() if r[0] else None,
                    "end_date": r[1].isoformat() if r[1] else None,
                    "exception_kind": r[2],
                    "opens_at": _time_to_hhmm(r[3]) if r[3] else None,
                    "closes_at": _time_to_hhmm(r[4]) if r[4] else None,
                    "crosses_midnight": bool(r[5]),
                    "note": r[6],
                }
            )

    hours_ok = _hours_satisfied(
        regular=regular,
        exceptions=exceptions,
        uncertainty=uncertainty,
        notes=None,
    )

    return {
        "listing": listing,
        "profile": profile,
        "location": location,
        "descriptions": descriptions,
        "hours": {
            "uncertainty_level": uncertainty,
            "regular": regular,
            "exceptions": exceptions,
        },
        "contact": {
            "supported": False,
            "phone": None,
            "email": None,
            "website": None,
        },
        "basics": {
            "display_name": profile.get("display_name"),
            "address_line_1": location.get("address_line_1"),
            "locality_id": location.get("locality_id"),
            "short_description": descriptions.get("short_description"),
            "hours_ok": hours_ok,
        },
    }


def _load_staged_core_details_payload(proposal_id: str) -> dict[str, Any] | None:
    """Full staged core_details fields for form hydration (Phase A.1)."""
    display_name = short_description = long_description = None
    address_line_1 = address_line_2 = postal_code = locality_id = None
    country_code = latitude = longitude = None
    uncertainty = notes = None
    reg: list[Any] = []
    exc: list[Any] = []

    with connection.cursor() as c:
        c.execute(
            """
            SELECT proposed_display_name, proposed_short_description, proposed_long_description
            FROM public.venue_proposal_staging_profile
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        prof = c.fetchone()
        if prof:
            display_name, short_description, long_description = prof[0], prof[1], prof[2]

        c.execute(
            """
            SELECT
              proposed_address_line_1, proposed_address_line_2, proposed_postal_code,
              proposed_locality_id::text, proposed_country_code,
              proposed_latitude, proposed_longitude
            FROM public.venue_proposal_staging_location
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        loc = c.fetchone()
        if loc:
            (
                address_line_1,
                address_line_2,
                postal_code,
                locality_id,
                country_code,
                latitude,
                longitude,
            ) = loc

        c.execute(
            """
            SELECT proposed_uncertainty_level, regular_hours_json, exceptions_json, notes
            FROM public.venue_proposal_staging_hours
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        hrs = c.fetchone()
        if hrs:
            uncertainty = hrs[0]
            reg = hrs[1] if isinstance(hrs[1], list) else json.loads(hrs[1] or "[]")
            exc = hrs[2] if isinstance(hrs[2], list) else json.loads(hrs[2] or "[]")
            notes = hrs[3]

    if not any(
        (
            display_name,
            short_description,
            long_description,
            address_line_1,
            address_line_2,
            postal_code,
            locality_id,
            country_code,
            latitude is not None,
            longitude is not None,
            reg,
            exc,
            uncertainty,
            notes,
        )
    ):
        return None

    return {
        "display_name": display_name,
        "address_line_1": address_line_1,
        "address_line_2": address_line_2,
        "postal_code": postal_code,
        "locality_id": locality_id,
        "country_code": country_code or "AU",
        "latitude": float(latitude) if latitude is not None else None,
        "longitude": float(longitude) if longitude is not None else None,
        "short_description": short_description,
        "long_description": long_description,
        "opening_hours": {
            "uncertainty_level": uncertainty,
            "regular_hours_json": reg,
            "exceptions_json": exc,
            "notes": notes,
        },
    }


def _load_staged_basics(proposal_id: str) -> dict[str, Any] | None:
    display_name = short_description = address_line_1 = locality_id = None
    uncertainty = notes = None
    reg: list[Any] = []
    exc: list[Any] = []

    with connection.cursor() as c:
        c.execute(
            """
            SELECT proposed_display_name, proposed_short_description
            FROM public.venue_proposal_staging_profile
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        prof = c.fetchone()
        if prof:
            display_name, short_description = prof[0], prof[1]

        c.execute(
            """
            SELECT proposed_address_line_1, proposed_locality_id::text
            FROM public.venue_proposal_staging_location
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        loc = c.fetchone()
        if loc:
            address_line_1, locality_id = loc[0], loc[1]

        c.execute(
            """
            SELECT proposed_uncertainty_level, regular_hours_json, exceptions_json, notes
            FROM public.venue_proposal_staging_hours
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        hrs = c.fetchone()
        if hrs:
            uncertainty = hrs[0]
            reg = hrs[1] if isinstance(hrs[1], list) else json.loads(hrs[1] or "[]")
            exc = hrs[2] if isinstance(hrs[2], list) else json.loads(hrs[2] or "[]")
            notes = hrs[3]

    if not any(
        (display_name, short_description, address_line_1, locality_id, reg, exc, uncertainty, notes)
    ):
        return None

    return {
        "display_name": display_name,
        "short_description": short_description,
        "address_line_1": address_line_1,
        "locality_id": locality_id,
        "hours_ok": _hours_satisfied(
            regular=reg,
            exceptions=exc,
            uncertainty=uncertainty,
            notes=notes,
        ),
    }


def _load_owner_proposals(
    venue_id: str, owner_account_id: UUID
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    draft = {
        "proposal_id": None,
        "lifecycle_status": None,
        "last_saved_at": None,
        "payload_preview": {
            "display_name": None,
            "address_line_1": None,
            "locality_id": None,
        },
        "core_details_payload": None,
    }
    pending = {
        "proposal_id": None,
        "lifecycle_status": None,
        "submitted_at": None,
        "reviewed_at": None,
        "review_outcome": None,
    }
    latest_staged_basics: dict[str, Any] | None = None

    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              p.id::text,
              p.lifecycle_status::text,
              p.created_at,
              p.submitted_at
            FROM public.venue_change_proposal p
            WHERE p.venue_id = %s::uuid
              AND p.actor_type = 'owner'
              AND p.channel = 'owner_portal'
              AND p.actor_owner_account_id = %s::uuid
            ORDER BY p.created_at DESC
            """,
            [venue_id, str(owner_account_id)],
        )
        rows = c.fetchall()

    for row in rows:
        pid, lifecycle, created_at, submitted_at = row
        if lifecycle == "staged" and draft["proposal_id"] is None:
            draft["proposal_id"] = pid
            draft["lifecycle_status"] = lifecycle
            draft["last_saved_at"] = (
                created_at.isoformat() if created_at else None
            )
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT
                      sp.proposed_display_name,
                      sl.proposed_address_line_1,
                      sl.proposed_locality_id::text
                    FROM public.venue_change_proposal p
                    LEFT JOIN public.venue_proposal_staging_profile sp
                      ON sp.venue_change_proposal_id = p.id
                    LEFT JOIN public.venue_proposal_staging_location sl
                      ON sl.venue_change_proposal_id = p.id
                    WHERE p.id = %s::uuid
                    """,
                    [pid],
                )
                prev = c.fetchone()
            if prev:
                draft["payload_preview"] = {
                    "display_name": prev[0],
                    "address_line_1": prev[1],
                    "locality_id": prev[2],
                }
            draft["core_details_payload"] = _load_staged_core_details_payload(pid)
            latest_staged_basics = _load_staged_basics(pid)

        if submitted_at is not None and pending["proposal_id"] is None:
            if lifecycle in ("in_review", "staged", "approved", "rejected"):
                pending["proposal_id"] = pid
                pending["lifecycle_status"] = lifecycle
                pending["submitted_at"] = submitted_at.isoformat()
                with connection.cursor() as c:
                    c.execute(
                        """
                        SELECT review_outcome, reviewed_at
                        FROM public.proposal_review
                        WHERE venue_change_proposal_id = %s::uuid
                        ORDER BY review_sequence DESC
                        LIMIT 1
                        """,
                        [pid],
                    )
                    rev = c.fetchone()
                if rev:
                    pending["review_outcome"] = rev[0]
                    pending["reviewed_at"] = (
                        rev[1].isoformat() if rev[1] else None
                    )

    return draft, pending, latest_staged_basics


def _derive_onboarding_status(
    *,
    required_basics_complete: bool,
    has_owner_proposal_ever: bool,
    draft: dict[str, Any],
    pending: dict[str, Any],
) -> str:
    outcome = pending.get("review_outcome")
    lifecycle = pending.get("lifecycle_status")
    if outcome in ("rejected", "changes_requested"):
        return "needs_changes"
    if lifecycle == "rejected":
        return "needs_changes"
    if pending.get("proposal_id") and lifecycle in ("in_review", "staged"):
        if pending.get("submitted_at"):
            return "submitted"
    if draft.get("proposal_id"):
        return "in_progress"
    if required_basics_complete and not draft.get("proposal_id"):
        if lifecycle not in ("in_review", "staged") or not pending.get("proposal_id"):
            return "complete"
    if not has_owner_proposal_ever and not required_basics_complete:
        return "not_started"
    return "in_progress"


def _count_pending_proposals(venue_id: str, owner_account_id: UUID) -> int:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.venue_change_proposal p
            WHERE p.venue_id = %s::uuid
              AND p.actor_type = 'owner'
              AND p.channel = 'owner_portal'
              AND p.actor_owner_account_id = %s::uuid
              AND p.submitted_at IS NOT NULL
              AND p.lifecycle_status IN ('in_review', 'staged')
            """,
            [venue_id, str(owner_account_id)],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


def _has_owner_core_proposal_ever(venue_id: str, owner_account_id: UUID) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1
            FROM public.venue_change_proposal p
            INNER JOIN public.venue_proposal_target t
              ON t.venue_change_proposal_id = p.id
            WHERE p.venue_id = %s::uuid
              AND p.actor_type = 'owner'
              AND p.channel = 'owner_portal'
              AND p.actor_owner_account_id = %s::uuid
              AND t.target_family IN ('profile', 'geo', 'hours')
            LIMIT 1
            """,
            [venue_id, str(owner_account_id)],
        )
        return c.fetchone() is not None


def list_owner_venues(auth: AuthContext) -> dict[str, Any]:
    owner_id = get_owner_account_id(auth)
    if owner_id is None:
        return {"venues": [], "meta": {"total": 0, "default_venue_id": None}}

    with connection.cursor() as c:
        c.execute(
            """
            SELECT DISTINCT
              v.id::text,
              COALESCE(vpp.display_name, 'Venue') AS display_name,
              l.name AS locality_name,
              COALESCE(
                CASE WHEN gr.region_level = 'state' THEN gr.region_code END,
                pgr.region_code
              ) AS state_code,
              bvmr.relationship_lifecycle::text
            FROM public.owner_business_membership obm
            INNER JOIN public.business_venue_management_relationship bvmr
              ON bvmr.business_id = obm.business_id
            INNER JOIN public.venue v ON v.id = bvmr.venue_id
            LEFT JOIN public.venue_published_profile vpp ON vpp.venue_id = v.id
            LEFT JOIN public.venue_published_location vpl ON vpl.venue_id = v.id
            LEFT JOIN public.locality l ON l.id = vpl.locality_id
            LEFT JOIN public.geographic_region gr ON gr.id = l.geographic_region_id
            LEFT JOIN public.geographic_region pgr ON pgr.id = gr.parent_region_id
            WHERE obm.owner_account_id = %s::uuid
              AND obm.membership_status = 'active'
              AND bvmr.relationship_lifecycle = 'approved'
            ORDER BY display_name ASC
            """,
            [str(owner_id)],
        )
        rows = c.fetchall()

    venues: list[dict[str, Any]] = []
    for row in rows:
        vid = row[0]
        published = _load_published_snapshot(vid)
        draft, pending, staged_basics = _load_owner_proposals(vid, owner_id)
        basics = _merge_basics_sources(
            published=published["basics"],
            staged=staged_basics,
        )
        completeness = _compute_venue_completeness(vid, basics, pending)
        venues.append(
            {
                "venue_id": vid,
                "display_name": row[1],
                "locality_name": row[2],
                "state_code": row[3],
                "relationship_lifecycle": "approved",
                "onboarding_status": _derive_onboarding_status(
                    required_basics_complete=completeness["required_basics_complete"],
                    has_owner_proposal_ever=_has_owner_core_proposal_ever(
                        vid, owner_id
                    ),
                    draft=draft,
                    pending=pending,
                ),
                "pending_proposal_count": _count_pending_proposals(vid, owner_id),
                "completeness_percent": completeness["percent"],
                "required_basics_complete": completeness["required_basics_complete"],
            }
        )

    total = len(venues)
    meta: dict[str, Any] = {"total": total, "default_venue_id": None}
    if total == 1:
        meta["default_venue_id"] = venues[0]["venue_id"]
    return {"venues": venues, "meta": meta}


def get_owner_venue_detail(
    auth: AuthContext, venue_id: str
) -> tuple[dict[str, Any] | None, str]:
    access, err = assert_owner_manages_venue(auth, venue_id)
    if access is None:
        return None, err

    published = _load_published_snapshot(venue_id)
    draft, pending, staged_basics = _load_owner_proposals(
        venue_id, access.owner_account_id
    )
    basics = _merge_basics_sources(
        published=published["basics"],
        staged=staged_basics,
    )
    completeness = _compute_venue_completeness(venue_id, basics, pending)
    caps = _load_capabilities(access.relationship_id, access.owner_account_id)
    (
        _features_status,
        _meal_specials_status,
        _tap_list_status,
        _photos_status,
        photos_available,
    ) = _load_section_statuses(venue_id)

    display_name = (
        published["profile"].get("display_name")
        or draft["payload_preview"].get("display_name")
        or "Venue"
    )

    return {
        "venue_id": venue_id,
        "display_name": display_name,
        "listing": published["listing"],
        "relationship": {
            "lifecycle": "approved",
            "business_id": str(access.business_id),
            "capabilities": caps,
        },
        "published": {
            "profile": published["profile"],
            "location": published["location"],
            "descriptions": published["descriptions"],
            "hours": published["hours"],
            "contact": published["contact"],
        },
        "draft": draft,
        "pending_review": pending,
        "completeness": {
            "percent": completeness["percent"],
            "required_basics_complete": completeness["required_basics_complete"],
            "sections": completeness["sections"],
            "restricted_pending_review": completeness["restricted_pending_review"],
        },
        "sections_available": {
            "core_details": True,
            "events": False,
            "meal_specials": True,
            "tap_list": True,
            "features": True,
            "photos": photos_available,
            "menus": False,
        },
    }, "ok"


def _validate_opening_hours(
    opening_hours: Any, *, submit: bool
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if opening_hours is None:
        if submit:
            return None, {"opening_hours": ["Opening hours are required on submit."]}
        return None, None
    if not isinstance(opening_hours, dict):
        return None, {"opening_hours": ["opening_hours must be an object."]}

    details: dict[str, list[str]] = {}
    unc = opening_hours.get("uncertainty_level", "resolved_confident")
    if unc is not None and (not isinstance(unc, str) or unc not in _UNCERTAINTY):
        details["opening_hours.uncertainty_level"] = [
            "uncertainty_level has an invalid value."
        ]
    reg = opening_hours.get("regular_hours_json", [])
    exc = opening_hours.get("exceptions_json", [])
    notes = opening_hours.get("notes")
    if reg is None:
        reg = []
    if exc is None:
        exc = []
    if not isinstance(reg, list):
        details["opening_hours.regular_hours_json"] = ["Must be an array."]
        reg = []
    if not isinstance(exc, list):
        details["opening_hours.exceptions_json"] = ["Must be an array."]
        exc = []

    for i, row in enumerate(reg):
        if not isinstance(row, dict):
            details[f"opening_hours.regular_hours_json[{i}]"] = [
                "Each row must be an object."
            ]
            continue
        dow = row.get("day_of_week")
        if not isinstance(dow, int) or dow < 0 or dow > 6:
            details[f"opening_hours.regular_hours_json[{i}].day_of_week"] = [
                "day_of_week must be an integer 0–6."
            ]
        for tk in ("opens_at", "closes_at"):
            tv = row.get(tk)
            if not isinstance(tv, str) or not _TIME_RE.fullmatch(tv):
                details[f"opening_hours.regular_hours_json[{i}].{tk}"] = [
                    "Time must be HH:MM (24-hour)."
                ]

    if submit and not details:
        if not _hours_satisfied(
            regular=reg,
            exceptions=exc,
            uncertainty=unc if isinstance(unc, str) else None,
            notes=notes if isinstance(notes, str) else None,
        ):
            details["opening_hours"] = [
                "Provide regular hours, exceptions, a non-confident uncertainty level, or notes (min 10 characters)."
            ]

    if details:
        return None, details

    return {
        "uncertainty_level": unc,
        "regular_hours_json": reg,
        "exceptions_json": exc,
        "notes": notes,
    }, None


def _validate_core_payload(
    payload: Any, *, intent: str
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(payload, dict):
        return None, {"payload": ["payload must be a JSON object."]}

    unsupported = sorted(_UNSUPPORTED_PAYLOAD_KEYS.intersection(payload.keys()))
    if unsupported:
        return None, {
            k: ["This field is not supported in Phase A."]
            for k in unsupported
        }

    submit = intent == "submit"
    details: dict[str, list[str]] = {}
    out: dict[str, Any] = {}

    def req_str(key: str, *, min_len: int, max_len: int, required: bool) -> None:
        raw = payload.get(key)
        if raw is None:
            if required and submit:
                details[key] = ["This field is required."]
            return
        if not isinstance(raw, str):
            details[key] = ["Must be a string."]
            return
        val = raw.strip()
        if required and submit and not val:
            details[key] = ["This field is required."]
            return
        if val and (len(val) < min_len or len(val) > max_len):
            details[key] = [f"Must be between {min_len} and {max_len} characters."]
            return
        if val:
            out[key] = val

    req_str("display_name", min_len=2, max_len=120, required=True)
    req_str("address_line_1", min_len=3, max_len=200, required=True)

    line_2 = payload.get("address_line_2")
    if line_2 is not None:
        if not isinstance(line_2, str):
            details["address_line_2"] = ["Must be a string or null."]
        else:
            v2 = line_2.strip()
            if len(v2) > 200:
                details["address_line_2"] = ["Must be at most 200 characters."]
            else:
                out["address_line_2"] = v2 or None

    pc = payload.get("postal_code")
    if pc is not None:
        if not isinstance(pc, str):
            details["postal_code"] = ["Must be a string."]
        else:
            pv = pc.strip()
            if pv and (len(pv) > 12 or not _POSTAL_RE.fullmatch(pv)):
                details["postal_code"] = [
                    "Must be at most 12 characters (letters, digits, spaces, hyphens)."
                ]
            elif pv:
                out["postal_code"] = pv

    loc = payload.get("locality_id")
    if loc is None:
        if submit:
            details["locality_id"] = ["This field is required."]
    elif _bad_uuid(loc):
        details["locality_id"] = ["Must be a valid UUID."]
    else:
        loc_s = str(loc)
        if submit and not _locality_exists(loc_s):
            details["locality_id"] = ["locality_id does not reference an existing locality."]
        else:
            out["locality_id"] = loc_s

    cc = payload.get("country_code")
    if cc is None:
        out["country_code"] = "AU"
    elif not isinstance(cc, str) or not re.fullmatch(r"[A-Za-z]{2}", cc):
        details["country_code"] = ["Must be a two-letter ISO country code."]
    else:
        out["country_code"] = cc.upper()

    lat = payload.get("latitude")
    lng = payload.get("longitude")
    if (lat is None) != (lng is None):
        details["latitude"] = ["latitude and longitude must be provided together."]
        details["longitude"] = ["latitude and longitude must be provided together."]
    else:
        for key, val in (("latitude", lat), ("longitude", lng)):
            if val is None:
                continue
            if not isinstance(val, (int, float)):
                details[key] = ["Must be a number or null."]
            elif key == "latitude" and not (-90 <= float(val) <= 90):
                details["latitude"] = ["Must be between -90 and 90."]
            elif key == "longitude" and not (-180 <= float(val) <= 180):
                details["longitude"] = ["Must be between -180 and 180."]
            else:
                out[key] = float(val)

    sd = payload.get("short_description")
    if sd is None:
        if submit:
            details["short_description"] = ["This field is required."]
    elif not isinstance(sd, str):
        details["short_description"] = ["Must be a string."]
    else:
        sval = sd.strip()
        if submit and not sval:
            details["short_description"] = ["This field is required."]
        elif sval and len(sval) > 500:
            details["short_description"] = ["Must be at most 500 characters."]
        elif sval:
            out["short_description"] = sval

    ld = payload.get("long_description")
    if ld is not None:
        if not isinstance(ld, str):
            details["long_description"] = ["Must be a string or null."]
        else:
            lv = ld.strip()
            if lv and len(lv) > 2000:
                details["long_description"] = ["Must be at most 2000 characters."]
            else:
                out["long_description"] = lv or None

    hours_pack, hours_err = _validate_opening_hours(
        payload.get("opening_hours"), submit=submit
    )
    if hours_err:
        details.update(hours_err)
    elif hours_pack is not None:
        out["opening_hours"] = hours_pack

    confirm = payload.get("owner_confirms_management")
    if confirm is not None and not isinstance(confirm, bool):
        details["owner_confirms_management"] = ["Must be a boolean."]

    if details:
        return None, details
    return out, None


def _owner_ever_submitted(venue_id: str, owner_account_id: UUID) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1
            FROM public.venue_change_proposal
            WHERE venue_id = %s::uuid
              AND actor_owner_account_id = %s::uuid
              AND actor_type = 'owner'
              AND submitted_at IS NOT NULL
            LIMIT 1
            """,
            [venue_id, str(owner_account_id)],
        )
        return c.fetchone() is not None


def _find_open_in_review_proposal(
    venue_id: str, owner_account_id: UUID
) -> dict[str, Any] | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id::text, submitted_at
            FROM public.venue_change_proposal
            WHERE venue_id = %s::uuid
              AND actor_type = 'owner'
              AND channel = 'owner_portal'
              AND actor_owner_account_id = %s::uuid
              AND lifecycle_status = 'in_review'
            ORDER BY submitted_at DESC NULLS LAST, created_at DESC
            LIMIT 1
            """,
            [venue_id, str(owner_account_id)],
        )
        row = c.fetchone()
    if not row:
        return None
    submitted_at = row[1]
    return {
        "proposal_id": row[0],
        "lifecycle_status": "in_review",
        "submitted_at": submitted_at.isoformat() if submitted_at else None,
    }


def _find_open_staged_proposal(venue_id: str, owner_account_id: UUID) -> str | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id::text
            FROM public.venue_change_proposal
            WHERE venue_id = %s::uuid
              AND actor_type = 'owner'
              AND channel = 'owner_portal'
              AND actor_owner_account_id = %s::uuid
              AND lifecycle_status = 'staged'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [venue_id, str(owner_account_id)],
        )
        row = c.fetchone()
    return str(row[0]) if row else None


def _latest_proposal_terminal(venue_id: str, owner_account_id: UUID) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT lifecycle_status::text
            FROM public.venue_change_proposal
            WHERE venue_id = %s::uuid
              AND actor_type = 'owner'
              AND channel = 'owner_portal'
              AND actor_owner_account_id = %s::uuid
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [venue_id, str(owner_account_id)],
        )
        row = c.fetchone()
    if not row:
        return False
    return row[0] in _TERMINAL_PROPOSAL_STATUSES


def _upsert_proposal_targets(proposal_id: str) -> None:
    with connection.cursor() as c:
        for tf in _CORE_TARGETS:
            c.execute(
                """
                INSERT INTO public.venue_proposal_target (venue_change_proposal_id, target_family)
                VALUES (%s::uuid, %s)
                ON CONFLICT (venue_change_proposal_id, target_family) DO NOTHING
                """,
                [proposal_id, tf],
            )


def _upsert_staging_rows(
    proposal_id: str, venue_id: str, fields: dict[str, Any]
) -> None:
    hours = fields.get("opening_hours") or {}
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_proposal_staging_profile (
                venue_change_proposal_id, venue_id,
                proposed_display_name, proposed_short_description, proposed_long_description
            ) VALUES (%s::uuid, %s::uuid, %s, %s, %s)
            ON CONFLICT (venue_change_proposal_id) DO UPDATE SET
                proposed_display_name = EXCLUDED.proposed_display_name,
                proposed_short_description = EXCLUDED.proposed_short_description,
                proposed_long_description = EXCLUDED.proposed_long_description
            """,
            [
                proposal_id,
                venue_id,
                fields.get("display_name"),
                fields.get("short_description"),
                fields.get("long_description"),
            ],
        )
        c.execute(
            """
            INSERT INTO public.venue_proposal_staging_location (
                venue_change_proposal_id, venue_id,
                proposed_locality_id, proposed_address_line_1, proposed_address_line_2,
                proposed_postal_code, proposed_country_code,
                proposed_latitude, proposed_longitude
            ) VALUES (
                %s::uuid, %s::uuid,
                %s::uuid, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (venue_change_proposal_id) DO UPDATE SET
                proposed_locality_id = EXCLUDED.proposed_locality_id,
                proposed_address_line_1 = EXCLUDED.proposed_address_line_1,
                proposed_address_line_2 = EXCLUDED.proposed_address_line_2,
                proposed_postal_code = EXCLUDED.proposed_postal_code,
                proposed_country_code = EXCLUDED.proposed_country_code,
                proposed_latitude = EXCLUDED.proposed_latitude,
                proposed_longitude = EXCLUDED.proposed_longitude
            """,
            [
                proposal_id,
                venue_id,
                fields.get("locality_id"),
                fields.get("address_line_1"),
                fields.get("address_line_2"),
                fields.get("postal_code"),
                fields.get("country_code", "AU"),
                fields.get("latitude"),
                fields.get("longitude"),
            ],
        )
        c.execute(
            """
            INSERT INTO public.venue_proposal_staging_hours (
                venue_change_proposal_id, venue_id,
                proposed_uncertainty_level,
                regular_hours_json, exceptions_json, notes
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s::jsonb, %s::jsonb, %s
            )
            ON CONFLICT (venue_change_proposal_id) DO UPDATE SET
                proposed_uncertainty_level = EXCLUDED.proposed_uncertainty_level,
                regular_hours_json = EXCLUDED.regular_hours_json,
                exceptions_json = EXCLUDED.exceptions_json,
                notes = EXCLUDED.notes
            """,
            [
                proposal_id,
                venue_id,
                hours.get("uncertainty_level"),
                json.dumps(hours.get("regular_hours_json", [])),
                json.dumps(hours.get("exceptions_json", [])),
                hours.get("notes"),
            ],
        )


def _count_published_profile_rows(venue_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            "SELECT COUNT(*)::int FROM public.venue_published_profile WHERE venue_id = %s::uuid",
            [venue_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


@transaction.atomic
def create_or_update_owner_core_details_proposal(
    auth: AuthContext,
    venue_id: str,
    *,
    section: str,
    intent: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_manages_venue(auth, venue_id)
    if access is None:
        return None, err, None

    if section != "core_details":
        return None, "validation_error", {
            "section": ["Only section 'core_details' is supported in Phase A."]
        }
    if intent not in ("draft", "submit"):
        return None, "validation_error", {
            "intent": ["intent must be 'draft' or 'submit'."]
        }

    fields, val_err = _validate_core_payload(payload, intent=intent)
    if val_err:
        return None, "validation_error", val_err

    existing_in_review = _find_open_in_review_proposal(
        venue_id, access.owner_account_id
    )
    if existing_in_review is not None:
        if intent == "submit":
            return {
                "proposal_id": existing_in_review["proposal_id"],
                "venue_id": venue_id,
                "section": "core_details",
                "intent": "submit",
                "lifecycle_status": "in_review",
                "submitted_at": existing_in_review["submitted_at"],
                "message": "Your changes are already submitted for review.",
            }, "already_in_review", None
        return None, "proposal_already_in_review", None

    if intent == "submit":
        if not _owner_ever_submitted(venue_id, access.owner_account_id):
            if payload.get("owner_confirms_management") is not True:
                return None, "validation_error", {
                    "owner_confirms_management": [
                        "You must confirm you manage this venue before first submit."
                    ]
                }

    proposal_id: str | None = None
    if intent == "draft":
        proposal_id = _find_open_staged_proposal(
            venue_id, access.owner_account_id
        )
    elif _find_open_staged_proposal(venue_id, access.owner_account_id):
        proposal_id = _find_open_staged_proposal(
            venue_id, access.owner_account_id
        )
    elif _latest_proposal_terminal(venue_id, access.owner_account_id):
        proposal_id = None
    else:
        proposal_id = _find_open_staged_proposal(
            venue_id, access.owner_account_id
        )

    now = datetime.now(timezone.utc)
    lifecycle = "in_review" if intent == "submit" else "staged"
    submitted_at = now if intent == "submit" else None

    profile_before = _count_published_profile_rows(venue_id)

    if proposal_id is None:
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.venue_change_proposal (
                    venue_id,
                    actor_type,
                    actor_owner_account_id,
                    channel,
                    proposal_kind,
                    lifecycle_status,
                    submitted_at
                ) VALUES (
                    %s::uuid, 'owner', %s::uuid, 'owner_portal', 'field_family',
                    %s, %s
                )
                RETURNING id::text
                """,
                [
                    venue_id,
                    str(access.owner_account_id),
                    lifecycle,
                    submitted_at,
                ],
            )
            proposal_id = c.fetchone()[0]
    else:
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE public.venue_change_proposal
                SET lifecycle_status = %s,
                    submitted_at = %s
                WHERE id = %s::uuid
                """,
                [lifecycle, submitted_at, proposal_id],
            )

    _upsert_proposal_targets(proposal_id)
    if fields:
        _upsert_staging_rows(proposal_id, venue_id, fields)

    profile_after = _count_published_profile_rows(venue_id)
    if profile_after != profile_before:
        logger.error(
            "Owner proposal unexpectedly changed published profile count for venue %s",
            venue_id,
        )

    if intent == "draft":
        message = (
            "Draft saved. You can continue editing or submit for review when ready."
        )
    else:
        message = (
            "Submitted for review. Your changes will be reviewed before they "
            "appear publicly."
        )

    return {
        "proposal_id": proposal_id,
        "venue_id": venue_id,
        "section": "core_details",
        "intent": intent,
        "lifecycle_status": lifecycle,
        "submitted_at": submitted_at.isoformat() if submitted_at else None,
        "message": message,
    }, "ok", None


def _load_descriptive_copy(venue_id: str) -> dict[str, str | None]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT short_description, long_description
            FROM public.venue_published_descriptive_copy
            WHERE venue_id = %s::uuid
            """,
            [venue_id],
        )
        row = c.fetchone()
    if not row:
        return {"short_description": None, "long_description": None}
    return {"short_description": row[0], "long_description": row[1]}


def _write_owner_direct_edit_audit(
    *,
    owner_account_id: UUID,
    venue_id: str,
    entity_table: str,
    field_family: str,
    endpoint: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.audit_event (
                actor_type,
                actor_owner_account_id,
                entity_table,
                entity_id,
                action,
                detail
            ) VALUES (
                'owner',
                %s::uuid,
                %s,
                %s::uuid,
                'owner_direct_edit',
                %s::jsonb
            )
            """,
            [
                str(owner_account_id),
                entity_table,
                venue_id,
                json.dumps(
                    {
                        "field_family": field_family,
                        "endpoint": endpoint,
                        "channel": "owner_portal",
                        "before": before,
                        "after": after,
                    }
                ),
            ],
        )


def _validate_operational_profile_patch(
    body: Any,
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(body, dict):
        return None, {"body": ["Request body must be a JSON object."]}

    unknown = sorted(
        set(body.keys())
        - _OPERATIONAL_PROFILE_ALLOWED_KEYS
        - _OPERATIONAL_PROFILE_FORBIDDEN_KEYS
    )
    details: dict[str, list[str]] = {}
    if unknown:
        for key in unknown:
            details[key] = ["Unknown field."]

    forbidden = sorted(_OPERATIONAL_PROFILE_FORBIDDEN_KEYS.intersection(body.keys()))
    for key in forbidden:
        details[key] = ["This field cannot be updated on this endpoint."]

    if not _OPERATIONAL_PROFILE_ALLOWED_KEYS.intersection(body.keys()):
        details.setdefault("body", []).append(
            "At least one of short_description or long_description must be provided."
        )

    out: dict[str, Any] = {}
    for key in ("short_description", "long_description"):
        if key not in body:
            continue
        val = body[key]
        if val is None:
            out[key] = None
            continue
        if not isinstance(val, str):
            details[key] = ["Must be a string or null."]
            continue
        trimmed = val.strip()
        max_len = 500 if key == "short_description" else 2000
        if len(trimmed) > max_len:
            details[key] = [f"Must be at most {max_len} characters."]
        else:
            out[key] = trimmed or None

    if details:
        return None, details
    return out, None


@transaction.atomic
def patch_owner_operational_profile(
    auth: AuthContext,
    venue_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    fields, val_err = _validate_operational_profile_patch(body)
    if val_err:
        return None, "validation_error", val_err

    before = _load_descriptive_copy(venue_id)
    after = dict(before)
    for key, val in (fields or {}).items():
        after[key] = val

    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_published_descriptive_copy (
                venue_id, short_description, long_description, updated_at
            ) VALUES (%s::uuid, %s, %s, now())
            ON CONFLICT (venue_id) DO UPDATE SET
                short_description = EXCLUDED.short_description,
                long_description = EXCLUDED.long_description,
                updated_at = now()
            """,
            [
                venue_id,
                after["short_description"],
                after["long_description"],
            ],
        )

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_published_descriptive_copy",
        field_family="descriptions",
        endpoint=f"/api/v1/owner/venues/{venue_id}/operational-profile",
        before=before,
        after=after,
    )

    return {
        "venue_id": venue_id,
        "updated": {
            "short_description": after["short_description"],
            "long_description": after["long_description"],
        },
        "message": "Changes saved.",
    }, "ok", None


def _validate_hours_patch_body(
    body: Any,
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(body, dict):
        return None, {"body": ["Request body must be a JSON object."]}

    details: dict[str, list[str]] = {}
    forbidden = sorted(_HOURS_PATCH_FORBIDDEN_KEYS.intersection(body.keys()))
    for key in forbidden:
        details[key] = ["This field cannot be updated on this endpoint."]

    unknown = sorted(
        set(body.keys())
        - {"uncertainty_level", "regular_hours_json", "exceptions_json", "notes"}
        - _HOURS_PATCH_FORBIDDEN_KEYS
    )
    for key in unknown:
        details[key] = ["Unknown field."]

    if details:
        return None, details

    hours_pack, hours_err = _validate_opening_hours(body, submit=True)
    if hours_err:
        return None, hours_err

    notes = body.get("notes")
    if isinstance(notes, str) and len(notes.strip()) > _HOURS_NOTES_MAX_LEN:
        return None, {
            "notes": [f"Must be at most {_HOURS_NOTES_MAX_LEN} characters."]
        }

    exc = body.get("exceptions_json", [])
    if isinstance(exc, list) and len(exc) > 0:
        return None, {
            "exceptions_json": [
                "Structured hour exceptions are not supported on this endpoint yet."
            ]
        }

    return hours_pack, None


def _load_published_hours_for_response(venue_id: str) -> dict[str, Any]:
    uncertainty = get_published_hours_uncertainty(venue_id) or "resolved_confident"
    notes: str | None = None
    with connection.cursor() as c:
        c.execute(
            """
            SELECT notes
            FROM public.venue_hours_uncertainty
            WHERE venue_id = %s::uuid
            """,
            [venue_id],
        )
        unc_row = c.fetchone()
        if unc_row:
            notes = unc_row[0]

        regular: list[dict[str, Any]] = []
        c.execute(
            """
            SELECT day_of_week, opens_at, closes_at, crosses_midnight
            FROM public.venue_hours_regular
            WHERE venue_id = %s::uuid
            ORDER BY day_of_week, sort_order, opens_at
            """,
            [venue_id],
        )
        for r in c.fetchall():
            regular.append(
                {
                    "day_of_week": int(r[0]),
                    "opens_at": _time_to_hhmm(r[1]),
                    "closes_at": _time_to_hhmm(r[2]),
                    "crosses_midnight": bool(r[3]),
                }
            )

        exceptions: list[dict[str, Any]] = []
        c.execute(
            """
            SELECT start_date, end_date, exception_kind, opens_at, closes_at,
                   crosses_midnight, note
            FROM public.venue_hours_exception
            WHERE venue_id = %s::uuid
            ORDER BY start_date
            """,
            [venue_id],
        )
        for r in c.fetchall():
            exceptions.append(
                {
                    "start_date": r[0].isoformat() if r[0] else None,
                    "end_date": r[1].isoformat() if r[1] else None,
                    "exception_kind": r[2],
                    "opens_at": _time_to_hhmm(r[3]) if r[3] else None,
                    "closes_at": _time_to_hhmm(r[4]) if r[4] else None,
                    "crosses_midnight": bool(r[5]),
                    "note": r[6],
                }
            )

    return {
        "uncertainty_level": uncertainty,
        "regular": regular,
        "exceptions": exceptions,
        "notes": notes,
    }


def _snapshot_hours_for_audit(venue_id: str) -> dict[str, Any]:
    block = _load_published_hours_for_response(venue_id)
    return {
        "uncertainty_level": block["uncertainty_level"],
        "regular_hours_json": block["regular"],
        "exceptions_json": block["exceptions"],
        "notes": block["notes"],
    }


@transaction.atomic
def patch_owner_venue_hours(
    auth: AuthContext,
    venue_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    hours_pack, val_err = _validate_hours_patch_body(body)
    if val_err:
        return None, "validation_error", val_err
    assert hours_pack is not None

    before = _snapshot_hours_for_audit(venue_id)

    reg = hours_pack.get("regular_hours_json") or []
    unc = hours_pack.get("uncertainty_level") or "resolved_confident"
    notes = hours_pack.get("notes")
    if isinstance(notes, str):
        notes = notes.strip() or None

    with connection.cursor() as c:
        c.execute(
            "DELETE FROM public.venue_hours_regular WHERE venue_id = %s::uuid",
            [venue_id],
        )
        for index, row in enumerate(reg):
            if not isinstance(row, dict):
                continue
            c.execute(
                """
                INSERT INTO public.venue_hours_regular (
                    venue_id, day_of_week, opens_at, closes_at,
                    crosses_midnight, sort_order, updated_at
                ) VALUES (
                    %s::uuid, %s, %s::time, %s::time, %s, %s, now()
                )
                """,
                [
                    venue_id,
                    int(row["day_of_week"]),
                    row["opens_at"],
                    row["closes_at"],
                    bool(row.get("crosses_midnight", False)),
                    int(row.get("sort_order", index)),
                ],
            )

        if body.get("exceptions_json") is not None:
            c.execute(
                "DELETE FROM public.venue_hours_exception WHERE venue_id = %s::uuid",
                [venue_id],
            )

        c.execute(
            """
            INSERT INTO public.venue_hours_uncertainty (
                venue_id, uncertainty_level, notes, updated_at
            ) VALUES (%s::uuid, %s, %s, now())
            ON CONFLICT (venue_id) DO UPDATE SET
                uncertainty_level = EXCLUDED.uncertainty_level,
                notes = EXCLUDED.notes,
                updated_at = now()
            """,
            [venue_id, unc, notes],
        )

    after_block = _load_published_hours_for_response(venue_id)
    after = {
        "uncertainty_level": after_block["uncertainty_level"],
        "regular_hours_json": after_block["regular"],
        "exceptions_json": after_block["exceptions"],
        "notes": after_block["notes"],
    }

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_hours_regular",
        field_family="hours",
        endpoint=f"/api/v1/owner/venues/{venue_id}/hours",
        before=before,
        after=after,
    )

    return {
        "venue_id": venue_id,
        "hours": after_block,
        "message": "Opening hours saved.",
    }, "ok", None


def _find_open_in_review_restricted_proposal(
    venue_id: str, owner_account_id: UUID
) -> dict[str, Any] | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT p.id::text, p.submitted_at
            FROM public.venue_change_proposal p
            WHERE p.venue_id = %s::uuid
              AND p.actor_type = 'owner'
              AND p.channel = 'owner_portal'
              AND p.actor_owner_account_id = %s::uuid
              AND p.lifecycle_status = 'in_review'
              AND NOT EXISTS (
                SELECT 1
                FROM public.venue_proposal_target t
                WHERE t.venue_change_proposal_id = p.id
                  AND t.target_family = 'hours'
              )
            ORDER BY p.submitted_at DESC NULLS LAST, p.created_at DESC
            LIMIT 1
            """,
            [venue_id, str(owner_account_id)],
        )
        row = c.fetchone()
    if not row:
        return None
    submitted_at = row[1]
    return {
        "proposal_id": row[0],
        "lifecycle_status": "in_review",
        "submitted_at": submitted_at.isoformat() if submitted_at else None,
    }


def _validate_restricted_identity_payload(
    payload: Any,
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(payload, dict):
        return None, {"payload": ["payload must be a JSON object."]}

    details: dict[str, list[str]] = {}
    forbidden = sorted(_RESTRICTED_FORBIDDEN_PAYLOAD_KEYS.intersection(payload.keys()))
    for key in forbidden:
        details[key] = ["This field cannot be included in a restricted change request."]

    unsupported = sorted(_UNSUPPORTED_PAYLOAD_KEYS.intersection(payload.keys()))
    for key in unsupported:
        details[key] = ["This field is not supported."]

    if details:
        return None, details

    out: dict[str, Any] = {}

    dn = payload.get("display_name")
    if dn is not None:
        if not isinstance(dn, str):
            details["display_name"] = ["Must be a string."]
        else:
            val = dn.strip()
            if val and (len(val) < 2 or len(val) > 120):
                details["display_name"] = ["Must be between 2 and 120 characters."]
            elif val:
                out["display_name"] = val

    raw_addr = payload.get("address_line_1")
    if raw_addr is not None:
        if not isinstance(raw_addr, str):
            details["address_line_1"] = ["Must be a string."]
        else:
            val = raw_addr.strip()
            if val and (len(val) < 3 or len(val) > 200):
                details["address_line_1"] = ["Must be between 3 and 200 characters."]
            elif val:
                out["address_line_1"] = val

    line_2 = payload.get("address_line_2")
    if line_2 is not None:
        if not isinstance(line_2, str):
            details["address_line_2"] = ["Must be a string or null."]
        else:
            v2 = line_2.strip()
            if len(v2) > 200:
                details["address_line_2"] = ["Must be at most 200 characters."]
            else:
                out["address_line_2"] = v2 or None

    pc = payload.get("postal_code")
    if pc is not None:
        if not isinstance(pc, str):
            details["postal_code"] = ["Must be a string."]
        else:
            pv = pc.strip()
            if pv and (len(pv) > 12 or not _POSTAL_RE.fullmatch(pv)):
                details["postal_code"] = [
                    "Must be at most 12 characters (letters, digits, spaces, hyphens)."
                ]
            elif pv:
                out["postal_code"] = pv

    loc = payload.get("locality_id")
    if loc is not None:
        if _bad_uuid(loc):
            details["locality_id"] = ["Must be a valid UUID."]
        else:
            loc_s = str(loc)
            if not _locality_exists(loc_s):
                details["locality_id"] = [
                    "locality_id does not reference an existing locality."
                ]
            else:
                out["locality_id"] = loc_s

    cc = payload.get("country_code")
    if cc is None and any(
        k in out for k in ("address_line_1", "address_line_2", "postal_code", "locality_id")
    ):
        out["country_code"] = "AU"
    elif cc is not None:
        if not isinstance(cc, str) or not re.fullmatch(r"[A-Za-z]{2}", cc):
            details["country_code"] = ["Must be a two-letter ISO country code."]
        else:
            out["country_code"] = cc.upper()

    lat = payload.get("latitude")
    lng = payload.get("longitude")
    if (lat is None) != (lng is None):
        details["latitude"] = ["latitude and longitude must be provided together."]
        details["longitude"] = ["latitude and longitude must be provided together."]
    else:
        for key, val in (("latitude", lat), ("longitude", lng)):
            if val is None:
                continue
            if not isinstance(val, (int, float)):
                details[key] = ["Must be a number or null."]
            elif key == "latitude" and not (-90 <= float(val) <= 90):
                details["latitude"] = ["Must be between -90 and 90."]
            elif key == "longitude" and not (-180 <= float(val) <= 180):
                details["longitude"] = ["Must be between -180 and 180."]
            else:
                out[key] = float(val)

    if not out:
        details.setdefault("payload", []).append(
            "At least one restricted field must be provided."
        )

    if details:
        return None, details
    return out, None


def _upsert_restricted_staging_rows(
    proposal_id: str, venue_id: str, fields: dict[str, Any]
) -> None:
    with connection.cursor() as c:
        if "display_name" in fields:
            c.execute(
                """
                INSERT INTO public.venue_proposal_staging_profile (
                    venue_change_proposal_id, venue_id, proposed_display_name
                ) VALUES (%s::uuid, %s::uuid, %s)
                ON CONFLICT (venue_change_proposal_id) DO UPDATE SET
                    proposed_display_name = EXCLUDED.proposed_display_name
                """,
                [proposal_id, venue_id, fields.get("display_name")],
            )

        geo_keys = (
            "address_line_1",
            "address_line_2",
            "postal_code",
            "locality_id",
            "country_code",
            "latitude",
            "longitude",
        )
        if any(k in fields for k in geo_keys):
            c.execute(
                """
                INSERT INTO public.venue_proposal_staging_location (
                    venue_change_proposal_id, venue_id,
                    proposed_locality_id, proposed_address_line_1, proposed_address_line_2,
                    proposed_postal_code, proposed_country_code,
                    proposed_latitude, proposed_longitude
                ) VALUES (
                    %s::uuid, %s::uuid,
                    %s::uuid, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (venue_change_proposal_id) DO UPDATE SET
                    proposed_locality_id = EXCLUDED.proposed_locality_id,
                    proposed_address_line_1 = EXCLUDED.proposed_address_line_1,
                    proposed_address_line_2 = EXCLUDED.proposed_address_line_2,
                    proposed_postal_code = EXCLUDED.proposed_postal_code,
                    proposed_country_code = EXCLUDED.proposed_country_code,
                    proposed_latitude = EXCLUDED.proposed_latitude,
                    proposed_longitude = EXCLUDED.proposed_longitude
                """,
                [
                    proposal_id,
                    venue_id,
                    fields.get("locality_id"),
                    fields.get("address_line_1"),
                    fields.get("address_line_2"),
                    fields.get("postal_code"),
                    fields.get("country_code", "AU"),
                    fields.get("latitude"),
                    fields.get("longitude"),
                ],
            )


def _upsert_restricted_proposal_targets(
    proposal_id: str, fields: dict[str, Any]
) -> None:
    targets: list[str] = []
    if "display_name" in fields:
        targets.append("profile")
    if any(
        k in fields
        for k in (
            "address_line_1",
            "address_line_2",
            "postal_code",
            "locality_id",
            "country_code",
            "latitude",
            "longitude",
        )
    ):
        targets.append("geo")
    with connection.cursor() as c:
        for tf in targets:
            c.execute(
                """
                INSERT INTO public.venue_proposal_target (venue_change_proposal_id, target_family)
                VALUES (%s::uuid, %s)
                ON CONFLICT (venue_change_proposal_id, target_family) DO NOTHING
                """,
                [proposal_id, tf],
            )


@transaction.atomic
def create_owner_restricted_change_request(
    auth: AuthContext,
    venue_id: str,
    *,
    section: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_submit_restricted_change(auth, venue_id)
    if access is None:
        return None, err, None

    if section != "identity_location":
        return None, "validation_error", {
            "section": ["Only section 'identity_location' is supported."]
        }

    fields, val_err = _validate_restricted_identity_payload(payload)
    if val_err:
        return None, "validation_error", val_err

    existing = _find_open_in_review_restricted_proposal(
        venue_id, access.owner_account_id
    )
    if existing is not None:
        return {
            "proposal_id": existing["proposal_id"],
            "venue_id": venue_id,
            "section": "identity_location",
            "lifecycle_status": "in_review",
            "submitted_at": existing["submitted_at"],
            "message": "Your change request is already waiting for review.",
        }, "already_in_review", None

    now = datetime.now(timezone.utc)
    profile_before = _count_published_profile_rows(venue_id)

    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_change_proposal (
                venue_id,
                actor_type,
                actor_owner_account_id,
                channel,
                proposal_kind,
                lifecycle_status,
                submitted_at
            ) VALUES (
                %s::uuid, 'owner', %s::uuid, 'owner_portal', 'field_family',
                'in_review', %s
            )
            RETURNING id::text
            """,
            [venue_id, str(access.owner_account_id), now],
        )
        proposal_id = c.fetchone()[0]

    assert fields is not None
    _upsert_restricted_proposal_targets(proposal_id, fields)
    _upsert_restricted_staging_rows(proposal_id, venue_id, fields)

    profile_after = _count_published_profile_rows(venue_id)
    if profile_after != profile_before:
        logger.error(
            "Restricted change request unexpectedly changed published profile count for venue %s",
            venue_id,
        )

    return {
        "proposal_id": proposal_id,
        "venue_id": venue_id,
        "section": "identity_location",
        "lifecycle_status": "in_review",
        "submitted_at": now.isoformat(),
        "message": (
            "Change request submitted. We'll review it before updating your listing."
        ),
    }, "ok", None


def _load_mvp_feature_definitions() -> list[dict[str, Any]]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id::text, stable_key, display_label, value_shape
            FROM public.venue_attribute_definition
            WHERE stable_key = ANY(%s::text[])
              AND value_shape = 'boolean'
              AND is_discovery_driving = true
            ORDER BY display_label ASC, stable_key ASC
            """,
            [list(_MVP_OWNER_EDITABLE_FEATURE_KEYS)],
        )
        rows = c.fetchall()
    return [
        {
            "attribute_definition_id": row[0],
            "stable_key": row[1],
            "label": row[2],
            "value_shape": row[3],
            "group": _FEATURE_UI_GROUPS.get(row[1]),
        }
        for row in rows
    ]


def _load_venue_boolean_feature_values(venue_id: str) -> dict[str, bool]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT ad.stable_key, pav.value_boolean
            FROM public.venue_published_attribute_value pav
            INNER JOIN public.venue_attribute_definition ad
              ON ad.id = pav.attribute_definition_id
            WHERE pav.venue_id = %s::uuid
              AND ad.stable_key = ANY(%s::text[])
              AND ad.value_shape = 'boolean'
              AND pav.allowed_value_id IS NULL
            """,
            [venue_id, list(_MVP_OWNER_EDITABLE_FEATURE_KEYS)],
        )
        rows = c.fetchall()
    return {str(row[0]): bool(row[1]) for row in rows if row[1] is not None}


def _build_features_response(venue_id: str) -> dict[str, Any]:
    definitions = _load_mvp_feature_definitions()
    values = _load_venue_boolean_feature_values(venue_id)
    features = [
        {
            "attribute_definition_id": d["attribute_definition_id"],
            "stable_key": d["stable_key"],
            "label": d["label"],
            "value_shape": d["value_shape"],
            "group": d.get("group"),
            "value": values.get(d["stable_key"], False),
        }
        for d in definitions
    ]
    return {"venue_id": venue_id, "features": features}


def _snapshot_features_for_audit(venue_id: str) -> dict[str, bool]:
    return _load_venue_boolean_feature_values(venue_id)


def get_owner_venue_features(
    auth: AuthContext, venue_id: str
) -> tuple[dict[str, Any] | None, str]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err
    return _build_features_response(venue_id), "ok"


def _validate_features_patch_body(
    body: Any,
) -> tuple[list[dict[str, Any]] | None, dict[str, list[str]] | None]:
    if not isinstance(body, dict):
        return None, {"body": ["Request body must be a JSON object."]}

    features = body.get("features")
    if features is None:
        return None, {"features": ["features array is required."]}
    if not isinstance(features, list):
        return None, {"features": ["features must be an array."]}
    if not features:
        return None, {"features": ["At least one feature must be provided."]}

    details: dict[str, list[str]] = {}
    seen_ids: set[str] = set()
    out: list[dict[str, Any]] = []

    for i, item in enumerate(features):
        prefix = f"features[{i}]"
        if not isinstance(item, dict):
            details[prefix] = ["Each feature must be an object."]
            continue
        def_id = item.get("attribute_definition_id")
        if def_id is None:
            details[f"{prefix}.attribute_definition_id"] = ["This field is required."]
            continue
        if _bad_uuid(def_id):
            details[f"{prefix}.attribute_definition_id"] = ["Must be a valid UUID."]
            continue
        def_id_s = str(def_id)
        if def_id_s in seen_ids:
            details[f"{prefix}.attribute_definition_id"] = ["Duplicate attribute ID."]
            continue
        seen_ids.add(def_id_s)

        val = item.get("value_boolean")
        if not isinstance(val, bool):
            details[f"{prefix}.value_boolean"] = ["Must be a boolean."]
            continue
        out.append({"attribute_definition_id": def_id_s, "value_boolean": val})

    if details:
        return None, details
    return out, None


def _resolve_owner_editable_feature_definition(
    attribute_definition_id: str,
) -> dict[str, Any] | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id::text, stable_key, display_label, value_shape
            FROM public.venue_attribute_definition
            WHERE id = %s::uuid
              AND stable_key = ANY(%s::text[])
              AND value_shape = 'boolean'
              AND is_discovery_driving = true
            """,
            [attribute_definition_id, list(_MVP_OWNER_EDITABLE_FEATURE_KEYS)],
        )
        row = c.fetchone()
    if not row:
        return None
    return {
        "attribute_definition_id": row[0],
        "stable_key": row[1],
        "label": row[2],
        "value_shape": row[3],
    }


def _upsert_published_boolean_feature(
    venue_id: str, attribute_definition_id: str, value_boolean: bool
) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id::text
            FROM public.venue_published_attribute_value
            WHERE venue_id = %s::uuid
              AND attribute_definition_id = %s::uuid
              AND allowed_value_id IS NULL
            LIMIT 1
            """,
            [venue_id, attribute_definition_id],
        )
        row = c.fetchone()
        if row:
            c.execute(
                """
                UPDATE public.venue_published_attribute_value
                SET value_boolean = %s, updated_at = now()
                WHERE id = %s::uuid
                """,
                [value_boolean, row[0]],
            )
        else:
            c.execute(
                """
                INSERT INTO public.venue_published_attribute_value (
                    venue_id, attribute_definition_id, value_boolean, updated_at
                ) VALUES (%s::uuid, %s::uuid, %s, now())
                """,
                [venue_id, attribute_definition_id, value_boolean],
            )


@transaction.atomic
def patch_owner_venue_features(
    auth: AuthContext,
    venue_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    items, val_err = _validate_features_patch_body(body)
    if val_err:
        return None, "validation_error", val_err
    assert items is not None

    details: dict[str, list[str]] = {}
    for i, item in enumerate(items):
        definition = _resolve_owner_editable_feature_definition(
            item["attribute_definition_id"]
        )
        if definition is None:
            details[f"features[{i}].attribute_definition_id"] = [
                "Unknown or non-editable attribute definition."
            ]

    if details:
        return None, "validation_error", details

    before = _snapshot_features_for_audit(venue_id)

    for item in items:
        _upsert_published_boolean_feature(
            venue_id,
            item["attribute_definition_id"],
            item["value_boolean"],
        )

    after = _snapshot_features_for_audit(venue_id)

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_published_attribute_value",
        field_family="attributes",
        endpoint=f"/api/v1/owner/venues/{venue_id}/features",
        before=before,
        after=after,
    )

    response = _build_features_response(venue_id)
    response["message"] = (
        "Features saved. These updates are now reflected on your listing."
    )
    return response, "ok", None


def _normalize_meal_special_days(days: Any) -> list[int] | None:
    if days is None:
        return list(range(7))
    if not isinstance(days, list):
        return None
    out: list[int] = []
    for day in days:
        if not isinstance(day, int) or day < 0 or day > 6:
            return None
        if day not in out:
            out.append(day)
    out.sort()
    return out if out else list(range(7))


def _validate_meal_special_input(
    body: Any,
    *,
    require_title: bool,
    partial: bool,
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(body, dict):
        return None, {"body": ["Request body must be a JSON object."]}

    details: dict[str, list[str]] = {}
    unknown = sorted(set(body.keys()) - _MEAL_SPECIAL_INPUT_ALLOWED_KEYS)
    for key in unknown:
        details[key] = ["Unsupported field."]

    if require_title and "title" not in body:
        details.setdefault("title", []).append("This field is required.")

    if not partial and not _MEAL_SPECIAL_INPUT_ALLOWED_KEYS.intersection(body.keys()):
        details.setdefault("body", []).append("At least one field must be provided.")

    title = body.get("title")
    if title is not None:
        if not isinstance(title, str):
            details.setdefault("title", []).append("Must be a string.")
        else:
            title = title.strip()
            if len(title) < _MEAL_SPECIAL_TITLE_MIN:
                details.setdefault("title", []).append(
                    f"Must be at least {_MEAL_SPECIAL_TITLE_MIN} characters."
                )
            elif len(title) > _MEAL_SPECIAL_TITLE_MAX:
                details.setdefault("title", []).append(
                    f"Must be at most {_MEAL_SPECIAL_TITLE_MAX} characters."
                )

    description = body.get("description")
    if "description" in body:
        if description is not None and not isinstance(description, str):
            details.setdefault("description", []).append("Must be a string or null.")
        elif isinstance(description, str) and len(description.strip()) > _MEAL_SPECIAL_DESCRIPTION_MAX:
            details.setdefault("description", []).append(
                f"Must be at most {_MEAL_SPECIAL_DESCRIPTION_MAX} characters."
            )

    days_available = body.get("days_available")
    normalized_days: list[int] | None = None
    if days_available is not None:
        normalized_days = _normalize_meal_special_days(days_available)
        if normalized_days is None:
            details.setdefault("days_available", []).append(
                "Each day must be an integer from 0 (Sunday) to 6 (Saturday)."
            )

    start_time = body.get("start_time")
    end_time = body.get("end_time")
    has_start = start_time is not None and start_time != ""
    has_end = end_time is not None and end_time != ""
    if has_start != has_end:
        details.setdefault("start_time", []).append(
            "start_time and end_time must both be provided or both omitted."
        )
    if has_start:
        if not isinstance(start_time, str) or not _TIME_RE.match(start_time.strip()):
            details.setdefault("start_time", []).append("Must be HH:MM (24-hour).")
        if not isinstance(end_time, str) or not _TIME_RE.match(end_time.strip()):
            details.setdefault("end_time", []).append("Must be HH:MM (24-hour).")

    price_text = body.get("price_text")
    if "price_text" in body:
        if price_text is not None and not isinstance(price_text, str):
            details.setdefault("price_text", []).append("Must be a string or null.")
        elif isinstance(price_text, str) and len(price_text.strip()) > _MEAL_SPECIAL_PRICE_TEXT_MAX:
            details.setdefault("price_text", []).append(
                f"Must be at most {_MEAL_SPECIAL_PRICE_TEXT_MAX} characters."
            )

    conditions = body.get("conditions")
    if "conditions" in body:
        if conditions is not None and not isinstance(conditions, str):
            details.setdefault("conditions", []).append("Must be a string or null.")
        elif isinstance(conditions, str) and len(conditions.strip()) > _MEAL_SPECIAL_CONDITIONS_MAX:
            details.setdefault("conditions", []).append(
                f"Must be at most {_MEAL_SPECIAL_CONDITIONS_MAX} characters."
            )

    active = body.get("active")
    if active is not None and not isinstance(active, bool):
        details.setdefault("active", []).append("Must be a boolean.")

    sort_order = body.get("sort_order")
    parsed_sort: int | None = None
    if sort_order is not None:
        if not isinstance(sort_order, int) or isinstance(sort_order, bool):
            details.setdefault("sort_order", []).append("Must be an integer.")
        elif (
            sort_order < _MEAL_SPECIAL_SORT_ORDER_MIN
            or sort_order > _MEAL_SPECIAL_SORT_ORDER_MAX
        ):
            details.setdefault("sort_order", []).append(
                f"Must be between {_MEAL_SPECIAL_SORT_ORDER_MIN} and "
                f"{_MEAL_SPECIAL_SORT_ORDER_MAX}."
            )
        else:
            parsed_sort = sort_order

    if details:
        return None, details

    out: dict[str, Any] = {}
    if title is not None and isinstance(title, str):
        out["title"] = title.strip()
    if "description" in body:
        out["description"] = (
            description.strip() if isinstance(description, str) and description.strip()
            else None
        )
    if normalized_days is not None:
        out["days_available"] = normalized_days
    elif "days_available" not in body:
        out["days_available"] = list(range(7))
    if has_start:
        out["start_time"] = start_time.strip()  # type: ignore[union-attr]
        out["end_time"] = end_time.strip()  # type: ignore[union-attr]
    elif "start_time" in body or "end_time" in body:
        out["start_time"] = None
        out["end_time"] = None
    if "price_text" in body:
        out["price_text"] = (
            price_text.strip() if isinstance(price_text, str) and price_text.strip()
            else None
        )
    if "conditions" in body:
        out["conditions"] = (
            conditions.strip() if isinstance(conditions, str) and conditions.strip()
            else None
        )
    if active is not None:
        out["active"] = active
    if parsed_sort is not None:
        out["sort_order"] = parsed_sort
    return out, None


def _load_owner_meal_special_rows(venue_id: str) -> list[dict[str, Any]]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              s.id::text,
              s.short_label,
              s.catalog_record_status,
              s.created_at,
              m.headline,
              m.body,
              m.terms_and_conditions,
              rp.recurring_days_of_week,
              rp.window_start_time_local::text,
              rp.window_end_time_local::text,
              rp.crosses_local_midnight,
              de.tier_notes
            FROM public.venue_published_structured_special s
            LEFT JOIN public.venue_published_structured_special_marketing_copy m
              ON m.structured_special_id = s.id
            LEFT JOIN public.venue_published_special_recurring_pattern rp
              ON rp.structured_special_id = s.id
            LEFT JOIN public.venue_published_structured_special_discovery_eligibility de
              ON de.structured_special_id = s.id
            WHERE s.venue_id = %s::uuid
              AND s.structured_kind = %s
            ORDER BY s.created_at ASC, s.short_label ASC
            """,
            [venue_id, _MEAL_SPECIAL_STRUCTURED_KIND],
        )
        rows = c.fetchall()

    items: list[dict[str, Any]] = []
    for row in rows:
        start_raw = row[8]
        end_raw = row[9]
        start_time = _time_to_hhmm(start_raw) if start_raw else None
        end_time = _time_to_hhmm(end_raw) if end_raw else None
        days = list(row[7]) if row[7] is not None else []
        sort_order = _parse_owner_sort_order_from_tier_notes(row[11])
        items.append(
            {
                "id": row[0],
                "title": row[1],
                "description": row[5],
                "days_available": sorted(int(d) for d in days),
                "start_time": start_time,
                "end_time": end_time,
                "price_text": row[4],
                "conditions": row[6],
                "active": row[2] == "active",
                "sort_order": sort_order,
                "_created_at": row[3],
            }
        )

    items.sort(
        key=lambda item: (
            item["sort_order"],
            item.get("_created_at") or datetime.min.replace(tzinfo=timezone.utc),
            item["title"] or "",
        )
    )
    for index, item in enumerate(items):
        if item["sort_order"] == _MEAL_SPECIAL_SORT_ORDER_MAX:
            item["sort_order"] = index
        item.pop("_created_at", None)
    return items


def _meal_special_row_to_public(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "title": item["title"],
        "description": item.get("description"),
        "days_available": item.get("days_available", []),
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "price_text": item.get("price_text"),
        "conditions": item.get("conditions"),
        "active": item.get("active", True),
        "sort_order": item.get("sort_order", 0),
    }


def _build_meal_specials_response(venue_id: str) -> dict[str, Any]:
    rows = _load_owner_meal_special_rows(venue_id)
    return {
        "venue_id": venue_id,
        "meal_specials": [_meal_special_row_to_public(row) for row in rows],
    }


def _snapshot_meal_specials_for_audit(venue_id: str) -> list[dict[str, Any]]:
    return [
        _meal_special_row_to_public(row) for row in _load_owner_meal_special_rows(venue_id)
    ]


def _owner_meal_special_belongs_to_venue(venue_id: str, special_id: str) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1
            FROM public.venue_published_structured_special
            WHERE id = %s::uuid
              AND venue_id = %s::uuid
              AND structured_kind = %s
            """,
            [special_id, venue_id, _MEAL_SPECIAL_STRUCTURED_KIND],
        )
        return c.fetchone() is not None


def _crosses_local_midnight(start_time: str, end_time: str) -> bool:
    return end_time <= start_time


def _insert_meal_special_satellites(
    *,
    special_id: str,
    description: str | None,
    price_text: str | None,
    conditions: str | None,
    days_available: list[int],
    start_time: str,
    end_time: str,
    sort_order: int,
) -> None:
    crosses = _crosses_local_midnight(start_time, end_time)
    tier_notes = _format_owner_sort_order_tier_notes(
        sort_order, "Owner portal meal special."
    )
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_published_structured_special_marketing_copy (
                structured_special_id, headline, body, terms_and_conditions
            ) VALUES (%s::uuid, %s, %s, %s)
            ON CONFLICT (structured_special_id) DO UPDATE SET
                headline = EXCLUDED.headline,
                body = EXCLUDED.body,
                terms_and_conditions = EXCLUDED.terms_and_conditions,
                updated_at = now()
            """,
            [special_id, price_text, description, conditions],
        )
        c.execute(
            """
            INSERT INTO public.venue_published_special_recurring_pattern (
                structured_special_id,
                recurrence_kind,
                anchor_timezone,
                recurring_days_of_week,
                window_start_time_local,
                window_end_time_local,
                crosses_local_midnight
            ) VALUES (
                %s::uuid,
                'weekly_local_time_window',
                %s,
                %s::smallint[],
                %s::time,
                %s::time,
                %s
            )
            ON CONFLICT (structured_special_id) DO UPDATE SET
                recurrence_kind = EXCLUDED.recurrence_kind,
                anchor_timezone = EXCLUDED.anchor_timezone,
                recurring_days_of_week = EXCLUDED.recurring_days_of_week,
                window_start_time_local = EXCLUDED.window_start_time_local,
                window_end_time_local = EXCLUDED.window_end_time_local,
                crosses_local_midnight = EXCLUDED.crosses_local_midnight,
                updated_at = now()
            """,
            [
                special_id,
                _MEAL_SPECIAL_DEFAULT_TIMEZONE,
                days_available,
                start_time,
                end_time,
                crosses,
            ],
        )
        c.execute(
            """
            INSERT INTO public.venue_published_structured_special_validity (
                structured_special_id,
                offer_valid_from,
                offer_valid_to,
                validity_bounds_kind,
                timing_signal_strength,
                suppress_due_to_weak_or_stale_timing
            ) VALUES (%s::uuid, NULL, NULL, 'unknown', 'strong', false)
            ON CONFLICT (structured_special_id) DO UPDATE SET
                validity_bounds_kind = EXCLUDED.validity_bounds_kind,
                timing_signal_strength = EXCLUDED.timing_signal_strength,
                suppress_due_to_weak_or_stale_timing = EXCLUDED.suppress_due_to_weak_or_stale_timing,
                updated_at = now()
            """,
            [special_id],
        )
        c.execute(
            """
            INSERT INTO public.venue_published_structured_special_discovery_eligibility (
                structured_special_id,
                safe_for_detail_display,
                safe_for_card_badge,
                safe_for_filter_search,
                safe_for_active_now_ranking,
                tier_notes
            ) VALUES (%s::uuid, true, true, true, true, %s)
            ON CONFLICT (structured_special_id) DO UPDATE SET
                safe_for_detail_display = EXCLUDED.safe_for_detail_display,
                safe_for_card_badge = EXCLUDED.safe_for_card_badge,
                safe_for_filter_search = EXCLUDED.safe_for_filter_search,
                safe_for_active_now_ranking = EXCLUDED.safe_for_active_now_ranking,
                tier_notes = EXCLUDED.tier_notes,
                updated_at = now()
            """,
            [special_id, tier_notes],
        )


def get_owner_venue_meal_specials(
    auth: AuthContext, venue_id: str
) -> tuple[dict[str, Any] | None, str]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err
    return _build_meal_specials_response(venue_id), "ok"


@transaction.atomic
def create_owner_venue_meal_special(
    auth: AuthContext,
    venue_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    parsed, val_err = _validate_meal_special_input(
        body, require_title=True, partial=False
    )
    if val_err:
        return None, "validation_error", val_err
    assert parsed is not None

    before = _snapshot_meal_specials_for_audit(venue_id)

    start_time = parsed.get("start_time") or "00:00"
    end_time = parsed.get("end_time") or "23:59"
    days_available = parsed.get("days_available", list(range(7)))
    sort_order = parsed.get("sort_order", len(before))
    active = parsed.get("active", True)
    catalog_status = "active" if active else "retired"

    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_published_structured_special (
                venue_id, structured_kind, schedule_class, short_label, catalog_record_status
            ) VALUES (%s::uuid, %s, 'recurring', %s, %s)
            RETURNING id::text
            """,
            [venue_id, _MEAL_SPECIAL_STRUCTURED_KIND, parsed["title"], catalog_status],
        )
        row = c.fetchone()
    assert row is not None
    special_id = row[0]

    _insert_meal_special_satellites(
        special_id=special_id,
        description=parsed.get("description"),
        price_text=parsed.get("price_text"),
        conditions=parsed.get("conditions"),
        days_available=days_available,
        start_time=start_time,
        end_time=end_time,
        sort_order=sort_order,
    )

    after = _snapshot_meal_specials_for_audit(venue_id)
    saved = next(item for item in after if item["id"] == special_id)

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_published_structured_special",
        field_family="meal_specials",
        endpoint=f"/api/v1/owner/venues/{venue_id}/meal-specials",
        before={"meal_specials": before},
        after={"meal_specials": after},
    )

    response = {
        "venue_id": venue_id,
        "meal_special": saved,
        "message": "Special saved. These updates are now reflected on your listing.",
    }
    return response, "ok", None


@transaction.atomic
def patch_owner_venue_meal_special(
    auth: AuthContext,
    venue_id: str,
    special_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    if not _owner_meal_special_belongs_to_venue(venue_id, special_id):
        return None, "not_found", None

    parsed, val_err = _validate_meal_special_input(
        body, require_title=False, partial=True
    )
    if val_err:
        return None, "validation_error", val_err
    assert parsed is not None

    before = _snapshot_meal_specials_for_audit(venue_id)
    current = next((r for r in before if r["id"] == special_id), None)
    if current is None:
        return None, "not_found", None

    merged = {**current, **parsed}

    catalog_status = "active" if merged.get("active", True) else "retired"
    start_time = merged.get("start_time") or "00:00"
    end_time = merged.get("end_time") or "23:59"
    days_available = merged.get("days_available", list(range(7)))
    sort_order = merged.get("sort_order", current.get("sort_order", 0))

    with connection.cursor() as c:
        c.execute(
            """
            UPDATE public.venue_published_structured_special
            SET short_label = %s,
                catalog_record_status = %s,
                updated_at = now()
            WHERE id = %s::uuid AND venue_id = %s::uuid
            """,
            [merged["title"], catalog_status, special_id, venue_id],
        )

    _insert_meal_special_satellites(
        special_id=special_id,
        description=merged.get("description"),
        price_text=merged.get("price_text"),
        conditions=merged.get("conditions"),
        days_available=days_available,
        start_time=start_time,
        end_time=end_time,
        sort_order=sort_order,
    )

    after = _snapshot_meal_specials_for_audit(venue_id)
    saved = next(item for item in after if item["id"] == special_id)

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_published_structured_special",
        field_family="meal_specials",
        endpoint=f"/api/v1/owner/venues/{venue_id}/meal-specials/{special_id}",
        before={"meal_specials": before},
        after={"meal_specials": after},
    )

    response = {
        "venue_id": venue_id,
        "meal_special": saved,
        "message": "Special saved. These updates are now reflected on your listing.",
    }
    return response, "ok", None


@transaction.atomic
def deactivate_owner_venue_meal_special(
    auth: AuthContext,
    venue_id: str,
    special_id: str,
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    return patch_owner_venue_meal_special(
        auth,
        venue_id,
        special_id,
        {"active": False},
    )


def _parse_owner_tap_meta_from_tier_notes(tier_notes: str | None) -> dict[str, Any]:
    if not tier_notes:
        return {}
    for part in str(tier_notes).split("|"):
        part = part.strip()
        if part.startswith(_TAP_OWNER_META_PREFIX):
            payload = part[len(_TAP_OWNER_META_PREFIX) :]
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
    return {}


def _format_owner_tap_tier_notes(
    *,
    brewery_or_brand: str | None,
    drink_type: str | None,
    abv: str | None,
    price_text: str | None,
    notes: str | None,
    availability: str | None,
    sort_order: int,
) -> str:
    meta: dict[str, str] = {}
    if brewery_or_brand:
        meta["brewery_or_brand"] = brewery_or_brand
    if drink_type:
        meta["drink_type"] = drink_type
    if abv:
        meta["abv"] = abv
    if price_text:
        meta["price_text"] = price_text
    if notes:
        meta["notes"] = notes
    if availability:
        meta["availability"] = availability
    parts = [f"{_SORT_ORDER_TIER_NOTES_PREFIX}{sort_order}"]
    if meta:
        parts.append(f"{_TAP_OWNER_META_PREFIX}{json.dumps(meta, separators=(',', ':'))}")
    return "|".join(parts)


def _availability_to_traits(availability: str | None) -> tuple[bool, bool]:
    avail = availability or "permanent"
    if avail == "rotating":
        return True, False
    if avail in ("seasonal", "limited"):
        return False, True
    return False, False


def _traits_to_availability(
    *,
    is_rotating: bool,
    is_limited_run: bool,
    meta: dict[str, Any],
) -> str:
    stored = meta.get("availability")
    if isinstance(stored, str) and stored in _TAP_LIST_AVAILABILITY:
        return stored
    if is_rotating:
        return "rotating"
    if is_limited_run:
        return "limited"
    return "permanent"


def _validate_tap_list_input(
    body: Any,
    *,
    require_drink_name: bool,
    partial: bool,
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(body, dict):
        return None, {"body": ["Request body must be a JSON object."]}

    details: dict[str, list[str]] = {}
    unknown = sorted(set(body.keys()) - _TAP_LIST_INPUT_ALLOWED_KEYS)
    for key in unknown:
        details[key] = ["Unsupported field."]

    if require_drink_name and "drink_name" not in body:
        details.setdefault("drink_name", []).append("This field is required.")

    if not partial and not _TAP_LIST_INPUT_ALLOWED_KEYS.intersection(body.keys()):
        details.setdefault("body", []).append("At least one field must be provided.")

    drink_name = body.get("drink_name")
    if drink_name is not None:
        if not isinstance(drink_name, str):
            details.setdefault("drink_name", []).append("Must be a string.")
        else:
            drink_name = drink_name.strip()
            if len(drink_name) < _TAP_LIST_DRINK_NAME_MIN:
                details.setdefault("drink_name", []).append(
                    f"Must be at least {_TAP_LIST_DRINK_NAME_MIN} characters."
                )
            elif len(drink_name) > _TAP_LIST_DRINK_NAME_MAX:
                details.setdefault("drink_name", []).append(
                    f"Must be at most {_TAP_LIST_DRINK_NAME_MAX} characters."
                )
            elif _contains_markup(drink_name):
                details.setdefault("drink_name", []).append(
                    "Must not contain HTML or script-like markup."
                )

    _MISSING = object()

    def _validate_optional_text(key: str, max_len: int) -> tuple[str | None | object, bool]:
        val = body.get(key)
        if key not in body:
            return _MISSING, False
        if val is None:
            return None, True
        if not isinstance(val, str):
            details.setdefault(key, []).append("Must be a string or null.")
            return _MISSING, True
        trimmed = val.strip()
        if len(trimmed) > max_len:
            details.setdefault(key, []).append(
                f"Must be at most {max_len} characters."
            )
            return _MISSING, True
        if trimmed and _contains_markup(trimmed):
            details.setdefault(key, []).append(
                "Must not contain HTML or script-like markup."
            )
            return _MISSING, True
        return trimmed or None, True

    brewery_or_brand, _ = _validate_optional_text("brewery_or_brand", _TAP_LIST_BREWERY_MAX)
    drink_type, _ = _validate_optional_text("drink_type", _TAP_LIST_TYPE_MAX)
    abv, _ = _validate_optional_text("abv", _TAP_LIST_ABV_MAX)
    price_text, _ = _validate_optional_text("price_text", _TAP_LIST_PRICE_TEXT_MAX)
    notes, _ = _validate_optional_text("notes", _TAP_LIST_NOTES_MAX)

    availability = body.get("availability")
    if availability is not None:
        if availability == "":
            availability = None
        elif not isinstance(availability, str):
            details.setdefault("availability", []).append("Must be a string or null.")
        elif availability not in _TAP_LIST_AVAILABILITY:
            details.setdefault("availability", []).append(
                "Must be one of: permanent, rotating, seasonal, limited."
            )

    active = body.get("active")
    if active is not None and not isinstance(active, bool):
        details.setdefault("active", []).append("Must be a boolean.")

    parsed_sort: int | None = None
    sort_order = body.get("sort_order")
    if sort_order is not None:
        if not isinstance(sort_order, int):
            details.setdefault("sort_order", []).append("Must be an integer.")
        elif sort_order < _TAP_LIST_SORT_ORDER_MIN or sort_order > _TAP_LIST_SORT_ORDER_MAX:
            details.setdefault("sort_order", []).append(
                f"Must be between {_TAP_LIST_SORT_ORDER_MIN} and {_TAP_LIST_SORT_ORDER_MAX}."
            )
        else:
            parsed_sort = sort_order

    if details:
        return None, details

    out: dict[str, Any] = {}
    if drink_name is not None and isinstance(drink_name, str):
        out["drink_name"] = drink_name.strip()
    for key, val in (
        ("brewery_or_brand", brewery_or_brand),
        ("drink_type", drink_type),
        ("abv", abv),
        ("price_text", price_text),
        ("notes", notes),
    ):
        if val is not _MISSING:
            out[key] = val
    if "availability" in body:
        out["availability"] = availability
    if active is not None:
        out["active"] = active
    if parsed_sort is not None:
        out["sort_order"] = parsed_sort
    return out, None


def _load_owner_tap_list_rows(venue_id: str) -> list[dict[str, Any]]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              t.id::text,
              t.unstructured_line_label,
              t.catalog_record_status,
              t.is_rotating,
              t.is_limited_run,
              t.sort_order,
              t.created_at,
              p.display_name,
              br.display_name,
              st.display_name,
              de.tier_notes
            FROM public.venue_published_tap_offering t
            LEFT JOIN public.beverage_product p
              ON p.id = t.beverage_product_id
            LEFT JOIN public.beverage_brewery br
              ON br.id = p.brewery_id
            LEFT JOIN public.beverage_style st
              ON st.id = p.style_id
            LEFT JOIN public.venue_published_tap_offering_discovery_eligibility de
              ON de.tap_offering_id = t.id
            WHERE t.venue_id = %s::uuid
            ORDER BY t.created_at ASC, t.id ASC
            """,
            [venue_id],
        )
        rows = c.fetchall()

    items: list[dict[str, Any]] = []
    for row in rows:
        tier_notes = row[10]
        meta = _parse_owner_tap_meta_from_tier_notes(tier_notes)
        parsed_sort = _parse_owner_sort_order_from_tier_notes(tier_notes)
        sort_order = (
            parsed_sort
            if parsed_sort != _MEAL_SPECIAL_SORT_ORDER_MAX
            else (int(row[5]) if row[5] is not None else _MEAL_SPECIAL_SORT_ORDER_MAX)
        )
        drink_name = (row[1] or row[7] or "").strip()
        items.append(
            {
                "id": row[0],
                "drink_name": drink_name,
                "brewery_or_brand": meta.get("brewery_or_brand") or row[8],
                "drink_type": meta.get("drink_type") or row[9],
                "abv": meta.get("abv"),
                "price_text": meta.get("price_text"),
                "notes": meta.get("notes"),
                "availability": _traits_to_availability(
                    is_rotating=bool(row[3]),
                    is_limited_run=bool(row[4]),
                    meta=meta,
                ),
                "active": row[2] == "active",
                "sort_order": sort_order,
                "_created_at": row[6],
            }
        )

    items.sort(
        key=lambda item: (
            item["sort_order"],
            item.get("_created_at") or datetime.min.replace(tzinfo=timezone.utc),
            item["drink_name"] or "",
        )
    )
    for index, item in enumerate(items):
        if item["sort_order"] == _MEAL_SPECIAL_SORT_ORDER_MAX:
            item["sort_order"] = index
        item.pop("_created_at", None)
    return items


def _tap_list_row_to_public(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "drink_name": item["drink_name"],
        "brewery_or_brand": item.get("brewery_or_brand"),
        "drink_type": item.get("drink_type"),
        "abv": item.get("abv"),
        "price_text": item.get("price_text"),
        "availability": item.get("availability"),
        "notes": item.get("notes"),
        "active": item.get("active", True),
        "sort_order": item.get("sort_order", 0),
    }


def _build_tap_list_response(venue_id: str) -> dict[str, Any]:
    rows = _load_owner_tap_list_rows(venue_id)
    return {
        "venue_id": venue_id,
        "tap_list": [_tap_list_row_to_public(row) for row in rows],
    }


def _snapshot_tap_list_for_audit(venue_id: str) -> list[dict[str, Any]]:
    return [_tap_list_row_to_public(row) for row in _load_owner_tap_list_rows(venue_id)]


def _owner_tap_item_belongs_to_venue(venue_id: str, item_id: str) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1
            FROM public.venue_published_tap_offering
            WHERE id = %s::uuid AND venue_id = %s::uuid
            """,
            [item_id, venue_id],
        )
        return c.fetchone() is not None


def _insert_tap_offering_satellites(
    *,
    tap_offering_id: str,
    brewery_or_brand: str | None,
    drink_type: str | None,
    abv: str | None,
    price_text: str | None,
    notes: str | None,
    availability: str | None,
    sort_order: int,
) -> None:
    tier_notes = _format_owner_tap_tier_notes(
        brewery_or_brand=brewery_or_brand,
        drink_type=drink_type,
        abv=abv,
        price_text=price_text,
        notes=notes,
        availability=availability,
        sort_order=sort_order,
    )
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_published_tap_offering_validity (
                tap_offering_id,
                freshness_signal_strength,
                availability_truth_state,
                suppress_strong_current_tap_claim
            ) VALUES (%s::uuid, 'weak', 'uncertain', true)
            ON CONFLICT (tap_offering_id) DO UPDATE SET
                updated_at = now()
            """,
            [tap_offering_id],
        )
        c.execute(
            """
            INSERT INTO public.venue_published_tap_offering_discovery_eligibility (
                tap_offering_id,
                safe_for_detail_display,
                safe_for_card_or_list_row,
                safe_for_filter_search,
                safe_for_strong_current_tap_claim,
                tier_notes
            ) VALUES (%s::uuid, true, true, false, false, %s)
            ON CONFLICT (tap_offering_id) DO UPDATE SET
                tier_notes = EXCLUDED.tier_notes,
                safe_for_detail_display = EXCLUDED.safe_for_detail_display,
                safe_for_card_or_list_row = EXCLUDED.safe_for_card_or_list_row,
                updated_at = now()
            """,
            [tap_offering_id, tier_notes],
        )


def get_owner_venue_tap_list(
    auth: AuthContext, venue_id: str
) -> tuple[dict[str, Any] | None, str]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err
    return _build_tap_list_response(venue_id), "ok"


@transaction.atomic
def create_owner_venue_tap_list_item(
    auth: AuthContext,
    venue_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    parsed, val_err = _validate_tap_list_input(
        body, require_drink_name=True, partial=False
    )
    if val_err:
        return None, "validation_error", val_err
    assert parsed is not None

    before = _snapshot_tap_list_for_audit(venue_id)
    sort_order = parsed.get("sort_order", len(before))
    active = parsed.get("active", True)
    catalog_status = "active" if active else "retired"
    availability = parsed.get("availability") or "permanent"
    is_rotating, is_limited_run = _availability_to_traits(availability)

    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_published_tap_offering (
                venue_id,
                beverage_product_id,
                catalog_record_status,
                is_rotating,
                is_guest_tap,
                is_limited_run,
                unstructured_line_label,
                sort_order
            ) VALUES (%s::uuid, NULL, %s, %s, false, %s, %s, %s)
            RETURNING id::text
            """,
            [
                venue_id,
                catalog_status,
                is_rotating,
                is_limited_run,
                parsed["drink_name"],
                sort_order,
            ],
        )
        row = c.fetchone()
    assert row is not None
    item_id = row[0]

    _insert_tap_offering_satellites(
        tap_offering_id=item_id,
        brewery_or_brand=parsed.get("brewery_or_brand"),
        drink_type=parsed.get("drink_type"),
        abv=parsed.get("abv"),
        price_text=parsed.get("price_text"),
        notes=parsed.get("notes"),
        availability=availability,
        sort_order=sort_order,
    )

    after = _snapshot_tap_list_for_audit(venue_id)
    saved = next(item for item in after if item["id"] == item_id)

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_published_tap_offering",
        field_family="tap_list",
        endpoint=f"/api/v1/owner/venues/{venue_id}/tap-list",
        before={"tap_list": before},
        after={"tap_list": after},
    )

    return {
        "venue_id": venue_id,
        "tap_item": saved,
        "message": "Drink list saved. These updates are now reflected on your listing.",
    }, "ok", None


@transaction.atomic
def patch_owner_venue_tap_list_item(
    auth: AuthContext,
    venue_id: str,
    item_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    if not _owner_tap_item_belongs_to_venue(venue_id, item_id):
        return None, "not_found", None

    parsed, val_err = _validate_tap_list_input(
        body, require_drink_name=False, partial=True
    )
    if val_err:
        return None, "validation_error", val_err
    assert parsed is not None

    before = _snapshot_tap_list_for_audit(venue_id)
    current = next((r for r in before if r["id"] == item_id), None)
    if current is None:
        return None, "not_found", None

    merged = {**current, **parsed}
    catalog_status = "active" if merged.get("active", True) else "retired"
    availability = merged.get("availability") or "permanent"
    is_rotating, is_limited_run = _availability_to_traits(availability)
    sort_order = merged.get("sort_order", current.get("sort_order", 0))

    with connection.cursor() as c:
        c.execute(
            """
            UPDATE public.venue_published_tap_offering
            SET catalog_record_status = %s,
                is_rotating = %s,
                is_limited_run = %s,
                unstructured_line_label = %s,
                sort_order = %s,
                updated_at = now()
            WHERE id = %s::uuid AND venue_id = %s::uuid
            """,
            [
                catalog_status,
                is_rotating,
                is_limited_run,
                merged["drink_name"],
                sort_order,
                item_id,
                venue_id,
            ],
        )

    _insert_tap_offering_satellites(
        tap_offering_id=item_id,
        brewery_or_brand=merged.get("brewery_or_brand"),
        drink_type=merged.get("drink_type"),
        abv=merged.get("abv"),
        price_text=merged.get("price_text"),
        notes=merged.get("notes"),
        availability=availability,
        sort_order=sort_order,
    )

    after = _snapshot_tap_list_for_audit(venue_id)
    saved = next(item for item in after if item["id"] == item_id)

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_published_tap_offering",
        field_family="tap_list",
        endpoint=f"/api/v1/owner/venues/{venue_id}/tap-list/{item_id}",
        before={"tap_list": before},
        after={"tap_list": after},
    )

    return {
        "venue_id": venue_id,
        "tap_item": saved,
        "message": "Drink list saved. These updates are now reflected on your listing.",
    }, "ok", None


@transaction.atomic
def deactivate_owner_venue_tap_list_item(
    auth: AuthContext,
    venue_id: str,
    item_id: str,
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    return patch_owner_venue_tap_list_item(
        auth,
        venue_id,
        item_id,
        {"active": False},
    )
