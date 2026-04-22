import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from common.auth.context import AuthContext
from common.geo.haversine import distance_m
from common.storage import public_storage_object_url

from apps.venues.public_read.card import public_venue_card_to_dict
from apps.venues.services.published_venue_read import (
    PublishedAttributeRow,
    PublishedCoreRow,
    PublishedDescriptiveRow,
    PublishedRegularHoursRow,
    PublishedSpecialRow,
    PublishedTapRow,
    PublishedVenueReadBundle,
)
from apps.venues.services.save_enrichment import apply_save_to_card
from apps.venues.public_read.detail import public_venue_detail_to_dict
from apps.venues.services.venue_read_service import (
    bundle_to_public_venue_card,
    bundle_to_public_venue_detail,
)
from apps.venues.services.venue_media import resolve_hero_and_gallery
from apps.venues.services.published_venue_read import PublishedMediaRef


def _sample_bundle() -> PublishedVenueReadBundle:
    core = PublishedCoreRow(
        venue_id="f1111111-1111-4111-8111-111111111101",
        display_name="Test Pub",
        slug="test-pub",
        operational_status="open",
        suburb_name="Sydney",
        address_line_1="1 Test St",
        address_line_2=None,
        postal_code="2000",
        country_code="AU",
        latitude=-33.86,
        longitude=151.21,
    )
    return PublishedVenueReadBundle(
        core=core,
        descriptive=PublishedDescriptiveRow("Short copy.", "Long copy."),
        attributes=[
            PublishedAttributeRow(
                "venue_style",
                "Venue style",
                True,
                "pub",
                "Pub",
                None,
            ),
            PublishedAttributeRow(
                "serves_food",
                "Serves food",
                True,
                None,
                None,
                True,
            ),
        ],
        hours_regular=[
            PublishedRegularHoursRow(0, "11:00", "23:00", False, 0),
        ],
        hours_exceptions=[],
        specials=[
            PublishedSpecialRow(
                id="a" * 36, structured_kind="meal_special", short_label="Parma", headline="Parmy night"
            )
        ],
        taps=[
            PublishedTapRow("b" * 36, "Guest tap", "Best Bitter", False, False, 0),
        ],
    )


class PublicVenueCardShapingTests(SimpleTestCase):
    def test_card_fields_and_no_internal_leakage_in_json(self):
        c = bundle_to_public_venue_card(_sample_bundle())
        d = public_venue_card_to_dict(c)
        raw = json.dumps(d)
        for fragment in (
            "discovery_eligibility",
            "workflow",
            "proposal",
            "moderation",
        ):
            self.assertNotIn(fragment, raw.lower())
        self.assertEqual(d["id"], "f1111111-1111-4111-8111-111111111101")
        self.assertEqual(d["venue_type"], "pub")
        self.assertEqual(d["suburb"], "Sydney")
        self.assertIn("Serves food", d["feature_badges"])
        self.assertEqual(d["open_now"], None)
        self.assertIs(d["open_now_uncomputed"], True)
        self.assertIsNone(d["is_saved"])
        self.assertEqual(
            d["specials_summary"],
            ["Parmy night"],
        )

    def test_distance_m_when_origin_provided(self):
        b = _sample_bundle()
        c = bundle_to_public_venue_card(
            b, origin_lat=-33.87, origin_lon=151.20
        )
        self.assertIsNotNone(c.distance_m)
        expected = round(
            distance_m(-33.87, 151.20, b.core.latitude, b.core.longitude), 1
        )
        self.assertEqual(c.distance_m, expected)

    @patch(
        "apps.venues.services.save_enrichment.venue_id_in_any_user_list",
        return_value=True,
    )
    def test_apply_save_auth_sets_is_saved(self, _m) -> None:
        auth = AuthContext(
            subject="aaaaaaaa-bbbb-cccc-dddd-eeeeffffffff",
            audience="authenticated",
            issuer="x",
            role="authenticated",
            email=None,
            claims={},
        )
        c = bundle_to_public_venue_card(_sample_bundle())
        out = apply_save_to_card(c, auth=auth, venue_id=c.id)
        self.assertIs(out.is_saved, True)


class PublicVenueDetailShapingTests(SimpleTestCase):
    def test_detail_blocks_and_scaffold_flags(self):
        b = _sample_bundle()
        d = bundle_to_public_venue_detail(b, auth=None)
        raw = json.dumps(public_venue_detail_to_dict(d))
        for fragment in (
            "discovery_eligibility",
            "workflow",
            "proposal",
        ):
            self.assertNotIn(fragment, raw.lower())
        self.assertTrue(d.events.not_implemented)
        self.assertTrue(d.contact.not_implemented)
        self.assertTrue(d.actions.save_requires_auth)
        self.assertIsNone(d.actions.is_saved)
        self.assertIsNone(d.hours.open_now)
        self.assertEqual(len(d.drinks.highlights), 1)
        self.assertEqual(len(d.photos.items), 0)


@override_settings(
    SUPABASE_URL="https://abcdefgh.supabase.co", SUPABASE_STORAGE_BUCKET_VENUES="venues"
)
class StorageUrlTests(SimpleTestCase):
    def test_resolves_supabase_public_storage_pattern(self):
        u = public_storage_object_url(
            "https://abcdefgh.supabase.co",
            "venues",
            "venue_id/hero.jpg",
        )
        self.assertTrue(u.startswith("https://abcdefgh.supabase.co/"))
        self.assertIn("/storage/v1/object/public/venues/", u)
        self.assertTrue(u.endswith("venue_id/hero.jpg"))


@override_settings(
    SUPABASE_URL="https://abcdefgh.supabase.co", SUPABASE_STORAGE_BUCKET_VENUES="venues"
)
class VenueMediaResolverTests(SimpleTestCase):
    def test_resolve_gallery_uses_direct_storage_url(self):
        res = resolve_hero_and_gallery(
            [
                PublishedMediaRef("a/hero.png", 0, True),
                PublishedMediaRef("a/other.png", 1, False),
            ]
        )
        self.assertIsNotNone(res.hero_url)
        for p in res.photos:
            self.assertIsNotNone(p.url)
            self.assertTrue(p.url.startswith("https://abcdefgh.supabase.co/"))
            self.assertIn("storage/v1/object/public/venues", p.url)
            self.assertNotIn("localhost", p.url)
            self.assertNotIn("/media/", p.url)


class SaveEnrichmentAnonTests(SimpleTestCase):
    def test_apply_save_anon_leaves_is_saved_null(self):
        c = bundle_to_public_venue_card(_sample_bundle())
        out = apply_save_to_card(c, auth=None, venue_id=c.id)
        d = public_venue_card_to_dict(out)
        self.assertIsNone(d["is_saved"])
