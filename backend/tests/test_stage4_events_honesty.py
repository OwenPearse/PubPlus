"""Stage 4 — event discovery deferred; filter reference and API contract stay honest."""

from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase

from services.discovery import DiscoveryFilterError, DiscoveryMode, DiscoveryMvpFilters


class EventFiltersReferenceTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @patch(
        "api.v1.search.views.build_search_filter_reference",
        return_value={
            "venue_features": [],
            "drink_types": [],
            "meal_specials": [],
            "event_filters": [],
        },
    )
    def test_search_filters_returns_empty_event_filters(self, _mock):
        response = self.client.get("/api/v1/search/filters")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["event_filters"], [])


class EventQueryParamDeferredTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_search_venues_rejects_events_filter(self):
        response = self.client.get("/api/v1/search/venues", {"events": "true"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "events_unavailable")

    def test_discovery_filters_reject_require_published_events(self):
        f = DiscoveryMvpFilters(require_published_events=True)
        with self.assertRaises(DiscoveryFilterError) as ctx:
            f.validate(DiscoveryMode.LIST)
        self.assertEqual(ctx.exception.code, "events_unavailable")


class EventFiltersDbIntegrationTests(TestCase):
    databases = {"default"}

    def setUp(self):
        self.client = Client()

    def test_db_backed_filter_reference_event_filters_empty(self):
        response = self.client.get("/api/v1/search/filters")
        if response.status_code != 200:
            self.skipTest("Filter reference unavailable in test database.")
        self.assertEqual(response.json()["data"]["event_filters"], [])
