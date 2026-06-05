"""
Owner venue claim intake: candidate search and claim request submission.

Owners without approved venue management can search published listings and submit
claim requests for admin review. No claim is self-approved.
"""

from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from django.db import connection, transaction

from common.auth.context import AuthContext
from common.owner_account import admin_account_exists_for_auth, get_owner_account_id

MAX_CLAIMANT_NOTE_LEN = 2000
_OPEN_CLAIM_STATUSES = frozenset({"draft", "submitted", "under_review"})
_GOOD_MATCH_SCORE = 55
_MAX_CANDIDATES = 10


def _bad_uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    try:
        UUID(value)
    except (ValueError, TypeError):
        return True
    return False


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _score_candidate(
    *,
    query_name: str,
    candidate_name: str,
    locality_id: str | None,
    candidate_locality_id: str | None,
    address_line_1: str | None,
    candidate_address: str | None,
) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []
    qn = _normalize_name(query_name)
    cn = _normalize_name(candidate_name)

    if qn == cn:
        score += 70
        reasons.append("Exact name match")
    elif cn.startswith(qn) or qn.startswith(cn):
        score += 55
        reasons.append("Similar name")
    elif qn in cn or cn in qn:
        score += 40
        reasons.append("Name contains search text")
    else:
        return 0, ""

    if locality_id and candidate_locality_id and str(locality_id) == str(
        candidate_locality_id
    ):
        score += 25
        reasons.append("Same locality")

    if address_line_1 and candidate_address:
        qa = _normalize_name(address_line_1)
        ca = _normalize_name(candidate_address)
        if qa == ca:
            score += 15
            reasons.append("Same address")
        elif qa in ca or ca in qa:
            score += 8
            reasons.append("Similar address")

    return min(score, 100), "; ".join(reasons)


def _locality_exists(locality_id: str) -> bool:
    with connection.cursor() as c:
        c.execute(
            "SELECT 1 FROM public.locality WHERE id = %s::uuid",
            [locality_id],
        )
        return c.fetchone() is not None


def _published_venue_exists(venue_id: str) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1
            FROM public.venue v
            INNER JOIN public.venue_published_profile vpp ON vpp.venue_id = v.id
            WHERE v.id = %s::uuid
            """,
            [venue_id],
        )
        return c.fetchone() is not None


def _find_open_claim_id(owner_account_id: str, venue_id: str) -> str | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id::text
            FROM public.venue_claim_request
            WHERE initiated_by_owner_account_id = %s::uuid
              AND venue_id = %s::uuid
              AND claim_lifecycle_status = ANY(%s)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [owner_account_id, venue_id, list(_OPEN_CLAIM_STATUSES)],
        )
        row = c.fetchone()
    return str(row[0]) if row else None


def _resolve_owner_business_id(owner_account_id: str, *, business_label: str) -> str:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT business_id::text
            FROM public.owner_business_membership
            WHERE owner_account_id = %s::uuid
              AND membership_status = 'active'
            ORDER BY activated_at DESC NULLS LAST, created_at ASC
            LIMIT 1
            """,
            [owner_account_id],
        )
        row = c.fetchone()
        if row:
            return str(row[0])

        c.execute(
            """
            INSERT INTO public.business (display_name)
            VALUES (%s)
            RETURNING id
            """,
            [business_label.strip()[:200] or "Pending venue claim"],
        )
        business_id = c.fetchone()[0]
        c.execute(
            """
            INSERT INTO public.owner_business_membership (
                owner_account_id,
                business_id,
                membership_status,
                membership_role,
                activated_at
            ) VALUES (
                %s::uuid, %s::uuid, 'active', 'org_owner', now()
            )
            ON CONFLICT (owner_account_id, business_id) DO UPDATE SET
                membership_status = 'active',
                updated_at = now()
            RETURNING business_id
            """,
            [owner_account_id, str(business_id)],
        )
        return str(c.fetchone()[0])


def search_venue_claim_candidates(
    auth: AuthContext,
    *,
    name: str | None = None,
    locality_id: str | None = None,
    q: str | None = None,
    address_line_1: str | None = None,
) -> tuple[dict | None, str, dict[str, list[str]] | None]:
    if admin_account_exists_for_auth(auth):
        return None, "admin_forbidden", None

    owner_id = get_owner_account_id(auth)
    if owner_id is None:
        return None, "forbidden", None

    search_name = (name or q or "").strip()
    if not search_name:
        return None, "validation_error", {"name": ["Venue name is required."]}

    if locality_id is not None:
        if _bad_uuid(locality_id):
            return None, "validation_error", {
                "locality_id": ["Must be a valid UUID string or null."]
            }
        if not _locality_exists(locality_id):
            return None, "validation_error", {
                "locality_id": ["locality_id does not reference an existing locality."]
            }

    pattern = f"%{search_name}%"
    params: list[Any] = [pattern]
    locality_filter = ""
    if locality_id:
        locality_filter = "AND vpl.locality_id = %s::uuid"
        params.append(locality_id)

    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT
                v.id::text,
                vpp.display_name,
                l.name,
                gr.state_code,
                vpl.address_line_1,
                vpl.locality_id::text
            FROM public.venue v
            INNER JOIN public.venue_published_profile vpp ON vpp.venue_id = v.id
            INNER JOIN public.venue_published_location vpl ON vpl.venue_id = v.id
            LEFT JOIN public.locality l ON l.id = vpl.locality_id
            LEFT JOIN public.geographic_region gr ON gr.id = l.geographic_region_id
            WHERE vpp.display_name ILIKE %s
            {locality_filter}
            ORDER BY vpp.display_name ASC
            LIMIT 50
            """,
            params,
        )
        rows = c.fetchall()

    candidates: list[dict[str, Any]] = []
    for row in rows:
        venue_id, display_name, locality_name, state_code, addr, loc_id = row
        score, reason = _score_candidate(
            query_name=search_name,
            candidate_name=display_name or "",
            locality_id=locality_id,
            candidate_locality_id=loc_id,
            address_line_1=address_line_1,
            candidate_address=addr,
        )
        if score <= 0:
            continue
        candidates.append(
            {
                "venue_id": venue_id,
                "display_name": display_name,
                "locality_name": locality_name,
                "state_code": state_code,
                "address_line_1": addr,
                "match_reason": reason,
                "match_score": score,
            }
        )

    candidates.sort(key=lambda item: item["match_score"], reverse=True)
    trimmed = candidates[:_MAX_CANDIDATES]
    best = trimmed[0] if trimmed and trimmed[0]["match_score"] >= _GOOD_MATCH_SCORE else None

    return (
        {
            "candidates": trimmed,
            "best_match": best,
            "has_good_match": best is not None,
        },
        "ok",
        None,
    )


def _validate_claimant_note(note: Any) -> tuple[str | None, str | None]:
    if note is None:
        return None, None
    if not isinstance(note, str):
        return None, "Must be a string or null."
    trimmed = note.strip()
    if len(trimmed) > MAX_CLAIMANT_NOTE_LEN:
        return None, f"Must be at most {MAX_CLAIMANT_NOTE_LEN} characters."
    return trimmed or None, None


@transaction.atomic
def submit_venue_claim_request(
    auth: AuthContext, body: dict[str, Any]
) -> tuple[dict | None, str, dict[str, list[str]] | None]:
    if admin_account_exists_for_auth(auth):
        return None, "admin_forbidden", None

    owner_id = get_owner_account_id(auth)
    if owner_id is None:
        return None, "forbidden", None

    owner_account_id = str(owner_id)
    mode = body.get("mode")
    if mode not in ("claim_existing", "submit_new", "submit_new_or_claim"):
        return None, "validation_error", {
            "mode": ["mode must be claim_existing, submit_new, or submit_new_or_claim."]
        }

    note, note_err = _validate_claimant_note(body.get("claimant_note"))
    if note_err:
        return None, "validation_error", {"claimant_note": [note_err]}

    if mode == "claim_existing":
        venue_id = body.get("venue_id")
        if not isinstance(venue_id, str) or _bad_uuid(venue_id):
            return None, "validation_error", {
                "venue_id": ["venue_id must be a valid UUID string."]
            }
        if not _published_venue_exists(venue_id):
            return None, "not_found", None

        existing = _find_open_claim_id(owner_account_id, venue_id)
        if existing:
            return (
                {
                    "claim_request_id": existing,
                    "status": "submitted",
                    "message": (
                        "You already have an open claim request for this venue. "
                        "We'll review that you are authorised to manage it."
                    ),
                },
                "duplicate_open",
                None,
            )

        with connection.cursor() as c:
            c.execute(
                """
                SELECT vpp.display_name
                FROM public.venue_published_profile vpp
                WHERE vpp.venue_id = %s::uuid
                """,
                [venue_id],
            )
            row = c.fetchone()
        business_label = (row[0] if row else None) or "Venue claim"

        business_id = _resolve_owner_business_id(
            owner_account_id, business_label=str(business_label)
        )
        summary = json.dumps(
            {
                "mode": "claim_existing",
                "claimant_note": note,
            }
        )
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.venue_claim_request (
                    venue_id,
                    business_id,
                    initiated_by_owner_account_id,
                    claim_lifecycle_status,
                    summary
                ) VALUES (
                    %s::uuid, %s::uuid, %s::uuid, 'submitted', %s
                )
                RETURNING id::text
                """,
                [venue_id, business_id, owner_account_id, summary],
            )
            claim_id = c.fetchone()[0]

        return (
            {
                "claim_request_id": claim_id,
                "status": "submitted",
                "message": (
                    "Claim request submitted. We'll review that you're authorised "
                    "to manage this venue."
                ),
            },
            "ok",
            None,
        )

    venue_name = body.get("venue_name")
    if not isinstance(venue_name, str) or not venue_name.strip():
        return None, "validation_error", {"venue_name": ["This field is required."]}

    locality_id = body.get("locality_id")
    if mode == "submit_new_or_claim":
        if locality_id is None:
            return None, "validation_error", {
                "locality_id": ["This field is required."]
            }
        if _bad_uuid(locality_id):
            return None, "validation_error", {
                "locality_id": ["Must be a valid UUID string."]
            }
        if not _locality_exists(str(locality_id)):
            return None, "validation_error", {
                "locality_id": ["locality_id does not reference an existing locality."]
            }
    elif locality_id is not None:
        if _bad_uuid(locality_id):
            return None, "validation_error", {
                "locality_id": ["Must be a valid UUID string or null."]
            }
        if not _locality_exists(str(locality_id)):
            return None, "validation_error", {
                "locality_id": ["locality_id does not reference an existing locality."]
            }

    address_line_1 = body.get("address_line_1")
    if mode == "submit_new_or_claim":
        if not isinstance(address_line_1, str) or not address_line_1.strip():
            return None, "validation_error", {
                "address_line_1": ["This field is required."]
            }
    elif address_line_1 is not None and not isinstance(address_line_1, str):
        return None, "validation_error", {
            "address_line_1": ["Must be a string or null."]
        }

    trimmed_name = venue_name.strip()
    trimmed_address = (address_line_1 or "").strip() if isinstance(address_line_1, str) else ""

    duplicate_candidates: list[dict[str, Any]] = []
    possible_duplicate_venue_ids: list[str] = []
    if mode == "submit_new_or_claim":
        dup_result, dup_code, _ = search_venue_claim_candidates(
            auth,
            name=trimmed_name,
            locality_id=str(locality_id),
            address_line_1=trimmed_address,
        )
        if dup_code == "ok" and dup_result:
            for candidate in dup_result.get("candidates", []):
                possible_duplicate_venue_ids.append(candidate["venue_id"])
                duplicate_candidates.append(
                    {
                        "venue_id": candidate["venue_id"],
                        "display_name": candidate["display_name"],
                        "match_score": candidate["match_score"],
                        "match_reason": candidate["match_reason"],
                    }
                )

    business_id = _resolve_owner_business_id(
        owner_account_id, business_label=trimmed_name
    )

    with connection.cursor() as c:
        c.execute("INSERT INTO public.venue DEFAULT VALUES RETURNING id")
        new_venue_id = str(c.fetchone()[0])

    existing = _find_open_claim_id(owner_account_id, new_venue_id)
    if existing:
        return (
            {
                "claim_request_id": existing,
                "status": "submitted",
                "message": (
                    "You already have an open claim request for this venue. "
                    "We'll review that you are authorised to manage it."
                ),
            },
            "duplicate_open",
            None,
        )

    summary_payload: dict[str, Any] = {
        "mode": mode,
        "venue_name": trimmed_name,
        "address_line_1": trimmed_address or None,
        "locality_id": str(locality_id) if locality_id else None,
        "claimant_note": note,
    }
    if mode == "submit_new_or_claim":
        summary_payload["possible_duplicate_venue_ids"] = possible_duplicate_venue_ids
        summary_payload["duplicate_candidates"] = duplicate_candidates

    summary = json.dumps(summary_payload)
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_claim_request (
                venue_id,
                business_id,
                initiated_by_owner_account_id,
                claim_lifecycle_status,
                summary
            ) VALUES (
                %s::uuid, %s::uuid, %s::uuid, 'submitted', %s
            )
            RETURNING id::text
            """,
            [new_venue_id, business_id, owner_account_id, summary],
        )
        claim_id = c.fetchone()[0]

    if mode == "submit_new_or_claim":
        message = (
            "Thanks — your venue details have been submitted for review. "
            "We'll check the details and let you know when you can manage the listing."
        )
    else:
        message = (
            "Claim request submitted. We'll review that you're authorised "
            "to manage this venue."
        )

    return (
        {
            "claim_request_id": claim_id,
            "status": "submitted",
            "message": message,
        },
        "ok",
        None,
    )
