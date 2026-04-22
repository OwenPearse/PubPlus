from unittest.mock import patch

from django.test import Client, SimpleTestCase

from common.auth.context import AuthContext
from common.auth.errors import InvalidTokenError


class AuthBoundaryEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_private_endpoint_without_token_returns_401(self):
        response = self.client.get("/api/v1/auth-probe/private")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "unauthorized")

    def test_private_endpoint_with_invalid_token_returns_401(self):
        with patch(
            "common.auth.guards.verify_supabase_jwt",
            side_effect=InvalidTokenError("bad token"),
        ):
            response = self.client.get(
                "/api/v1/auth-probe/private",
                HTTP_AUTHORIZATION="Bearer invalid",
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "unauthorized")

    def test_private_endpoint_with_valid_verified_token_is_allowed(self):
        verified_context = AuthContext(
            subject="consumer-user-123",
            audience="authenticated",
            issuer="https://example.supabase.co/auth/v1",
            role="authenticated",
            email="consumer@example.com",
            claims={"sub": "consumer-user-123"},
        )
        with patch("common.auth.guards.verify_supabase_jwt", return_value=verified_context):
            response = self.client.get(
                "/api/v1/auth-probe/private",
                HTTP_AUTHORIZATION="Bearer valid-token",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "subject": "consumer-user-123"},
        )

    def test_public_endpoint_accessible_without_auth(self):
        response = self.client.get("/api/v1/auth-probe/public")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "authenticated": False},
        )
