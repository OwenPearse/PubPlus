from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase

from apps.venues.services.published_venue_read import (
    PublishedCoreRow,
    PublishedDescriptiveRow,
    PublishedSpecialRow,
    PublishedTapRow,
    PublishedVenueReadBundle,
    load_published_venue_read_bundle,
    load_published_venue_read_bundles,
)
from apps.venues.services.venue_read_service import bundle_to_public_venue_card


def _sample_bundle(venue_id: str = "11111111-1111-4111-8111-111111111111") -> PublishedVenueReadBundle:
    core = PublishedCoreRow(
        venue_id=venue_id,
        display_name="Venue One",
        slug="venue-one",
        operational_status="open",
        suburb_name="Melbourne",
        address_line_1="1 Test St",
        address_line_2=None,
        postal_code="3000",
        country_code="AU",
        latitude=-37.81,
        longitude=144.96,
    )
    return PublishedVenueReadBundle(
        core=core,
        descriptive=PublishedDescriptiveRow("Short", "Long"),
        attributes=[],
        hours_regular=[],
        hours_exceptions=[],
        specials=[
            PublishedSpecialRow(
                id="a" * 36,
                structured_kind="meal_special",
                short_label="Steak",
                headline="Steak night",
            )
        ],
        taps=[
            PublishedTapRow(
                id="b" * 36,
                unstructured_line_label=None,
                product_name="House lager",
                is_rotating=False,
                is_guest_tap=False,
                sort_order=0,
            )
        ],
    )


class PublishedVenueBatchLoadTests(SimpleTestCase):
    @patch("apps.venues.services.published_venue_read._load_core_rows")
    @patch("apps.venues.services.published_venue_read._load_descriptive_rows")
    @patch("apps.venues.services.published_venue_read._load_attribute_rows")
    @patch("apps.venues.services.published_venue_read._load_regular_hours_rows")
    @patch("apps.venues.services.published_venue_read._load_exception_hours_rows")
    @patch("apps.venues.services.published_venue_read._load_special_rows")
    @patch("apps.venues.services.published_venue_read._load_tap_rows")
    def test_batch_loader_assembles_equivalent_cards(
        self,
        tap_rows_mock,
        special_rows_mock,
        exception_rows_mock,
        regular_rows_mock,
        attribute_rows_mock,
        descriptive_rows_mock,
        core_rows_mock,
    ):
        bundle = _sample_bundle()
        vid = bundle.core.venue_id
        core_rows_mock.return_value = {vid: bundle.core}
        descriptive_rows_mock.return_value = {vid: bundle.descriptive}
        attribute_rows_mock.return_value = {vid: bundle.attributes}
        regular_rows_mock.return_value = {vid: bundle.hours_regular}
        exception_rows_mock.return_value = {vid: bundle.hours_exceptions}
        special_rows_mock.return_value = {vid: bundle.specials}
        tap_rows_mock.return_value = {vid: bundle.taps}

        loaded = load_published_venue_read_bundles([vid])
        single = load_published_venue_read_bundle(vid)

        self.assertIn(vid, loaded)
        self.assertEqual(loaded[vid].core.display_name, single.core.display_name)
        self.assertEqual(loaded[vid].specials[0].headline, single.specials[0].headline)

        expected_card = bundle_to_public_venue_card(bundle)
        actual_card = bundle_to_public_venue_card(loaded[vid])
        self.assertEqual(
            actual_card,
            expected_card,
        )

    @patch("apps.venues.services.published_venue_read.load_published_venue_read_bundles")
    def test_single_loader_delegates_to_batch(self, batch_mock):
        bundle = _sample_bundle()
        batch_mock.return_value = {bundle.core.venue_id: bundle}

        result = load_published_venue_read_bundle(bundle.core.venue_id)

        batch_mock.assert_called_once_with([bundle.core.venue_id])
        self.assertEqual(result.core.venue_id, bundle.core.venue_id)


class DiscoveryBatchLoadTests(SimpleTestCase):
    @patch("services.discovery.query.load_published_venue_read_bundles")
    @patch("services.discovery.query.map_published_hours_uncertainty", return_value={})
    @patch("services.discovery.query.connection")
    def test_run_discovery_batch_loads_missing_bundles_once(
        self,
        connection_mock,
        _uncertainty_mock,
        batch_mock,
    ):
        from services.discovery import DiscoveryMode, DiscoveryMvpFilters, run_discovery

        vid_a = "11111111-1111-4111-8111-111111111111"
        vid_b = "22222222-2222-4222-8222-222222222222"
        bundle_a = _sample_bundle(vid_a)
        bundle_b = _sample_bundle(vid_b)
        batch_mock.return_value = {vid_a: bundle_a, vid_b: bundle_b}

        cursor = connection_mock.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            (vid_a, True, "A", "Melbourne", "AU", -37.81, 144.96, None),
            (vid_b, False, "B", "Melbourne", "AU", -37.82, 144.97, None),
        ]

        cache: dict = {}
        run_discovery(
            DiscoveryMode.LIST,
            DiscoveryMvpFilters(limit=2),
            bundle_cache=cache,
        )

        batch_mock.assert_called_once_with([vid_a, vid_b])
        self.assertEqual(set(cache.keys()), {vid_a, vid_b})

        batch_mock.reset_mock()
        run_discovery(
            DiscoveryMode.LIST,
            DiscoveryMvpFilters(limit=2),
            bundle_cache=cache,
        )
        batch_mock.assert_not_called()
