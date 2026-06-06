"""
E2E fixtures for internal owner claim review API tests.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass

from django.db import DatabaseError, connection

from tests.support.owner_claim_e2e_data import (
    E2E_CLAIM_OWNER_AUTH_USER_ID,
    E2E_CLAIM_OWNER_EMAIL,
    try_install_owner_claim_e2e_fixtures,
)

logger = logging.getLogger(__name__)

E2E_CLAIM_REVIEW_ADMIN_AUTH_USER_ID = "bada0007-0000-4000-8000-0000000000d1"
E2E_CLAIM_REVIEW_ADMIN_EMAIL = "e2e-admin-claim-review@pubplus.test"


@dataclass(frozen=True, slots=True)
class OwnerClaimReviewE2EInstall:
    claim_request_id: str
    stub_venue_id: str
    existing_venue_id: str
    owner_account_id: str
    owner_auth_user_id: str
    business_id: str
    admin_auth_user_id: str
    admin_account_id: str
    locality_id: str
    published_display_name: str


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


def try_install_owner_claim_review_e2e_fixtures() -> OwnerClaimReviewE2EInstall | None:
    base = try_install_owner_claim_e2e_fixtures()
    if base is None:
        return None

    c = connection.cursor()
    if not _insert_auth_user(
        c,
        user_id=E2E_CLAIM_REVIEW_ADMIN_AUTH_USER_ID,
        email=E2E_CLAIM_REVIEW_ADMIN_EMAIL,
    ):
        return None

    try:
        c.execute(
            """
            INSERT INTO public.admin_account (auth_user_id)
            VALUES (%s::uuid)
            ON CONFLICT (auth_user_id) DO NOTHING
            """,
            [E2E_CLAIM_REVIEW_ADMIN_AUTH_USER_ID],
        )
        c.execute(
            """
            SELECT id::text FROM public.admin_account
            WHERE auth_user_id = %s::uuid
            """,
            [E2E_CLAIM_REVIEW_ADMIN_AUTH_USER_ID],
        )
        admin_row = c.fetchone()
        if not admin_row:
            return None
        admin_account_id = str(admin_row[0])

        c.execute(
            """
            INSERT INTO public.business (display_name)
            VALUES ('E2E Claim Review Business')
            RETURNING id::text
            """
        )
        business_id = str(c.fetchone()[0])

        c.execute(
            """
            INSERT INTO public.owner_business_membership (
                owner_account_id, business_id, membership_status, membership_role, activated_at
            ) VALUES (%s::uuid, %s::uuid, 'active', 'org_owner', now())
            """,
            [base.owner_account_id, business_id],
        )

        c.execute("INSERT INTO public.venue DEFAULT VALUES RETURNING id::text")
        stub_venue_id = str(c.fetchone()[0])

        claim_request_id = str(uuid.uuid4())
        summary = json.dumps(
            {
                "mode": "submit_new_or_claim",
                "venue_name": "Submitted Claim Pub",
                "address_line_1": "42 Review Street",
                "locality_id": base.locality_id,
                "claimant_note": "I manage this venue.",
                "possible_duplicate_venue_ids": [base.venue_id],
                "duplicate_candidates": [
                    {
                        "venue_id": base.venue_id,
                        "display_name": base.published_display_name,
                        "match_score": 95,
                        "match_reason": "Exact name match; Same locality",
                    }
                ],
            }
        )
        c.execute(
            """
            INSERT INTO public.venue_claim_request (
                id,
                venue_id,
                business_id,
                initiated_by_owner_account_id,
                claim_lifecycle_status,
                summary
            ) VALUES (
                %s::uuid, %s::uuid, %s::uuid, %s::uuid, 'submitted', %s
            )
            """,
            [
                claim_request_id,
                stub_venue_id,
                business_id,
                base.owner_account_id,
                summary,
            ],
        )
    except DatabaseError as exc:  # noqa: BLE001
        logger.info("owner claim review fixture install failed: %s", exc)
        return None

    return OwnerClaimReviewE2EInstall(
        claim_request_id=claim_request_id,
        stub_venue_id=stub_venue_id,
        existing_venue_id=base.venue_id,
        owner_account_id=base.owner_account_id,
        owner_auth_user_id=E2E_CLAIM_OWNER_AUTH_USER_ID,
        business_id=business_id,
        admin_auth_user_id=E2E_CLAIM_REVIEW_ADMIN_AUTH_USER_ID,
        admin_account_id=admin_account_id,
        locality_id=base.locality_id,
        published_display_name=base.published_display_name,
    )
