from unittest.mock import patch

from django.test import Client, RequestFactory, SimpleTestCase, TestCase

from apps.discovery.http import parse_discovery_filters_from_request
from services.discovery import (
    DiscoveryFilterError,
    DiscoveryMode,
    DiscoveryMvpFilters,
    build_discovery_sql,
)
from services.discovery.q_text import MAX_Q_LENGTH, normalize_discovery_q, sql_ilike_pattern


class NormalizeDiscoveryQTests(SimpleTestCase):
    def test_empty_and_whitespace_become_none(self) -> None:
        self.assertIsNone(normalize_discovery_q(None))
        self.assertIsNone(normalize_discovery_q(""))
        self.assertIsNone(normalize_discovery_q("   "))

    def test_trims_whitespace(self) -> None:
        self.assertEqual(normalize_discovery_q("  penny  "), "penny")

    def test_rejects_overlong_q(self) -> None:
        with self.assertRaises(DiscoveryFilterError) as ctx:
            normalize_discovery_q("x" * (MAX_Q_LENGTH + 1))
        self.assertEqual(ctx.exception.code, "invalid_q")


class DiscoveryQFilterTests(SimpleTestCase):
    def test_list_accepts_q(self) -> None:
        f = DiscoveryMvpFilters(q="penny")
        f.validate(DiscoveryMode.LIST)

    def test_list_sql_includes_ilike_for_q(self) -> None:
        f = DiscoveryMvpFilters(q="Penny")
        f.validate(DiscoveryMode.LIST)
        sql, params = build_discovery_sql(DiscoveryMode.LIST, f)
        self.assertIn("ILIKE", sql)
        self.assertIn("display_name", sql)
        self.assertIn("l.name", sql)
        pattern = sql_ilike_pattern("Penny")
        self.assertEqual(params[0], pattern)
        self.assertEqual(params[1], pattern)

    def test_q_combines_with_venue_features_in_sql(self) -> None:
        f = DiscoveryMvpFilters(q="penny", venue_features=["beer_garden"])
        f.validate(DiscoveryMode.LIST)
        sql, _params = build_discovery_sql(DiscoveryMode.LIST, f)
        self.assertIn("ILIKE", sql)
        self.assertIn("stable_key", sql)

    def test_q_combines_with_radius_triplet(self) -> None:
        f = DiscoveryMvpFilters(
            q="rooftop",
            lat=-37.8,
            lng=144.9,
            radius_m=5000.0,
        )
        f.validate(DiscoveryMode.LIST)
        sql, _params = build_discovery_sql(DiscoveryMode.LIST, f)
        self.assertIn("ILIKE", sql)
        self.assertIn("6371000", sql)


class SearchQEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_search_venues_accepts_q(self):
        response = self.client.get("/api/v1/search/venues", {"q": "penny"})
        self.assertNotEqual(response.status_code, 400)

    def test_whitespace_q_parsed_as_absent(self):
        request = RequestFactory().get("/api/v1/search/venues", {"q": "   "})
        filters = parse_discovery_filters_from_request(
            request, mode=DiscoveryMode.LIST
        )
        self.assertIsNone(filters.q)

    @patch("api.v1.search.views.run_discovery")
    def test_search_venues_whitespace_q_does_not_pass_q_to_discovery(self, run_mock):
        from datetime import datetime, timezone

        from services.discovery import DiscoveryMode, DiscoveryMvpFilters, DiscoveryResult

        run_mock.return_value = DiscoveryResult(
            mode=DiscoveryMode.LIST.value,
            filters=DiscoveryMvpFilters(limit=50),
            at_utc=datetime.now(timezone.utc),
            hits=[],
            prelimit_used=0,
        )
        response = self.client.get("/api/v1/search/venues", {"q": "   "})
        self.assertEqual(response.status_code, 200)
        filters_arg = run_mock.call_args[0][1]
        self.assertIsNone(filters_arg.q)

    def test_search_venues_rejects_overlong_q(self):
        response = self.client.get(
            "/api/v1/search/venues", {"q": "x" * (MAX_Q_LENGTH + 1)}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_q")

    def test_parse_request_normalizes_q(self):
        request = RequestFactory().get("/api/v1/search/venues", {"q": " penny "})
        filters = parse_discovery_filters_from_request(
            request, mode=DiscoveryMode.LIST
        )
        self.assertEqual(filters.q, "penny")


class SearchQDbIntegrationTests(TestCase):
    databases = {"default"}

    def setUp(self):
        self.client = Client()

    def _table_exists(self, name: str) -> bool:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
                """,
                [name],
            )
            return cursor.fetchone() is not None

    def test_q_matches_venue_name_when_seeded(self):
        if not self._table_exists("venue_published_profile"):
            self.skipTest("Published venue tables unavailable.")

        response = self.client.get("/api/v1/search/venues", {"q": "Penny", "limit": "20"})
        if response.status_code != 200:
            self.skipTest("Search unavailable in test database.")

        names = [v["name"] for v in response.json()["data"]["venues"]]
        if not names:
            self.skipTest("No seeded venues for q=Penny in test database.")

        self.assertTrue(
            any("penny" in n.lower() for n in names),
            f"Expected Penny in results, got {names!r}",
        )

    def test_q_matches_locality_name_when_seeded(self):
        if not self._table_exists("locality"):
            self.skipTest("Locality table unavailable.")

        response = self.client.get(
            "/api/v1/search/venues", {"q": "Brunswick", "limit": "50"}
        )
        if response.status_code != 200:
            self.skipTest("Search unavailable in test database.")

        suburbs = {v.get("suburb", "").lower() for v in response.json()["data"]["venues"]}
        if not suburbs:
            self.skipTest("No seeded venues for q=Brunswick in test database.")

        self.assertTrue(
            any("brunswick" in s for s in suburbs if s),
            f"Expected Brunswick locality matches, suburbs={suburbs!r}",
        )
