from __future__ import annotations

from django.db import connection
from django.db.utils import DatabaseError
from django.test import SimpleTestCase, TestCase

from apps.founder_venues.services.contact_safety import (
    classify_email_contact_safety,
    is_high_confidence_business_email,
)
from apps.founder_venues.services.csv_mapping import (
    build_header_map,
    map_row_to_lead_fields,
    parse_csv_rows,
)
from apps.founder_venues.services.import_service import (
    compute_import_confidence,
    import_founder_venue_leads_csv,
    normalize_import_row,
)
from apps.founder_venues.services.import_service import RowError


def _founder_tables_available() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM public.founder_venue_leads LIMIT 1")
        return True
    except DatabaseError:
        return False


SAMPLE_CSV = """business_name,type,street,city,state,postal_code,business_phone,business_website,email_1
Belmont Hotel,Pub,77 High St,Belmont,VIC,3216,+61 3 5243 2802,https://belmonthotel.example,info@belmonthotel.example
"""

DUPLICATE_CSV = """business_name,business_phone,business_website
Second Belmont,03 5243 2802,https://belmonthotel.example
"""


class CsvMappingTests(SimpleTestCase):
    def test_flexible_column_mapping(self) -> None:
        headers = [
            "business_name",
            "type",
            "street",
            "city",
            "postal_code",
            "business_phone",
            "business_website",
        ]
        header_map = build_header_map(headers)
        self.assertEqual(header_map["business_name"], "name")
        self.assertEqual(header_map["type"], "category")
        self.assertEqual(header_map["street"], "address_line")
        self.assertEqual(header_map["city"], "suburb")
        self.assertEqual(header_map["postal_code"], "postcode")

    def test_missing_name_column_detected(self) -> None:
        header_map = build_header_map(["phone", "website"])
        self.assertNotIn("name", header_map.values())

    def test_email_1_and_email_2_columns_map(self) -> None:
        headers = ["business_name", "email_1", "email_2"]
        header_map = build_header_map(headers)
        row = {
            "business_name": "Test Pub",
            "email_1": "",
            "email_2": "bookings@venue.com.au",
        }
        fields = map_row_to_lead_fields(row, header_map)
        self.assertEqual(fields["email"], "bookings@venue.com.au")


class NormalizationIntegrationTests(SimpleTestCase):
    def test_required_venue_name_validation(self) -> None:
        parsed = normalize_import_row(
            2,
            {"name": None},
            {},
            source_type="csv_import",
        )
        self.assertIsInstance(parsed, RowError)

    def test_minimal_name_suburb_state_row(self) -> None:
        parsed = normalize_import_row(
            2,
            {"name": "Corner Pub", "suburb": "Richmond", "state": "VIC"},
            {},
            source_type="csv_import",
        )
        self.assertNotIsInstance(parsed, RowError)
        assert not isinstance(parsed, RowError)
        self.assertEqual(parsed.name, "Corner Pub")
        self.assertEqual(parsed.state, "VIC")
        self.assertIsNone(parsed.email)

    def test_contact_permission_with_public_contact(self) -> None:
        parsed = normalize_import_row(
            2,
            {"name": "Pub", "phone": "03 9421 0001"},
            {},
            source_type="csv_import",
        )
        assert not isinstance(parsed, RowError)
        self.assertEqual(parsed.contact_permission_status, "public_business_contact")

    def test_contact_permission_unknown_without_contact(self) -> None:
        parsed = normalize_import_row(
            2,
            {"name": "Pub Only"},
            {},
            source_type="csv_import",
        )
        assert not isinstance(parsed, RowError)
        self.assertEqual(parsed.contact_permission_status, "unknown")


class ContactSafetyTests(SimpleTestCase):
    def test_generic_business_email(self) -> None:
        self.assertEqual(
            classify_email_contact_safety("info@venue.com.au"),
            "generic_business_contact",
        )
        self.assertTrue(is_high_confidence_business_email("info@venue.com.au"))

    def test_unsafe_personal_email(self) -> None:
        self.assertEqual(
            classify_email_contact_safety("owner@gmail.com"),
            "likely_personal_or_unsafe",
        )
        self.assertFalse(is_high_confidence_business_email("owner@gmail.com"))


class ImportConfidenceTests(SimpleTestCase):
    def test_confidence_caps_at_80(self) -> None:
        score = compute_import_confidence(
            source_type="csv_import",
            phone="+61352432802",
            website="https://example.com",
            email="info@example.com",
            instagram_url="https://instagram.com/x",
            facebook_url=None,
            address_line="1 St",
            suburb="Melbourne",
            state="VIC",
            latitude=-37.8,
            longitude=144.9,
        )
        self.assertLessEqual(score, 80)
        self.assertGreaterEqual(score, 30)


class ImportDryRunTests(TestCase):
    def test_dry_run_does_not_write_leads(self) -> None:
        if not _founder_tables_available():
            self.skipTest("founder_venue_leads table not available (apply migration 0033).")

        before = _lead_count()
        result = import_founder_venue_leads_csv(
            SAMPLE_CSV,
            source_name="dry-run-test",
            dry_run=True,
        )
        after = _lead_count()
        self.assertEqual(before, after)
        self.assertTrue(result.dry_run)
        self.assertEqual(result.rows_processed, 1)
        self.assertGreaterEqual(result.leads_created, 0)


def _lead_count() -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM public.founder_venue_leads")
        return int(cursor.fetchone()[0])


def _delete_leads_by_name_prefix(prefix: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM public.founder_venue_leads WHERE name LIKE %s",
            [f"{prefix}%"],
        )


class FounderVenueImportDbTests(TestCase):
    """DB integration tests; skipped when migration 0033 is not applied."""

    def setUp(self) -> None:
        if not _founder_tables_available():
            self.skipTest("founder_venue_leads table not available (apply migration 0033).")
        _delete_leads_by_name_prefix("ZZ_ImportTest")

    def tearDown(self) -> None:
        if _founder_tables_available():
            _delete_leads_by_name_prefix("ZZ_ImportTest")

    def test_new_lead_insert_with_source_and_attribution(self) -> None:
        csv_text = """business_name,business_phone,business_website,email_1
ZZ_ImportTest Alpha,03 9000 1001,https://zz-alpha-import.example,info@zz-alpha-import.example
"""
        result = import_founder_venue_leads_csv(
            csv_text,
            source_name="unit-test",
        )
        self.assertEqual(result.leads_created, 1)
        self.assertEqual(result.invalid_rows, [])

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id::text, confidence_score, contact_permission_status
                FROM public.founder_venue_leads
                WHERE name = 'ZZ_ImportTest Alpha'
                """
            )
            lead = cursor.fetchone()
            self.assertIsNotNone(lead)
            lead_id, confidence, permission = lead
            self.assertGreaterEqual(confidence, 30)
            self.assertEqual(permission, "public_business_contact")

            cursor.execute(
                "SELECT COUNT(*) FROM public.founder_venue_lead_sources WHERE lead_id = %s::uuid",
                [lead_id],
            )
            self.assertEqual(cursor.fetchone()[0], 1)

            cursor.execute(
                """
                SELECT COUNT(*) FROM public.founder_venue_lead_field_attributions
                WHERE lead_id = %s::uuid
                """,
                [lead_id],
            )
            self.assertGreater(cursor.fetchone()[0], 0)

            cursor.execute(
                """
                SELECT event_type FROM public.founder_venue_lead_events
                WHERE lead_id = %s::uuid
                """,
                [lead_id],
            )
            events = [row[0] for row in cursor.fetchall()]
            self.assertIn("import_created", events)

    def test_strong_duplicate_skip(self) -> None:
        first = import_founder_venue_leads_csv(
            """business_name,business_phone
ZZ_ImportTest Dup,+61 3 9000 2002
""",
            source_name="dup-a",
        )
        self.assertEqual(first.leads_created, 1)

        second = import_founder_venue_leads_csv(
            """business_name,business_phone
ZZ_ImportTest Dup Other,+61 3 9000 2002
""",
            source_name="dup-b",
        )
        self.assertEqual(second.leads_created, 0)
        self.assertEqual(second.duplicates_skipped, 1)

    def test_update_existing_fills_empty_fields_only(self) -> None:
        import_founder_venue_leads_csv(
            """business_name,business_phone
ZZ_ImportTest Update,+61 3 9000 3003
""",
            source_name="upd-a",
        )
        result = import_founder_venue_leads_csv(
            """business_name,business_phone,business_website,email_1
ZZ_ImportTest Update,+61 3 9000 3003,https://zz-update-import.example,info@zz-update-import.example
""",
            source_name="upd-b",
            update_existing=True,
        )
        self.assertEqual(result.leads_updated, 1)
        self.assertEqual(result.leads_created, 0)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT website, email FROM public.founder_venue_leads
                WHERE name = 'ZZ_ImportTest Update'
                """
            )
            website, email = cursor.fetchone()
            self.assertEqual(website, "https://zz-update-import.example")
            self.assertEqual(email, "info@zz-update-import.example")

    def test_probable_duplicate_needs_review(self) -> None:
        import_founder_venue_leads_csv(
            """business_name,city,state,postal_code
ZZ_ImportTest Prob,Richmond,VIC,3121
""",
            source_name="prob-a",
        )
        result = import_founder_venue_leads_csv(
            """business_name,city,state,postal_code
ZZ_ImportTest Prob,Richmond,VIC,3121
""",
            source_name="prob-b",
        )
        self.assertEqual(result.leads_created, 1)
        self.assertEqual(len(result.duplicates_needing_review), 1)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT enrichment_status FROM public.founder_venue_leads
                WHERE name = 'ZZ_ImportTest Prob'
                ORDER BY created_at DESC
                LIMIT 1
                """
            )
            self.assertEqual(cursor.fetchone()[0], "needs_review")
