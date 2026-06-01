from __future__ import annotations

from django.test import SimpleTestCase

from apps.founder_venues.services.normalization import (
    build_soft_dedupe_key,
    normalize_email,
    normalize_phone_au,
    normalize_postcode,
    normalize_state,
    normalize_venue_name,
    normalize_website_url,
)


class FounderVenueNormalizationTests(SimpleTestCase):
    def test_normalize_venue_name_strips_legal_suffix(self) -> None:
        self.assertEqual(
            normalize_venue_name("The Royal Hotel Pty Ltd"),
            "the royal hotel",
        )

    def test_normalize_state(self) -> None:
        self.assertEqual(normalize_state("Victoria"), "VIC")
        self.assertEqual(normalize_state("vic"), "VIC")
        self.assertIsNone(normalize_state(""))

    def test_normalize_website_url(self) -> None:
        self.assertEqual(
            normalize_website_url("www.example.com.au/"),
            "https://example.com.au",
        )

    def test_normalize_phone_au(self) -> None:
        self.assertEqual(normalize_phone_au("+61 3 5243 2802"), "+61352432802")
        self.assertEqual(normalize_phone_au("03 5243 2802"), "+61352432802")

    def test_normalize_email(self) -> None:
        self.assertEqual(normalize_email("  Info@Example.COM "), "info@example.com")

    def test_normalize_postcode(self) -> None:
        self.assertEqual(normalize_postcode(3216.0), "3216")

    def test_build_soft_dedupe_key_prefers_strong_identifiers(self) -> None:
        phone = normalize_phone_au("+61 3 5243 2802")
        key = build_soft_dedupe_key(
            normalized_name=normalize_venue_name("Belmont Hotel"),
            postcode="3216",
            website="https://belmonthotelgeelong.com.au",
            phone=phone,
            email=None,
        )
        self.assertIn("web:belmonthotelgeelong.com.au", key or "")
        self.assertIn("phone:+61352432802", key or "")
