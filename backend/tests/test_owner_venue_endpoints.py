from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

from django.db import connection
from django.test import Client, SimpleTestCase, TestCase, override_settings

from common.auth.context import AuthContext
from common.auth.errors import InvalidTokenError

from tests.support.owner_venues_e2e_data import (
    E2E_CAPABILITY_DIRECT_EDIT,
    E2E_CAPABILITY_SUBMIT,
    E2E_MVP_BEER_GARDEN_ATTR_ID,
    E2E_MVP_DOG_FRIENDLY_ATTR_ID,
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
        "address_line_2": "Suite 2",
        "postal_code": "3065",
        "locality_id": locality_id,
        "country_code": "AU",
        "short_description": "Updated neighbourhood pub.",
        "long_description": "A longer draft description for hydration tests.",
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
            "notes": "Draft hours notes for QA.",
        },
        "owner_confirms_management": confirm,
    }


def _count_owner_direct_edit_audits(venue_id: str, owner_account_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.audit_event
            WHERE actor_type = 'owner'
              AND actor_owner_account_id = %s::uuid
              AND entity_id = %s::uuid
              AND action = 'owner_direct_edit'
            """,
            [owner_account_id, venue_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


def _revoke_owner_capability(
    venue_id: str, owner_account_id: str, capability_code: str
) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            UPDATE public.venue_capability_grant vcg
            SET grant_status = 'revoked', revoked_at = now(), updated_at = now()
            FROM public.business_venue_management_relationship bvmr
            WHERE vcg.business_venue_management_relationship_id = bvmr.id
              AND bvmr.venue_id = %s::uuid
              AND vcg.owner_account_id = %s::uuid
              AND vcg.capability_code = %s
            """,
            [venue_id, owner_account_id, capability_code],
        )


def _restore_owner_capability(
    relationship_id: str, owner_account_id: str, capability_code: str
) -> None:
    with connection.cursor() as c:
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
            ) DO UPDATE SET
                grant_status = 'active',
                revoked_at = NULL,
                updated_at = now()
            """,
            [relationship_id, owner_account_id, capability_code],
        )


def _count_in_review_proposals(venue_id: str, owner_account_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.venue_change_proposal
            WHERE venue_id = %s::uuid
              AND actor_owner_account_id = %s::uuid
              AND actor_type = 'owner'
              AND channel = 'owner_portal'
              AND lifecycle_status = 'in_review'
            """,
            [venue_id, owner_account_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


def _count_staging_attribute_rows(venue_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.venue_proposal_staging_attribute sa
            INNER JOIN public.venue_change_proposal p
              ON p.id = sa.venue_change_proposal_id
            WHERE p.venue_id = %s::uuid
              AND p.actor_type = 'owner'
              AND p.channel = 'owner_portal'
            """,
            [venue_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


def _structured_specials_tables_available() -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'venue_published_structured_special'
            """
        )
        if not c.fetchone():
            return False
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'venue_published_special_recurring_pattern'
            """
        )
        return c.fetchone() is not None


def _meal_special_payload(**overrides) -> dict:
    body = {
        "title": "Thursday Parma Night",
        "description": "$20 parmas every Thursday.",
        "days_available": [4],
        "start_time": "17:00",
        "end_time": "21:00",
        "price_text": "$20",
        "conditions": "Dine-in only",
        "active": True,
    }
    body.update(overrides)
    return body


def _count_owner_meal_special_audits(venue_id: str, owner_account_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.audit_event
            WHERE actor_type = 'owner'
              AND actor_owner_account_id = %s::uuid
              AND entity_id = %s::uuid
              AND action = 'owner_direct_edit'
              AND detail->>'field_family' = 'meal_specials'
            """,
            [owner_account_id, venue_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


def _tap_offering_tables_available() -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'venue_published_tap_offering'
            """
        )
        if not c.fetchone():
            return False
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'venue_published_tap_offering_discovery_eligibility'
            """
        )
        return c.fetchone() is not None


def _tap_list_payload(**overrides) -> dict:
    body = {
        "drink_name": "Stone & Wood Pacific Ale",
        "brewery_or_brand": "Stone & Wood",
        "drink_type": "Pale ale",
        "abv": "4.4%",
        "price_text": "$12 schooner",
        "availability": "permanent",
        "notes": "House favourite",
        "active": True,
    }
    body.update(overrides)
    return body


def _count_owner_tap_list_audits(venue_id: str, owner_account_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.audit_event
            WHERE actor_type = 'owner'
              AND actor_owner_account_id = %s::uuid
              AND entity_id = %s::uuid
              AND action = 'owner_direct_edit'
              AND detail->>'field_family' = 'tap_list'
            """,
            [owner_account_id, venue_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


def _mvp_feature_definitions_available() -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.venue_attribute_definition
            WHERE stable_key = 'beer_garden'
              AND value_shape = 'boolean'
            """
        )
        row = c.fetchone()
    return bool(row and int(row[0]) > 0)


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

    def test_operational_profile_patch_without_token_returns_401(self) -> None:
        r = self.client.patch(
            f"/api/v1/owner/venues/{uuid4()}/operational-profile",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    def test_hours_patch_without_token_returns_401(self) -> None:
        r = self.client.patch(
            f"/api/v1/owner/venues/{uuid4()}/hours",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    def test_features_get_without_token_returns_401(self) -> None:
        r = self.client.get(f"/api/v1/owner/venues/{uuid4()}/features")
        self.assertEqual(r.status_code, 401)

    def test_features_patch_without_token_returns_401(self) -> None:
        r = self.client.patch(
            f"/api/v1/owner/venues/{uuid4()}/features",
            data='{"features":[]}',
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    def test_meal_specials_get_without_token_returns_401(self) -> None:
        r = self.client.get(f"/api/v1/owner/venues/{uuid4()}/meal-specials")
        self.assertEqual(r.status_code, 401)

    def test_meal_specials_post_without_token_returns_401(self) -> None:
        r = self.client.post(
            f"/api/v1/owner/venues/{uuid4()}/meal-specials",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    def test_tap_list_get_without_token_returns_401(self) -> None:
        r = self.client.get(f"/api/v1/owner/venues/{uuid4()}/tap-list")
        self.assertEqual(r.status_code, 401)

    def test_tap_list_post_without_token_returns_401(self) -> None:
        r = self.client.post(
            f"/api/v1/owner/venues/{uuid4()}/tap-list",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    def test_media_get_without_token_returns_401(self) -> None:
        r = self.client.get(f"/api/v1/owner/venues/{uuid4()}/media")
        self.assertEqual(r.status_code, 401)

    def test_media_upload_intent_without_token_returns_401(self) -> None:
        r = self.client.post(
            f"/api/v1/owner/venues/{uuid4()}/media/upload-intent",
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
        self.assertTrue(data["sections_available"]["features"])
        self.assertTrue(data["sections_available"]["meal_specials"])
        self.assertTrue(data["sections_available"]["tap_list"])
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
        self.assertIn(E2E_CAPABILITY_DIRECT_EDIT, caps)

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

    def test_detail_core_details_payload_hydrates_full_draft(self) -> None:
        self._skip_if_no_db()
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM public.venue_change_proposal WHERE venue_id = %s::uuid",
                [self.e2e.venue_id],
            )
        payload = _core_payload(locality_id=self.e2e.locality_id, confirm=False)
        body = {
            "section": "core_details",
            "intent": "draft",
            "payload": payload,
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            save = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
            self.assertEqual(save.status_code, 201)
            detail = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}",
                **_auth_headers(),
            )
        self.assertEqual(detail.status_code, 200)
        data = detail.json()["data"]
        core = data["draft"]["core_details_payload"]
        self.assertIsNotNone(core)
        self.assertEqual(core["display_name"], payload["display_name"])
        self.assertEqual(core["address_line_1"], payload["address_line_1"])
        self.assertEqual(core["address_line_2"], payload["address_line_2"])
        self.assertEqual(core["postal_code"], payload["postal_code"])
        self.assertEqual(core["locality_id"], payload["locality_id"])
        self.assertEqual(core["short_description"], payload["short_description"])
        self.assertEqual(core["long_description"], payload["long_description"])
        self.assertEqual(core["opening_hours"]["notes"], payload["opening_hours"]["notes"])
        self.assertEqual(
            core["opening_hours"]["regular_hours_json"],
            payload["opening_hours"]["regular_hours_json"],
        )
        self.assertEqual(
            data["published"]["profile"]["display_name"],
            "E2E Saved Venues Pub",
        )

    def test_resubmit_while_in_review_returns_existing_proposal(self) -> None:
        self._skip_if_no_db()
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM public.venue_change_proposal WHERE venue_id = %s::uuid",
                [self.e2e.venue_id],
            )
        body = {
            "section": "core_details",
            "intent": "submit",
            "payload": _core_payload(locality_id=self.e2e.locality_id),
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            first = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
            self.assertEqual(first.status_code, 201)
            first_id = first.json()["data"]["proposal_id"]
            count_after_first = _count_in_review_proposals(
                self.e2e.venue_id, self.e2e.owner_account_id
            )
            second = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(second.status_code, 200)
        second_data = second.json()["data"]
        self.assertEqual(second_data["proposal_id"], first_id)
        self.assertEqual(second_data["lifecycle_status"], "in_review")
        self.assertIn("already submitted", second_data["message"].lower())
        self.assertEqual(
            _count_in_review_proposals(self.e2e.venue_id, self.e2e.owner_account_id),
            count_after_first,
        )

    def test_draft_blocked_while_in_review(self) -> None:
        self._skip_if_no_db()
        submit_body = {
            "section": "core_details",
            "intent": "submit",
            "payload": _core_payload(locality_id=self.e2e.locality_id),
        }
        draft_body = {
            "section": "core_details",
            "intent": "draft",
            "payload": _core_payload(locality_id=self.e2e.locality_id, confirm=False),
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(submit_body),
                content_type="application/json",
                **_auth_headers(),
            )
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(draft_body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "proposal_already_in_review")

    def test_patch_operational_profile_updates_published_copy(self) -> None:
        self._skip_if_no_db()
        audits_before = _count_owner_direct_edit_audits(
            self.e2e.venue_id, self.e2e.owner_account_id
        )
        body = {
            "short_description": "Direct-edit short description.",
            "long_description": "Direct-edit long description.",
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/operational-profile",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertEqual(data["venue_id"], self.e2e.venue_id)
        self.assertEqual(data["updated"]["short_description"], body["short_description"])
        self.assertEqual(data["updated"]["long_description"], body["long_description"])
        self.assertEqual(data["message"], "Changes saved.")

        with connection.cursor() as c:
            c.execute(
                """
                SELECT short_description, long_description
                FROM public.venue_published_descriptive_copy
                WHERE venue_id = %s::uuid
                """,
                [self.e2e.venue_id],
            )
            row = c.fetchone()
        self.assertEqual(row[0], body["short_description"])
        self.assertEqual(row[1], body["long_description"])
        self.assertEqual(
            _count_owner_direct_edit_audits(
                self.e2e.venue_id, self.e2e.owner_account_id
            ),
            audits_before + 1,
        )

    def test_patch_operational_profile_rejects_display_name(self) -> None:
        self._skip_if_no_db()
        body = {"display_name": "Sneaky rename"}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/operational-profile",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("display_name", r.json()["error"]["details"])

    def test_patch_operational_profile_rejects_address_fields(self) -> None:
        self._skip_if_no_db()
        body = {"short_description": "Ok", "address_line_1": "1 Hack St"}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/operational-profile",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("address_line_1", r.json()["error"]["details"])

    def test_patch_operational_profile_rejects_google_place_id(self) -> None:
        self._skip_if_no_db()
        body = {"short_description": "Ok", "google_place_id": "ChIJxxxx"}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/operational-profile",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("google_place_id", r.json()["error"]["details"])

    def test_patch_operational_profile_missing_capability_returns_403(self) -> None:
        self._skip_if_no_db()
        _revoke_owner_capability(
            self.e2e.venue_id,
            self.e2e.owner_account_id,
            E2E_CAPABILITY_DIRECT_EDIT,
        )
        try:
            with patch(
                "common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx
            ):
                r = self.client.patch(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/operational-profile",
                    data=json.dumps({"short_description": "Blocked"}),
                    content_type="application/json",
                    **_auth_headers(),
                )
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.json()["error"]["code"], "forbidden")
        finally:
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT bvmr.id::text
                    FROM public.business_venue_management_relationship bvmr
                    WHERE bvmr.venue_id = %s::uuid
                    LIMIT 1
                    """,
                    [self.e2e.venue_id],
                )
                rel = c.fetchone()
            if rel:
                _restore_owner_capability(
                    rel[0], self.e2e.owner_account_id, E2E_CAPABILITY_DIRECT_EDIT
                )

    def test_patch_operational_profile_forbidden_for_unscoped_venue(self) -> None:
        self._skip_if_no_db()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.other_venue_id}/operational-profile",
                data=json.dumps({"short_description": "Nope"}),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)

    def test_patch_hours_replaces_regular_hours_transactionally(self) -> None:
        self._skip_if_no_db()
        audits_before = _count_owner_direct_edit_audits(
            self.e2e.venue_id, self.e2e.owner_account_id
        )
        body = {
            "uncertainty_level": "resolved_confident",
            "regular_hours_json": [
                {
                    "day_of_week": 1,
                    "opens_at": "10:00",
                    "closes_at": "22:00",
                    "crosses_midnight": False,
                }
            ],
            "exceptions_json": [],
            "notes": "Monday hours only for direct-edit test.",
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/hours",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertEqual(data["message"], "Opening hours saved.")
        self.assertEqual(len(data["hours"]["regular"]), 1)
        self.assertEqual(data["hours"]["regular"][0]["day_of_week"], 1)
        self.assertEqual(data["hours"]["regular"][0]["opens_at"], "10:00")
        self.assertEqual(data["hours"]["notes"], body["notes"])

        with connection.cursor() as c:
            c.execute(
                """
                SELECT day_of_week, opens_at::text, closes_at::text
                FROM public.venue_hours_regular
                WHERE venue_id = %s::uuid
                ORDER BY day_of_week
                """,
                [self.e2e.venue_id],
            )
            rows = c.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(int(rows[0][0]), 1)
        self.assertTrue(rows[0][1].startswith("10:00"))
        self.assertTrue(rows[0][2].startswith("22:00"))
        self.assertEqual(
            _count_owner_direct_edit_audits(
                self.e2e.venue_id, self.e2e.owner_account_id
            ),
            audits_before + 1,
        )

        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            detail = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}",
                **_auth_headers(),
            )
        self.assertEqual(detail.status_code, 200)
        regular = detail.json()["data"]["published"]["hours"]["regular"]
        self.assertEqual(len(regular), 1)
        self.assertEqual(regular[0]["day_of_week"], 1)

    def test_patch_hours_rejects_invalid_time(self) -> None:
        self._skip_if_no_db()
        body = {
            "regular_hours_json": [
                {
                    "day_of_week": 2,
                    "opens_at": "25:99",
                    "closes_at": "22:00",
                }
            ],
            "exceptions_json": [],
            "notes": "Invalid time should fail validation here.",
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/hours",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        dumped = json.dumps(r.json()["error"]["details"])
        self.assertIn("opens_at", dumped)

    def test_patch_hours_rejects_invalid_day(self) -> None:
        self._skip_if_no_db()
        body = {
            "regular_hours_json": [
                {
                    "day_of_week": 9,
                    "opens_at": "10:00",
                    "closes_at": "22:00",
                }
            ],
            "exceptions_json": [],
            "notes": "Invalid day should fail validation here.",
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/hours",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn(
            "day_of_week",
            json.dumps(r.json()["error"]["details"]),
        )

    def test_patch_hours_missing_capability_returns_403(self) -> None:
        self._skip_if_no_db()
        _revoke_owner_capability(
            self.e2e.venue_id,
            self.e2e.owner_account_id,
            E2E_CAPABILITY_DIRECT_EDIT,
        )
        body = {
            "regular_hours_json": [],
            "exceptions_json": [],
            "uncertainty_level": "unknown",
            "notes": "Capability missing should block this save.",
        }
        try:
            with patch(
                "common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx
            ):
                r = self.client.patch(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/hours",
                    data=json.dumps(body),
                    content_type="application/json",
                    **_auth_headers(),
                )
            self.assertEqual(r.status_code, 403)
        finally:
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT bvmr.id::text
                    FROM public.business_venue_management_relationship bvmr
                    WHERE bvmr.venue_id = %s::uuid
                    LIMIT 1
                    """,
                    [self.e2e.venue_id],
                )
                rel = c.fetchone()
            if rel:
                _restore_owner_capability(
                    rel[0], self.e2e.owner_account_id, E2E_CAPABILITY_DIRECT_EDIT
                )

    def test_restricted_change_request_stages_proposal_without_published_mutation(
        self,
    ) -> None:
        self._skip_if_no_db()
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM public.venue_change_proposal WHERE venue_id = %s::uuid",
                [self.e2e.venue_id],
            )
            c.execute(
                """
                SELECT proposed_display_name
                FROM public.venue_published_profile
                WHERE venue_id = %s::uuid
                """,
                [self.e2e.venue_id],
            )
            pub_name_before = c.fetchone()[0]

        body = {
            "section": "identity_location",
            "payload": {
                "display_name": "E2E Restricted Name Request",
                "address_line_1": "100 Restricted Ave",
                "locality_id": self.e2e.locality_id,
            },
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/restricted-change-requests",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 201)
        data = r.json()["data"]
        self.assertEqual(data["section"], "identity_location")
        self.assertEqual(data["lifecycle_status"], "in_review")
        proposal_id = data["proposal_id"]

        with connection.cursor() as c:
            c.execute(
                """
                SELECT lifecycle_status::text, submitted_at IS NOT NULL
                FROM public.venue_change_proposal WHERE id = %s::uuid
                """,
                [proposal_id],
            )
            row = c.fetchone()
            c.execute(
                """
                SELECT proposed_display_name
                FROM public.venue_proposal_staging_profile
                WHERE venue_change_proposal_id = %s::uuid
                """,
                [proposal_id],
            )
            staged_name = c.fetchone()[0]
            c.execute(
                """
                SELECT COUNT(*)::int
                FROM public.venue_proposal_target
                WHERE venue_change_proposal_id = %s::uuid
                  AND target_family = 'hours'
                """,
                [proposal_id],
            )
            hours_target = c.fetchone()[0]
            c.execute(
                """
                SELECT proposed_display_name
                FROM public.venue_published_profile
                WHERE venue_id = %s::uuid
                """,
                [self.e2e.venue_id],
            )
            pub_name_after = c.fetchone()[0]

        self.assertEqual(row[0], "in_review")
        self.assertTrue(row[1])
        self.assertEqual(staged_name, "E2E Restricted Name Request")
        self.assertEqual(hours_target, 0)
        self.assertEqual(pub_name_after, pub_name_before)

    def test_restricted_change_rejects_operational_fields(self) -> None:
        self._skip_if_no_db()
        body = {
            "section": "identity_location",
            "payload": {"short_description": "Sneaky desc"},
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/restricted-change-requests",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("short_description", r.json()["error"]["details"])

    def test_restricted_change_rejects_google_place_id(self) -> None:
        self._skip_if_no_db()
        body = {
            "section": "identity_location",
            "payload": {
                "display_name": "Test",
                "google_place_id": "ChIJxxxx",
            },
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/restricted-change-requests",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("google_place_id", r.json()["error"]["details"])

    def test_restricted_change_missing_capability_returns_403(self) -> None:
        self._skip_if_no_db()
        _revoke_owner_capability(
            self.e2e.venue_id,
            self.e2e.owner_account_id,
            E2E_CAPABILITY_SUBMIT,
        )
        body = {
            "section": "identity_location",
            "payload": {"display_name": "Blocked Name"},
        }
        try:
            with patch(
                "common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx
            ):
                r = self.client.post(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/restricted-change-requests",
                    data=json.dumps(body),
                    content_type="application/json",
                    **_auth_headers(),
                )
            self.assertEqual(r.status_code, 403)
        finally:
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT bvmr.id::text
                    FROM public.business_venue_management_relationship bvmr
                    WHERE bvmr.venue_id = %s::uuid
                    LIMIT 1
                    """,
                    [self.e2e.venue_id],
                )
                rel = c.fetchone()
            if rel:
                _restore_owner_capability(
                    rel[0], self.e2e.owner_account_id, E2E_CAPABILITY_SUBMIT
                )

    def test_restricted_duplicate_in_review_returns_existing_proposal(self) -> None:
        self._skip_if_no_db()
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM public.venue_change_proposal WHERE venue_id = %s::uuid",
                [self.e2e.venue_id],
            )
        body = {
            "section": "identity_location",
            "payload": {
                "display_name": "Duplicate Restricted Name",
                "address_line_1": "200 Restricted St",
                "locality_id": self.e2e.locality_id,
            },
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            first = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/restricted-change-requests",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
            self.assertEqual(first.status_code, 201)
            first_id = first.json()["data"]["proposal_id"]
            second = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/restricted-change-requests",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["data"]["proposal_id"], first_id)
        self.assertIn("already waiting", second.json()["data"]["message"].lower())

    def test_get_features_returns_mvp_boolean_definitions(self) -> None:
        self._skip_if_no_db()
        if not _mvp_feature_definitions_available():
            self.skipTest("MVP feature attribute definitions not seeded in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/features",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertEqual(data["venue_id"], self.e2e.venue_id)
        features = data["features"]
        self.assertGreaterEqual(len(features), 8)
        keys = {f["stable_key"] for f in features}
        self.assertIn("beer_garden", keys)
        self.assertIn("dog_friendly", keys)
        for feature in features:
            self.assertEqual(feature["value_shape"], "boolean")
            self.assertIsInstance(feature["value"], bool)
        dumped = json.dumps(data)
        self.assertNotIn("google_place_id", dumped)

    def test_patch_features_updates_published_values_and_audit(self) -> None:
        self._skip_if_no_db()
        if not _mvp_feature_definitions_available():
            self.skipTest("MVP feature attribute definitions not seeded in test DB.")
        staging_before = _count_staging_attribute_rows(self.e2e.venue_id)
        audits_before = _count_owner_direct_edit_audits(
            self.e2e.venue_id, self.e2e.owner_account_id
        )
        body = {
            "features": [
                {
                    "attribute_definition_id": E2E_MVP_BEER_GARDEN_ATTR_ID,
                    "value_boolean": True,
                },
                {
                    "attribute_definition_id": E2E_MVP_DOG_FRIENDLY_ATTR_ID,
                    "value_boolean": False,
                },
            ]
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/features",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertIn("Features saved", data["message"])
        beer = next(f for f in data["features"] if f["stable_key"] == "beer_garden")
        dog = next(f for f in data["features"] if f["stable_key"] == "dog_friendly")
        self.assertTrue(beer["value"])
        self.assertFalse(dog["value"])

        with connection.cursor() as c:
            c.execute(
                """
                SELECT value_boolean
                FROM public.venue_published_attribute_value pav
                INNER JOIN public.venue_attribute_definition ad
                  ON ad.id = pav.attribute_definition_id
                WHERE pav.venue_id = %s::uuid AND ad.stable_key = 'beer_garden'
                """,
                [self.e2e.venue_id],
            )
            row = c.fetchone()
        self.assertIsNotNone(row)
        self.assertTrue(row[0])

        self.assertEqual(
            _count_owner_direct_edit_audits(
                self.e2e.venue_id, self.e2e.owner_account_id
            ),
            audits_before + 1,
        )
        self.assertEqual(
            _count_staging_attribute_rows(self.e2e.venue_id), staging_before
        )

    def test_patch_features_rejects_unknown_attribute_id(self) -> None:
        self._skip_if_no_db()
        if not _mvp_feature_definitions_available():
            self.skipTest("MVP feature attribute definitions not seeded in test DB.")
        body = {
            "features": [
                {"attribute_definition_id": str(uuid4()), "value_boolean": True},
            ]
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/features",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_patch_features_rejects_non_boolean_attribute(self) -> None:
        self._skip_if_no_db()
        if not _mvp_feature_definitions_available():
            self.skipTest("MVP feature attribute definitions not seeded in test DB.")
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.venue_attribute_definition (
                  id, stable_key, display_label, value_shape, cardinality, is_discovery_driving
                ) VALUES (
                  'bada9999-0000-4000-8000-0000000000f1',
                  'e2e_text_attr_owner',
                  'E2E text',
                  'text_non_discovery',
                  'single',
                  false
                ) ON CONFLICT (stable_key) DO NOTHING
                """
            )
        body = {
            "features": [
                {
                    "attribute_definition_id": "bada9999-0000-4000-8000-0000000000f1",
                    "value_boolean": True,
                },
            ]
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/features",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_patch_features_missing_capability_returns_403(self) -> None:
        self._skip_if_no_db()
        if not _mvp_feature_definitions_available():
            self.skipTest("MVP feature attribute definitions not seeded in test DB.")
        _revoke_owner_capability(
            self.e2e.venue_id,
            self.e2e.owner_account_id,
            E2E_CAPABILITY_DIRECT_EDIT,
        )
        body = {
            "features": [
                {
                    "attribute_definition_id": E2E_MVP_BEER_GARDEN_ATTR_ID,
                    "value_boolean": True,
                },
            ]
        }
        try:
            with patch(
                "common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx
            ):
                r = self.client.patch(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/features",
                    data=json.dumps(body),
                    content_type="application/json",
                    **_auth_headers(),
                )
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.json()["error"]["code"], "forbidden")
        finally:
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT bvmr.id::text
                    FROM public.business_venue_management_relationship bvmr
                    WHERE bvmr.venue_id = %s::uuid
                    LIMIT 1
                    """,
                    [self.e2e.venue_id],
                )
                rel = c.fetchone()
            if rel:
                _restore_owner_capability(
                    rel[0], self.e2e.owner_account_id, E2E_CAPABILITY_DIRECT_EDIT
                )

    def test_patch_features_forbidden_for_unscoped_venue(self) -> None:
        self._skip_if_no_db()
        if not _mvp_feature_definitions_available():
            self.skipTest("MVP feature attribute definitions not seeded in test DB.")
        body = {
            "features": [
                {
                    "attribute_definition_id": E2E_MVP_BEER_GARDEN_ATTR_ID,
                    "value_boolean": True,
                },
            ]
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.other_venue_id}/features",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)

    def test_proposal_still_works_after_direct_edit_endpoints(self) -> None:
        self._skip_if_no_db()
        body = {
            "section": "core_details",
            "intent": "draft",
            "payload": _core_payload(
                locality_id=self.e2e.locality_id, confirm=False
            ),
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/proposals",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["data"]["lifecycle_status"], "staged")

    def test_get_meal_specials_returns_list(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertEqual(data["venue_id"], self.e2e.venue_id)
        self.assertIsInstance(data["meal_specials"], list)

    def test_create_meal_special_writes_published_row_and_audit(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        proposals_before = _count_in_review_proposals(
            self.e2e.venue_id, self.e2e.owner_account_id
        )
        audits_before = _count_owner_meal_special_audits(
            self.e2e.venue_id, self.e2e.owner_account_id
        )
        body = _meal_special_payload()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 201)
        data = r.json()["data"]
        self.assertIn("Special saved", data["message"])
        special = data["meal_special"]
        self.assertEqual(special["title"], body["title"])
        self.assertEqual(special["days_available"], [4])
        self.assertTrue(special["active"])

        with connection.cursor() as c:
            c.execute(
                """
                SELECT s.short_label, s.structured_kind, s.catalog_record_status
                FROM public.venue_published_structured_special s
                WHERE s.id = %s::uuid
                """,
                [special["id"]],
            )
            row = c.fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row[0], body["title"])
        self.assertEqual(row[1], "meal_special")
        self.assertEqual(row[2], "active")

        self.assertEqual(
            _count_owner_meal_special_audits(
                self.e2e.venue_id, self.e2e.owner_account_id
            ),
            audits_before + 1,
        )
        self.assertEqual(
            _count_in_review_proposals(self.e2e.venue_id, self.e2e.owner_account_id),
            proposals_before,
        )

    def test_patch_meal_special_updates_row(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            created = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials",
                data=json.dumps(_meal_special_payload(title="Sunday Roast")),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(created.status_code, 201)
        special_id = created.json()["data"]["meal_special"]["id"]
        patch_body = {"price_text": "$25", "description": "Updated roast special."}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials/{special_id}",
                data=json.dumps(patch_body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        updated = r.json()["data"]["meal_special"]
        self.assertEqual(updated["price_text"], "$25")
        self.assertEqual(updated["description"], "Updated roast special.")

    def test_delete_meal_special_deactivates_row(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            created = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials",
                data=json.dumps(_meal_special_payload(title="Kids Meals")),
                content_type="application/json",
                **_auth_headers(),
            )
        special_id = created.json()["data"]["meal_special"]["id"]
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.delete(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials/{special_id}",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["data"]["meal_special"]["active"])
        with connection.cursor() as c:
            c.execute(
                """
                SELECT catalog_record_status
                FROM public.venue_published_structured_special
                WHERE id = %s::uuid
                """,
                [special_id],
            )
            row = c.fetchone()
        self.assertEqual(row[0], "retired")

    def test_create_meal_special_rejects_invalid_day(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        body = _meal_special_payload(days_available=[7])
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_create_meal_special_rejects_invalid_time_pair(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        body = _meal_special_payload(start_time="17:00", end_time=None)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_create_meal_special_rejects_unsupported_fields(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        body = _meal_special_payload(extra_field="nope")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_meal_specials_missing_capability_returns_403(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        _revoke_owner_capability(
            self.e2e.venue_id,
            self.e2e.owner_account_id,
            E2E_CAPABILITY_DIRECT_EDIT,
        )
        try:
            with patch(
                "common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx
            ):
                r = self.client.post(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/meal-specials",
                    data=json.dumps(_meal_special_payload()),
                    content_type="application/json",
                    **_auth_headers(),
                )
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.json()["error"]["code"], "forbidden")
        finally:
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT bvmr.id::text
                    FROM public.business_venue_management_relationship bvmr
                    WHERE bvmr.venue_id = %s::uuid
                    LIMIT 1
                    """,
                    [self.e2e.venue_id],
                )
                rel = c.fetchone()
            if rel:
                _restore_owner_capability(
                    rel[0], self.e2e.owner_account_id, E2E_CAPABILITY_DIRECT_EDIT
                )

    def test_meal_specials_forbidden_for_unscoped_venue(self) -> None:
        self._skip_if_no_db()
        if not _structured_specials_tables_available():
            self.skipTest("Structured specials tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.other_venue_id}/meal-specials",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)

    def test_get_tap_list_returns_list(self) -> None:
        self._skip_if_no_db()
        if not _tap_offering_tables_available():
            self.skipTest("Tap offering tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertEqual(data["venue_id"], self.e2e.venue_id)
        self.assertIsInstance(data["tap_list"], list)

    def test_create_tap_list_item_writes_published_row_and_audit(self) -> None:
        self._skip_if_no_db()
        if not _tap_offering_tables_available():
            self.skipTest("Tap offering tables not present in test DB.")
        proposals_before = _count_in_review_proposals(
            self.e2e.venue_id, self.e2e.owner_account_id
        )
        audits_before = _count_owner_tap_list_audits(
            self.e2e.venue_id, self.e2e.owner_account_id
        )
        body = _tap_list_payload()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 201)
        data = r.json()["data"]
        self.assertIn("Drink list saved", data["message"])
        item = data["tap_item"]
        self.assertEqual(item["drink_name"], body["drink_name"])
        self.assertEqual(item["availability"], "permanent")
        self.assertTrue(item["active"])

        with connection.cursor() as c:
            c.execute(
                """
                SELECT t.unstructured_line_label, t.catalog_record_status, t.beverage_product_id
                FROM public.venue_published_tap_offering t
                WHERE t.id = %s::uuid
                """,
                [item["id"]],
            )
            row = c.fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row[0], body["drink_name"])
        self.assertEqual(row[1], "active")
        self.assertIsNone(row[2])

        self.assertEqual(
            _count_owner_tap_list_audits(
                self.e2e.venue_id, self.e2e.owner_account_id
            ),
            audits_before + 1,
        )
        self.assertEqual(
            _count_in_review_proposals(self.e2e.venue_id, self.e2e.owner_account_id),
            proposals_before,
        )

    def test_patch_tap_list_item_updates_row(self) -> None:
        self._skip_if_no_db()
        if not _tap_offering_tables_available():
            self.skipTest("Tap offering tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            created = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list",
                data=json.dumps(_tap_list_payload(drink_name="Guinness")),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(created.status_code, 201)
        item_id = created.json()["data"]["tap_item"]["id"]
        patch_body = {"price_text": "$14 pint", "availability": "rotating"}
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.patch(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list/{item_id}",
                data=json.dumps(patch_body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        updated = r.json()["data"]["tap_item"]
        self.assertEqual(updated["price_text"], "$14 pint")
        self.assertEqual(updated["availability"], "rotating")

    def test_delete_tap_list_item_deactivates_row(self) -> None:
        self._skip_if_no_db()
        if not _tap_offering_tables_available():
            self.skipTest("Tap offering tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            created = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list",
                data=json.dumps(_tap_list_payload(drink_name="House red wine")),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(created.status_code, 201)
        item_id = created.json()["data"]["tap_item"]["id"]
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.delete(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list/{item_id}",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["data"]["tap_item"]["active"])

        with connection.cursor() as c:
            c.execute(
                """
                SELECT catalog_record_status
                FROM public.venue_published_tap_offering
                WHERE id = %s::uuid
                """,
                [item_id],
            )
            row = c.fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row[0], "retired")

    def test_create_tap_list_item_rejects_invalid_drink_name(self) -> None:
        self._skip_if_no_db()
        if not _tap_offering_tables_available():
            self.skipTest("Tap offering tables not present in test DB.")
        body = _tap_list_payload(drink_name="A")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_create_tap_list_item_rejects_unsupported_fields(self) -> None:
        self._skip_if_no_db()
        if not _tap_offering_tables_available():
            self.skipTest("Tap offering tables not present in test DB.")
        body = _tap_list_payload(extra_field="nope")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_tap_list_missing_capability_returns_403(self) -> None:
        self._skip_if_no_db()
        if not _tap_offering_tables_available():
            self.skipTest("Tap offering tables not present in test DB.")
        _revoke_owner_capability(
            self.e2e.venue_id,
            self.e2e.owner_account_id,
            E2E_CAPABILITY_DIRECT_EDIT,
        )
        try:
            with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
                r = self.client.post(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/tap-list",
                    data=json.dumps(_tap_list_payload()),
                    content_type="application/json",
                    **_auth_headers(),
                )
            self.assertEqual(r.status_code, 403)
            self.assertEqual(r.json()["error"]["code"], "forbidden")
        finally:
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT id::text
                    FROM public.business_venue_management_relationship
                    WHERE venue_id = %s::uuid
                    LIMIT 1
                    """,
                    [self.e2e.venue_id],
                )
                rel = c.fetchone()
            if rel:
                _restore_owner_capability(
                    rel[0], self.e2e.owner_account_id, E2E_CAPABILITY_DIRECT_EDIT
                )

    def test_tap_list_forbidden_for_unscoped_venue(self) -> None:
        self._skip_if_no_db()
        if not _tap_offering_tables_available():
            self.skipTest("Tap offering tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.other_venue_id}/tap-list",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)

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


def _venue_media_tables_available() -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'venue_published_media'
            """
        )
        if not c.fetchone():
            return False
        c.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = 'owner_venue_media_upload_intent'
            """
        )
        return c.fetchone() is not None


def _media_upload_intent_payload(**overrides) -> dict:
    body = {
        "purpose": "gallery",
        "file_name": "front-bar.jpg",
        "content_type": "image/jpeg",
        "file_size_bytes": 120000,
    }
    body.update(overrides)
    return body


def _count_owner_media_audits(venue_id: str, owner_account_id: str) -> int:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.audit_event
            WHERE actor_type = 'owner'
              AND actor_owner_account_id = %s::uuid
              AND entity_id = %s::uuid
              AND action = 'owner_direct_edit'
              AND detail->>'field_family' = 'media'
            """,
            [owner_account_id, venue_id],
        )
        row = c.fetchone()
    return int(row[0]) if row else 0


@override_settings(SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys")
class OwnerVenueMediaValidationTests(SimpleTestCase):
    def test_upload_intent_rejects_invalid_content_type(self) -> None:
        from apps.owner.services.owner_venue_media_service import (
            _validate_upload_intent_body,
        )

        _, err = _validate_upload_intent_body(
            {
                "purpose": "gallery",
                "file_name": "photo.gif",
                "content_type": "image/gif",
                "file_size_bytes": 1000,
            }
        )
        self.assertIsNotNone(err)
        self.assertIn("content_type", err)

    def test_create_rejects_arbitrary_storage_path(self) -> None:
        from apps.owner.services.owner_venue_media_service import _validate_create_body

        _, err = _validate_create_body(
            {
                "media_id": str(uuid4()),
                "purpose": "gallery",
                "storage_bucket": "venue-media",
                "storage_path": "other/random/path.jpg",
            }
        )
        self.assertIsNotNone(err)
        self.assertIn("storage_path", err)


@override_settings(SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys")
class OwnerVenueMediaE2ETests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.e2e = try_install_owner_venues_e2e_fixtures()
        if self.e2e is None:
            return
        self.owner_ctx = _ctx(self.e2e.owner_auth_user_id, email="e2e-owner@pubplus.test")

    def _skip_if_no_db(self) -> None:
        if self.e2e is None:
            self.skipTest("PubPlus owner venue schema not available in test database.")

    @patch(
        "apps.owner.services.owner_venue_media_service.storage_object_exists",
        return_value=True,
    )
    @patch(
        "apps.owner.services.owner_venue_media_service.create_signed_upload_url",
    )
    def test_media_upload_intent_and_create_flow(
        self, mock_signed, _mock_exists
    ) -> None:
        self._skip_if_no_db()
        if not _venue_media_tables_available():
            self.skipTest("Venue media tables not present in test DB.")

        from common.storage.supabase_storage import SignedUploadResult

        mock_signed.return_value = SignedUploadResult(
            signed_upload_url="https://example.supabase.co/upload/signed",
            path="venues/x/gallery/y.jpg",
            token=None,
        )

        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            intent_r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/media/upload-intent",
                data=json.dumps(_media_upload_intent_payload(purpose="profile")),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(intent_r.status_code, 200)
        intent = intent_r.json()["data"]
        self.assertEqual(intent["storage_bucket"], "venue-media")
        self.assertIn(f"venues/{self.e2e.venue_id}/profile/", intent["storage_path"])
        self.assertTrue(intent["signed_upload_url"])

        audits_before = _count_owner_media_audits(
            self.e2e.venue_id, self.e2e.owner_account_id
        )
        create_body = {
            "media_id": intent["media_id"],
            "purpose": "profile",
            "storage_bucket": intent["storage_bucket"],
            "storage_path": intent["storage_path"],
            "alt_text": "Front bar",
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            create_r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/media",
                data=json.dumps(create_body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(create_r.status_code, 201)
        self.assertIn("Photo saved", create_r.json()["data"]["message"])
        self.assertEqual(
            _count_owner_media_audits(
                self.e2e.venue_id, self.e2e.owner_account_id
            ),
            audits_before + 1,
        )

        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            list_r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/media",
                **_auth_headers(),
            )
        self.assertEqual(list_r.status_code, 200)
        media = list_r.json()["data"]["media"]
        self.assertTrue(any(m["purpose"] == "profile" for m in media))

    @patch(
        "apps.owner.services.owner_venue_media_service.create_signed_upload_url",
    )
    def test_upload_intent_validates_file_size(self, mock_signed) -> None:
        self._skip_if_no_db()
        if not _venue_media_tables_available():
            self.skipTest("Venue media tables not present in test DB.")
        mock_signed.side_effect = AssertionError("should not call storage")

        body = _media_upload_intent_payload(file_size_bytes=10_000_000)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/media/upload-intent",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    @patch(
        "apps.owner.services.owner_venue_media_service.storage_object_exists",
        return_value=True,
    )
    @patch(
        "apps.owner.services.owner_venue_media_service.create_signed_upload_url",
    )
    def test_profile_create_deactivates_previous_profile(
        self, mock_signed, _mock_exists
    ) -> None:
        self._skip_if_no_db()
        if not _venue_media_tables_available():
            self.skipTest("Venue media tables not present in test DB.")

        from common.storage.supabase_storage import SignedUploadResult

        mock_signed.return_value = SignedUploadResult(
            signed_upload_url="https://example.supabase.co/upload/signed",
            path="venues/x/gallery/y.jpg",
            token=None,
        )

        def _create_profile(label: str) -> str:
            with patch(
                "common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx
            ):
                intent_r = self.client.post(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/media/upload-intent",
                    data=json.dumps(
                        _media_upload_intent_payload(
                            purpose="profile", file_name=f"{label}.jpg"
                        )
                    ),
                    content_type="application/json",
                    **_auth_headers(),
                )
            intent = intent_r.json()["data"]
            with patch(
                "common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx
            ):
                create_r = self.client.post(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/media",
                    data=json.dumps(
                        {
                            "media_id": intent["media_id"],
                            "purpose": "profile",
                            "storage_bucket": intent["storage_bucket"],
                            "storage_path": intent["storage_path"],
                        }
                    ),
                    content_type="application/json",
                    **_auth_headers(),
                )
            self.assertEqual(create_r.status_code, 201)
            return intent["media_id"]

        first_id = _create_profile("first")
        second_id = _create_profile("second")
        self.assertNotEqual(first_id, second_id)

        with connection.cursor() as c:
            c.execute(
                """
                SELECT catalog_record_status
                FROM public.venue_published_media
                WHERE id = %s::uuid
                """,
                [first_id],
            )
            first_status = c.fetchone()[0]
            c.execute(
                """
                SELECT catalog_record_status
                FROM public.venue_published_media
                WHERE id = %s::uuid
                """,
                [second_id],
            )
            second_status = c.fetchone()[0]
        self.assertEqual(first_status, "retired")
        self.assertEqual(second_status, "active")

    @patch(
        "apps.owner.services.owner_venue_media_service.storage_object_exists",
        return_value=False,
    )
    def test_create_rejects_missing_storage_object(self, _mock_exists) -> None:
        self._skip_if_no_db()
        if not _venue_media_tables_available():
            self.skipTest("Venue media tables not present in test DB.")

        media_id = str(uuid4())
        storage_path = f"venues/{self.e2e.venue_id}/gallery/{media_id}.jpg"
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO public.owner_venue_media_upload_intent (
                    id, venue_id, owner_account_id, purpose,
                    storage_bucket, storage_path, content_type, expires_at
                ) VALUES (
                    %s::uuid, %s::uuid, %s::uuid, 'gallery',
                    'venue-media', %s, 'image/jpeg', now() + interval '10 minutes'
                )
                """,
                [media_id, self.e2e.venue_id, self.e2e.owner_account_id, storage_path],
            )

        body = {
            "media_id": media_id,
            "purpose": "gallery",
            "storage_bucket": "venue-media",
            "storage_path": storage_path,
        }
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.post(
                f"/api/v1/owner/venues/{self.e2e.venue_id}/media",
                data=json.dumps(body),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    def test_media_missing_capability_returns_403(self) -> None:
        self._skip_if_no_db()
        if not _venue_media_tables_available():
            self.skipTest("Venue media tables not present in test DB.")
        _revoke_owner_capability(
            self.e2e.venue_id,
            self.e2e.owner_account_id,
            E2E_CAPABILITY_DIRECT_EDIT,
        )
        try:
            with patch(
                "common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx
            ):
                r = self.client.get(
                    f"/api/v1/owner/venues/{self.e2e.venue_id}/media",
                    **_auth_headers(),
                )
            self.assertEqual(r.status_code, 403)
        finally:
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT bvmr.id::text
                    FROM public.business_venue_management_relationship bvmr
                    WHERE bvmr.venue_id = %s::uuid
                    LIMIT 1
                    """,
                    [self.e2e.venue_id],
                )
                rel = c.fetchone()
            if rel:
                _restore_owner_capability(
                    rel[0], self.e2e.owner_account_id, E2E_CAPABILITY_DIRECT_EDIT
                )

    def test_media_forbidden_for_unscoped_venue(self) -> None:
        self._skip_if_no_db()
        if not _venue_media_tables_available():
            self.skipTest("Venue media tables not present in test DB.")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=self.owner_ctx):
            r = self.client.get(
                f"/api/v1/owner/venues/{self.e2e.other_venue_id}/media",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 403)
