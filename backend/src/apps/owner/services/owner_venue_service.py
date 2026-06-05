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
_HOURS_NOTES_MAX_LEN = 1000
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


def _completeness_percent(basics: dict[str, Any]) -> int:
    checks = [
        bool(basics.get("display_name")),
        bool(basics.get("address_line_1") and basics.get("locality_id")),
        bool(basics.get("short_description")),
        bool(basics.get("hours_ok")),
    ]
    return int(25 * sum(1 for x in checks if x))


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


def _completeness_sections(basics: dict[str, Any]) -> list[dict[str, Any]]:
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
            "key": "events",
            "label": "Events",
            "status": "deferred",
            "required": False,
            "available": False,
        },
        {
            "key": "meal_specials",
            "label": "Meal specials",
            "status": "missing",
            "required": False,
            "available": False,
        },
        {
            "key": "tap_list",
            "label": "Tap list",
            "status": "missing",
            "required": False,
            "available": False,
        },
        {
            "key": "features",
            "label": "Features",
            "status": "missing",
            "required": False,
            "available": False,
        },
        {
            "key": "photos",
            "label": "Photos",
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
        required_complete = _compute_required_basics(basics)
        venues.append(
            {
                "venue_id": vid,
                "display_name": row[1],
                "locality_name": row[2],
                "state_code": row[3],
                "relationship_lifecycle": "approved",
                "onboarding_status": _derive_onboarding_status(
                    required_basics_complete=required_complete,
                    has_owner_proposal_ever=_has_owner_core_proposal_ever(
                        vid, owner_id
                    ),
                    draft=draft,
                    pending=pending,
                ),
                "pending_proposal_count": _count_pending_proposals(vid, owner_id),
                "completeness_percent": _completeness_percent(basics),
                "required_basics_complete": required_complete,
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
    required_complete = _compute_required_basics(basics)
    caps = _load_capabilities(access.relationship_id, access.owner_account_id)

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
            "percent": _completeness_percent(basics),
            "required_basics_complete": required_complete,
            "sections": _completeness_sections(basics),
        },
        "sections_available": {
            "core_details": True,
            "events": False,
            "meal_specials": False,
            "tap_list": False,
            "features": False,
            "photos": False,
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
