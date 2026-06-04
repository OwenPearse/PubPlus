from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from apps.venues.public_read.card import PublicVenueCard
from apps.venues.services.save_enrichment import (
    apply_save_to_cards,
    map_venue_ids_in_any_user_list,
)
from common.auth.context import AuthContext


def _card(venue_id: str) -> PublicVenueCard:
    return PublicVenueCard(
        id=venue_id,
        name="Venue",
        venue_type="pub",
        suburb="Melbourne",
        address_short="1 St",
        latitude=-37.81,
        longitude=144.96,
        hero_photo_url=None,
    )


class SaveEnrichmentBatchTests(SimpleTestCase):
    @patch("apps.venues.services.save_enrichment.map_venue_ids_in_any_user_list")
    def test_apply_save_to_cards_uses_single_lookup(self, saved_map_mock):
        saved_map_mock.return_value = {
            "11111111-1111-4111-8111-111111111111": True,
            "22222222-2222-4222-8222-222222222222": False,
        }
        auth = AuthContext(
            subject="consumer-123",
            audience="authenticated",
            issuer="https://example.supabase.co/auth/v1",
            role="authenticated",
            email="consumer@example.com",
            claims={"sub": "consumer-123"},
        )
        cards = [
            _card("11111111-1111-4111-8111-111111111111"),
            _card("22222222-2222-4222-8222-222222222222"),
        ]

        enriched = apply_save_to_cards(cards, auth=auth)

        saved_map_mock.assert_called_once()
        self.assertTrue(enriched[0].is_saved)
        self.assertFalse(enriched[1].is_saved)

    @patch("apps.venues.services.save_enrichment.connection")
    def test_map_venue_ids_in_any_user_list_batches_query(self, connection_mock):
        cursor = connection_mock.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            ("11111111-1111-4111-8111-111111111111",),
        ]
        auth = AuthContext(
            subject="consumer-123",
            audience="authenticated",
            issuer="https://example.supabase.co/auth/v1",
            role="authenticated",
            email="consumer@example.com",
            claims={"sub": "consumer-123"},
        )

        result = map_venue_ids_in_any_user_list(
            venue_ids=[
                "11111111-1111-4111-8111-111111111111",
                "22222222-2222-4222-8222-222222222222",
            ],
            auth=auth,
        )

        self.assertEqual(cursor.execute.call_count, 1)
        self.assertTrue(result["11111111-1111-4111-8111-111111111111"])
        self.assertFalse(result["22222222-2222-4222-8222-222222222222"])
