from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from django.db import connection, transaction

from common.auth.context import AuthContext

OPEN_STATUSES = frozenset({"staged", "in_review"})
TERMINAL_STATUSES = frozenset({"approved", "rejected", "withdrawn", "superseded"})
DECISION_TO_OUTCOME = {"approve": "approved", "reject": "rejected"}
NOTE_MAX_LEN = 2000
REASON_MAX_LEN = 2000


class ModerationWriteValidationError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ModerationWriteNotFoundError(LookupError):
    pass


class ModerationDecisionConflictError(RuntimeError):
    pass


class InternalOperatorResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedOperator:
    admin_account_id: str
    auth_subject: str
    email: str | None


def _parse_uuid(value: str, *, key: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError) as exc:
        raise ModerationWriteValidationError(
            f"{key} must be a valid UUID."
        ) from exc


def _normalize_decision(value: Any) -> str:
    if not isinstance(value, str):
        raise ModerationWriteValidationError("decision must be one of: approve, reject.")
    v = value.strip().lower()
    if v not in DECISION_TO_OUTCOME:
        raise ModerationWriteValidationError("decision must be one of: approve, reject.")
    return v


def _normalize_optional_reason(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ModerationWriteValidationError("reason must be a string when provided.")
    out = value.strip()
    if not out:
        return None
    if len(out) > REASON_MAX_LEN:
        raise ModerationWriteValidationError(
            f"reason must be at most {REASON_MAX_LEN} characters."
        )
    return out


def _normalize_note_body(value: Any) -> str:
    if not isinstance(value, str):
        raise ModerationWriteValidationError("body is required and must be a string.")
    out = value.strip()
    if not out:
        raise ModerationWriteValidationError("body cannot be empty.")
    if len(out) > NOTE_MAX_LEN:
        raise ModerationWriteValidationError(
            f"body must be at most {NOTE_MAX_LEN} characters."
        )
    return out


def resolve_admin_account_for_internal_operator(auth_context: AuthContext) -> ResolvedOperator:
    auth_subject = _parse_uuid(auth_context.subject, key="auth subject")
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id::text
            FROM public.admin_account
            WHERE auth_user_id = %s::uuid
            """,
            [auth_subject],
        )
        row = c.fetchone()
    if not row:
        raise InternalOperatorResolutionError(
            "Authenticated internal operator is not linked to an admin_account row."
        )
    email = auth_context.email if isinstance(auth_context.email, str) else None
    return ResolvedOperator(
        admin_account_id=str(row[0]),
        auth_subject=auth_subject,
        email=email,
    )


def _load_proposal_for_write(proposal_id: str) -> tuple[str, str | None]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT lifecycle_status::text, closed_at
            FROM public.venue_change_proposal
            WHERE id = %s::uuid
            """,
            [proposal_id],
        )
        row = c.fetchone()
    if not row:
        raise ModerationWriteNotFoundError
    return str(row[0]), row[1].isoformat() if row[1] else None


def _next_review_sequence(proposal_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COALESCE(MAX(review_sequence), 0) + 1
            FROM public.proposal_review
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 1


@transaction.atomic
def decide_moderation_item(
    item_id: str,
    decision: Any,
    reason: Any,
    operator: ResolvedOperator,
) -> dict[str, Any]:
    proposal_id = _parse_uuid(item_id, key="item_id")
    normalized_decision = _normalize_decision(decision)
    reason_text = _normalize_optional_reason(reason)
    outcome = DECISION_TO_OUTCOME[normalized_decision]

    lifecycle_status, _ = _load_proposal_for_write(proposal_id)
    if lifecycle_status in TERMINAL_STATUSES:
        raise ModerationDecisionConflictError(
            "Moderation item is already in a terminal status and cannot be re-decided."
        )
    if lifecycle_status not in OPEN_STATUSES:
        raise ModerationDecisionConflictError(
            "Moderation item is not in a decisionable workflow state."
        )

    seq = _next_review_sequence(proposal_id)
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.proposal_review (
                venue_change_proposal_id,
                reviewer_admin_account_id,
                review_sequence,
                review_outcome,
                decision_reason_text
            ) VALUES (
                %s::uuid,
                %s::uuid,
                %s,
                %s,
                %s
            )
            RETURNING id::text, reviewed_at
            """,
            [
                proposal_id,
                operator.admin_account_id,
                seq,
                outcome,
                reason_text,
            ],
        )
        review_row = c.fetchone()

        c.execute(
            """
            UPDATE public.venue_change_proposal
            SET lifecycle_status = %s,
                closed_at = COALESCE(closed_at, now())
            WHERE id = %s::uuid
            RETURNING closed_at
            """,
            [outcome, proposal_id],
        )
        proposal_row = c.fetchone()

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
                'venue_change_proposal',
                %s::uuid,
                'moderation_decision',
                %s::jsonb
            )
            """,
            [
                operator.admin_account_id,
                proposal_id,
                json.dumps(
                    {
                        "decision": normalized_decision,
                        "review_outcome": outcome,
                        "review_id": str(review_row[0]),
                        "review_sequence": seq,
                        "reason": reason_text,
                        "operator_subject": operator.auth_subject,
                        "operator_email": operator.email,
                    }
                ),
            ],
        )

    return {
        "item_id": proposal_id,
        "status": outcome,
        "closed_at": proposal_row[0].isoformat() if proposal_row and proposal_row[0] else None,
        "review": {
            "id": str(review_row[0]),
            "review_outcome": outcome,
            "review_sequence": seq,
            "decision_reason_text": reason_text,
            "reviewed_at": review_row[1].isoformat() if review_row and review_row[1] else None,
            "reviewer_admin_account_id": operator.admin_account_id,
        },
    }


@transaction.atomic
def add_moderation_note(
    item_id: str,
    body: Any,
    operator: ResolvedOperator,
) -> dict[str, Any]:
    proposal_id = _parse_uuid(item_id, key="item_id")
    note_body = _normalize_note_body(body)
    _load_proposal_for_write(proposal_id)

    with connection.cursor() as c:
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
                'venue_change_proposal',
                %s::uuid,
                'internal_note',
                %s::jsonb
            )
            RETURNING id::text, occurred_at
            """,
            [
                operator.admin_account_id,
                proposal_id,
                json.dumps(
                    {
                        "body": note_body,
                        "operator_subject": operator.auth_subject,
                        "operator_email": operator.email,
                    }
                ),
            ],
        )
        row = c.fetchone()

    return {
        "item_id": proposal_id,
        "note": {
            "id": str(row[0]),
            "body": note_body,
            "created_at": row[1].isoformat() if row and row[1] else None,
            "actor_admin_account_id": operator.admin_account_id,
        },
    }
