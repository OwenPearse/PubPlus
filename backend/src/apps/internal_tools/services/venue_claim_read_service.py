from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from django.db import connection

OPEN_CLAIM_STATUSES = ("submitted", "under_review")
ALLOWED_CLAIM_STATUSES = frozenset(
    {"draft", "submitted", "under_review", "withdrawn", "denied", "closed"}
)


class VenueClaimReadValidationError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class VenueClaimNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class VenueClaimQueueFilters:
    statuses: tuple[str, ...]


def _parse_uuid(value: str, *, key: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError) as exc:
        raise VenueClaimReadValidationError(
            f"{key} must be a valid UUID."
        ) from exc


def _parse_csv_values(value: str) -> tuple[str, ...]:
    out: list[str] = []
    for raw in value.split(","):
        item = raw.strip()
        if item:
            out.append(item)
    return tuple(out)


def parse_claim_queue_filters(raw: dict[str, str]) -> VenueClaimQueueFilters:
    allowed = {"status"}
    unknown = sorted(set(raw.keys()) - allowed)
    if unknown:
        raise VenueClaimReadValidationError(
            f"Unsupported query parameter(s): {', '.join(unknown)}."
        )

    raw_status = raw.get("status", "").strip()
    if raw_status:
        vals = _parse_csv_values(raw_status)
        if not vals:
            raise VenueClaimReadValidationError("status filter cannot be empty.")
        bad = sorted(v for v in vals if v not in ALLOWED_CLAIM_STATUSES)
        if bad:
            raise VenueClaimReadValidationError(
                f"status must be one of: {', '.join(sorted(ALLOWED_CLAIM_STATUSES))}."
            )
        return VenueClaimQueueFilters(statuses=vals)
    return VenueClaimQueueFilters(statuses=OPEN_CLAIM_STATUSES)


def _parse_summary(summary: str | None) -> dict[str, Any]:
    if not summary:
        return {}
    try:
        data = json.loads(summary)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _enrich_duplicate_candidates(
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    stored = summary.get("duplicate_candidates")
    if not isinstance(stored, list):
        return []

    venue_ids = [
        str(item["venue_id"])
        for item in stored
        if isinstance(item, dict) and item.get("venue_id")
    ]
    if not venue_ids:
        return []

    with connection.cursor() as c:
        c.execute(
            """
            SELECT
                v.id::text,
                vpp.display_name,
                vpl.address_line_1,
                l.name,
                COALESCE(
                    CASE WHEN gr.region_level = 'state' THEN gr.region_code END,
                    pgr.region_code
                )
            FROM public.venue v
            LEFT JOIN public.venue_published_profile vpp ON vpp.venue_id = v.id
            LEFT JOIN public.venue_published_location vpl ON vpl.venue_id = v.id
            LEFT JOIN public.locality l ON l.id = vpl.locality_id
            LEFT JOIN public.geographic_region gr ON gr.id = l.geographic_region_id
            LEFT JOIN public.geographic_region pgr ON pgr.id = gr.parent_region_id
            WHERE v.id = ANY(%s::uuid[])
            """,
            [venue_ids],
        )
        rows = {str(row[0]): row for row in c.fetchall()}

    enriched: list[dict[str, Any]] = []
    for item in stored:
        if not isinstance(item, dict):
            continue
        venue_id = str(item.get("venue_id", ""))
        row = rows.get(venue_id)
        enriched.append(
            {
                "venue_id": venue_id,
                "display_name": item.get("display_name")
                or (row[1] if row else None),
                "address_line_1": row[2] if row else None,
                "locality_name": row[3] if row else None,
                "state_code": row[4] if row else None,
                "match_score": item.get("match_score"),
                "match_reason": item.get("match_reason"),
            }
        )
    return enriched


def _locality_labels(locality_id: str | None) -> tuple[str | None, str | None]:
    if not locality_id:
        return None, None
    try:
        parsed_id = str(UUID(locality_id))
    except (ValueError, TypeError):
        return None, None
    with connection.cursor() as c:
        c.execute(
            """
            SELECT l.name, COALESCE(
                CASE WHEN gr.region_level = 'state' THEN gr.region_code END,
                pgr.region_code
            )
            FROM public.locality l
            LEFT JOIN public.geographic_region gr ON gr.id = l.geographic_region_id
            LEFT JOIN public.geographic_region pgr ON pgr.id = gr.parent_region_id
            WHERE l.id = %s::uuid
            """,
            [parsed_id],
        )
        row = c.fetchone()
    if not row:
        return None, None
    return row[0], row[1]


def _claim_list_row(row: tuple[Any, ...]) -> dict[str, Any]:
    (
        claim_id,
        status,
        created_at,
        owner_account_id,
        claimant_email,
        summary_text,
    ) = row
    summary = _parse_summary(summary_text)
    locality_id = summary.get("locality_id")
    locality_name, state_code = _locality_labels(
        str(locality_id) if locality_id else None
    )
    duplicate_candidates = summary.get("duplicate_candidates")
    duplicate_count = (
        len(duplicate_candidates) if isinstance(duplicate_candidates, list) else 0
    )
    return {
        "claim_request_id": str(claim_id),
        "status": str(status),
        "submitted_at": created_at.isoformat() if created_at else None,
        "owner_account_id": str(owner_account_id),
        "claimant_email": claimant_email,
        "venue_name": summary.get("venue_name"),
        "address_line_1": summary.get("address_line_1"),
        "locality_id": locality_id,
        "locality_name": locality_name,
        "state_code": state_code,
        "claimant_note": summary.get("claimant_note"),
        "duplicate_candidate_count": duplicate_count,
    }


def get_owner_claims_summary() -> dict[str, int]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT claim_lifecycle_status, COUNT(*)::int
            FROM public.venue_claim_request
            WHERE claim_lifecycle_status = ANY(%s)
            GROUP BY claim_lifecycle_status
            """,
            [list(OPEN_CLAIM_STATUSES)],
        )
        rows = c.fetchall()

    submitted_count = 0
    under_review_count = 0
    for status, count in rows:
        if status == "submitted":
            submitted_count = int(count)
        elif status == "under_review":
            under_review_count = int(count)
    open_count = submitted_count + under_review_count
    return {
        "open_count": open_count,
        "submitted_count": submitted_count,
        "under_review_count": under_review_count,
    }


def list_owner_claim_queue(filters: VenueClaimQueueFilters) -> dict[str, Any]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
                vcr.id,
                vcr.claim_lifecycle_status,
                vcr.created_at,
                vcr.initiated_by_owner_account_id,
                au.email,
                vcr.summary
            FROM public.venue_claim_request vcr
            INNER JOIN public.owner_account oa
                ON oa.id = vcr.initiated_by_owner_account_id
            LEFT JOIN auth.users au ON au.id = oa.auth_user_id
            WHERE vcr.claim_lifecycle_status = ANY(%s)
            ORDER BY vcr.created_at DESC
            """,
            [list(filters.statuses)],
        )
        rows = c.fetchall()

    items = [_claim_list_row(row) for row in rows]
    return {"items": items, "meta": {"total": len(items)}}


def get_owner_claim_detail(claim_request_id: str) -> dict[str, Any]:
    claim_id = _parse_uuid(claim_request_id, key="claim_request_id")
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
                vcr.id,
                vcr.claim_lifecycle_status,
                vcr.created_at,
                vcr.updated_at,
                vcr.venue_id::text,
                vcr.business_id::text,
                vcr.initiated_by_owner_account_id::text,
                vcr.resulting_business_venue_management_relationship_id::text,
                vcr.summary,
                au.email,
                b.display_name
            FROM public.venue_claim_request vcr
            INNER JOIN public.owner_account oa
                ON oa.id = vcr.initiated_by_owner_account_id
            LEFT JOIN auth.users au ON au.id = oa.auth_user_id
            INNER JOIN public.business b ON b.id = vcr.business_id
            WHERE vcr.id = %s::uuid
            """,
            [claim_id],
        )
        row = c.fetchone()

    if not row:
        raise VenueClaimNotFoundError

    summary = _parse_summary(row[8])
    locality_name, state_code = _locality_labels(
        str(summary.get("locality_id")) if summary.get("locality_id") else None
    )
    duplicate_candidates = _enrich_duplicate_candidates(summary)
    return {
        "claim_request_id": str(row[0]),
        "status": str(row[1]),
        "submitted_at": row[2].isoformat() if row[2] else None,
        "updated_at": row[3].isoformat() if row[3] else None,
        "venue_id": row[4],
        "business_id": row[5],
        "owner_account_id": row[6],
        "resulting_relationship_id": row[7],
        "claimant_email": row[9],
        "business_display_name": row[10],
        "submitted": {
            "mode": summary.get("mode"),
            "venue_name": summary.get("venue_name"),
            "address_line_1": summary.get("address_line_1"),
            "locality_id": summary.get("locality_id"),
            "locality_name": locality_name,
            "state_code": state_code,
            "claimant_note": summary.get("claimant_note"),
        },
        "possible_duplicate_venue_ids": summary.get("possible_duplicate_venue_ids") or [],
        "duplicate_candidates": duplicate_candidates,
    }
