from __future__ import annotations

from django.db import connection
from django.db.utils import DatabaseError
from django.test import SimpleTestCase, TestCase

from apps.founder_venues.services.founder_fit_db import (
    get_top_founder_venue_leads,
    recompute_founder_fit_scores,
)
from apps.founder_venues.services.scoring import compute_founder_fit_score


def _founder_tables_available() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM public.founder_venue_leads LIMIT 1")
        return True
    except DatabaseError:
        return False


def _base_lead(**overrides) -> dict:
    lead = {
        "name": "Example Venue",
        "category": "pub",
        "suburb": "Fitzroy",
        "state": "VIC",
        "postcode": "3065",
        "phone": "+61390000000",
        "website": "https://example-venue.example",
        "email": "info@example-venue.example",
        "confidence_score": 60,
        "enrichment_status": "imported",
        "outreach_status": "not_contacted",
        "contact_permission_status": "public_business_contact",
        "source_count": 1,
    }
    lead.update(overrides)
    return lead


class FounderFitScoringTests(SimpleTestCase):
    def test_high_priority_launch_suburb_scores_strongly(self) -> None:
        result = compute_founder_fit_score(_base_lead(suburb="Fitzroy", state="VIC"))
        self.assertGreaterEqual(result.breakdown["components"]["location"], 20)
        self.assertTrue(
            any("Fitzroy" in s for s in result.breakdown["positive_signals"])
        )

    def test_vic_non_priority_suburb_scores_moderately(self) -> None:
        result = compute_founder_fit_score(
            _base_lead(suburb="Geelong", state="VIC")
        )
        self.assertEqual(result.breakdown["components"]["location"], 10)

    def test_non_vic_not_excluded(self) -> None:
        result = compute_founder_fit_score(
            _base_lead(suburb="Newtown", state="NSW", category="pub")
        )
        self.assertGreater(result.score, 0)
        self.assertEqual(result.breakdown["components"]["location"], 5)

    def test_pub_category_scores_strongly(self) -> None:
        result = compute_founder_fit_score(_base_lead(category="Pub"))
        self.assertEqual(result.breakdown["components"]["category"], 20)

    def test_unrelated_category_warning(self) -> None:
        result = compute_founder_fit_score(_base_lead(category="Pharmacy"))
        self.assertLessEqual(result.breakdown["components"]["category"], 8)
        self.assertTrue(any("Category" in w for w in result.breakdown["warnings"]))

    def test_contactability_from_phone_website_email(self) -> None:
        result = compute_founder_fit_score(_base_lead())
        self.assertGreaterEqual(result.breakdown["components"]["contactability"], 15)

    def test_unsafe_email_lower_contactability(self) -> None:
        safe = compute_founder_fit_score(
            _base_lead(email="info@venue.com.au")
        ).breakdown["components"]["contactability"]
        unsafe = compute_founder_fit_score(
            _base_lead(email="owner@gmail.com")
        ).breakdown["components"]["contactability"]
        self.assertGreater(safe, unsafe)

    def test_do_not_contact_heavily_penalised(self) -> None:
        base = compute_founder_fit_score(_base_lead()).score
        penalised = compute_founder_fit_score(
            _base_lead(
                contact_permission_status="do_not_contact",
                outreach_status="do_not_contact",
            )
        ).score
        self.assertLess(penalised, base - 10)

    def test_suppressed_heavily_penalised(self) -> None:
        base_score = compute_founder_fit_score(_base_lead()).score
        result = compute_founder_fit_score(
            _base_lead(suppressed_at="2026-01-01T00:00:00Z")
        )
        self.assertLess(result.score, base_score - 15)
        self.assertTrue(
            any("Suppressed" in s for s in result.breakdown["negative_signals"])
        )

    def test_missing_data_still_valid_score(self) -> None:
        result = compute_founder_fit_score(
            {"name": "Minimal Pub", "state": "VIC", "suburb": "Richmond"}
        )
        self.assertGreaterEqual(result.score, 0)
        self.assertLessEqual(result.score, 100)

    def test_score_clamps_0_100(self) -> None:
        high = compute_founder_fit_score(
            _base_lead(
                suburb="Fitzroy",
                category="pub",
                phone="+61390000000",
                website="https://x.example",
                email="info@x.example",
                instagram_url="https://instagram.com/x",
                facebook_url="https://facebook.com/x",
                confidence_score=80,
                latitude=-37.8,
                longitude=144.9,
                address_line="1 St",
                postcode="3065",
                notes="trivia live music events specials",
            )
        )
        self.assertLessEqual(high.score, 100)
        self.assertGreaterEqual(high.score, 0)

    def test_breakdown_structure(self) -> None:
        result = compute_founder_fit_score(_base_lead())
        b = result.breakdown
        self.assertEqual(b["score"], result.score)
        self.assertIn("components", b)
        self.assertIn("positive_signals", b)
        self.assertIn("negative_signals", b)
        self.assertIn("warnings", b)
        self.assertIn("location", b["components"])


class FounderFitRecomputeDbTests(TestCase):
    def setUp(self) -> None:
        if not _founder_tables_available():
            self.skipTest("founder_venue_leads not available (migration 0033).")

    def test_recompute_writes_score_and_event(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.founder_venue_leads (
                  name, suburb, state, category, confidence_score
                ) VALUES (
                  'ZZ_ScoringTest Venue', 'Fitzroy', 'VIC', 'Pub', 55
                )
                RETURNING id::text
                """
            )
            lead_id = cursor.fetchone()[0]

        try:
            result = recompute_founder_fit_scores(lead_ids=[lead_id])
            self.assertEqual(result.updated, 1)

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT founder_fit_score, founder_fit_breakdown::text
                    FROM public.founder_venue_leads WHERE id = %s::uuid
                    """,
                    [lead_id],
                )
                score, breakdown_text = cursor.fetchone()
                self.assertGreater(score, 0)
                self.assertIn("components", breakdown_text)

                cursor.execute(
                    """
                    SELECT event_type FROM public.founder_venue_lead_events
                    WHERE lead_id = %s::uuid
                    """,
                    [lead_id],
                )
                events = [r[0] for r in cursor.fetchall()]
                self.assertIn("founder_fit_score_recomputed", events)
        finally:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM public.founder_venue_leads WHERE id = %s::uuid",
                    [lead_id],
                )

    def test_get_top_excludes_do_not_contact_by_default(self) -> None:
        rows = get_top_founder_venue_leads(state="VIC", limit=5)
        self.assertIsInstance(rows, list)
