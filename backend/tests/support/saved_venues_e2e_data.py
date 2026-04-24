"""
Deterministic data for `test_saved_venues` DB E2E.

Installs, in the *current* DB connection (same transaction as Django's TestCase):

* `geographic_region`, `locality` (one chain)
* `venue`, `venue_published_profile`, `venue_published_location`, `venue_published_map_point`
  so `load_published_venue_read_bundle` can build a `PublicVenueCard`
* `auth.users` (+ `auth.identities` when the schema allows) for a dedicated test subject
  (FK for `public.consumer_account` on save)

Isolated `bada…` UUIDs avoid overlapping dev-seed data (c100…, f111…).

If the DB has no `public.venue` or `auth.users` (wrong engine / empty schema), returns None
so the caller can `skipTest` — without touching a live dev dataset.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.db import DatabaseError, connection

logger = logging.getLogger(__name__)

# Isolated E2E identity — not dev-seed IDs
E2E_AUTH_USER_ID = "bada0001-0000-4000-8000-0000000000ab"
E2E_AUTH_EMAIL = "e2e-saved-venues@pubplus.test"
E2E_VENUE_ID = "bada0001-0000-4000-8000-0000000000aa"
E2E_REGION_ID = "bada0001-0000-4000-8000-0000000000d1"
E2E_LOCALITY_ID = "bada0001-0000-4000-8000-0000000000d2"


@dataclass(frozen=True, slots=True)
class SavedVenuesE2EInstall:
    venue_id: str
    auth_user_id: str


def _schema_prereqs_ok(cursor) -> bool:
    try:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'venue'
            """
        )
        if not cursor.fetchone():
            return False
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'venue_published_profile'
            """
        )
        if not cursor.fetchone():
            return False
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'auth' AND table_name = 'users'
            """
        )
        return bool(cursor.fetchone())
    except DatabaseError:
        return False


def _try_create_pgcrypto() -> None:
    with connection.cursor() as c:
        for stmt in (
            "CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;",
            "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
        ):
            try:
                c.execute(stmt)
            except DatabaseError:  # noqa: BLE001
                pass


def _insert_e2e_identities_if_needed(cursor) -> bool:
    try:
        cursor.execute(
            """
            INSERT INTO auth.identities (
                id, user_id, identity_data, provider, provider_id,
                last_sign_in_at, created_at, updated_at
            )
            SELECT
                gen_random_uuid(),
                %s::uuid,
                jsonb_build_object('sub', %s, 'email', %s),
                'email',
                %s,
                now(), now(), now()
            WHERE NOT EXISTS (
                SELECT 1 FROM auth.identities i
                WHERE i.user_id = %s::uuid AND i.provider = 'email'
            )
            """,
            [
                E2E_AUTH_USER_ID,
                str(E2E_AUTH_USER_ID),
                E2E_AUTH_EMAIL,
                str(E2E_AUTH_USER_ID),
                E2E_AUTH_USER_ID,
            ],
        )
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("auth.identities optional row skipped: %s", exc)
    cursor.execute("SELECT 1 FROM auth.users WHERE id = %s::uuid", [E2E_AUTH_USER_ID])
    return cursor.fetchone() is not None


def _insert_auth_users_with_password_expr(cursor, password_expr: str) -> bool:
    """password_expr is SQL for second column, e.g. "extensions.crypt(%s, extensions.gen_salt('bf'))" """
    try:
        q = f"""
            INSERT INTO auth.users (
                instance_id,
                id,
                aud,
                role,
                email,
                encrypted_password,
                email_confirmed_at,
                raw_app_meta_data,
                raw_user_meta_data,
                created_at,
                updated_at
            )
            SELECT
                coalesce(
                    (SELECT id FROM auth.instances LIMIT 1),
                    '00000000-0000-0000-0000-000000000000'::uuid
                ),
                %s::uuid,
                'authenticated',
                'authenticated',
                %s,
                {password_expr},
                now(),
                jsonb_build_object('provider', 'email', 'providers', jsonb_build_array('email')),
                '{{}}'::jsonb,
                now(),
                now()
            WHERE NOT EXISTS (SELECT 1 FROM auth.users u WHERE u.id = %s::uuid)
        """
        # Three %s: uuid, email, password for crypt(); fourth %s: duplicate check
        cursor.execute(
            q,
            [E2E_AUTH_USER_ID, E2E_AUTH_EMAIL, "e2e-saved-venues-pw", E2E_AUTH_USER_ID],
        )
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("auth.users insert attempt failed: %s", exc)
        return False
    return _insert_e2e_identities_if_needed(cursor)


def _try_insert_e2e_auth_user(cursor) -> bool:
    for password_expr in (
        "extensions.crypt(%s, extensions.gen_salt('bf'))",
        "crypt(%s, gen_salt('bf'))",
    ):
        if _insert_auth_users_with_password_expr(cursor, password_expr):
            return True
    if _try_insert_e2e_auth_user_fallback_no_crypt(cursor):
        return True
    return False


def _try_insert_e2e_auth_user_fallback_no_crypt(cursor) -> bool:
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
            [E2E_AUTH_USER_ID, E2E_AUTH_EMAIL, E2E_AUTH_USER_ID],
        )
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("auth fallback (empty password) failed: %s", exc)
        return False
    return _insert_e2e_identities_if_needed(cursor)


def _insert_minimal_published_venue_chain(cursor) -> bool:
    slug = f"e2e-sv-{E2E_VENUE_ID.replace('-', '')[:20]}"
    try:
        cursor.execute(
            """
            INSERT INTO public.geographic_region (id, parent_region_id, name, region_code, region_level)
            VALUES (%s::uuid, null, 'E2Eland', 'E2E', 'country')
            ON CONFLICT (id) DO NOTHING
            """,
            [E2E_REGION_ID],
        )
        cursor.execute(
            """
            INSERT INTO public.locality (id, geographic_region_id, name, slug)
            VALUES (%s::uuid, %s::uuid, 'E2E Suburb', 'e2e-saved-venues-bada')
            ON CONFLICT (id) DO NOTHING
            """,
            [E2E_LOCALITY_ID, E2E_REGION_ID],
        )
        cursor.execute(
            """
            INSERT INTO public.venue (id) VALUES (%s::uuid)
            ON CONFLICT (id) DO NOTHING
            """,
            [E2E_VENUE_ID],
        )
        cursor.execute(
            """
            INSERT INTO public.venue_published_profile (
                venue_id, display_name, slug, discovery_eligibility_status, operational_status
            )
            VALUES (%s::uuid, 'E2E Saved Venues Pub', %s, 'eligible', 'open')
            ON CONFLICT (venue_id) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                discovery_eligibility_status = EXCLUDED.discovery_eligibility_status
            """,
            [E2E_VENUE_ID, slug],
        )
        cursor.execute(
            """
            INSERT INTO public.venue_published_location (
                venue_id, locality_id, address_line_1, country_code
            )
            VALUES (%s::uuid, %s::uuid, '1 E2E Street', 'AU')
            ON CONFLICT (venue_id) DO UPDATE SET locality_id = EXCLUDED.locality_id
            """,
            [E2E_VENUE_ID, E2E_LOCALITY_ID],
        )
        cursor.execute(
            """
            INSERT INTO public.venue_published_map_point (venue_id, latitude, longitude)
            VALUES (%s::uuid, -33.86, 151.20)
            ON CONFLICT (venue_id) DO UPDATE SET
                latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude
            """,
            [E2E_VENUE_ID],
        )
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("Published venue insert failed: %s", exc)
        return False
    return True


def _bundle_shape_ok(cursor) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM public.venue v
        INNER JOIN public.venue_published_profile vpp ON vpp.venue_id = v.id
        INNER JOIN public.venue_published_location vpl ON vpl.venue_id = v.id
        INNER JOIN public.locality l ON l.id = vpl.locality_id
        INNER JOIN public.venue_published_map_point vpm ON vpm.venue_id = v.id
        WHERE v.id = %s::uuid
          AND vpp.discovery_eligibility_status IN ('eligible', 'limited')
        """,
        [E2E_VENUE_ID],
    )
    return cursor.fetchone() is not None


def try_install_saved_venues_e2e_fixtures() -> SavedVenuesE2EInstall | None:
    """
    When Postgres has PubPlus `public` + `auth` tables, return stable E2E ids.
    All writes happen in the caller's transaction (Django TestCase = rolled back after test).

    Note: Django’s default test database is created with `manage.py migrate` (Django apps only).
    It does *not* apply the Supabase SQL in `database/supabase/migrations/`, so a fresh
    `test_*` database often has no `public.venue` table. In that case this returns `None` and
    the E2E test skips. To exercise the E2E locally, use a test database that already has the
    PubPlus schema (e.g. one-time: apply the project SQL migrations to the test database, or
    create the test database `WITH TEMPLATE` a database that already has those migrations).
    Data inserted here is all under `bada…` ids and is rolled back with the test.
    """
    c = connection.cursor()
    if not _schema_prereqs_ok(c):
        return None

    _try_create_pgcrypto()

    if not _try_insert_e2e_auth_user(c):
        return None
    if not _insert_minimal_published_venue_chain(c):
        return None
    if not _bundle_shape_ok(c):
        return None

    return SavedVenuesE2EInstall(venue_id=E2E_VENUE_ID, auth_user_id=E2E_AUTH_USER_ID)
