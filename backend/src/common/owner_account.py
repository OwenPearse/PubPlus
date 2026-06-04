"""
Resolve Supabase auth subject → `public.owner_account.id` (race-safe insert/lookup).

Owner rows are not insertable from browser clients (SELECT-only RLS); Django uses the
backend database role to provision after Supabase sign-up.
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


def get_owner_account_id(auth: AuthContext) -> UUID | None:
    """Return existing `owner_account.id` for this auth subject, or None."""
    auth_uid = _auth_user_uuid(auth)
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id
            FROM public.owner_account
            WHERE auth_user_id = %s::uuid
            """,
            [str(auth_uid)],
        )
        row = c.fetchone()
    if not row:
        return None
    return UUID(str(row[0]))


def admin_account_exists_for_auth(auth: AuthContext) -> bool:
    """True when the same auth subject already has an internal admin domain row."""
    auth_uid = _auth_user_uuid(auth)
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1
            FROM public.admin_account
            WHERE auth_user_id = %s::uuid
            LIMIT 1
            """,
            [str(auth_uid)],
        )
        return c.fetchone() is not None


@transaction.atomic
def get_or_create_owner_account_id(auth: AuthContext) -> tuple[UUID, bool]:
    """
    Resolve Supabase `sub` to `public.owner_account.id`, creating the row if missing.

    Returns (owner_account_id, created) where created is True only on a new insert.
    """
    auth_uid = _auth_user_uuid(auth)
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id
            FROM public.owner_account
            WHERE auth_user_id = %s::uuid
            """,
            [str(auth_uid)],
        )
        row = c.fetchone()
        if row:
            return UUID(str(row[0])), False
        try:
            c.execute(
                """
                INSERT INTO public.owner_account (auth_user_id)
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
                FROM public.owner_account
                WHERE auth_user_id = %s::uuid
                """,
                [str(auth_uid)],
            )
            ins = c.fetchone()
            if ins:
                return UUID(str(ins[0])), False
            raise
        if not ins:
            raise RuntimeError("Could not resolve owner_account.")
        return UUID(str(ins[0])), True
