from datetime import datetime, timezone
from unittest.mock import patch

from django.test import Client, SimpleTestCase

from apps.venues.public_read.card import PublicVenueCard
from common.auth.context import AuthContext
from services.discovery import (
    DiscoveryFilterError,
    DiscoveryHit,
    DiscoveryMode,
    DiscoveryMvpFilters,
    DiscoveryResult,
)
from services.discovery.open_now import OpenNowInternalState, OpenNowResult


def _result(mode: DiscoveryMode) -> DiscoveryResult:
    card = PublicVenueCard(
        id="11111111-1111-4111-8111-111111111111",
        name="Test Venue",
        venue_type="bar",
        suburb="Melbourne",
        address_short="1 Test St",
        latitude=-37.81,
        longitude=144.96,
        hero_photo_url="https://example.com/hero.jpg",
        open_now=True,
        open_now_uncomputed=False,
        distance_m=120.2,
        feature_badges=["Late night"],
        specials_summary=["$10 special"],
        events_summary=["Live jazz"],
        drink_highlights=["House IPA"],
        is_saved=None,
    )
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
        source_mode=mode.value,
    )
    filters = DiscoveryMvpFilters(
        south=-38.0,
        north=-37.0,
        west=144.0,
        east=145.0,
        limit=50,
    )
    if mode == DiscoveryMode.LIST:
        filters = DiscoveryMvpFilters(suburb="Melbourne", limit=50)
    return DiscoveryResult(
        mode=mode.value,
        filters=filters,
        at_utc=datetime.now(timezone.utc),
        hits=[hit],
        prelimit_used=1,
    )


class DiscoveryPublicEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @patch("api.v1.search.views.run_discovery")
    def test_search_public_allows_unauthenticated_access(self, run_discovery_mock):
        run_discovery_mock.return_value = _result(DiscoveryMode.LIST)

        response = self.client.get("/api/v1/search/venues")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["meta"]["mode"], "list")
        self.assertEqual(len(body["data"]["venues"]), 1)
        self.assertIsNone(body["data"]["venues"][0]["is_saved"])

    @patch("api.v1.map.views.run_discovery")
    def test_map_public_allows_unauthenticated_access(self, run_discovery_mock):
        run_discovery_mock.return_value = _result(DiscoveryMode.MAP)

        response = self.client.get(
            "/api/v1/map/venues",
            {"south": "-38", "north": "-37", "west": "144", "east": "145"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["meta"]["mode"], "map")
        marker = body["data"]["venues"][0]
        self.assertIn("latitude", marker)
        self.assertNotIn("feature_badges", marker)
        self.assertNotIn("address_short", marker)

    @patch("api.v1.search.views.run_discovery")
    def test_search_calls_shared_core_in_list_mode(self, run_discovery_mock):
        run_discovery_mock.return_value = _result(DiscoveryMode.LIST)

        response = self.client.get(
            "/api/v1/search/venues",
            {"suburb": "Melbourne", "open_now": "true", "limit": "20"},
        )

        self.assertEqual(response.status_code, 200)
        run_discovery_mock.assert_called_once()
        mode_arg, filters_arg = run_discovery_mock.call_args[0]
        self.assertEqual(mode_arg, DiscoveryMode.LIST)
        self.assertIsInstance(filters_arg, DiscoveryMvpFilters)
        self.assertEqual(filters_arg.suburb, "Melbourne")
        self.assertTrue(filters_arg.open_now)
        self.assertEqual(filters_arg.limit, 20)

    @patch("api.v1.map.views.run_discovery")
    def test_map_calls_shared_core_in_map_mode(self, run_discovery_mock):
        run_discovery_mock.return_value = _result(DiscoveryMode.MAP)

        response = self.client.get(
            "/api/v1/map/venues",
            {"south": "-38", "north": "-37", "west": "144", "east": "145", "limit": "30"},
        )

        self.assertEqual(response.status_code, 200)
        run_discovery_mock.assert_called_once()
        mode_arg, filters_arg = run_discovery_mock.call_args[0]
        self.assertEqual(mode_arg, DiscoveryMode.MAP)
        self.assertEqual(filters_arg.limit, 30)

    def test_validation_rejects_unsupported_param(self):
        response = self.client.get("/api/v1/search/venues", {"foo": "bar"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "unsupported_param")

    def test_validation_rejects_open_now_false(self):
        response = self.client.get("/api/v1/search/venues", {"open_now": "false"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"]["code"], "open_now_false_unsupported"
        )

    def test_validation_accepts_q_and_rejects_events(self):
        q_response = self.client.get("/api/v1/search/venues", {"q": "beer"})
        events_response = self.client.get("/api/v1/search/venues", {"events": "true"})

        self.assertNotEqual(q_response.json().get("error", {}).get("code"), "q_unsupported")
        self.assertEqual(events_response.status_code, 400)
        self.assertEqual(events_response.json()["error"]["code"], "events_unavailable")

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
    @patch("apps.venues.services.save_enrichment.apply_save_to_cards")
    @patch("api.v1.search.views.run_discovery")
    def test_authenticated_enrichment_is_optional(
        self,
        run_discovery_mock,
        apply_save_mock,
        _verify_token_mock,
    ):
        base = _result(DiscoveryMode.LIST)
        run_discovery_mock.return_value = base
        saved_card = base.hits[0].card
        saved_card.is_saved = True
        apply_save_mock.return_value = [saved_card]

        response = self.client.get(
            "/api/v1/search/venues",
            HTTP_AUTHORIZATION="Bearer valid-token",
        )

        self.assertEqual(response.status_code, 200)
        apply_save_mock.assert_called_once()
        self.assertEqual(response.json()["data"]["venues"][0]["is_saved"], True)

    @patch("api.v1.map.views.run_discovery")
    def test_discovery_filter_errors_map_to_stable_http_error(self, run_discovery_mock):
        run_discovery_mock.side_effect = DiscoveryFilterError(
            "invalid_limit", "limit must be between 1 and 200"
        )

        response = self.client.get(
            "/api/v1/map/venues",
            {"south": "-38", "north": "-37", "west": "144", "east": "145"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_limit")
