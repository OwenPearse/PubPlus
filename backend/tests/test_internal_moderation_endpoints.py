from __future__ import annotations

from unittest.mock import patch

from django.db import connection
from django.test import Client, SimpleTestCase, TestCase

from apps.submissions.services import submission_intake_service
from common.auth.context import AuthContext
from tests.support.submissions_e2e_data import (
    get_latest_proposal_id_for_venue,
    try_install_submissions_e2e_fixtures,
)


def _consumer_ctx(auth_user_id: str) -> AuthContext:
    return AuthContext(
        subject=auth_user_id,
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="consumer@example.com",
        claims={"sub": auth_user_id},
    )


def _internal_ctx() -> AuthContext:
    return AuthContext(
        subject="operator-sub-1",
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="operator@example.com",
        claims={"sub": "operator-sub-1", "pubplus_internal_admin": True},
    )


class InternalModerationAuthTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_internal_queue_requires_auth(self) -> None:
        r = self.client.get("/api/v1/internal/moderation/queue")
        self.assertEqual(r.status_code, 401)

    def test_internal_detail_requires_auth(self) -> None:
        r = self.client.get(
            "/api/v1/internal/moderation/items/00000000-0000-4000-8000-000000000000"
        )
        self.assertEqual(r.status_code, 401)

    def test_internal_venue_requires_auth(self) -> None:
        r = self.client.get(
            "/api/v1/internal/venues/00000000-0000-4000-8000-000000000000"
        )
        self.assertEqual(r.status_code, 401)

    def test_consumer_auth_is_rejected_for_internal_endpoints(self) -> None:
        ctx = AuthContext(
            subject="consumer-user-1",
            audience="authenticated",
            issuer="https://example.supabase.co/auth/v1",
            role="authenticated",
            email="consumer@example.com",
            claims={"sub": "consumer-user-1"},
        )
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            q = self.client.get(
                "/api/v1/internal/moderation/queue",
                HTTP_AUTHORIZATION="Bearer consumer-token",
            )
            d = self.client.get(
                "/api/v1/internal/moderation/items/00000000-0000-4000-8000-000000000000",
                HTTP_AUTHORIZATION="Bearer consumer-token",
            )
            v = self.client.get(
                "/api/v1/internal/venues/00000000-0000-4000-8000-000000000000",
                HTTP_AUTHORIZATION="Bearer consumer-token",
            )
        self.assertEqual(q.status_code, 403)
        self.assertEqual(d.status_code, 403)
        self.assertEqual(v.status_code, 403)


class InternalModerationReadEndpointTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.e2e = try_install_submissions_e2e_fixtures()
        if self.e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")

    def _auth_headers(self) -> dict[str, str]:
        return {"HTTP_AUTHORIZATION": "Bearer internal-token"}

    def _create_profile_proposal(self) -> str:
        result, code, _ = submission_intake_service.submit_consumer_correction(
            _consumer_ctx(self.e2e.auth_user_id),
            {
                "venue_id": self.e2e.venue_id,
                "domain": "profile",
                "proposed_values": {"display_name": "Queue Profile Proposal"},
            },
        )
        self.assertEqual(code, "ok", result)
        pid = get_latest_proposal_id_for_venue(self.e2e.venue_id)
        self.assertIsNotNone(pid)
        return str(pid)

    def _create_location_proposal(self) -> str:
        result, code, _ = submission_intake_service.submit_consumer_correction(
            _consumer_ctx(self.e2e.auth_user_id),
            {
                "venue_id": self.e2e.venue_id,
                "domain": "location",
                "proposed_values": {"address_line_1": "123 Queue Street"},
            },
        )
        self.assertEqual(code, "ok", result)
        pid = get_latest_proposal_id_for_venue(self.e2e.venue_id)
        self.assertIsNotNone(pid)
        return str(pid)

    def test_queue_invalid_filters_return_400(self) -> None:
        with patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx()):
            r = self.client.get(
                "/api/v1/internal/moderation/queue",
                {"status": "not_a_status"},
                **self._auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_queue_filters_by_status_domain_and_venue(self) -> None:
        rejected_id = self._create_profile_proposal()
        _ = self._create_location_proposal()
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE public.venue_change_proposal
                SET lifecycle_status = 'rejected', closed_at = now()
                WHERE id = %s::uuid
                """,
                [rejected_id],
            )

        with patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx()):
            by_status = self.client.get(
                "/api/v1/internal/moderation/queue",
                {"status": "rejected"},
                **self._auth_headers(),
            )
            by_domain = self.client.get(
                "/api/v1/internal/moderation/queue",
                {"domain": "location"},
                **self._auth_headers(),
            )
            by_venue = self.client.get(
                "/api/v1/internal/moderation/queue",
                {"venue_id": self.e2e.venue_id},
                **self._auth_headers(),
            )

        self.assertEqual(by_status.status_code, 200, by_status.content)
        self.assertTrue(
            all(i["status"] == "rejected" for i in by_status.json()["items"])
        )
        self.assertEqual(by_domain.status_code, 200, by_domain.content)
        self.assertTrue(
            any("geo" in i["domain_tags"] for i in by_domain.json()["items"])
        )
        self.assertEqual(by_venue.status_code, 200, by_venue.content)
        self.assertTrue(
            all(i["venue_id"] == self.e2e.venue_id for i in by_venue.json()["items"])
        )

    def test_detail_unknown_item_returns_404(self) -> None:
        with patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx()):
            r = self.client.get(
                "/api/v1/internal/moderation/items/00000000-0000-4000-8000-000000000000",
                **self._auth_headers(),
            )
        self.assertEqual(r.status_code, 404)

    def test_internal_venue_lookup_404_for_unknown_venue(self) -> None:
        with patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx()):
            r = self.client.get(
                "/api/v1/internal/venues/00000000-0000-4000-8000-000000000000",
                **self._auth_headers(),
            )
        self.assertEqual(r.status_code, 404)

    def test_internal_venue_lookup_returns_shell_fallback(self) -> None:
        body = {
            "name": "Shell Venue",
            "address_line_1": "1 Shell Street",
            "locality_id": self.e2e.locality_id,
        }
        result, code, _ = submission_intake_service.submit_new_venue_suggestion(
            _consumer_ctx(self.e2e.auth_user_id),
            body,
        )
        self.assertEqual(code, "ok", result)

        with connection.cursor() as c:
            c.execute(
                """
                SELECT p.venue_id::text
                FROM public.venue_change_proposal p
                WHERE p.proposal_kind = 'whole_record'
                  AND p.channel = 'app_consumer'
                ORDER BY p.created_at DESC
                LIMIT 1
                """
            )
            row = c.fetchone()
        self.assertIsNotNone(row)
        shell_venue_id = str(row[0])

        with patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx()):
            r = self.client.get(
                f"/api/v1/internal/venues/{shell_venue_id}",
                **self._auth_headers(),
            )
        self.assertEqual(r.status_code, 200, r.content)
        payload = r.json()
        self.assertEqual(payload["venue_id"], shell_venue_id)
        self.assertIsNone(payload["published"])
        self.assertIsNotNone(payload["shell_fallback"])
        self.assertGreaterEqual(
            payload["workflow_summary"]["open_proposal_count"],
            1,
        )
