from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

from django.db import connection
from django.test import Client, SimpleTestCase, TestCase, override_settings

from common.auth.context import AuthContext
from common.auth.errors import InvalidTokenError

from tests.support.owner_venues_e2e_data import (
    E2E_CAPABILITY_SUBMIT,
    try_install_owner_venues_e2e_fixtures,
)


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


def _core_payload(*, locality_id: str, confirm: bool = True) -> dict:
    return {
        "display_name": "E2E Owner Pub Updated",
        "address_line_1": "99 Owner Test Street",
        "postal_code": "3065",
        "locality_id": locality_id,
        "country_code": "AU",
        "short_description": "Updated neighbourhood pub.",
        "opening_hours": {
            "uncertainty_level": "resolved_confident",
            "regular_hours_json": [
                {
                    "day_of_week": 5,
                    "opens_at": "12:00",
                    "closes_at": "23:00",
                    "crosses_midnight": False,
                }
            ],
            "exceptions_json": [],
            "notes": None,
        },
        "owner_confirms_management": confirm,
    }


@override_settings(SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys")
class OwnerVenueEndpointAuthTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_list_without_token_returns_401(self) -> None:
        r = self.client.get("/api/v1/owner/venues")
        self.assertEqual(r.status_code, 401)

    def test_detail_without_token_returns_401(self) -> None:
        r = self.client.get(f"/api/v1/owner/venues/{uuid4()}")
        self.assertEqual(r.status_code, 401)

    def test_proposals_without_token_returns_401(self) -> None:
        r = self.client.post(
            f"/api/v1/owner/venues/{uuid4()}/proposals",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    @patch("common.auth.guards.get_owner_account_id", return_value=None)
    def test_list_without_owner_account_returns_403(self, _mock_owner) -> None:
        ctx = _ctx(str(uuid4()))
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.get("/api/v1/owner/venues", **_auth_headers())
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"]["code"], "owner_not_provisioned")

    @patch("api.v1.owner.views.admin_account_exists_for_auth", return_value=True)
    @patch("common.auth.guards.get_owner_account_id", return_value=uuid4())
    def test_admin_identity_blocked_on_venue_list(
        self, _mock_owner, _mock_admin
    ) -> None:
        ctx = _ctx(str(uuid4()))
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.get("/api/v1/owner/venues", **_auth_headers())
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"]["code"], "forbidden")

    @patch(
        "api.v1.owner.views.get_owner_venue_detail",
        return_value=(None, "admin_forbidden"),
    )
    @patch("common.auth.guards.get_owner_account_id", return_value=uuid4())
    def test_admin_identity_blocked_on_venue_detail(
        self, _mock_owner, _mock_detail
    ) -> None:
        ctx = _ctx(str(uuid4()))
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{uuid4()}",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"]["code"], "forbidden")

    @patch(
        "api.v1.owner.views.create_or_update_owner_core_details_proposal",
        return_value=(None, "forbidden", None),
    )
    @patch("common.auth.guards.get_owner_account_id", return_value=uuid4())
    def test_unscoped_owner_blocked_on_proposals(
        self, _mock_owner, _mock_proposal
    ) -> None:
        ctx = _ctx(str(uuid4()))
        body = {"section": "core_details", "intent": "draft", "payload": {}}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{uuid4()}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"]["code"], "forbidden")

    @patch(
        "api.v1.owner.views.get_owner_venue_detail",
        return_value=(None, "not_found"),
    )
    @patch("common.auth.guards.get_owner_account_id", return_value=uuid4())
    def test_detail_not_found_for_missing_venue(
        self, _mock_owner, _mock_detail
    ) -> None:
        ctx = _ctx(str(uuid4()))
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{uuid4()}",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["error"]["code"], "not_found")


@override_settings(SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys")
class OwnerVenueEndpointE2ETests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.e2e = try_install_owner_venues_e2e_fixtures()
        if self.e2e is None:
            return
        self.owner_ctx = _ctx(self.e2e.owner_auth_user_id, email="e2e-owner@pubplus.test")
        self.admin_ctx = _ctx(self.e2e.admin_auth_user_id, email="e2e-admin@pubplus.test")

    def _skip_if_no_db(self) -> None:
        if self.e2e is None:
            self.skipTest("PubPlus owner venue schema not available in test database.")

    def test_empty_list_for_owner_without_approved_venue(self) -> None:
        self._skip_if_no_db()
        orphan_id = str(uuid4())
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.owner_account (auth_user_id)
                VALUES (%s::uuid)
                ON CONFLICT (auth_user_id) DO NOTHING
                """,
                [orphan_id],
            )
        ctx = _ctx(orphan_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.get("/api/v1/owner/venues", **_auth_headers())
        self.assertEqual(r.status_code, 200)
        body = r.json()["data"]
        self.assertEqual(body["venues"], [])
        self.assertEqual(body["meta"]["total"], 0)
        self.assertIsNone(body["meta"]["default_venue_id"])

    def test_approved_owner_sees_managed_venue_only(self) -> None:
        self._skip_if_no_db()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get("/api/v1/owner/venues", **_auth_headers())
        self.assertEqual(r.status_code, 200)
        venues = r.json()["data"]["venues"]
        ids = {v["venue_id"] for v in venues}
        self.assertIn(self.e2e.venue_id, ids)
        self.assertNotIn(self.e2e.other_venue_id, ids)
        self.assertEqual(r.json()["data"]["meta"]["default_venue_id"], self.e2e.venue_id)

    def test_admin_without_owner_account_blocked(self) -> None:
        self._skip_if_no_db()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.admin_ctx):
            r = self.client.get("/api/v1/owner/venues", **_auth_headers())
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"]["code"], "owner_not_provisioned")

    def test_detail_forbidden_for_unscoped_venue(self) -> None:
        self._skip_if_no_db()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.other_venue_id}",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"]["code"], "forbidden")

    def test_proposal_forbidden_for_unscoped_venue(self) -> None:
        self._skip_if_no_db()
        body = {
            "section": "core_details",
            "intent": "draft",
            "payload": {},
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.other_venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["error"]["code"], "forbidden")

    def test_detail_includes_published_blocks_and_contact_disabled(self) -> None:
        self._skip_if_no_db()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertIn("published", data)
        self.assertEqual(data["published"]["contact"]["supported"], False)
        self.assertIsNone(data["published"]["contact"]["phone"])
        self.assertTrue(data["sections_available"]["core_details"])
        dumped = json.dumps(data)
        self.assertNotIn("google_place_id", dumped)

    def test_detail_includes_capabilities(self) -> None:
        self._skip_if_no_db()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}",
                **_auth_headers(),
            )
        caps = r.json()["data"]["relationship"]["capabilities"]
        self.assertIn(E2E_CAPABILITY_SUBMIT, caps)

    def test_proposal_rejects_unsupported_section(self) -> None:
        self._skip_if_no_db()
        body = {
            "section": "photos",
            "intent": "draft",
            "payload": {},
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_proposal_rejects_google_place_id(self) -> None:
        self._skip_if_no_db()
        body = {
            "section": "core_details",
            "intent": "draft",
            "payload": {"google_place_id": "ChIJxxxx"},
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("google_place_id", r.json()["error"]["details"])

    def test_proposal_rejects_contact_fields(self) -> None:
        self._skip_if_no_db()
        body = {
            "section": "core_details",
            "intent": "draft",
            "payload": {"phone": "0399999999"},
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("phone", r.json()["error"]["details"])

    def test_draft_saves_staged_proposal_and_staging_rows(self) -> None:
        self._skip_if_no_db()
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM public.venue_change_proposal WHERE venue_id = %s::uuid",
                [self.e2e.venue_id],
            )
        body = {
            "section": "core_details",
            "intent": "draft",
            "payload": _core_payload(locality_id=self.e2e.locality_id, confirm=False),
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 201)
        data = r.json()["data"]
        self.assertEqual(data["lifecycle_status"], "staged")
        self.assertIsNone(data["submitted_at"])
        proposal_id = data["proposal_id"]

        with connection.cursor() as c:
            c.execute(
                """
                SELECT lifecycle_status::text, submitted_at, actor_type, channel
                FROM public.venue_change_proposal WHERE id = %s::uuid
                """,
                [proposal_id],
            )
            row = c.fetchone()
            c.execute(
                "SELECT count(*)::int FROM public.venue_proposal_staging_profile WHERE venue_change_proposal_id = %s::uuid",
                [proposal_id],
            )
            prof = c.fetchone()[0]
            c.execute(
                "SELECT count(*)::int FROM public.venue_proposal_staging_location WHERE venue_change_proposal_id = %s::uuid",
                [proposal_id],
            )
            loc = c.fetchone()[0]
            c.execute(
                "SELECT count(*)::int FROM public.venue_proposal_staging_hours WHERE venue_change_proposal_id = %s::uuid",
                [proposal_id],
            )
            hrs = c.fetchone()[0]
            c.execute(
                "SELECT proposed_display_name FROM public.venue_published_profile WHERE venue_id = %s::uuid",
                [self.e2e.venue_id],
            )
            pub_name = c.fetchone()[0]

        self.assertEqual(row[0], "staged")
        self.assertIsNone(row[1])
        self.assertEqual(row[2], "owner")
        self.assertEqual(row[3], "owner_portal")
        self.assertEqual(prof, 1)
        self.assertEqual(loc, 1)
        self.assertEqual(hrs, 1)
        self.assertEqual(pub_name, "E2E Saved Venues Pub")

    def test_submit_sets_in_review_and_submitted_at(self) -> None:
        self._skip_if_no_db()
        body = {
            "section": "core_details",
            "intent": "submit",
            "payload": _core_payload(locality_id=self.e2e.locality_id),
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 201)
        data = r.json()["data"]
        self.assertEqual(data["lifecycle_status"], "in_review")
        self.assertIsNotNone(data["submitted_at"])

    def test_submit_validates_required_fields(self) -> None:
        self._skip_if_no_db()
        body = {"section": "core_details", "intent": "submit", "payload": {}}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        details = r.json()["error"]["details"]
        self.assertIn("display_name", details)
        self.assertIn("address_line_1", details)
        self.assertIn("locality_id", details)
        self.assertIn("short_description", details)

    def test_submit_validates_locality_exists(self) -> None:
        self._skip_if_no_db()
        payload = _core_payload(locality_id=str(uuid4()))
        body = {"section": "core_details", "intent": "submit", "payload": payload}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("locality_id", r.json()["error"]["details"])

    def test_submit_validates_opening_hours_shape(self) -> None:
        self._skip_if_no_db()
        payload = _core_payload(locality_id=self.e2e.locality_id)
        payload["opening_hours"]["regular_hours_json"][0]["opens_at"] = "25:99"
        body = {"section": "core_details", "intent": "submit", "payload": payload}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        dumped = json.dumps(r.json()["error"]["details"])
        self.assertIn("opens_at", dumped)

    def test_detail_shows_draft_after_save(self) -> None:
        self._skip_if_no_db()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}",
                **_auth_headers(),
            )
        draft = r.json()["data"]["draft"]
        self.assertIsNotNone(draft["proposal_id"])
        self.assertEqual(draft["lifecycle_status"], "staged")

    @patch("apps.owner.services.owner_venue_service.list_owner_venues")
    def test_multiple_venues_no_default(self, mock_list) -> None:
        self._skip_if_no_db()
        mock_list.return_value = {
            "venues": [
                {"venue_id": str(uuid4()), "display_name": "A"},
                {"venue_id": str(uuid4()), "display_name": "B"},
            ],
            "meta": {"total": 2, "default_venue_id": None},
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get("/api/v1/owner/venues", **_auth_headers())
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json()["data"]["meta"]["default_venue_id"])
