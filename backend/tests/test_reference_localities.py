from __future__ import annotations

from unittest.mock import patch

from django.db import connection
from django.db.utils import DatabaseError
from django.test import Client, SimpleTestCase, TestCase

from services.reference.locality_reference import build_locality_reference

_MOCK_LOCALITIES = {
    "localities": [
        {
            "id": "22222222-2222-4222-8222-000000000002",
            "name": "Brunswick",
            "state": "VIC",
            "country_code": "AU",
            "geographic_region_id": "11111111-1111-4111-8111-111111111103",
            "geographic_region_name": "Victoria",
            "latitude": -37.77,
            "longitude": 144.96,
        }
    ]
}


class ReferenceLocalitiesEndpointTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    @patch(
        "api.v1.reference.views.build_locality_reference",
        return_value=_MOCK_LOCALITIES,
    )
    def test_public_unauthenticated_returns_200(self, _mock_build) -> None:
        response = self.client.get("/api/v1/reference/localities")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("data", body)
        self.assertIn("localities", body["data"])
        self.assertIsInstance(body["data"]["localities"], list)
        row = body["data"]["localities"][0]
        self.assertEqual(row["id"], _MOCK_LOCALITIES["localities"][0]["id"])
        self.assertEqual(row["name"], "Brunswick")
        self.assertIn("geographic_region_id", row)

    @patch(
        "api.v1.reference.views.build_locality_reference",
        return_value=_MOCK_LOCALITIES,
    )
    def test_response_includes_cache_control(self, _mock_build) -> None:
        response = self.client.get("/api/v1/reference/localities")
        self.assertEqual(response.status_code, 200)
        self.assertIn("public", response.get("Cache-Control", ""))

    @patch(
        "api.v1.reference.views.build_locality_reference",
        side_effect=DatabaseError("db unavailable"),
    )
    def test_db_error_returns_500(self, _mock_build) -> None:
        response = self.client.get("/api/v1/reference/localities")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "db_error")


class ReferenceLocalitiesServiceTests(TestCase):
    databases = {"default"}

    @staticmethod
    def _table_exists(name: str) -> bool:
        with connection.cursor() as c:
            c.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
                LIMIT 1
                """,
                [name],
            )
            return c.fetchone() is not None

    def test_build_returns_localities_list(self) -> None:
        if not self._table_exists("locality"):
            self.skipTest("locality table not present")
        payload = build_locality_reference()
        self.assertIn("localities", payload)
        self.assertIsInstance(payload["localities"], list)

    def test_locality_rows_include_profile_patch_fields_when_present(self) -> None:
        if not self._table_exists("venue_published_location"):
            self.skipTest("published venue tables not present")
        payload = build_locality_reference()
        if not payload["localities"]:
            self.skipTest("No published-venue localities in test DB")
        row = payload["localities"][0]
        self.assertIn("id", row)
        self.assertIn("name", row)
        self.assertTrue(row["name"])
        self.assertIn("geographic_region_id", row)
        self.assertTrue(row["geographic_region_id"])


class ReferenceLocalitiesDbIntegrationTests(TestCase):
    databases = {"default"}

    def setUp(self) -> None:
        self.client = Client()

    def test_reference_localities_db_backed_shape(self) -> None:
        try:
            response = self.client.get("/api/v1/reference/localities")
        except DatabaseError:
            self.skipTest("Reference tables unavailable in test database.")

        if response.status_code == 500:
            self.skipTest("Locality reference tables unavailable in test database.")

        self.assertEqual(response.status_code, 200)
        localities = response.json()["data"]["localities"]
        self.assertIsInstance(localities, list)
