from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

from django.db import connection, transaction
from django.test import TestCase, override_settings
from django.test.client import Client

from common.auth.context import AuthContext
from common.auth.errors import InvalidTokenError

from tests.support.saved_venues_e2e_data import (
    E2E_AUTH_USER_ID,
    try_install_saved_venues_e2e_fixtures,
)


def _auth_headers():
    return {"HTTP_AUTHORIZATION": "Bearer test-token"}


def _make_context_for_auth_subject(subj: str) -> AuthContext:
    return AuthContext(
        subject=subj,
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="e2e-saved-venues@pubplus.test",
        claims={"sub": subj},
    )


@override_settings(
    SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys"
)
class SavedVenuesApiTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.csrf_client = Client(enforce_csrf_checks=True)

    @staticmethod
    def _clear_e2e_default_saved_state():
        with connection.cursor() as c:
            c.execute(
                """
                DELETE FROM public.saved_list_membership
                WHERE saved_list_id IN (
                    SELECT s.id
                    FROM public.saved_list s
                    INNER JOIN public.consumer_account ca ON ca.id = s.consumer_account_id
                    WHERE ca.auth_user_id = %s::uuid
                      AND s.name = 'Saved'
                      AND s.is_archived = false
                )
                """,
                [E2E_AUTH_USER_ID],
            )

    def test_unauthenticated_returns_401(self) -> None:
        self.assertEqual(self.client.get("/api/v1/saved/venues").status_code, 401)
        r_post = self.client.post(
            "/api/v1/saved/venues",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(r_post.status_code, 401)
        self.assertEqual(
            self.client.delete(f"/api/v1/saved/venues/{uuid4()}").status_code, 401
        )

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_make_context_for_auth_subject(E2E_AUTH_USER_ID))
    @patch("apps.saved.services.saved_venues_service.venue_row_exists", return_value=False)
    def test_post_rejects_malformed_json_and_invalid_venue_id(
        self, _venue_exists: object, _mock_jwt: object
    ) -> None:
        r = self.client.post(
            "/api/v1/saved/venues", data="not json", content_type="application/json", **_auth_headers()
        )
        self.assertEqual(r.status_code, 400)
        r2 = self.client.post(
            "/api/v1/saved/venues",
            data=json.dumps({}),
            content_type="application/json",
            **_auth_headers(),
        )
        self.assertEqual(r2.status_code, 400)
        r3 = self.client.post(
            "/api/v1/saved/venues",
            data=json.dumps({"venue_id": "not-a-uuid"}),
            content_type="application/json",
            **_auth_headers(),
        )
        self.assertEqual(r3.status_code, 400)
        r4 = self.client.post(
            "/api/v1/saved/venues",
            data=json.dumps({"venue_id": str(uuid4())}),
            content_type="application/json",
            **_auth_headers(),
        )
        self.assertEqual(r4.status_code, 404)
        self.assertEqual(r4.json()["error"]["code"], "venue_not_found")

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_make_context_for_auth_subject(E2E_AUTH_USER_ID))
    @patch("apps.saved.services.saved_venues_service.venue_row_exists", return_value=False)
    def test_post_with_bearer_token_does_not_require_csrf(
        self, _venue_exists: object, _mock_jwt: object
    ) -> None:
        response = self.csrf_client.post(
            "/api/v1/saved/venues",
            data=json.dumps({"venue_id": str(uuid4())}),
            content_type="application/json",
            **_auth_headers(),
        )
        self.assertNotEqual(response.status_code, 403, response.content)

    @patch(
        "common.auth.guards.verify_supabase_jwt",
        side_effect=InvalidTokenError("token invalid"),
    )
    def test_post_invalid_token_still_returns_401_without_csrf_requirement(
        self, _mock_jwt: object
    ) -> None:
        response = self.csrf_client.post(
            "/api/v1/saved/venues",
            data=json.dumps({"venue_id": str(uuid4())}),
            content_type="application/json",
            **_auth_headers(),
        )
        self.assertEqual(response.status_code, 401)

    def test_db_backed_idempotent_save_unsave_and_list(self) -> None:
        e2e = try_install_saved_venues_e2e_fixtures()
        if e2e is None:
            self.skipTest(
                "E2E fixtures skipped: database missing public.venue/auth schema "
                "(e.g. non-Postgres or no PubPlus migrations)."
            )

        with transaction.atomic():
            self._clear_e2e_default_saved_state()

        venue_id = e2e.venue_id
        ctx = _make_context_for_auth_subject(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            p1 = self.client.post(
                "/api/v1/saved/venues",
                data=json.dumps({"venue_id": venue_id}),
                content_type="application/json",
                **_auth_headers(),
            )
            self.assertEqual(p1.status_code, 200, p1.content)
            self.assertTrue(p1.json()["data"]["saved"])
            self.assertEqual(p1.json()["data"]["venue_id"], venue_id)

            p2 = self.client.post(
                "/api/v1/saved/venues",
                data=json.dumps({"venue_id": venue_id}),
                content_type="application/json",
                **_auth_headers(),
            )
            self.assertEqual(p2.status_code, 200, "repeat save must be idempotent")

        with connection.cursor() as c:
            c.execute(
                """
                SELECT 1
                FROM public.saved_list_membership m
                INNER JOIN public.saved_list s ON s.id = m.saved_list_id
                INNER JOIN public.consumer_account ca ON ca.id = s.consumer_account_id
                WHERE m.venue_id = %s::uuid
                  AND ca.auth_user_id = %s::uuid
                  AND s.name = 'Saved'
                """,
                [venue_id, e2e.auth_user_id],
            )
            self.assertIsNotNone(c.fetchone(), "DB must contain default-list membership after save")

        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            g1 = self.client.get("/api/v1/saved/venues", **_auth_headers())
        self.assertEqual(g1.status_code, 200, g1.content)
        body = g1.json()["data"]["venues"]
        self.assertGreater(len(body), 0)
        self.assertIn("open_now", body[0])
        ids = [v["id"] for v in body]
        self.assertIn(venue_id, ids, "GET must return saved card for this consumer only")

        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            d1 = self.client.delete(f"/api/v1/saved/venues/{venue_id}", **_auth_headers())
        self.assertEqual(d1.status_code, 204, d1.content)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            d2 = self.client.delete(f"/api/v1/saved/venues/{venue_id}", **_auth_headers())
        self.assertEqual(d2.status_code, 204, "repeat unsave idempotent")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            g2 = self.client.get("/api/v1/saved/venues", **_auth_headers())
        self.assertNotIn(venue_id, [v["id"] for v in g2.json()["data"]["venues"]])
