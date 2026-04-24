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


@transaction.atomic
def get_or_create_consumer_account_id(auth: AuthContext) -> UUID:
    """Resolve Supabase `sub` to `public.consumer_account.id`, creating the row if missing."""
    auth_uid = _auth_user_uuid(auth)
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
            return UUID(str(row[0]))
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
    return UUID(str(ins[0]))
