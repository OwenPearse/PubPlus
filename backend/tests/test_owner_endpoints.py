from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

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

    @patch("api.v1.owner.views.provision_owner_account")
    def test_provision_success_created_returns_201(self, mock_provision) -> None:
        owner_id = uuid4()
        mock_provision.return_value = (owner_id, True)
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
        self.assertEqual(body["next_step"], "enroll_mfa")

    @patch("api.v1.owner.views.provision_owner_account")
    def test_provision_idempotent_returns_200(self, mock_provision) -> None:
        owner_id = uuid4()
        mock_provision.return_value = (owner_id, False)
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
                "mfa_required": True,
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
        from common.owner_mfa import is_owner_mfa_satisfied, resolve_aal

        self.assertEqual(resolve_aal({"aal": "aal2"}), "aal2")
        self.assertFalse(is_owner_mfa_satisfied({"aal": "aal1"}))
        self.assertTrue(is_owner_mfa_satisfied({"aal": "aal2"}))
