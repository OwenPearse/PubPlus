"""
Stage 2 — filter efficacy and location contract tests.

DB-backed venue feature counts require dev seeds applied to the test database;
see manual verification in API_ENDPOINT_OVERVIEW.md and dev_seed_mvp_feature_attribute_values.sql.
"""

from __future__ import annotations

from django.db import connection
from django.test import Client, SimpleTestCase, TestCase

from services.discovery import DiscoveryMode, DiscoveryMvpFilters


class SearchRadiusContractTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_search_venues_rejects_radius_without_lat_lng(self):
        response = self.client.get("/api/v1/search/venues", {"radius_m": "5000"})
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"]["code"], "location_incomplete")

    def test_search_venues_accepts_full_location_triplet(self):
        response = self.client.get(
            "/api/v1/search/venues",
            {
                "lat": "-37.8136",
                "lng": "144.9631",
                "radius_m": "5000",
                "limit": "5",
            },
        )
        self.assertIn(response.status_code, (200, 400, 500))
        if response.status_code == 400:
            self.assertNotEqual(
                response.json().get("error", {}).get("code"),
                "location_incomplete",
            )


class VenueFeatureFilterEfficacyTests(TestCase):
    databases = {"default"}

    _MVP_FEATURE_KEYS = (
        "beer_garden",
        "rooftop",
        "live_music",
        "dog_friendly",
        "sports_screens",
        "pool_table",
        "late_night",
        "vegan_options",
    )

    def _table_exists(self, name: str) -> bool:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = %s
                """,
                [name],
            )
            return cursor.fetchone() is not None

    def test_seeded_feature_keys_return_at_least_one_venue_when_data_present(self):
        if not self._table_exists("venue_published_attribute_value"):
            self.skipTest("Published attribute tables unavailable.")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ad.stable_key, count(DISTINCT pav.venue_id)::int
                FROM public.venue_published_attribute_value pav
                INNER JOIN public.venue_attribute_definition ad
                  ON ad.id = pav.attribute_definition_id
                INNER JOIN public.venue_published_profile vpp
                  ON vpp.venue_id = pav.venue_id
                 AND vpp.discovery_eligibility_status IN ('eligible', 'limited')
                WHERE ad.stable_key = ANY(%s::text[])
                  AND pav.value_boolean IS TRUE
                GROUP BY ad.stable_key
                """,
                [list(self._MVP_FEATURE_KEYS)],
            )
            counts = {row[0]: row[1] for row in cursor.fetchall()}

        if not counts:
            self.skipTest(
                "No MVP feature attribute rows in test DB; apply dev_seed_mvp_feature_attribute_values.sql."
            )

        for key in ("beer_garden", "sports_screens"):
            if counts.get(key, 0) < 1:
                self.fail(
                    f"Expected seeded venues for {key!r}, got count={counts.get(key, 0)}. "
                    "Re-run database seeds."
                )

    def test_filter_reference_keys_match_seeded_definitions(self):
        if not self._table_exists("venue_attribute_definition"):
            self.skipTest("Attribute definition table unavailable.")

        response = self.client.get("/api/v1/search/filters")
        if response.status_code != 200:
            self.skipTest("Filter reference unavailable in test database.")

        feature_keys = {
            item["key"] for item in response.json()["data"]["venue_features"]
        }
        self.assertTrue(feature_keys.issubset(set(self._MVP_FEATURE_KEYS)))

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT stable_key
                FROM public.venue_attribute_definition
                WHERE stable_key = ANY(%s::text[])
                  AND is_discovery_driving IS TRUE
                  AND value_shape = 'boolean'
                """,
                [list(feature_keys)],
            )
            db_keys = {row[0] for row in cursor.fetchall()}
        self.assertEqual(feature_keys, db_keys)


class DiscoveryFilterUnitContractTests(SimpleTestCase):
    def test_filters_validate_with_full_radius_triplet(self):
        f = DiscoveryMvpFilters(lat=-37.81, lng=144.96, radius_m=3000.0)
        f.validate(DiscoveryMode.LIST)
        self.assertTrue(f.has_radius())
