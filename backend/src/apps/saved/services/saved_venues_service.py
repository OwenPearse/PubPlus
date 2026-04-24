"""
Consumer-private saved venue persistence: default named list + membership (list-native model).

Uses `public.saved_list` / `public.saved_list_membership` only. Does not mutate public venue truth.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from django.db import DatabaseError, connection, transaction

from apps.venues.public_read.card import public_venue_card_to_dict
from apps.venues.services import save_enrichment
from apps.venues.services.venue_read_service import build_public_venue_card
from common.auth.context import AuthContext
from common.consumer_account import get_or_create_consumer_account_id

# Convention: one MVP default list for simple save/unsave; list-native model (Worker 1 / Stage C).
DEFAULT_SAVED_LIST_NAME = "Saved"


@dataclass(frozen=True)
class SaveVenueResult:
    venue_id: str
    saved: bool


@transaction.atomic
def get_or_create_default_saved_list_id(*, consumer_account_id: UUID) -> UUID:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id
            FROM public.saved_list
            WHERE consumer_account_id = %s::uuid
              AND name = %s
              AND is_archived = false
            ORDER BY sort_order, created_at
            LIMIT 1
            """,
            [str(consumer_account_id), DEFAULT_SAVED_LIST_NAME],
        )
        row = c.fetchone()
        if row:
            return UUID(str(row[0]))
        c.execute(
            """
            INSERT INTO public.saved_list (consumer_account_id, name, sort_order, is_archived)
            VALUES (%s::uuid, %s, 0, false)
            RETURNING id
            """,
            [str(consumer_account_id), DEFAULT_SAVED_LIST_NAME],
        )
        created = c.fetchone()
        if not created:
            raise RuntimeError("Default saved list insert failed.")
        return UUID(str(created[0]))


def venue_row_exists(venue_id: UUID) -> bool:
    with connection.cursor() as c:
        c.execute("SELECT 1 FROM public.venue WHERE id = %s::uuid LIMIT 1", [str(venue_id)])
        return c.fetchone() is not None


@transaction.atomic
def add_venue_to_default_list(
    *, auth: AuthContext, venue_id: UUID
) -> SaveVenueResult | None:
    """Return None if the canonical `venue` row does not exist."""
    if not venue_row_exists(venue_id):
        return None

    consumer_id = get_or_create_consumer_account_id(auth)
    list_id = get_or_create_default_saved_list_id(consumer_account_id=consumer_id)

    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.saved_list_membership (saved_list_id, venue_id, position)
            VALUES (%s::uuid, %s::uuid, NULL)
            ON CONFLICT (saved_list_id, venue_id) DO NOTHING
            """,
            [str(list_id), str(venue_id)],
        )
    return SaveVenueResult(venue_id=str(venue_id), saved=True)


@transaction.atomic
def remove_venue_from_default_list(*, auth: AuthContext, venue_id: UUID) -> None:
    """Idempotent: no error if the membership row is already absent."""
    try:
        consumer_id = get_or_create_consumer_account_id(auth)
    except (ValueError, RuntimeError):
        return

    with connection.cursor() as c:
        c.execute(
            """
            SELECT s.id
            FROM public.saved_list s
            WHERE s.consumer_account_id = %s::uuid
              AND s.name = %s
              AND s.is_archived = false
            LIMIT 1
            """,
            [str(consumer_id), DEFAULT_SAVED_LIST_NAME],
        )
        row = c.fetchone()
        if not row:
            return
        list_id = row[0]
        c.execute(
            """
            DELETE FROM public.saved_list_membership
            WHERE saved_list_id = %s::uuid
              AND venue_id = %s::uuid
            """,
            [str(list_id), str(venue_id)],
        )


def _ordered_default_list_venue_ids(*, saved_list_id: UUID) -> list[str]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT m.venue_id::text
            FROM public.saved_list_membership m
            WHERE m.saved_list_id = %s::uuid
            ORDER BY m.added_at DESC, m.venue_id::text
            """,
            [str(saved_list_id)],
        )
        return [row[0] for row in c.fetchall()]


@transaction.atomic
def list_default_saved_venue_payloads(
    *, auth: AuthContext
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Returns JSON-ready card dicts for the default 'Saved' list, most recently added first.
    Returns (venues, error_code) where error_code is set on recoverable service failure.
    """
    try:
        consumer_id = get_or_create_consumer_account_id(auth)
    except ValueError:
        return [], "invalid_auth_subject"
    except (DatabaseError, RuntimeError):
        return [], "consumer_account_error"

    try:
        list_id = get_or_create_default_saved_list_id(consumer_account_id=consumer_id)
    except (DatabaseError, RuntimeError):
        return [], "saved_list_error"

    venue_ids = _ordered_default_list_venue_ids(saved_list_id=list_id)
    out: list[dict[str, Any]] = []
    for vid in venue_ids:
        card = build_public_venue_card(
            vid, auth=auth, origin_lat=None, origin_lon=None
        )
        if card is None:
            continue
        enriched = save_enrichment.apply_save_to_card(
            card, auth=auth, venue_id=card.id
        )
        out.append(public_venue_card_to_dict(enriched))
    return out, None


def parse_venue_id_from_request_body(body: bytes | str) -> tuple[UUID | None, str | None]:
    """Return (venue_id, error_code). error_code: malformed_json, missing_venue_id, invalid_venue_id."""
    if isinstance(body, bytes):
        if not body:
            return None, "missing_venue_id"
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return None, "malformed_json"
    else:
        if not (body or "").strip():
            return None, "missing_venue_id"
        try:
            payload = json.loads(str(body))
        except json.JSONDecodeError:
            return None, "malformed_json"
    if not isinstance(payload, dict):
        return None, "invalid_body"
    raw = payload.get("venue_id")
    if raw is None or raw == "":
        return None, "missing_venue_id"
    try:
        return UUID(str(raw)), None
    except (ValueError, TypeError):
        return None, "invalid_venue_id"


def parse_venue_id_path(raw: str) -> tuple[UUID | None, str | None]:
    if not raw or not str(raw).strip():
        return None, "invalid_venue_id"
    try:
        return UUID(str(raw)), None
    except (ValueError, TypeError):
        return None, "invalid_venue_id"
