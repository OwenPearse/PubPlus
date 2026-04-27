from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

from django.db import connection, transaction
from django.test import TestCase, override_settings
from django.test.client import Client

from common.auth.context import AuthContext

from tests.support.saved_venues_e2e_data import (
    E2E_AUTH_USER_ID,
    E2E_LOCALITY_ID,
    E2E_REGION_ID,
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
        email="e2e-profile@pubplus.test",
        claims={"sub": subj},
    )


@override_settings(
    SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys"
)
class ProfileApiTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.csrf_client = Client(enforce_csrf_checks=True)

    @staticmethod
    def _delete_e2e_consumer_state(auth_user_id: str) -> None:
        with connection.cursor() as c:
            c.execute(
                """
                DELETE FROM public.consumer_notification_settings
                WHERE consumer_account_id IN (
                    SELECT id FROM public.consumer_account
                    WHERE auth_user_id = %s::uuid
                )
                """,
                [auth_user_id],
            )
            c.execute(
                """
                DELETE FROM public.consumer_default_location_preference
                WHERE consumer_account_id IN (
                    SELECT id FROM public.consumer_account
                    WHERE auth_user_id = %s::uuid
                )
                """,
                [auth_user_id],
            )
            c.execute(
                """
                DELETE FROM public.consumer_profile
                WHERE consumer_account_id IN (
                    SELECT id FROM public.consumer_account
                    WHERE auth_user_id = %s::uuid
                )
                """,
                [auth_user_id],
            )
            c.execute(
                """
                DELETE FROM public.consumer_account
                WHERE auth_user_id = %s::uuid
                """,
                [auth_user_id],
            )

    def test_unauthenticated_returns_401(self) -> None:
        r = self.client.get("/api/v1/profile/")
        self.assertEqual(r.status_code, 401)
        r2 = self.client.patch(
            "/api/v1/profile/",
            data="{}",
            content_type="application/json",
        )
        self.assertEqual(r2.status_code, 401)

    def test_patch_rejects_unknown_field_and_malformed_json(
        self,
    ) -> None:
        e2e = try_install_saved_venues_e2e_fixtures()
        if e2e is None:
            self.skipTest("E2E DB fixtures not available for profile tests.")
        with transaction.atomic():
            self._delete_e2e_consumer_state(e2e.auth_user_id)
        ctx = _make_context_for_auth_subject(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r0 = self.client.patch(
                "/api/v1/profile/",
                data="not json",
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r0.status_code, 400)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r1 = self.client.patch(
                "/api/v1/profile/",
                data=json.dumps(
                    {
                        "display_name": "A",
                        "favourite_venue_features": ["beer_garden"],
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r1.status_code, 400, r1.content)
        self.assertIn("error", r1.json())
        errj = r1.json()["error"]
        self.assertIn(
            "unknown",
            (errj.get("message", "") + str(errj.get("details", {}))).lower(),
        )

    def test_db_get_patch_partial_update_bootstrap(
        self,
    ) -> None:
        e2e = try_install_saved_venues_e2e_fixtures()
        if e2e is None:
            self.skipTest("E2E DB fixtures not available for profile tests.")
        with transaction.atomic():
            self._delete_e2e_consumer_state(e2e.auth_user_id)

        ctx = _make_context_for_auth_subject(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            g1 = self.client.get(
                "/api/v1/profile/",
                **_auth_headers(),
            )
        self.assertEqual(g1.status_code, 200, g1.content)
        body1 = g1.json()["data"]
        self.assertEqual(body1.get("display_name"), "e2e-profile")
        self.assertEqual(
            body1.get("default_locality_id"), None, "Omitted rows read as null / defaults"
        )
        # Defaults from schema when no notification row
        self.assertEqual(body1.get("email_marketing_opt_in"), False)
        self.assertEqual(body1.get("email_transactional_opt_in"), True)
        self.assertIn("push_notifications_opt_in", body1)
        with connection.cursor() as c:
            c.execute(
                """
                SELECT count(1)
                FROM public.consumer_account
                WHERE auth_user_id = %s::uuid
                """,
                [e2e.auth_user_id],
            )
            account_count = c.fetchone()[0]
            c.execute(
                """
                SELECT count(1)
                FROM public.consumer_profile cp
                INNER JOIN public.consumer_account ca ON ca.id = cp.consumer_account_id
                WHERE ca.auth_user_id = %s::uuid
                """,
                [e2e.auth_user_id],
            )
            profile_count = c.fetchone()[0]
        self.assertEqual(account_count, 1)
        self.assertEqual(profile_count, 1)

        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            p1 = self.client.patch(
                "/api/v1/profile/",
                data=json.dumps(
                    {
                        "display_name": "Test User",
                        "email_marketing_opt_in": True,
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(p1.status_code, 200, p1.content)
        pbody = p1.json()["data"]
        self.assertEqual(pbody.get("display_name"), "Test User")
        self.assertIsNone(pbody.get("avatar_storage_ref"), "Omitted = unchanged (none)")
        self.assertEqual(pbody.get("email_marketing_opt_in"), True)
        self.assertEqual(
            pbody.get("email_transactional_opt_in"),
            True,
            "Transaction opt-in not in PATCH, unchanged (default or prior)",
        )

        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            p2 = self.client.patch(
                "/api/v1/profile/",
                data=json.dumps(
                    {
                        "default_locality_id": E2E_LOCALITY_ID,
                        "default_geographic_region_id": E2E_REGION_ID,
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(p2.status_code, 200, p2.content)
        self.assertEqual(
            p2.json()["data"].get("default_locality_id"), E2E_LOCALITY_ID
        )
        self.assertEqual(
            p2.json()["data"].get("default_geographic_region_id"), E2E_REGION_ID
        )
        # display name must remain from prior patch
        self.assertEqual(p2.json()["data"].get("display_name"), "Test User")
        # prior notification flag preserved
        self.assertEqual(p2.json()["data"].get("email_marketing_opt_in"), True)

        with connection.cursor() as c:
            c.execute(
                """
                SELECT display_name, c.id
                FROM public.consumer_profile cp
                INNER JOIN public.consumer_account c ON c.id = cp.consumer_account_id
                WHERE c.auth_user_id = %s::uuid
                """,
                [e2e.auth_user_id],
            )
            dr = c.fetchone()
        self.assertIsNotNone(dr)
        self.assertEqual(dr[0], "Test User")

    def test_invalid_type_for_boolean(
        self,
    ) -> None:
        e2e = try_install_saved_venues_e2e_fixtures()
        if e2e is None:
            self.skipTest("E2E DB fixtures not available.")
        ctx = _make_context_for_auth_subject(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.patch(
                "/api/v1/profile/",
                data=json.dumps({"email_marketing_opt_in": 1}),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400, r.content)

    @patch(
        "common.auth.guards.verify_supabase_jwt",
        return_value=_make_context_for_auth_subject(E2E_AUTH_USER_ID),
    )
    def test_patch_with_bearer_token_does_not_require_csrf(
        self, _mock_jwt: object
    ) -> None:
        response = self.csrf_client.patch(
            "/api/v1/profile/",
            data=json.dumps({"push_notifications_opt_in": False}),
            content_type="application/json",
            **_auth_headers(),
        )
        self.assertNotEqual(response.status_code, 403, response.content)

    def test_bad_locality_uuid_fk(
        self,
    ) -> None:
        e2e = try_install_saved_venues_e2e_fixtures()
        if e2e is None:
            self.skipTest("E2E DB fixtures not available.")
        ctx = _make_context_for_auth_subject(e2e.auth_user_id)
        bad = str(uuid4())
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.patch(
                "/api/v1/profile/",
                data=json.dumps({"default_locality_id": bad}),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400, r.json()["error"]["code"], r.content)
        deets = r.json()["error"].get("details", {})
        self.assertTrue("default_locality_id" in deets or "fields" in deets, r.json())

    def test_quiet_hours_both_or_neither(
        self,
    ) -> None:
        e2e = try_install_saved_venues_e2e_fixtures()
        if e2e is None:
            self.skipTest("E2E DB fixtures not available.")
        ctx = _make_context_for_auth_subject(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.patch(
                "/api/v1/profile/",
                data=json.dumps({"quiet_hours_start_local": "22:00:00"}),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400, r.content)
