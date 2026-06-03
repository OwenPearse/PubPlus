from __future__ import annotations

from django.db import connection
from django.db.utils import DatabaseError
from django.test import TestCase


class StageBDbBackedContractsTests(TestCase):
    def _seeded_venue_id(self) -> str | None:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT v.id::text
                    FROM public.venue v
                    INNER JOIN public.venue_published_profile vpp
                      ON vpp.venue_id = v.id
                     AND vpp.discovery_eligibility_status IN ('eligible', 'limited')
                    WHERE v.id::text LIKE 'f1111111-1111-4111-8111-0000%'
                    ORDER BY v.id::text
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
        except DatabaseError:
            self.skipTest("DB-backed published tables unavailable in this test environment.")

        return row[0] if row else None

    def _assert_seed_presence(self) -> str:
        venue_id = self._seeded_venue_id()
        if venue_id is None:
            self.skipTest("No seeded Melbourne data available in test DB.")
        return venue_id

    def test_search_map_and_detail_db_backed_contracts(self):
        venue_id = self._assert_seed_presence()

        search_response = self.client.get(
            "/api/v1/search/venues",
            {"suburb": "Melbourne", "limit": "20"},
        )
        self.assertEqual(search_response.status_code, 200)
        search_body = search_response.json()
        search_venues = search_body["data"]["venues"]
        self.assertGreaterEqual(len(search_venues), 1)
        self.assertTrue(any(v["id"] == venue_id for v in search_venues))
        self.assertTrue(all("open_now" in v for v in search_venues))
        self.assertTrue(all("open_now_uncomputed" in v for v in search_venues))

        radius_response = self.client.get(
            "/api/v1/search/venues",
            {
                "lat": "-37.8136",
                "lng": "144.9631",
                "radius_m": "5000",
                "limit": "20",
            },
        )
        self.assertEqual(radius_response.status_code, 200)
        radius_venues = radius_response.json()["data"]["venues"]
        self.assertGreaterEqual(len(radius_venues), 1)
        self.assertTrue(all("distance_m" in v for v in radius_venues))

        map_response = self.client.get(
            "/api/v1/map/venues",
            {
                "south": "-37.87",
                "north": "-37.76",
                "west": "144.92",
                "east": "145.05",
                "limit": "20",
            },
        )
        self.assertEqual(map_response.status_code, 200)
        map_venues = map_response.json()["data"]["venues"]
        self.assertGreaterEqual(len(map_venues), 1)
        marker = map_venues[0]
        self.assertIn("latitude", marker)
        self.assertIn("longitude", marker)
        self.assertNotIn("feature_badges", marker)
        self.assertNotIn("address_short", marker)

        detail_response = self.client.get(f"/api/v1/venues/{venue_id}")
        self.assertEqual(detail_response.status_code, 200)
        detail_body = detail_response.json()["data"]
        self.assertEqual(detail_body["identity"]["id"], venue_id)
        self.assertIn("open_now", detail_body["hours"])
        self.assertIn("open_now_uncomputed", detail_body["hours"])

    def test_home_db_backed_sections_and_open_now_shape(self):
        self._assert_seed_presence()

        response = self.client.get(
            "/api/v1/home",
            {"suburb": "Melbourne", "limit": "12"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        sections = body["data"]["sections"]
        section_ids = [s["id"] for s in sections]
        self.assertEqual(section_ids, ["nearby", "open_now", "specials_tonight"])
        self.assertNotIn("events_tonight", section_ids)

        for section in sections:
            for venue in section["venues"]:
                self.assertIn("open_now", venue)
                self.assertIn("open_now_uncomputed", venue)

    def test_public_stage_b_endpoints_remain_accessible_with_optional_auth_header(self):
        venue_id = self._assert_seed_presence()
        auth_header = {"HTTP_AUTHORIZATION": "Bearer invalid-token"}

        search_response = self.client.get("/api/v1/search/venues", {"suburb": "Melbourne"}, **auth_header)
        self.assertEqual(search_response.status_code, 200)

        map_response = self.client.get(
            "/api/v1/map/venues",
            {"south": "-37.87", "north": "-37.76", "west": "144.92", "east": "145.05"},
            **auth_header,
        )
        self.assertEqual(map_response.status_code, 200)

        detail_response = self.client.get(f"/api/v1/venues/{venue_id}", **auth_header)
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn("authenticated_actions", detail_response.json()["data"])

        home_response = self.client.get("/api/v1/home", {"suburb": "Melbourne"}, **auth_header)
        self.assertEqual(home_response.status_code, 200)
        self.assertIn("sections", home_response.json()["data"])
