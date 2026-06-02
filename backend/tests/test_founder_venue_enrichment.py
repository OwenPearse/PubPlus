from __future__ import annotations

import unittest
from unittest.mock import patch

from django.db import connection
from django.db.utils import DatabaseError
from django.test import Client, SimpleTestCase, TestCase

from apps.founder_venues.services.enrichment.extractors import (
    extract_emails_from_html,
    extract_phones_from_html,
    extract_product_signals_from_html,
    extract_social_links_from_html,
    is_email_auto_promotable,
)
from apps.founder_venues.services.enrichment.website import (
    FetchPageResult,
    fetch_venue_website_pages,
    select_same_origin_page_urls,
)
from apps.founder_venues.services.url_classification import (
    is_social_profile_url,
    website_url_is_fetchable,
)
from apps.founder_venues.services.enrichment_service import (
    _decide_promotions,
    enrich_founder_venue_lead_from_website,
)
from apps.founder_venues.services.enrichment.result import WebsiteEnrichmentCandidate
from common.auth.context import AuthContext

LEAD_ID = "00000000-0000-4000-8000-000000000099"


def _founder_tables_available() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM public.founder_venue_leads LIMIT 1")
        return True
    except DatabaseError:
        return False


def _internal_ctx() -> AuthContext:
    return AuthContext(
        subject="operator-sub-1",
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="operator@example.com",
        claims={"sub": "operator-sub-1", "pubplus_internal_admin": True},
    )


def _consumer_ctx() -> AuthContext:
    return AuthContext(
        subject="consumer-user-1",
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="consumer@example.com",
        claims={"sub": "consumer-user-1"},
    )


def _mock_fetcher(pages: dict[str, str]):
    def fetch(url: str) -> FetchPageResult:
        html = pages.get(url)
        if html is None:
            for key, value in pages.items():
                if url.rstrip("/") == key.rstrip("/"):
                    return FetchPageResult(url=url, html=value)
            return FetchPageResult(url=url, html=None, error="not found")
        return FetchPageResult(url=url, html=html)

    return fetch


HOME = "https://zz-test-pub.com.au"
CONTACT = "https://zz-test-pub.com.au/contact"
VENUE_HOST = "zz-test-pub.com.au"


class ExtractorEmailTests(SimpleTestCase):
    def test_email_from_visible_text(self) -> None:
        html = "<p>Email us at info@zz-test-pub.com.au for bookings</p>"
        found = extract_emails_from_html(
            html, source_url=HOME, venue_host=VENUE_HOST
        )
        self.assertTrue(any(c.normalized_value == "info@zz-test-pub.com.au" for c in found))

    def test_email_from_mailto(self) -> None:
        html = '<a href="mailto:bookings@zz-test-pub.com.au">Email</a>'
        found = extract_emails_from_html(
            html, source_url=HOME, venue_host=VENUE_HOST
        )
        self.assertTrue(
            any(c.normalized_value == "bookings@zz-test-pub.com.au" for c in found)
        )

    def test_generic_email_promotable(self) -> None:
        html = "<p>info@zz-test-pub.com.au</p>"
        found = extract_emails_from_html(
            html, source_url=HOME, venue_host=VENUE_HOST
        )
        email = next(c for c in found if c.field_name == "email")
        self.assertEqual(email.contact_safety_class, "generic_business_contact")
        self.assertTrue(is_email_auto_promotable(email.contact_safety_class))

    def test_unsafe_email_not_promotable(self) -> None:
        html = "<p>owner@gmail.com</p>"
        found = extract_emails_from_html(
            html, source_url=HOME, venue_host=VENUE_HOST
        )
        email = next(c for c in found if c.field_name == "email")
        self.assertEqual(email.contact_safety_class, "likely_personal_or_unsafe")
        self.assertFalse(is_email_auto_promotable(email.contact_safety_class))


class ExtractorPhoneTests(SimpleTestCase):
    def test_phone_from_visible_text(self) -> None:
        html = "<p>Call 03 9123 4567 today</p>"
        found = extract_phones_from_html(html, source_url=CONTACT, contact_page=True)
        self.assertTrue(any(c.normalized_value == "+61391234567" for c in found))

    def test_phone_from_tel_link(self) -> None:
        html = '<a href="tel:+61390001111">Call</a>'
        found = extract_phones_from_html(html, source_url=CONTACT, contact_page=True)
        self.assertTrue(any(c.normalized_value == "+61390001111" for c in found))


class ExtractorSocialTests(SimpleTestCase):
    def test_instagram_and_facebook_extracted(self) -> None:
        html = """
        <a href="https://www.instagram.com/examplepub/">IG</a>
        <a href="https://www.facebook.com/examplepub">FB</a>
        """
        found = extract_social_links_from_html(html, source_url=HOME)
        fields = {c.field_name: c.normalized_value for c in found}
        self.assertIn("instagram_url", fields)
        self.assertIn("facebook_url", fields)

    def test_share_and_login_urls_filtered(self) -> None:
        html = """
        <a href="https://www.facebook.com/sharer/sharer.php?u=x">share</a>
        <a href="https://www.facebook.com/login.php">login</a>
        <a href="https://www.instagram.com/">home</a>
        """
        found = extract_social_links_from_html(html, source_url=HOME)
        self.assertEqual(found, [])


class ExtractorProductSignalTests(SimpleTestCase):
    def test_product_fit_signals(self) -> None:
        html = "<p>Join us for trivia and live music with AFL on the big screen</p>"
        signals = extract_product_signals_from_html(html)
        self.assertIn("trivia", signals)
        self.assertIn("live music", signals)
        self.assertIn("AFL", signals)


class WebsiteFetchPolicyTests(SimpleTestCase):
    def test_rejects_pdf_and_images(self) -> None:
        from apps.founder_venues.services.enrichment.website import is_allowed_fetch_url

        self.assertFalse(is_allowed_fetch_url("https://venue.example/menu.pdf"))
        self.assertFalse(is_allowed_fetch_url("https://venue.example/photo.jpg"))

    def test_rejects_non_http(self) -> None:
        from apps.founder_venues.services.enrichment.website import is_allowed_fetch_url

        self.assertFalse(is_allowed_fetch_url("ftp://venue.example/contact"))

    def test_rejects_social_hosts_for_fetch(self) -> None:
        from apps.founder_venues.services.enrichment.website import is_allowed_fetch_url

        self.assertFalse(is_allowed_fetch_url("https://www.facebook.com/venue"))

    def test_facebook_website_not_fetchable(self) -> None:
        self.assertFalse(
            website_url_is_fetchable("https://www.facebook.com/somepub")
        )
        self.assertTrue(website_url_is_fetchable("https://somepub.com.au"))

    def test_same_origin_page_selection_limits_and_keywords(self) -> None:
        html = """
        <a href="/contact">Contact</a>
        <a href="/about">About</a>
        <a href="/events">Events</a>
        <a href="/random-page">Random</a>
        <a href="/functions">Functions</a>
        <a href="/sport">Sport</a>
        <a href="/gallery">Gallery</a>
        """
        urls = select_same_origin_page_urls(HOME, html, max_extra=4)
        self.assertLessEqual(len(urls), 4)
        joined = " ".join(urls)
        self.assertIn("contact", joined)
        self.assertNotIn("random-page", joined)

    def test_fetch_venue_pages_respects_max_five(self) -> None:
        pages = {
            HOME: '<a href="/contact">c</a><a href="/events">e</a>',
            CONTACT: "<p>info@zz-test-pub.com.au</p>",
            "https://zz-test-pub.com.au/events": "<p>events</p>",
        }

        def fetch(url: str) -> FetchPageResult:
            normalized = url.rstrip("/")
            key = HOME if normalized == HOME.rstrip("/") else url
            html = pages.get(key) or pages.get(url)
            return FetchPageResult(url=url, html=html or "<p>x</p>")

        fetched, urls, _ = fetch_venue_website_pages(HOME, page_fetcher=fetch)
        self.assertLessEqual(len(fetched), 5)
        self.assertGreaterEqual(len(urls), 1)


class PromotionLogicTests(SimpleTestCase):
    def test_conflicting_email_sets_needs_review(self) -> None:
        lead = {"email": "info@existing.example", "phone": None}
        best = {
            "email": WebsiteEnrichmentCandidate(
                field_name="email",
                raw_value="bookings@other.example",
                normalized_value="bookings@other.example",
                source_url=HOME,
                confidence=85,
                contact_safety_class="generic_business_contact",
            )
        }
        updates, needs_review, promoted = _decide_promotions(lead, best)
        self.assertTrue(needs_review)
        self.assertNotIn("email", updates)
        self.assertEqual(promoted, [])


class EnrichmentServiceUnitTests(SimpleTestCase):
    @patch("apps.founder_venues.services.enrichment_service._load_lead_row")
    def test_social_website_skips_fetch(self, mock_load) -> None:
        mock_load.return_value = {
            "id": LEAD_ID,
            "website": "https://www.facebook.com/somepub",
        }
        result = enrich_founder_venue_lead_from_website(LEAD_ID, dry_run=True)
        self.assertEqual(result.errors, ["website_not_fetchable"])
        self.assertEqual(result.fetched_urls, [])

    @patch("apps.founder_venues.services.enrichment_service._load_lead_row")
    def test_no_website_returns_warning_without_fetch(self, mock_load) -> None:
        mock_load.return_value = {"id": LEAD_ID, "website": None}
        result = enrich_founder_venue_lead_from_website(LEAD_ID, dry_run=True)
        self.assertIn("No website", result.warnings[0])
        self.assertEqual(result.errors, ["no_website"])
        self.assertEqual(result.fetched_urls, [])

    @patch("apps.founder_venues.services.enrichment_service.recompute_founder_fit_scores")
    @patch("apps.founder_venues.services.enrichment_service._load_lead_row")
    def test_dry_run_writes_nothing(self, mock_load, mock_recompute) -> None:
        mock_load.return_value = {
            "id": LEAD_ID,
            "website": HOME,
            "email": None,
            "phone": None,
            "instagram_url": None,
            "facebook_url": None,
            "source_summary": None,
            "notes": None,
            "confidence_score": 50,
            "enrichment_status": "imported",
            "address_line": None,
            "suburb": "Fitzroy",
            "state": "VIC",
            "postcode": "3065",
            "latitude": None,
            "longitude": None,
        }
        html = "<p>info@zz-test-pub.com.au</p><a href='tel:+61390001111'>call</a>"
        fetcher = _mock_fetcher({HOME: html})
        result = enrich_founder_venue_lead_from_website(
            LEAD_ID, dry_run=True, page_fetcher=fetcher
        )
        self.assertTrue(result.dry_run)
        self.assertGreater(len(result.candidates), 0)
        mock_recompute.assert_not_called()


class FounderVenueEnrichmentApiTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_enrich_requires_internal_admin(self) -> None:
        r = self.client.post(f"/api/v1/internal/founder-venues/leads/{LEAD_ID}/enrich")
        self.assertEqual(r.status_code, 401)

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_consumer_ctx())
    def test_consumer_rejected(self, _jwt) -> None:
        r = self.client.post(
            f"/api/v1/internal/founder-venues/leads/{LEAD_ID}/enrich",
            data="{}",
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 403)

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.enrich_founder_venue_lead_from_website")
    def test_enrich_calls_service(self, mock_enrich, _jwt) -> None:
        from apps.founder_venues.services.enrichment.result import WebsiteEnrichmentResult

        mock_enrich.return_value = WebsiteEnrichmentResult(
            lead_id=LEAD_ID,
            fetched_urls=[HOME],
            enrichment_status="enriched",
        )
        r = self.client.post(
            f"/api/v1/internal/founder-venues/leads/{LEAD_ID}/enrich",
            data='{"dry_run": true}',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        mock_enrich.assert_called_once()
        self.assertTrue(mock_enrich.call_args.kwargs["dry_run"])


@unittest.skipUnless(_founder_tables_available(), "migration 0033 not applied")
class FounderVenueEnrichmentDbTests(TestCase):
    def setUp(self) -> None:
        if not _founder_tables_available():
            self.skipTest("founder_venue_leads table not available.")
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM public.founder_venue_leads WHERE name LIKE 'ZZ_EnrichTest%'"
            )

    def tearDown(self) -> None:
        if _founder_tables_available():
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM public.founder_venue_leads WHERE name LIKE 'ZZ_EnrichTest%'"
                )

    def test_dry_run_does_not_write_events(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.founder_venue_leads (name, website, state, suburb)
                VALUES ('ZZ_EnrichTest Dry', %s, 'VIC', 'Fitzroy')
                RETURNING id::text
                """,
                [HOME],
            )
            lead_id = cursor.fetchone()[0]

        html = "<p>info@zz-test-pub.com.au</p>"
        result = enrich_founder_venue_lead_from_website(
            lead_id,
            dry_run=True,
            page_fetcher=_mock_fetcher({HOME: html}),
        )
        self.assertTrue(result.dry_run)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM public.founder_venue_lead_events
                WHERE lead_id = %s::uuid AND event_type LIKE 'website_enrichment%%'
                """,
                [lead_id],
            )
            self.assertEqual(cursor.fetchone()[0], 0)
