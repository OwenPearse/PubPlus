"""
Resolve Supabase auth subject → `public.consumer_account.id` (race-safe insert/lookup).

Shared by consumer-private services (profile, saved, etc.).
"""

from __future__ import annotations

from uuid import UUID

from django.db import IntegrityError, connection, transaction

from common.auth.context import AuthContext


def _auth_user_uuid(auth: AuthContext) -> UUID:
    try:
        return UUID(str(auth.subject))
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid auth subject; expected a UUID auth user id.") from exc


def _default_display_name(auth: AuthContext) -> str:
    email = (auth.email or "").strip()
    if email and "@" in email:
        prefix = email.split("@", 1)[0].strip()
        if prefix:
            return prefix
    if email:
        return email
    return "Test Consumer"


def _ensure_consumer_profile_row(consumer_id: UUID, auth: AuthContext) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.consumer_profile (consumer_account_id, display_name)
            VALUES (%s::uuid, %s)
            ON CONFLICT (consumer_account_id) DO NOTHING
            """,
            [str(consumer_id), _default_display_name(auth)],
        )


@transaction.atomic
def get_or_create_consumer_account_id(auth: AuthContext) -> UUID:
    """Resolve Supabase `sub` to `public.consumer_account.id`, creating the row if missing."""
    auth_uid = _auth_user_uuid(auth)
    consumer_id: UUID | None = None
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id
            FROM public.consumer_account
            WHERE auth_user_id = %s::uuid
            """,
            [str(auth_uid)],
        )
        row = c.fetchone()
        if row:
            consumer_id = UUID(str(row[0]))
            _ensure_consumer_profile_row(consumer_id, auth)
            return consumer_id
        try:
            c.execute(
                """
                INSERT INTO public.consumer_account (auth_user_id)
                VALUES (%s::uuid)
                RETURNING id
                """,
                [str(auth_uid)],
            )
            ins = c.fetchone()
        except IntegrityError:
            c.execute(
                """
                SELECT id
                FROM public.consumer_account
                WHERE auth_user_id = %s::uuid
                """,
                [str(auth_uid)],
            )
            ins = c.fetchone()
        if not ins:
            raise RuntimeError("Could not resolve consumer_account.")
        consumer_id = UUID(str(ins[0]))
    _ensure_consumer_profile_row(consumer_id, auth)
    return consumer_id
