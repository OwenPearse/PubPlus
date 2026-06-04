from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase
from django.db.utils import DatabaseError

from apps.venues.public_read.card import PublicVenueCard
from apps.venues.services.published_venue_read import load_published_venue_read_bundle
from common.auth.context import AuthContext
from services.discovery import DiscoveryHit, DiscoveryMode, DiscoveryMvpFilters, DiscoveryResult
from services.discovery.open_now import OpenNowInternalState, OpenNowResult
from services.home_feed.service import HomeFeedQuery, HomeFeedResult, HomeFeedSection


def _sample_card() -> PublicVenueCard:
    return PublicVenueCard(
        id="11111111-1111-4111-8111-111111111111",
        name="Venue One",
        venue_type="pub",
        suburb="Melbourne",
        address_short="1 Test St",
        latitude=-37.81,
        longitude=144.96,
        hero_photo_url="https://example.com/hero.jpg",
        open_now=True,
        open_now_uncomputed=False,
        distance_m=80.0,
        feature_badges=["Late night"],
        specials_summary=["Steak night"],
        events_summary=[],
        drink_highlights=["House lager"],
        is_saved=None,
    )


def _home_result() -> HomeFeedResult:
    card = _sample_card()
    return HomeFeedResult(
        sections=[
            HomeFeedSection(id="nearby", title="Nearby", items=[card]),
            HomeFeedSection(id="open_now", title="Open now", items=[card]),
            HomeFeedSection(id="specials_tonight", title="Specials tonight", items=[card]),
        ]
    )


class VenueDetailEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @patch("api.v1.venues.views.public_venue_detail_dict")
    def test_venue_detail_success_path(self, detail_mock):
        detail_mock.return_value = {
            "identity": {"id": "v1", "name": "Venue One", "slug": "venue-one"},
            "hours": {"open_now": True, "open_now_uncomputed": False, "regular": [], "exceptions": []},
            "events": {"items": [], "not_implemented": True},
            "contact": {"items": [], "not_implemented": True},
            "authenticated_actions": {"can_save": False, "is_saved": None, "save_requires_auth": True},
        }

        response = self.client.get("/api/v1/venues/v1")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["identity"]["id"], "v1")
        self.assertIn("open_now", body["data"]["hours"])
        self.assertTrue(body["data"]["events"]["not_implemented"])
        self.assertTrue(body["data"]["contact"]["not_implemented"])

    @patch("api.v1.venues.views.public_venue_detail_dict", return_value=None)
    def test_venue_detail_not_found_path(self, _detail_mock):
        response = self.client.get("/api/v1/venues/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "venue_not_found")

    @patch(
        "common.auth.guards.verify_supabase_jwt",
        return_value=AuthContext(
            subject="consumer-123",
            audience="authenticated",
            issuer="https://example.supabase.co/auth/v1",
            role="authenticated",
            email="consumer@example.com",
            claims={"sub": "consumer-123"},
        ),
    )
    @patch("api.v1.venues.views.public_venue_detail_dict")
    def test_venue_detail_optional_authenticated_enrichment_shape_stable(
        self, detail_mock, _verify_token_mock
    ):
        detail_mock.return_value = {
            "identity": {"id": "v1", "name": "Venue One"},
            "hours": {"open_now": False, "open_now_uncomputed": False, "regular": [], "exceptions": []},
            "authenticated_actions": {"can_save": True, "is_saved": True, "save_requires_auth": False},
        }

        response = self.client.get(
            "/api/v1/venues/v1",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("authenticated_actions", response.json()["data"])


class HomeEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @patch("api.v1.home.views.run_home_feed")
    def test_home_success_path(self, home_mock):
        home_mock.return_value = _home_result()

        response = self.client.get("/api/v1/home")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["meta"]["sections"], ["nearby", "open_now", "specials_tonight"])
        sections = {s["id"]: s for s in body["data"]["sections"]}
        self.assertIn("nearby", sections)
        self.assertIn("open_now", sections)
        self.assertIn("specials_tonight", sections)
        self.assertNotIn("events_tonight", sections)
        self.assertNotIn("for_you", sections)
        self.assertIn("open_now", sections["open_now"]["venues"][0])

    @patch("api.v1.home.views.run_home_feed")
    def test_home_unauthenticated_public_access(self, home_mock):
        home_mock.return_value = _home_result()

        response = self.client.get("/api/v1/home")

        self.assertEqual(response.status_code, 200)
        venues = response.json()["data"]["sections"][0]["venues"]
        self.assertIsNone(venues[0]["is_saved"])

    @patch("api.v1.home.views.run_home_feed")
    def test_home_default_limit_is_three_per_section(self, home_mock):
        home_mock.return_value = _home_result()

        response = self.client.get("/api/v1/home")

        self.assertEqual(response.status_code, 200)
        query_arg = home_mock.call_args[0][0]
        self.assertEqual(query_arg.limit, 3)

    @patch("api.v1.home.views.run_home_feed")
    def test_home_explicit_limit_three_allowed(self, home_mock):
        home_mock.return_value = _home_result()

        response = self.client.get("/api/v1/home", {"limit": "3"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(home_mock.call_args[0][0].limit, 3)

    @patch("api.v1.home.views.run_home_feed")
    def test_home_passes_query_params_to_service(self, home_mock):
        home_mock.return_value = _home_result()

        response = self.client.get(
            "/api/v1/home",
            {"lat": "-37.81", "lng": "144.96", "radius_m": "3000", "limit": "6", "suburb": "Melbourne"},
        )

        self.assertEqual(response.status_code, 200)
        query_arg = home_mock.call_args[0][0]
        self.assertIsInstance(query_arg, HomeFeedQuery)
        self.assertEqual(query_arg.limit, 6)
        self.assertEqual(query_arg.suburb, "Melbourne")

    @patch("api.v1.home.views.run_home_feed")
    def test_home_explicit_limit_six_allowed(self, home_mock):
        home_mock.return_value = _home_result()

        response = self.client.get("/api/v1/home", {"limit": "6"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(home_mock.call_args[0][0].limit, 6)

    def test_home_limit_seven_returns_400(self):
        response = self.client.get("/api/v1/home", {"limit": "7"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_limit")


class HomeFeedServiceTests(SimpleTestCase):
    @patch("services.home_feed.service.run_discovery")
    def test_home_service_sections_are_orchestrated_not_flat(self, run_discovery_mock):
        card = _sample_card()
        open_res = OpenNowResult(
            internal=OpenNowInternalState.DETERMINABLE_OPEN,
            public_open_now=True,
            public_open_now_uncomputed=False,
        )
        hit = DiscoveryHit(
            venue_id=card.id,
            distance_m=card.distance_m,
            open_now=card.open_now,
            open_now_uncomputed=card.open_now_uncomputed,
            open_now_result=open_res,
            rank_score=1.0,
            rank_components={},
            card=card,
            source_mode=DiscoveryMode.LIST.value,
        )
        result = DiscoveryResult(
            mode=DiscoveryMode.LIST.value,
            filters=DiscoveryMvpFilters(limit=12),
            at_utc=datetime.now(timezone.utc),
            hits=[hit],
            prelimit_used=1,
        )
        run_discovery_mock.side_effect = [result, result, result]

        from services.home_feed import run_home_feed

        output = run_home_feed(HomeFeedQuery(limit=12))

        self.assertEqual([s.id for s in output.sections], ["nearby", "open_now", "specials_tonight"])
        self.assertEqual(run_discovery_mock.call_count, 3)
        self.assertTrue(run_discovery_mock.call_args_list[1].args[1].open_now)

    @patch("apps.venues.services.save_enrichment.apply_save_to_cards")
    @patch("services.home_feed.service.run_discovery")
    def test_home_service_optional_authenticated_enrichment(
        self,
        run_discovery_mock,
        apply_save_mock,
    ):
        card = _sample_card()
        result = DiscoveryResult(
            mode=DiscoveryMode.LIST.value,
            filters=DiscoveryMvpFilters(limit=12),
            at_utc=datetime.now(timezone.utc),
            hits=[
                DiscoveryHit(
                    venue_id=card.id,
                    distance_m=card.distance_m,
                    open_now=card.open_now,
                    open_now_uncomputed=card.open_now_uncomputed,
                    open_now_result=OpenNowResult(
                        internal=OpenNowInternalState.DETERMINABLE_OPEN,
                        public_open_now=True,
                        public_open_now_uncomputed=False,
                    ),
                    rank_score=1.0,
                    rank_components={},
                    card=card,
                    source_mode=DiscoveryMode.LIST.value,
                )
            ],
            prelimit_used=1,
        )
        run_discovery_mock.side_effect = [result, result, result]
        apply_save_mock.return_value = [replace(card, is_saved=True)]

        from services.home_feed import run_home_feed

        auth = AuthContext(
            subject="consumer-123",
            audience="authenticated",
            issuer="https://example.supabase.co/auth/v1",
            role="authenticated",
            email="consumer@example.com",
            claims={"sub": "consumer-123"},
        )
        output = run_home_feed(HomeFeedQuery(limit=12), auth=auth)

        self.assertTrue(output.sections[0].items[0].is_saved)
        apply_save_mock.assert_called_once()


class VenueDetailDbBackedTests(TestCase):
    def test_db_backed_detail_has_open_now_fields_when_seed_data_present(self):
        # If no seeded published venue is available in the test DB, skip.
        from django.db import connection

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT v.id::text
                    FROM public.venue v
                    INNER JOIN public.venue_published_profile vpp
                      ON vpp.venue_id = v.id
                     AND vpp.discovery_eligibility_status IN ('eligible', 'limited')
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
        except DatabaseError:
            self.skipTest("DB-backed published tables unavailable in this test environment.")

        if not row:
            self.skipTest("No seeded published venue data available in test DB.")

        venue_id = row[0]
        response = self.client.get(f"/api/v1/venues/{venue_id}")
        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]["hours"]
        self.assertIn("open_now", payload)
        self.assertIn("open_now_uncomputed", payload)

        bundle = load_published_venue_read_bundle(venue_id)
        self.assertIsNotNone(bundle)
