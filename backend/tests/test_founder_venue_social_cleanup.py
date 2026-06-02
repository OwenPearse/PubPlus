from __future__ import annotations

import unittest
from unittest.mock import patch

from django.db import connection
from django.db.utils import DatabaseError
from django.test import SimpleTestCase, TestCase

from apps.founder_venues.services.import_service import RowError, normalize_import_row
from apps.founder_venues.services.social_cleanup import (
    _plan_change,
    cleanup_social_urls_in_founder_venue_leads,
)
from apps.founder_venues.services.url_classification import (
    apply_import_url_routing,
    classify_url_kind,
    is_social_profile_url,
    normalize_social_url,
    website_url_is_fetchable,
)


def _founder_tables_available() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM public.founder_venue_leads LIMIT 1")
        return True
    except DatabaseError:
        return False


class UrlClassificationTests(SimpleTestCase):
    def test_facebook_classified(self) -> None:
        self.assertEqual(
            classify_url_kind("https://www.facebook.com/examplepub"),
            "facebook",
        )

    def test_instagram_classified(self) -> None:
        self.assertEqual(
            classify_url_kind("https://www.instagram.com/examplepub/"),
            "instagram",
        )

    def test_normal_website_remains_website(self) -> None:
        self.assertEqual(
            classify_url_kind("https://example-pub.com.au/contact"),
            "website",
        )
        self.assertTrue(website_url_is_fetchable("https://example-pub.com.au"))

    def test_login_share_urls_not_useful_profiles(self) -> None:
        self.assertEqual(
            classify_url_kind("https://www.facebook.com/sharer/sharer.php?u=x"),
            "invalid",
        )
        self.assertEqual(
            classify_url_kind("https://www.facebook.com/login.php"),
            "invalid",
        )
        self.assertIsNone(
            normalize_social_url("https://www.facebook.com/sharer/sharer.php?u=x")
        )

    def test_google_maps_not_website(self) -> None:
        self.assertEqual(
            classify_url_kind("https://www.google.com/maps/place/pub"),
            "invalid",
        )

    def test_is_social_profile_url(self) -> None:
        self.assertTrue(is_social_profile_url("https://www.facebook.com/pub"))
        self.assertFalse(is_social_profile_url("https://venue.com.au"))


class ImportUrlRoutingTests(SimpleTestCase):
    def test_facebook_in_website_column_routes_to_facebook_url(self) -> None:
        website, fb, ig = apply_import_url_routing(
            website="https://www.facebook.com/my.pub",
            facebook_url=None,
            instagram_url=None,
        )
        self.assertIsNone(website)
        self.assertIn("facebook.com", fb or "")

    def test_instagram_in_website_column_routes_to_instagram_url(self) -> None:
        website, fb, ig = apply_import_url_routing(
            website="https://www.instagram.com/my.pub/",
            facebook_url=None,
            instagram_url=None,
        )
        self.assertIsNone(website)
        self.assertIn("instagram.com", ig or "")

    def test_does_not_overwrite_existing_facebook(self) -> None:
        existing = "https://www.facebook.com/existing/"
        website, fb, ig = apply_import_url_routing(
            website="https://www.facebook.com/other/",
            facebook_url=existing,
            instagram_url=None,
        )
        self.assertIsNone(website)
        self.assertEqual(fb, existing)

    def test_import_row_routes_facebook_website(self) -> None:
        row = normalize_import_row(
            2,
            {
                "name": "Test Pub",
                "website": "https://www.facebook.com/testpub",
                "suburb": "Fitzroy",
                "state": "VIC",
            },
            {},
            source_type="purchased_dataset",
        )
        self.assertNotIsInstance(row, RowError)
        self.assertIsNone(row.website)
        self.assertIn("facebook.com", row.facebook_url or "")


class SocialCleanupPlanTests(SimpleTestCase):
    def test_move_facebook_website(self) -> None:
        change = _plan_change(
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "website": "https://www.facebook.com/testpub",
                "facebook_url": None,
                "instagram_url": None,
            }
        )
        self.assertEqual(change.action, "moved_to_facebook")
        self.assertIsNone(change.website_after)
        self.assertIn("facebook.com", change.facebook_url_after or "")

    def test_move_instagram_website(self) -> None:
        change = _plan_change(
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "website": "https://www.instagram.com/testpub/",
                "facebook_url": None,
                "instagram_url": None,
            }
        )
        self.assertEqual(change.action, "moved_to_instagram")

    def test_skip_when_facebook_already_set(self) -> None:
        change = _plan_change(
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "website": "https://www.facebook.com/other",
                "facebook_url": "https://www.facebook.com/existing/",
                "instagram_url": None,
            }
        )
        self.assertEqual(change.action, "skipped_target_exists")
        self.assertIsNone(change.website_after)

    def test_clear_invalid_website(self) -> None:
        change = _plan_change(
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "website": "https://www.google.com/maps/place/pub",
                "facebook_url": None,
                "instagram_url": None,
            }
        )
        self.assertEqual(change.action, "cleared_social_website")


class SocialCleanupServiceTests(SimpleTestCase):
    @patch("apps.founder_venues.services.social_cleanup._find_leads_for_cleanup")
    @patch("apps.founder_venues.services.social_cleanup._apply_change")
    @patch("apps.founder_venues.services.social_cleanup.recompute_founder_fit_scores")
    def test_dry_run_writes_nothing(
        self, mock_recompute, mock_apply, mock_find
    ) -> None:
        mock_find.return_value = [
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "website": "https://www.facebook.com/testpub",
                "facebook_url": None,
                "instagram_url": None,
            }
        ]
        result = cleanup_social_urls_in_founder_venue_leads(dry_run=True)
        self.assertTrue(result.dry_run)
        self.assertEqual(result.moved_to_facebook, 1)
        mock_apply.assert_not_called()
        mock_recompute.assert_not_called()

    @patch("apps.founder_venues.services.social_cleanup.transaction.atomic")
    @patch("apps.founder_venues.services.social_cleanup._find_leads_for_cleanup")
    @patch("apps.founder_venues.services.social_cleanup._apply_change")
    @patch("apps.founder_venues.services.social_cleanup.recompute_founder_fit_scores")
    def test_recompute_when_enabled(
        self, mock_recompute, mock_apply, mock_find, _atomic
    ) -> None:
        _atomic.return_value.__enter__ = lambda s: None
        _atomic.return_value.__exit__ = lambda s, *a: None
        mock_find.return_value = [
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "website": "https://www.facebook.com/testpub",
                "facebook_url": None,
                "instagram_url": None,
            }
        ]
        mock_recompute.return_value = type("R", (), {"updated": 1})()
        cleanup_social_urls_in_founder_venue_leads(dry_run=False, recompute_scores=True)
        mock_apply.assert_called_once()
        mock_recompute.assert_called_once()


@unittest.skipUnless(_founder_tables_available(), "migration 0033 not applied")
class SocialCleanupDbTests(TestCase):
    def setUp(self) -> None:
        if not _founder_tables_available():
            self.skipTest("founder_venue_leads table not available.")
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM public.founder_venue_leads WHERE name LIKE 'ZZ_SocialCleanup%'"
            )

    def tearDown(self) -> None:
        if _founder_tables_available():
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM public.founder_venue_leads WHERE name LIKE 'ZZ_SocialCleanup%'"
                )

    def test_cleanup_writes_event(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.founder_venue_leads (name, website, state, suburb)
                VALUES ('ZZ_SocialCleanup FB', %s, 'VIC', 'Fitzroy')
                RETURNING id::text
                """,
                ["https://www.facebook.com/zzsocialtest"],
            )
            lead_id = cursor.fetchone()[0]

        result = cleanup_social_urls_in_founder_venue_leads(
            lead_ids=[lead_id],
            recompute_scores=False,
        )
        self.assertEqual(result.moved_to_facebook, 1)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT website, facebook_url FROM public.founder_venue_leads
                WHERE id = %s::uuid
                """,
                [lead_id],
            )
            website, facebook = cursor.fetchone()
            self.assertIsNone(website)
            self.assertIn("facebook.com", facebook)

            cursor.execute(
                """
                SELECT event_type FROM public.founder_venue_lead_events
                WHERE lead_id = %s::uuid
                """,
                [lead_id],
            )
            events = [row[0] for row in cursor.fetchall()]
        self.assertIn("social_url_cleanup_applied", events)
