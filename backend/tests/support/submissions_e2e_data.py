"""
DB fixture helpers for submission intake E2E tests.

Builds on `saved_venues_e2e_data` and requires workflow tables from PubPlus SQL migrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from django.db import DatabaseError, connection

from tests.support.saved_venues_e2e_data import (
    E2E_LOCALITY_ID,
    E2E_REGION_ID,
    try_install_saved_venues_e2e_fixtures,
)

logger = getLogger(__name__)

# Isolated E2E attribute definition (boolean shape)
E2E_ATTR_DEF_ID = "bada0001-0000-4000-8000-00000000e1a1"


@dataclass(frozen=True, slots=True)
class SubmissionsE2EInstall:
    venue_id: str
    auth_user_id: str
    attribute_definition_id: str
    region_id: str
    locality_id: str


def _workflow_tables_ok(cursor) -> bool:
    try:
        for name in (
            "venue_change_proposal",
            "venue_proposal_target",
            "venue_proposal_staging_profile",
            "venue_proposal_staging_location",
            "venue_proposal_staging_attribute",
            "venue_proposal_staging_hours",
        ):
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
                """,
                [name],
            )
            if not cursor.fetchone():
                return False
        return True
    except DatabaseError:
        return False


def try_install_submissions_e2e_fixtures() -> SubmissionsE2EInstall | None:
    base = try_install_saved_venues_e2e_fixtures()
    if base is None:
        return None
    c = connection.cursor()
    if not _workflow_tables_ok(c):
        return None
    try:
        c.execute(
            """
            INSERT INTO public.venue_attribute_definition (
                id, stable_key, display_label, value_shape, cardinality, is_discovery_driving
            ) VALUES (
                %s::uuid, 'e2e_bada_attr', 'E2E bool', 'boolean', 'single', true
            ) ON CONFLICT (stable_key) DO NOTHING
            """,
            [E2E_ATTR_DEF_ID],
        )
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("venue_attribute_definition e2e insert skipped: %s", exc)
    try:
        c.execute(
            "SELECT 1 FROM public.venue_attribute_definition WHERE id = %s::uuid",
            [E2E_ATTR_DEF_ID],
        )
        if not c.fetchone():
            return None
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("attribute definition check failed: %s", exc)
        return None
    c.execute("SELECT id FROM public.geographic_region WHERE id = %s::uuid", [E2E_REGION_ID])
    r = c.fetchone()
    c.execute("SELECT id FROM public.locality WHERE id = %s::uuid", [E2E_LOCALITY_ID])
    l = c.fetchone()
    if not r or not l:
        return None
    return SubmissionsE2EInstall(
        venue_id=base.venue_id,
        auth_user_id=base.auth_user_id,
        attribute_definition_id=E2E_ATTR_DEF_ID,
        region_id=str(r[0]),
        locality_id=str(l[0]),
    )


def count_proposals_for_venue(venue_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            "SELECT count(*)::int FROM public.venue_change_proposal WHERE venue_id = %s::uuid",
            [venue_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


def get_latest_proposal_id_for_venue(venue_id: str) -> str | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT id::text
            FROM public.venue_change_proposal
            WHERE venue_id = %s::uuid
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [venue_id],
        )
        row = c.fetchone()
    return str(row[0]) if row else None
