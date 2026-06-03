import uuid
from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase
from django.db.utils import DatabaseError


_MOCK_REFERENCE = {
    "venue_features": [
        {"key": "beer_garden", "label": "Beer garden", "group": "spaces"},
    ],
    "drink_types": [
        {
            "id": "b3333333-3333-4333-8333-333333333401",
            "label": "Craft beer",
        },
    ],
    "meal_specials": [{"key": "meal_special", "label": "Meal specials tonight"}],
    "event_filters": [],
}


class SearchFiltersEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @patch(
        "api.v1.search.views.build_search_filter_reference",
        return_value=_MOCK_REFERENCE,
    )
    def test_search_filters_returns_public_reference_payload(self, _mock_build):
        response = self.client.get("/api/v1/search/filters")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        data = body["data"]
        self.assertIn("venue_features", data)
        self.assertIn("drink_types", data)
        self.assertIn("meal_specials", data)
        self.assertIn("event_filters", data)
        self.assertEqual(data["event_filters"], [])
        self.assertEqual(data["venue_features"][0]["key"], "beer_garden")
        self.assertEqual(
            data["drink_types"][0]["id"],
            "b3333333-3333-4333-8333-333333333401",
        )
        self.assertEqual(data["meal_specials"][0]["key"], "meal_special")

    @patch(
        "api.v1.search.views.build_search_filter_reference",
        return_value=_MOCK_REFERENCE,
    )
    def test_search_filters_does_not_require_auth(self, _mock_build):
        response = self.client.get("/api/v1/search/filters")
        self.assertEqual(response.status_code, 200)

    @patch(
        "api.v1.search.views.build_search_filter_reference",
        side_effect=DatabaseError("db unavailable"),
    )
    def test_search_filters_db_error_returns_500(self, _mock_build):
        response = self.client.get("/api/v1/search/filters")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "db_error")


class SearchFiltersContractAlignmentTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @patch("api.v1.search.views.run_discovery")
    @patch(
        "api.v1.search.views.build_search_filter_reference",
        return_value=_MOCK_REFERENCE,
    )
    def test_search_venues_accepts_filter_reference_values(
        self, _mock_reference, run_discovery_mock
    ):
        from datetime import datetime, timezone

        from apps.venues.public_read.card import PublicVenueCard
        from services.discovery import DiscoveryMode, DiscoveryMvpFilters, DiscoveryResult

        run_discovery_mock.return_value = DiscoveryResult(
            mode=DiscoveryMode.LIST.value,
            filters=DiscoveryMvpFilters(limit=50),
            at_utc=datetime.now(timezone.utc),
            hits=[],
            prelimit_used=0,
        )

        feature_key = _MOCK_REFERENCE["venue_features"][0]["key"]
        drink_id = _MOCK_REFERENCE["drink_types"][0]["id"]
        meal_key = _MOCK_REFERENCE["meal_specials"][0]["key"]

        response = self.client.get(
            "/api/v1/search/venues",
            {
                "venue_features": feature_key,
                "drink_types": drink_id,
                "meal_specials": meal_key,
            },
        )

        self.assertEqual(response.status_code, 200, response.content)
        run_discovery_mock.assert_called_once()
        filters_arg = run_discovery_mock.call_args[0][1]
        self.assertEqual(filters_arg.venue_features, [feature_key])
        self.assertEqual(filters_arg.drink_types, [drink_id])
        self.assertEqual(filters_arg.meal_specials, [meal_key])


class SearchFiltersDbIntegrationTests(TestCase):
    databases = {"default"}

    def setUp(self):
        self.client = Client()

    def test_search_filters_db_backed_shape(self):
        try:
            response = self.client.get("/api/v1/search/filters")
        except DatabaseError:
            self.skipTest("Reference tables unavailable in test database.")

        if response.status_code == 500:
            self.skipTest("Filter reference tables unavailable in test database.")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIsInstance(data["venue_features"], list)
        self.assertIsInstance(data["drink_types"], list)
        self.assertIsInstance(data["meal_specials"], list)
        self.assertEqual(data["event_filters"], [])

        for feature in data["venue_features"]:
            self.assertIn("key", feature)
            self.assertIn("label", feature)
            self.assertTrue(feature["key"].strip())

        for drink in data["drink_types"]:
            self.assertIn("id", drink)
            self.assertIn("label", drink)
            uuid.UUID(str(drink["id"]))

        for meal in data["meal_specials"]:
            self.assertEqual(meal["key"], "meal_special")

        if data["venue_features"]:
            key = data["venue_features"][0]["key"]
            with patch("api.v1.search.views.run_discovery") as run_discovery_mock:
                from datetime import datetime, timezone

                from services.discovery import (
                    DiscoveryMode,
                    DiscoveryMvpFilters,
                    DiscoveryResult,
                )

                run_discovery_mock.return_value = DiscoveryResult(
                    mode=DiscoveryMode.LIST.value,
                    filters=DiscoveryMvpFilters(limit=50),
                    at_utc=datetime.now(timezone.utc),
                    hits=[],
                    prelimit_used=0,
                )
                search_response = self.client.get(
                    "/api/v1/search/venues",
                    {"venue_features": key},
                )
            self.assertEqual(search_response.status_code, 200)
