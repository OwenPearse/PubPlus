from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from django.http import HttpRequest
from django.test import Client, SimpleTestCase, TestCase, override_settings

from common.auth.context import AuthContext
from common.auth.errors import InvalidTokenError


def _owner_context(*, aal: str = "aal1", subject: str | None = None) -> AuthContext:
    sub = subject or str(uuid4())
    return AuthContext(
        subject=sub,
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="owner@example.com",
        claims={"sub": sub, "aal": aal},
    )


class OwnerEndpointAuthTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_provision_without_token_returns_401(self) -> None:
        response = self.client.post("/api/v1/owner/provision")
        self.assertEqual(response.status_code, 401)

    def test_auth_probe_without_token_returns_401(self) -> None:
        response = self.client.get("/api/v1/owner/auth-probe")
        self.assertEqual(response.status_code, 401)

    def test_provision_with_invalid_token_returns_401(self) -> None:
        with patch(
            "common.auth.guards.verify_supabase_jwt",
            side_effect=InvalidTokenError("bad token"),
        ):
            response = self.client.post(
                "/api/v1/owner/provision",
                HTTP_AUTHORIZATION="Bearer invalid",
            )
        self.assertEqual(response.status_code, 401)

    @patch("apps.owner.services.owner_access_service.load_owner_access_counts")
    @patch("api.v1.owner.views.provision_owner_account")
    def test_provision_success_created_returns_201(
        self, mock_provision, mock_counts
    ) -> None:
        from apps.owner.services.owner_access_service import OwnerAccessCounts

        owner_id = uuid4()
        mock_provision.return_value = (owner_id, True)
        mock_counts.return_value = OwnerAccessCounts(business_count=0, venue_count=0)
        ctx = _owner_context()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            response = self.client.post(
                "/api/v1/owner/provision",
                HTTP_AUTHORIZATION="Bearer valid",
            )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["created"])
        self.assertTrue(body["provisioned"])
        self.assertEqual(body["owner_account_id"], str(owner_id))
        self.assertIn(
            body["next_step"],
            ("owner_waiting_for_membership", "owner_waiting_for_venue_access", "portal_home"),
        )
        self.assertFalse(body["mfa_required"])

    @patch("apps.owner.services.owner_access_service.load_owner_access_counts")
    @patch("api.v1.owner.views.provision_owner_account")
    def test_provision_idempotent_returns_200(
        self, mock_provision, mock_counts
    ) -> None:
        from apps.owner.services.owner_access_service import OwnerAccessCounts

        owner_id = uuid4()
        mock_provision.return_value = (owner_id, False)
        mock_counts.return_value = OwnerAccessCounts(business_count=0, venue_count=0)
        ctx = _owner_context()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            response = self.client.post(
                "/api/v1/owner/provision",
                HTTP_AUTHORIZATION="Bearer valid",
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["created"])

    @patch("api.v1.owner.views.resolve_owner_auth_probe")
    def test_auth_probe_no_owner_returns_403(self, mock_probe) -> None:
        mock_probe.return_value = (
            {
                "authenticated": True,
                "owner_account_exists": False,
                "next_step": "complete_owner_provisioning",
            },
            403,
        )
        ctx = _owner_context()
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            response = self.client.get(
                "/api/v1/owner/auth-probe",
                HTTP_AUTHORIZATION="Bearer valid",
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"],
            "owner_not_provisioned",
        )

    @patch("api.v1.owner.views.resolve_owner_auth_probe")
    def test_auth_probe_ready_owner_returns_200(self, mock_probe) -> None:
        owner_id = uuid4()
        mock_probe.return_value = (
            {
                "authenticated": True,
                "owner_account_exists": True,
                "owner_account_active": True,
                "mfa_required": False,
                "mfa_enabled": True,
                "aal": "aal2",
                "owner_account_id": str(owner_id),
                "next_step": "portal_home",
                "business_count": 1,
                "venue_count": 2,
            },
            200,
        )
        ctx = _owner_context(aal="aal2")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            response = self.client.get(
                "/api/v1/owner/auth-probe",
                HTTP_AUTHORIZATION="Bearer valid",
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["next_step"], "portal_home")


@override_settings(
    SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys",
    PUBPLUS_OWNER_PROVISION_DISABLED=False,
)
class OwnerMfaGuardTests(SimpleTestCase):
    def test_owner_mfa_helper(self) -> None:
        from common.owner_mfa import (
            OWNER_MFA_REQUIRED,
            is_owner_mfa_enabled,
            is_owner_mfa_satisfied,
            resolve_aal,
        )

        self.assertFalse(OWNER_MFA_REQUIRED)
        self.assertEqual(resolve_aal({"aal": "aal2"}), "aal2")
        self.assertFalse(is_owner_mfa_satisfied({"aal": "aal1"}))
        self.assertTrue(is_owner_mfa_satisfied({"aal": "aal2"}))
        self.assertFalse(is_owner_mfa_enabled({"aal": "aal1"}))
        self.assertTrue(is_owner_mfa_enabled({"aal": "aal2"}))

    def test_resolve_owner_next_step_aal1_not_blocked(self) -> None:
        from apps.owner.services.owner_access_service import (
            OwnerAccessCounts,
            resolve_owner_next_step,
        )

        self.assertEqual(
            resolve_owner_next_step(
                claims={"aal": "aal1"},
                counts=OwnerAccessCounts(business_count=0, venue_count=0),
            ),
            "owner_waiting_for_membership",
        )
        self.assertEqual(
            resolve_owner_next_step(
                claims={"aal": "aal1"},
                counts=OwnerAccessCounts(business_count=1, venue_count=0),
            ),
            "owner_waiting_for_venue_access",
        )

    def test_require_owner_portal_auth_aal2_returns_mfa_required(self) -> None:
        from django.http import HttpResponse
        from django.test import RequestFactory

        from common.auth.guards import require_owner_portal_auth_aal2

        @require_owner_portal_auth_aal2
        def sample_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("ok")

        factory = RequestFactory()
        request = factory.get("/", HTTP_AUTHORIZATION="Bearer valid")
        ctx = _owner_context(aal="aal1")
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            with patch(
                "common.auth.guards.get_owner_account_id",
                return_value=uuid4(),
            ):
                response = sample_view(request)
        self.assertEqual(response.status_code, 403)
        import json

        body = json.loads(response.content)
        self.assertEqual(body["error"]["code"], "mfa_required")
