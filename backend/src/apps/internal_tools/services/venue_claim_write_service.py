from __future__ import annotations

import json
import re
from typing import Any
from uuid import UUID

from django.db import connection, transaction

from apps.internal_tools.services.moderation_write_service import ResolvedOperator

OPEN_CLAIM_STATUSES = frozenset({"draft", "submitted", "under_review"})
TERMINAL_CLAIM_STATUSES = frozenset({"withdrawn", "denied", "closed"})
_OWNER_CAPABILITIES = (
    "manage_published_venue_operations",
    "submit_restricted_changes_for_review",
)
_NOTE_MAX_LEN = 2000


class VenueClaimWriteValidationError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class VenueClaimWriteNotFoundError(LookupError):
    pass


class VenueClaimDecisionConflictError(RuntimeError):
    pass


def _parse_uuid(value: Any, *, key: str) -> str:
    if not isinstance(value, str):
        raise VenueClaimWriteValidationError(f"{key} must be a valid UUID string.")
    try:
        return str(UUID(value))
    except (ValueError, TypeError) as exc:
        raise VenueClaimWriteValidationError(
            f"{key} must be a valid UUID string."
        ) from exc


def _normalize_optional_note(value: Any, *, key: str = "admin_note") -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise VenueClaimWriteValidationError(f"{key} must be a string when provided.")
    trimmed = value.strip()
    if not trimmed:
        return None
    if len(trimmed) > _NOTE_MAX_LEN:
        raise VenueClaimWriteValidationError(
            f"{key} must be at most {_NOTE_MAX_LEN} characters."
        )
    return trimmed


def _parse_summary(summary: str | None) -> dict[str, Any]:
    if not summary:
        return {}
    try:
        data = json.loads(summary)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:120] or "venue"


def _load_claim_for_write(claim_id: str) -> dict[str, Any]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
                id::text,
                claim_lifecycle_status,
                venue_id::text,
                business_id::text,
                initiated_by_owner_account_id::text,
                summary,
                resulting_business_venue_management_relationship_id::text
            FROM public.venue_claim_request
            WHERE id = %s::uuid
            """,
            [claim_id],
        )
        row = c.fetchone()
    if not row:
        raise VenueClaimWriteNotFoundError
    return {
        "claim_request_id": row[0],
        "status": row[1],
        "venue_id": row[2],
        "business_id": row[3],
        "owner_account_id": row[4],
        "summary": row[5],
        "resulting_relationship_id": row[6],
    }


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


def _ensure_active_membership(owner_account_id: str, business_id: str) -> None:
    with connection.cursor() as c:
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
            """,
            [owner_account_id, business_id],
        )


def _upsert_approved_relationship(
    *,
    business_id: str,
    venue_id: str,
    claim_request_id: str,
) -> str:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.business_venue_management_relationship (
                business_id,
                venue_id,
                relationship_lifecycle,
                source_venue_claim_request_id
            ) VALUES (
                %s::uuid, %s::uuid, 'approved', %s::uuid
            )
            ON CONFLICT (business_id, venue_id) DO UPDATE SET
                relationship_lifecycle = 'approved',
                source_venue_claim_request_id = EXCLUDED.source_venue_claim_request_id,
                updated_at = now()
            RETURNING id::text
            """,
            [business_id, venue_id, claim_request_id],
        )
        row = c.fetchone()
    if not row:
        raise VenueClaimDecisionConflictError(
            "Could not create approved business venue management relationship."
        )
    return str(row[0])


def _ensure_verification_and_rights(
    relationship_id: str, *, claim_request_id: str
) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_verification_state (
                business_venue_management_relationship_id,
                context_venue_claim_request_id,
                verification_status,
                last_evaluated_at
            ) VALUES (
                %s::uuid, %s::uuid, 'verified', now()
            )
            ON CONFLICT (business_venue_management_relationship_id) DO UPDATE SET
                verification_status = 'verified',
                context_venue_claim_request_id = EXCLUDED.context_venue_claim_request_id,
                last_evaluated_at = now(),
                updated_at = now()
            """,
            [relationship_id, claim_request_id],
        )
        c.execute(
            """
            INSERT INTO public.venue_management_rights (
                business_venue_management_relationship_id,
                rights_status,
                effective_from
            ) VALUES (
                %s::uuid, 'active', now()
            )
            ON CONFLICT (business_venue_management_relationship_id) DO UPDATE SET
                rights_status = 'active',
                effective_from = COALESCE(
                    public.venue_management_rights.effective_from, now()
                ),
                updated_at = now()
            """,
            [relationship_id],
        )


def _grant_owner_capabilities(relationship_id: str, owner_account_id: str) -> None:
    with connection.cursor() as c:
        for capability in _OWNER_CAPABILITIES:
            c.execute(
                """
                INSERT INTO public.venue_capability_grant (
                    business_venue_management_relationship_id,
                    owner_account_id,
                    capability_code,
                    grant_status
                ) VALUES (
                    %s::uuid, %s::uuid, %s, 'active'
                )
                ON CONFLICT (
                    business_venue_management_relationship_id,
                    owner_account_id,
                    capability_code
                ) DO UPDATE SET
                    grant_status = 'active',
                    revoked_at = NULL,
                    updated_at = now()
                """,
                [relationship_id, owner_account_id, capability],
            )


def _publish_minimum_venue_rows(
    *,
    venue_id: str,
    venue_name: str,
    address_line_1: str | None,
    locality_id: str,
) -> None:
    slug_base = _slugify(venue_name)
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM public.venue_published_profile WHERE venue_id = %s::uuid
            """,
            [venue_id],
        )
        if not c.fetchone():
            c.execute(
                """
                INSERT INTO public.venue_published_profile (
                    venue_id, display_name, slug
                ) VALUES (
                    %s::uuid, %s, %s
                )
                """,
                [venue_id, venue_name, f"{slug_base}-{venue_id[:8]}"],
            )
        c.execute(
            """
            SELECT 1 FROM public.venue_published_location WHERE venue_id = %s::uuid
            """,
            [venue_id],
        )
        if not c.fetchone():
            c.execute(
                """
                INSERT INTO public.venue_published_location (
                    venue_id, locality_id, address_line_1
                ) VALUES (
                    %s::uuid, %s::uuid, %s
                )
                """,
                [venue_id, locality_id, address_line_1],
            )


def _record_authority_audit(
    *,
    operator: ResolvedOperator,
    claim_request_id: str,
    business_id: str,
    venue_id: str,
    owner_account_id: str,
    relationship_id: str | None,
    decision_outcome: str,
    rationale: str | None,
    event_kind: str,
) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_authority_decision (
                decided_by_admin_account_id,
                decision_kind,
                venue_claim_request_id,
                business_venue_management_relationship_id,
                decision_outcome,
                rationale
            ) VALUES (
                %s::uuid, 'claim_decision', %s::uuid, %s::uuid, %s, %s
            )
            RETURNING id::text
            """,
            [
                operator.admin_account_id,
                claim_request_id,
                relationship_id,
                decision_outcome,
                rationale,
            ],
        )
        decision_id = c.fetchone()[0]
        c.execute(
            """
            INSERT INTO public.venue_authority_event (
                event_kind,
                venue_id,
                business_id,
                owner_account_id,
                venue_claim_request_id,
                business_venue_management_relationship_id,
                payload_note
            ) VALUES (
                %s, %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s, %s
            )
            """,
            [
                event_kind,
                venue_id,
                business_id,
                owner_account_id,
                claim_request_id,
                relationship_id,
                rationale,
            ],
        )
        c.execute(
            """
            INSERT INTO public.audit_event (
                actor_type,
                actor_admin_account_id,
                entity_table,
                entity_id,
                action,
                detail
            ) VALUES (
                'admin',
                %s::uuid,
                'venue_claim_request',
                %s::uuid,
                'claim_review_decision',
                %s::jsonb
            )
            """,
            [
                operator.admin_account_id,
                claim_request_id,
                json.dumps(
                    {
                        "decision_outcome": decision_outcome,
                        "event_kind": event_kind,
                        "authority_decision_id": decision_id,
                        "relationship_id": relationship_id,
                        "venue_id": venue_id,
                        "rationale": rationale,
                        "operator_subject": operator.auth_subject,
                        "operator_email": operator.email,
                    }
                ),
            ],
        )


def _finalize_claim_approval(
    *,
    claim: dict[str, Any],
    venue_id: str,
    operator: ResolvedOperator,
    admin_note: str | None,
    decision_outcome: str,
    event_kind: str,
) -> dict[str, Any]:
    if claim["status"] in TERMINAL_CLAIM_STATUSES:
        raise VenueClaimDecisionConflictError(
            "Claim request is already in a terminal status."
        )
    if claim["status"] not in OPEN_CLAIM_STATUSES:
        raise VenueClaimDecisionConflictError(
            "Claim request is not in a reviewable workflow state."
        )
    if claim["resulting_relationship_id"]:
        raise VenueClaimDecisionConflictError(
            "Claim request already has an approved management relationship."
        )

    _ensure_active_membership(claim["owner_account_id"], claim["business_id"])
    relationship_id = _upsert_approved_relationship(
        business_id=claim["business_id"],
        venue_id=venue_id,
        claim_request_id=claim["claim_request_id"],
    )
    _ensure_verification_and_rights(
        relationship_id, claim_request_id=claim["claim_request_id"]
    )
    _grant_owner_capabilities(relationship_id, claim["owner_account_id"])

    with connection.cursor() as c:
        c.execute(
            """
            UPDATE public.venue_claim_request
            SET claim_lifecycle_status = 'closed',
                resulting_business_venue_management_relationship_id = %s::uuid,
                updated_at = now()
            WHERE id = %s::uuid
            RETURNING updated_at
            """,
            [relationship_id, claim["claim_request_id"]],
        )
        updated_row = c.fetchone()

    _record_authority_audit(
        operator=operator,
        claim_request_id=claim["claim_request_id"],
        business_id=claim["business_id"],
        venue_id=venue_id,
        owner_account_id=claim["owner_account_id"],
        relationship_id=relationship_id,
        decision_outcome=decision_outcome,
        rationale=admin_note,
        event_kind=event_kind,
    )

    return {
        "claim_request_id": claim["claim_request_id"],
        "status": "closed",
        "venue_id": venue_id,
        "relationship_id": relationship_id,
        "updated_at": updated_row[0].isoformat() if updated_row and updated_row[0] else None,
        "message": "Claim approved and owner venue access granted.",
    }


@transaction.atomic
def approve_owner_claim_existing(
    claim_request_id: str,
    *,
    venue_id: Any,
    admin_note: Any,
    operator: ResolvedOperator,
) -> dict[str, Any]:
    claim_id = _parse_uuid(claim_request_id, key="claim_request_id")
    target_venue_id = _parse_uuid(venue_id, key="venue_id")
    note = _normalize_optional_note(admin_note)

    if not _published_venue_exists(target_venue_id):
        raise VenueClaimWriteValidationError(
            "venue_id must reference an existing published venue."
        )

    claim = _load_claim_for_write(claim_id)
    return _finalize_claim_approval(
        claim=claim,
        venue_id=target_venue_id,
        operator=operator,
        admin_note=note,
        decision_outcome="approved_existing",
        event_kind="claim_approved_existing",
    )


@transaction.atomic
def approve_owner_claim_new(
    claim_request_id: str,
    *,
    admin_note: Any,
    operator: ResolvedOperator,
) -> dict[str, Any]:
    claim_id = _parse_uuid(claim_request_id, key="claim_request_id")
    note = _normalize_optional_note(admin_note)
    claim = _load_claim_for_write(claim_id)
    summary = _parse_summary(claim["summary"])

    venue_name = summary.get("venue_name")
    locality_id = summary.get("locality_id")
    if not isinstance(venue_name, str) or not venue_name.strip():
        raise VenueClaimWriteValidationError(
            "Submitted claim is missing venue_name in summary."
        )
    if not locality_id:
        raise VenueClaimWriteValidationError(
            "Submitted claim is missing locality_id in summary."
        )
    locality_uuid = _parse_uuid(str(locality_id), key="locality_id")
    address_line_1 = summary.get("address_line_1")
    if address_line_1 is not None and not isinstance(address_line_1, str):
        raise VenueClaimWriteValidationError(
            "Submitted claim address_line_1 must be a string."
        )

    target_venue_id = claim["venue_id"]
    _publish_minimum_venue_rows(
        venue_id=target_venue_id,
        venue_name=venue_name.strip(),
        address_line_1=(address_line_1 or "").strip() or None,
        locality_id=locality_uuid,
    )

    return _finalize_claim_approval(
        claim=claim,
        venue_id=target_venue_id,
        operator=operator,
        admin_note=note,
        decision_outcome="approved_new",
        event_kind="claim_approved_new",
    )


@transaction.atomic
def reject_owner_claim(
    claim_request_id: str,
    *,
    admin_note: Any,
    operator: ResolvedOperator,
) -> dict[str, Any]:
    claim_id = _parse_uuid(claim_request_id, key="claim_request_id")
    note = _normalize_optional_note(admin_note, key="admin_note")
    claim = _load_claim_for_write(claim_id)

    if claim["status"] in TERMINAL_CLAIM_STATUSES:
        raise VenueClaimDecisionConflictError(
            "Claim request is already in a terminal status."
        )
    if claim["status"] not in OPEN_CLAIM_STATUSES:
        raise VenueClaimDecisionConflictError(
            "Claim request is not in a reviewable workflow state."
        )

    with connection.cursor() as c:
        c.execute(
            """
            UPDATE public.venue_claim_request
            SET claim_lifecycle_status = 'denied',
                updated_at = now()
            WHERE id = %s::uuid
            RETURNING updated_at
            """,
            [claim_id],
        )
        updated_row = c.fetchone()

    _record_authority_audit(
        operator=operator,
        claim_request_id=claim["claim_request_id"],
        business_id=claim["business_id"],
        venue_id=claim["venue_id"],
        owner_account_id=claim["owner_account_id"],
        relationship_id=None,
        decision_outcome="rejected",
        rationale=note,
        event_kind="claim_rejected",
    )

    return {
        "claim_request_id": claim["claim_request_id"],
        "status": "denied",
        "updated_at": updated_row[0].isoformat() if updated_row and updated_row[0] else None,
        "message": "Claim request rejected.",
    }


@transaction.atomic
def mark_owner_claim_needs_more_info(
    claim_request_id: str,
    *,
    admin_note: Any,
    operator: ResolvedOperator,
) -> dict[str, Any]:
    claim_id = _parse_uuid(claim_request_id, key="claim_request_id")
    note = _normalize_optional_note(admin_note, key="admin_note")
    if not note:
        raise VenueClaimWriteValidationError(
            "admin_note is required when requesting more information."
        )

    claim = _load_claim_for_write(claim_id)
    if claim["status"] in TERMINAL_CLAIM_STATUSES:
        raise VenueClaimDecisionConflictError(
            "Claim request is already in a terminal status."
        )
    if claim["status"] not in OPEN_CLAIM_STATUSES:
        raise VenueClaimDecisionConflictError(
            "Claim request is not in a reviewable workflow state."
        )

    with connection.cursor() as c:
        c.execute(
            """
            UPDATE public.venue_claim_request
            SET claim_lifecycle_status = 'under_review',
                updated_at = now()
            WHERE id = %s::uuid
            RETURNING updated_at
            """,
            [claim_id],
        )
        updated_row = c.fetchone()

    _record_authority_audit(
        operator=operator,
        claim_request_id=claim["claim_request_id"],
        business_id=claim["business_id"],
        venue_id=claim["venue_id"],
        owner_account_id=claim["owner_account_id"],
        relationship_id=None,
        decision_outcome="needs_more_info",
        rationale=note,
        event_kind="claim_needs_more_info",
    )

    return {
        "claim_request_id": claim["claim_request_id"],
        "status": "under_review",
        "updated_at": updated_row[0].isoformat() if updated_row and updated_row[0] else None,
        "message": "Claim marked as needing more information.",
    }
