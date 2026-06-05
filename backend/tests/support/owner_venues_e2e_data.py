"""
E2E fixtures for owner venue Phase A API tests.
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

E2E_OWNER_AUTH_USER_ID = "bada0002-0000-4000-8000-0000000000ac"
E2E_OWNER_EMAIL = "e2e-owner-venues@pubplus.test"
E2E_ADMIN_AUTH_USER_ID = "bada0003-0000-4000-8000-0000000000ad"
E2E_ADMIN_EMAIL = "e2e-admin-no-owner@pubplus.test"
E2E_BUSINESS_ID = "bada0004-0000-4000-8000-0000000000b1"
E2E_OTHER_VENUE_ID = "bada0005-0000-4000-8000-0000000000b2"
E2E_CAPABILITY_SUBMIT = "submit_restricted_changes_for_review"


@dataclass(frozen=True, slots=True)
class OwnerVenuesE2EInstall:
    venue_id: str
    other_venue_id: str
    owner_auth_user_id: str
    admin_auth_user_id: str
    owner_account_id: str
    locality_id: str


def _owner_tables_ok(cursor) -> bool:
    for name in (
        "owner_account",
        "owner_business_membership",
        "business",
        "business_venue_management_relationship",
        "venue_change_proposal",
        "venue_proposal_staging_profile",
        "venue_proposal_staging_location",
        "venue_proposal_staging_hours",
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


def try_install_owner_venues_e2e_fixtures() -> OwnerVenuesE2EInstall | None:
    base = try_install_saved_venues_e2e_fixtures()
    if base is None:
        return None
    c = connection.cursor()
    if not _owner_tables_ok(c):
        return None

    if not _insert_auth_user(
        c, user_id=E2E_OWNER_AUTH_USER_ID, email=E2E_OWNER_EMAIL
    ):
        return None
    if not _insert_auth_user(
        c, user_id=E2E_ADMIN_AUTH_USER_ID, email=E2E_ADMIN_EMAIL
    ):
        return None

    try:
        c.execute(
            """
            INSERT INTO public.owner_account (auth_user_id)
            VALUES (%s::uuid)
            ON CONFLICT (auth_user_id) DO NOTHING
            """,
            [E2E_OWNER_AUTH_USER_ID],
        )
        c.execute(
            """
            SELECT id::text FROM public.owner_account
            WHERE auth_user_id = %s::uuid
            """,
            [E2E_OWNER_AUTH_USER_ID],
        )
        owner_row = c.fetchone()
        if not owner_row:
            return None
        owner_account_id = owner_row[0]

        c.execute(
            """
            INSERT INTO public.admin_account (auth_user_id)
            VALUES (%s::uuid)
            ON CONFLICT (auth_user_id) DO NOTHING
            """,
            [E2E_ADMIN_AUTH_USER_ID],
        )

        c.execute(
            """
            INSERT INTO public.business (id, display_name)
            VALUES (%s::uuid, 'E2E Owner Business')
            ON CONFLICT (id) DO NOTHING
            """,
            [E2E_BUSINESS_ID],
        )
        c.execute(
            """
            INSERT INTO public.owner_business_membership (
                owner_account_id, business_id, membership_status, membership_role, activated_at
            )
            VALUES (%s::uuid, %s::uuid, 'active', 'org_owner', now())
            ON CONFLICT (owner_account_id, business_id) DO UPDATE SET
                membership_status = 'active'
            """,
            [owner_account_id, E2E_BUSINESS_ID],
        )
        c.execute(
            """
            INSERT INTO public.business_venue_management_relationship (
                business_id, venue_id, relationship_lifecycle
            )
            VALUES (%s::uuid, %s::uuid, 'approved')
            ON CONFLICT (business_id, venue_id) DO UPDATE SET
                relationship_lifecycle = 'approved'
            RETURNING id::text
            """,
            [E2E_BUSINESS_ID, E2E_VENUE_ID],
        )
        rel_row = c.fetchone()
        if not rel_row:
            return None
        rel_id = rel_row[0]

        c.execute(
            """
            INSERT INTO public.venue_capability_grant (
                business_venue_management_relationship_id,
                owner_account_id,
                capability_code,
                grant_status
            )
            VALUES (%s::uuid, %s::uuid, %s, 'active')
            ON CONFLICT (
                business_venue_management_relationship_id,
                owner_account_id,
                capability_code
            ) DO NOTHING
            """,
            [rel_id, owner_account_id, E2E_CAPABILITY_SUBMIT],
        )

        c.execute(
            """
            INSERT INTO public.venue (id) VALUES (%s::uuid)
            ON CONFLICT (id) DO NOTHING
            """,
            [E2E_OTHER_VENUE_ID],
        )

        c.execute(
            """
            INSERT INTO public.venue_published_descriptive_copy (
                venue_id, short_description
            )
            VALUES (%s::uuid, 'E2E short description for owner detail.')
            ON CONFLICT (venue_id) DO UPDATE SET
                short_description = EXCLUDED.short_description
            """,
            [E2E_VENUE_ID],
        )
        c.execute(
            """
            INSERT INTO public.venue_hours_regular (
                venue_id, day_of_week, opens_at, closes_at, crosses_midnight, sort_order
            )
            SELECT %s::uuid, 5, '12:00'::time, '23:00'::time, false, 0
            WHERE NOT EXISTS (
                SELECT 1 FROM public.venue_hours_regular
                WHERE venue_id = %s::uuid AND day_of_week = 5
            )
            """,
            [E2E_VENUE_ID, E2E_VENUE_ID],
        )
        c.execute(
            """
            INSERT INTO public.venue_hours_uncertainty (venue_id, uncertainty_level)
            VALUES (%s::uuid, 'resolved_confident')
            ON CONFLICT (venue_id) DO NOTHING
            """,
            [E2E_VENUE_ID],
        )
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("owner venues e2e install failed: %s", exc)
        return None

    return OwnerVenuesE2EInstall(
        venue_id=E2E_VENUE_ID,
        other_venue_id=E2E_OTHER_VENUE_ID,
        owner_auth_user_id=E2E_OWNER_AUTH_USER_ID,
        admin_auth_user_id=E2E_ADMIN_AUTH_USER_ID,
        owner_account_id=owner_account_id,
        locality_id=E2E_LOCALITY_ID,
    )
