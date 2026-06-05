"""
E2E fixtures for owner venue claim API tests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import DatabaseError, connection

from tests.support.saved_venues_e2e_data import (
    E2E_LOCALITY_ID,
    E2E_VENUE_ID,
    try_install_saved_venues_e2e_fixtures,
)

logger = logging.getLogger(__name__)

E2E_CLAIM_OWNER_AUTH_USER_ID = "bada0006-0000-4000-8000-0000000000c1"
E2E_CLAIM_OWNER_EMAIL = "e2e-owner-claim@pubplus.test"


@dataclass(frozen=True, slots=True)
class OwnerClaimE2EInstall:
    venue_id: str
    owner_auth_user_id: str
    owner_account_id: str
    locality_id: str
    published_display_name: str


def _tables_ok(cursor) -> bool:
    for name in (
        "owner_account",
        "owner_business_membership",
        "business",
        "venue_claim_request",
        "venue_published_profile",
        "venue_published_location",
    ):
        cursor.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
            """,
            [name],
        )
        if not cursor.fetchone():
            return False
    return True


def _insert_auth_user(cursor, *, user_id: str, email: str) -> bool:
    try:
        cursor.execute(
            """
            INSERT INTO auth.users (
                instance_id, id, aud, role, email, encrypted_password,
                email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
                created_at, updated_at
            )
            SELECT
                coalesce((SELECT id FROM auth.instances LIMIT 1), '00000000-0000-0000-0000-000000000000'::uuid),
                %s::uuid, 'authenticated', 'authenticated', %s, '',
                now(), '{}'::jsonb, '{}'::jsonb, now(), now()
            WHERE NOT EXISTS (SELECT 1 FROM auth.users u WHERE u.id = %s::uuid)
            """,
            [user_id, email, user_id],
        )
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("auth.users insert skipped: %s", exc)
        return False
    cursor.execute("SELECT 1 FROM auth.users WHERE id = %s::uuid", [user_id])
    return cursor.fetchone() is not None


def try_install_owner_claim_e2e_fixtures() -> OwnerClaimE2EInstall | None:
    base = try_install_saved_venues_e2e_fixtures()
    if base is None:
        return None
    c = connection.cursor()
    if not _tables_ok(c):
        return None

    if not _insert_auth_user(
        c, user_id=E2E_CLAIM_OWNER_AUTH_USER_ID, email=E2E_CLAIM_OWNER_EMAIL
    ):
        return None

    try:
        c.execute(
            """
            INSERT INTO public.owner_account (auth_user_id)
            VALUES (%s::uuid)
            ON CONFLICT (auth_user_id) DO NOTHING
            """,
            [E2E_CLAIM_OWNER_AUTH_USER_ID],
        )
        c.execute(
            """
            SELECT id::text FROM public.owner_account
            WHERE auth_user_id = %s::uuid
            """,
            [E2E_CLAIM_OWNER_AUTH_USER_ID],
        )
        owner_row = c.fetchone()
        if not owner_row:
            return None
        owner_account_id = str(owner_row[0])

        c.execute(
            """
            SELECT display_name
            FROM public.venue_published_profile
            WHERE venue_id = %s::uuid
            """,
            [E2E_VENUE_ID],
        )
        profile_row = c.fetchone()
        if not profile_row:
            return None
        display_name = str(profile_row[0])
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("owner claim fixture install failed: %s", exc)
        return None

    return OwnerClaimE2EInstall(
        venue_id=E2E_VENUE_ID,
        owner_auth_user_id=E2E_CLAIM_OWNER_AUTH_USER_ID,
        owner_account_id=owner_account_id,
        locality_id=E2E_LOCALITY_ID,
        published_display_name=display_name,
    )
