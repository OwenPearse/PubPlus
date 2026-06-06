from __future__ import annotations

import json
from unittest.mock import patch

from django.db import connection
from django.test import Client, SimpleTestCase, TestCase

from common.auth.context import AuthContext

from tests.support.owner_claim_review_e2e_data import (
    try_install_owner_claim_review_e2e_fixtures,
)


def _auth_headers() -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": "Bearer internal-token"}


def _internal_ctx(subject: str) -> AuthContext:
    return AuthContext(
        subject=subject,
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="operator@example.com",
        claims={"sub": subject, "pubplus_internal_admin": True},
    )


def _owner_ctx(subject: str) -> AuthContext:
    return AuthContext(
        subject=subject,
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="owner@example.com",
        claims={"sub": subject},
    )


class InternalOwnerClaimReviewAuthTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_list_requires_auth(self) -> None:
        response = self.client.get("/api/v1/internal/owner-claims/")
        self.assertEqual(response.status_code, 401)

    def test_non_admin_cannot_list_claims(self) -> None:
        with patch(
            "common.auth.guards.verify_supabase_jwt",
            return_value=_owner_ctx("owner-sub-1"),
        ):
            response = self.client.get(
                "/api/v1/internal/owner-claims/",
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 403)


def _create_submitted_claim(e2e) -> str:
    claim_request_id = "cccc0001-0001-4001-8001-000000000001"
    with connection.cursor() as c:
        c.execute("INSERT INTO public.venue DEFAULT VALUES RETURNING id::text")
        stub_venue_id = str(c.fetchone()[0])
        summary = json.dumps(
            {
                "mode": "submit_new_or_claim",
                "venue_name": "Another Claim Pub",
                "address_line_1": "9 Test Street",
                "locality_id": e2e.locality_id,
                "claimant_note": "Please review.",
                "possible_duplicate_venue_ids": [e2e.existing_venue_id],
                "duplicate_candidates": [
                    {
                        "venue_id": e2e.existing_venue_id,
                        "display_name": e2e.published_display_name,
                        "match_score": 90,
                        "match_reason": "Similar name",
                    }
                ],
            }
        )
        c.execute(
            """
            INSERT INTO public.venue_claim_request (
                id, venue_id, business_id, initiated_by_owner_account_id,
                claim_lifecycle_status, summary
            ) VALUES (
                %s::uuid, %s::uuid, %s::uuid, %s::uuid, 'submitted', %s
            )
            ON CONFLICT (id) DO UPDATE SET
                claim_lifecycle_status = 'submitted',
                resulting_business_venue_management_relationship_id = NULL,
                summary = EXCLUDED.summary,
                updated_at = now()
            """,
            [
                claim_request_id,
                stub_venue_id,
                e2e.business_id,
                e2e.owner_account_id,
                summary,
            ],
        )
    return claim_request_id


class InternalOwnerClaimReviewEndpointTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.e2e = try_install_owner_claim_review_e2e_fixtures()

    def _skip_if_no_schema(self) -> None:
        if self.e2e is None:
            self.skipTest("PubPlus owner claim review schema not available in test database.")

    def test_admin_can_list_submitted_claims(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        with patch(
            "common.auth.guards.verify_supabase_jwt",
            return_value=_internal_ctx(self.e2e.admin_auth_user_id),
        ):
            response = self.client.get(
                "/api/v1/internal/owner-claims/",
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 200)
        items = response.json()["data"]["items"]
        self.assertTrue(
            any(item["claim_request_id"] == self.e2e.claim_request_id for item in items)
        )

    def test_detail_includes_duplicate_candidates_from_summary(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        with patch(
            "common.auth.guards.verify_supabase_jwt",
            return_value=_internal_ctx(self.e2e.admin_auth_user_id),
        ):
            response = self.client.get(
                f"/api/v1/internal/owner-claims/{self.e2e.claim_request_id}",
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["submitted"]["venue_name"], "Submitted Claim Pub")
        self.assertGreaterEqual(len(data["duplicate_candidates"]), 1)
        self.assertEqual(
            data["duplicate_candidates"][0]["venue_id"],
            self.e2e.existing_venue_id,
        )
        self.assertNotIn("google_place_id", json.dumps(data))

    def test_approve_existing_creates_relationship_grants_and_audit(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        claim_id = _create_submitted_claim(self.e2e)
        with patch(
            "common.auth.guards.verify_supabase_jwt",
            return_value=_internal_ctx(self.e2e.admin_auth_user_id),
        ):
            response = self.client.post(
                f"/api/v1/internal/owner-claims/{claim_id}/approve-existing",
                data=json.dumps(
                    {
                        "venue_id": self.e2e.existing_venue_id,
                        "admin_note": "Verified licensee.",
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()["data"]
        self.assertEqual(result["status"], "closed")
        relationship_id = result["relationship_id"]

        with connection.cursor() as c:
            c.execute(
                """
                SELECT claim_lifecycle_status,
                       resulting_business_venue_management_relationship_id::text
                FROM public.venue_claim_request
                WHERE id = %s::uuid
                """,
                [claim_id],
            )
            claim_row = c.fetchone()
            c.execute(
                """
                SELECT relationship_lifecycle
                FROM public.business_venue_management_relationship
                WHERE id = %s::uuid
                """,
                [relationship_id],
            )
            rel_row = c.fetchone()
            c.execute(
                """
                SELECT capability_code
                FROM public.venue_capability_grant
                WHERE business_venue_management_relationship_id = %s::uuid
                  AND owner_account_id = %s::uuid
                  AND grant_status = 'active'
                ORDER BY capability_code
                """,
                [relationship_id, self.e2e.owner_account_id],
            )
            grants = [row[0] for row in c.fetchall()]
            c.execute(
                """
                SELECT 1
                FROM public.venue_authority_decision
                WHERE venue_claim_request_id = %s::uuid
                  AND decision_outcome = 'approved_existing'
                """,
                [claim_id],
            )
            decision_row = c.fetchone()
            c.execute(
                """
                SELECT 1
                FROM public.audit_event
                WHERE entity_table = 'venue_claim_request'
                  AND entity_id = %s::uuid
                  AND action = 'claim_review_decision'
                """,
                [claim_id],
            )
            audit_row = c.fetchone()

        self.assertEqual(claim_row[0], "closed")
        self.assertEqual(claim_row[1], relationship_id)
        self.assertEqual(rel_row[0], "approved")
        self.assertEqual(
            grants,
            [
                "manage_published_venue_operations",
                "submit_restricted_changes_for_review",
            ],
        )
        self.assertIsNotNone(decision_row)
        self.assertIsNotNone(audit_row)

    def test_reject_updates_status_and_writes_audit(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        claim_id = _create_submitted_claim(self.e2e)
        with patch(
            "common.auth.guards.verify_supabase_jwt",
            return_value=_internal_ctx(self.e2e.admin_auth_user_id),
        ):
            response = self.client.post(
                f"/api/v1/internal/owner-claims/{claim_id}/reject",
                data=json.dumps({"admin_note": "Insufficient proof."}),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["data"]["status"], "denied")

        with connection.cursor() as c:
            c.execute(
                """
                SELECT claim_lifecycle_status,
                       resulting_business_venue_management_relationship_id
                FROM public.venue_claim_request
                WHERE id = %s::uuid
                """,
                [claim_id],
            )
            claim_row = c.fetchone()
            c.execute(
                """
                SELECT 1
                FROM public.venue_authority_decision
                WHERE venue_claim_request_id = %s::uuid
                  AND decision_outcome = 'rejected'
                """,
                [claim_id],
            )
            decision_row = c.fetchone()

        self.assertEqual(claim_row[0], "denied")
        self.assertIsNone(claim_row[1])
        self.assertIsNotNone(decision_row)

    def test_owner_does_not_gain_access_before_approval(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        with connection.cursor() as c:
            c.execute(
                """
                SELECT COUNT(*)
                FROM public.business_venue_management_relationship bvm
                INNER JOIN public.venue_capability_grant vcg
                    ON vcg.business_venue_management_relationship_id = bvm.id
                WHERE bvm.business_id = %s::uuid
                  AND vcg.owner_account_id = %s::uuid
                  AND bvm.relationship_lifecycle = 'approved'
                  AND vcg.grant_status = 'active'
                """,
                [self.e2e.business_id, self.e2e.owner_account_id],
            )
            before = c.fetchone()[0]
        self.assertEqual(before, 0)
