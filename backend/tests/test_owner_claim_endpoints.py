from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

from django.db import connection
from django.test import Client, SimpleTestCase, TestCase, override_settings

from common.auth.context import AuthContext
from common.auth.errors import InvalidTokenError

from tests.support.owner_claim_e2e_data import try_install_owner_claim_e2e_fixtures


def _auth_headers() -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": "Bearer test-token"}


def _ctx(subject: str, *, email: str = "owner@example.com") -> AuthContext:
    return AuthContext(
        subject=subject,
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email=email,
        claims={"sub": subject},
    )


@override_settings(SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys")
class OwnerClaimEndpointAuthTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_candidates_without_token_returns_401(self) -> None:
        response = self.client.get("/api/v1/owner/venue-claim-candidates?name=Pub")
        self.assertEqual(response.status_code, 401)

    def test_claim_request_without_token_returns_401(self) -> None:
        response = self.client.post(
            "/api/v1/owner/venue-claim-requests",
            data=json.dumps({"mode": "submit_new", "venue_name": "X"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_candidates_with_invalid_token_returns_401(self) -> None:
        with patch(
            "common.auth.guards.verify_supabase_jwt",
            side_effect=InvalidTokenError("bad token"),
        ):
            response = self.client.get(
                "/api/v1/owner/venue-claim-candidates?name=Pub",
                HTTP_AUTHORIZATION="Bearer invalid",
            )
        self.assertEqual(response.status_code, 401)


@override_settings(SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys")
class OwnerClaimEndpointIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.e2e = try_install_owner_claim_e2e_fixtures()

    def _skip_if_no_schema(self) -> None:
        if self.e2e is None:
            self.skipTest("PubPlus owner claim schema not available in test database.")

    def test_owner_can_search_candidates_without_business_membership(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        ctx = _ctx(self.e2e.owner_auth_user_id, email="e2e-owner-claim@pubplus.test")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            response = self.client.get(
                "/api/v1/owner/venue-claim-candidates",
                {
                    "name": self.e2e.published_display_name,
                    "locality_id": self.e2e.locality_id,
                },
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()["data"]
        self.assertTrue(body["has_good_match"])
        self.assertGreaterEqual(len(body["candidates"]), 1)
        first = body["candidates"][0]
        self.assertEqual(first["venue_id"], self.e2e.venue_id)
        self.assertNotIn("google_place_id", first)

    def test_owner_can_submit_claim_for_existing_venue(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        ctx = _ctx(self.e2e.owner_auth_user_id, email="e2e-owner-claim@pubplus.test")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            response = self.client.post(
                "/api/v1/owner/venue-claim-requests",
                data=json.dumps(
                    {
                        "mode": "claim_existing",
                        "venue_id": self.e2e.venue_id,
                        "claimant_note": "I manage this pub.",
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]
        self.assertEqual(data["status"], "submitted")
        claim_id = data["claim_request_id"]

        with connection.cursor() as c:
            c.execute(
                """
                SELECT claim_lifecycle_status, venue_id::text, resulting_business_venue_management_relationship_id
                FROM public.venue_claim_request
                WHERE id = %s::uuid
                """,
                [claim_id],
            )
            row = c.fetchone()
        self.assertIsNotNone(row)
        status, venue_id, relationship_id = row
        self.assertEqual(status, "submitted")
        self.assertEqual(venue_id, self.e2e.venue_id)
        self.assertIsNone(relationship_id, "claim must not self-approve management access")

    def test_owner_can_submit_new_venue_claim(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        ctx = _ctx(self.e2e.owner_auth_user_id, email="e2e-owner-claim@pubplus.test")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            response = self.client.post(
                "/api/v1/owner/venue-claim-requests",
                data=json.dumps(
                    {
                        "mode": "submit_new",
                        "venue_name": "Brand New Claim Pub",
                        "address_line_1": "12 Claim Street",
                        "locality_id": self.e2e.locality_id,
                        "claimant_note": "Opening soon.",
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 201)
        claim_id = response.json()["data"]["claim_request_id"]
        with connection.cursor() as c:
            c.execute(
                """
                SELECT claim_lifecycle_status, summary, resulting_business_venue_management_relationship_id
                FROM public.venue_claim_request
                WHERE id = %s::uuid
                """,
                [claim_id],
            )
            row = c.fetchone()
        self.assertIsNotNone(row)
        status, summary, relationship_id = row
        self.assertEqual(status, "submitted")
        self.assertIn("Brand New Claim Pub", summary)
        self.assertIsNone(relationship_id)

    def test_duplicate_open_claim_is_handled_safely(self) -> None:
        self._skip_if_no_schema()
        assert self.e2e is not None
        ctx = _ctx(self.e2e.owner_auth_user_id, email="e2e-owner-claim@pubplus.test")
        payload = {
            "mode": "claim_existing",
            "venue_id": self.e2e.venue_id,
            "claimant_note": "First claim.",
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            first = self.client.post(
                "/api/v1/owner/venue-claim-requests",
                data=json.dumps(payload),
                content_type="application/json",
                **_auth_headers(),
            )
            second = self.client.post(
                "/api/v1/owner/venue-claim-requests",
                data=json.dumps(payload),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            first.json()["data"]["claim_request_id"],
            second.json()["data"]["claim_request_id"],
        )

    @patch("common.auth.guards.get_owner_account_id", return_value=None)
    def test_unprovisioned_owner_subject_rejected(self, _mock_owner_id) -> None:
        ctx = _ctx(str(uuid4()))
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            response = self.client.get(
                "/api/v1/owner/venue-claim-candidates?name=Pub",
                **_auth_headers(),
            )
        self.assertEqual(response.status_code, 403)
