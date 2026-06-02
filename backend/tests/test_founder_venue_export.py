from __future__ import annotations

import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.db import connection
from django.db.utils import DatabaseError
from django.test import Client, SimpleTestCase, TestCase

from apps.founder_venues.services.export_service import (
    DEFAULT_CSV_COLUMNS,
    ExportExcludedCounts,
    FounderVenueExportResult,
    export_founder_venue_leads_csv,
    parse_export_filters,
    resolve_export_email,
    truncate_notes_summary,
)
from apps.founder_venues.services.lead_validation import LeadValidationError
from common.auth.context import AuthContext


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


def _parse_csv(csv_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(csv_text)))


def _delete_export_test_leads() -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM public.founder_venue_leads WHERE name LIKE 'ZZ_ExportTest%'"
        )


def _insert_export_test_lead(
    *,
    name: str,
    email: str | None = None,
    state: str = "VIC",
    suburb: str = "Fitzroy",
    founder_fit_score: int = 75,
    outreach_status: str = "not_contacted",
    contact_permission_status: str = "public_business_contact",
    notes: str | None = None,
    suppressed_at: str | None = None,
) -> str:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.founder_venue_leads (
              name, normalized_name, suburb, state, postcode, email,
              founder_fit_score, confidence_score,
              outreach_status, contact_permission_status, notes, suppressed_at
            ) VALUES (
              %s, %s, %s, %s, '3065', %s,
              %s, 60,
              %s, %s, %s,
              CASE WHEN %s IS NULL THEN NULL ELSE %s::timestamptz END
            )
            RETURNING id::text
            """,
            [
                name,
                name.lower(),
                suburb,
                state,
                email,
                founder_fit_score,
                outreach_status,
                contact_permission_status,
                notes,
                suppressed_at,
                suppressed_at,
            ],
        )
        return cursor.fetchone()[0]


class ExportSafetyUnitTests(SimpleTestCase):
    def test_default_csv_columns_include_email_redacted_reason(self) -> None:
        self.assertIn("email_redacted_reason", DEFAULT_CSV_COLUMNS)
        self.assertIn("venue_name", DEFAULT_CSV_COLUMNS)
        self.assertNotIn("notes", DEFAULT_CSV_COLUMNS)

    def test_safe_generic_email_included(self) -> None:
        email, reason = resolve_export_email(
            email="info@venue.com.au",
            email_safety_class="generic_business_contact",
            outreach_status="not_contacted",
            contact_permission_status="public_business_contact",
            suppressed_at=None,
            include_unsafe_emails=False,
        )
        self.assertEqual(email, "info@venue.com.au")
        self.assertEqual(reason, "")

    def test_unsafe_personal_email_redacted_by_default(self) -> None:
        email, reason = resolve_export_email(
            email="owner@gmail.com",
            email_safety_class="likely_personal_or_unsafe",
            outreach_status="not_contacted",
            contact_permission_status="public_business_contact",
            suppressed_at=None,
            include_unsafe_emails=False,
        )
        self.assertEqual(email, "")
        self.assertEqual(reason, "likely_personal_or_unsafe")

    def test_unsafe_email_included_with_flag(self) -> None:
        email, reason = resolve_export_email(
            email="owner@gmail.com",
            email_safety_class="likely_personal_or_unsafe",
            outreach_status="not_contacted",
            contact_permission_status="public_business_contact",
            suppressed_at=None,
            include_unsafe_emails=True,
        )
        self.assertEqual(email, "owner@gmail.com")
        self.assertEqual(reason, "")

    def test_dnc_redacts_email_even_when_included(self) -> None:
        email, reason = resolve_export_email(
            email="info@venue.com.au",
            email_safety_class="generic_business_contact",
            outreach_status="do_not_contact",
            contact_permission_status="do_not_contact",
            suppressed_at=None,
            include_unsafe_emails=True,
        )
        self.assertEqual(email, "")
        self.assertEqual(reason, "do_not_contact")

    def test_opted_out_redacts_email(self) -> None:
        email, reason = resolve_export_email(
            email="info@venue.com.au",
            email_safety_class="generic_business_contact",
            outreach_status="not_contacted",
            contact_permission_status="opted_out",
            suppressed_at=None,
            include_unsafe_emails=False,
        )
        self.assertEqual(email, "")
        self.assertEqual(reason, "opted_out")

    def test_suppressed_redacts_email(self) -> None:
        email, reason = resolve_export_email(
            email="info@venue.com.au",
            email_safety_class="generic_business_contact",
            outreach_status="not_contacted",
            contact_permission_status="public_business_contact",
            suppressed_at="2026-01-01T00:00:00Z",
            include_unsafe_emails=False,
        )
        self.assertEqual(email, "")
        self.assertEqual(reason, "suppressed")

    def test_notes_truncated_by_default(self) -> None:
        long_notes = "word " * 80
        summary = truncate_notes_summary(long_notes)
        self.assertLessEqual(len(summary), 200)
        self.assertTrue(summary.endswith("..."))

    def test_parse_export_filters_passes_state_and_score(self) -> None:
        filters = parse_export_filters(
            {"state": "vic", "score_min": "60", "limit": "500"}
        )
        self.assertEqual(filters.state, "VIC")
        self.assertEqual(filters.score_min, 60)
        self.assertEqual(filters.limit, 500)

    def test_parse_export_rejects_limit_over_max(self) -> None:
        with self.assertRaises(LeadValidationError):
            parse_export_filters({"limit": "6000"})


class FounderVenueExportApiTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_export_requires_internal_admin(self) -> None:
        self.assertEqual(
            self.client.get("/api/v1/internal/founder-venues/export.csv").status_code,
            401,
        )

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_consumer_ctx())
    def test_consumer_rejected_for_export(self, _jwt) -> None:
        r = self.client.get(
            "/api/v1/internal/founder-venues/export.csv",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 403)

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.export_founder_venue_leads_csv")
    def test_export_returns_text_csv(self, mock_export, _jwt) -> None:
        mock_export.return_value = FounderVenueExportResult(
            csv_text="founder_venue_lead_id,venue_name\n1,Pub\n",
            row_count=1,
            filters_applied={},
            excluded_counts=ExportExcludedCounts(),
            generated_at="2026-06-01T00:00:00+00:00",
        )
        r = self.client.get(
            "/api/v1/internal/founder-venues/export.csv?state=VIC",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/csv", r["Content-Type"])
        self.assertIn("pubplus_founder_venues_", r["Content-Disposition"])
        mock_export.assert_called_once()
        self.assertEqual(mock_export.call_args.kwargs["state"], "VIC")

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.export_founder_venue_leads_csv")
    def test_export_validates_max_limit(self, mock_export, _jwt) -> None:
        r = self.client.get(
            "/api/v1/internal/founder-venues/export.csv?limit=6000",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 400)
        mock_export.assert_not_called()


class FounderVenueExportCommandTests(SimpleTestCase):
    @patch("apps.founder_venues.management.commands.export_founder_venue_leads.export_founder_venue_leads_csv")
    def test_command_writes_output_file(self, mock_export) -> None:
        mock_export.return_value = FounderVenueExportResult(
            csv_text="founder_venue_lead_id,venue_name\n",
            row_count=0,
            filters_applied={"state": "VIC"},
            excluded_counts=ExportExcludedCounts(),
            generated_at="2026-06-01T00:00:00+00:00",
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as tmp:
            path = tmp.name

        out = StringIO()
        call_command(
            "export_founder_venue_leads",
            "--state",
            "VIC",
            "--output",
            path,
            stdout=out,
        )
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("founder_venue_lead_id", content)
        self.assertIn("Rows exported", out.getvalue())
        mock_export.assert_called_once()


@unittest.skipUnless(_founder_tables_available(), "migration 0033 not applied")
class FounderVenueExportDbTests(TestCase):
    def setUp(self) -> None:
        if not _founder_tables_available():
            self.skipTest("founder_venue_leads table not available.")
        _delete_export_test_leads()

    def tearDown(self) -> None:
        if _founder_tables_available():
            _delete_export_test_leads()

    def test_export_includes_safe_email_and_default_columns(self) -> None:
        _insert_export_test_lead(
            name="ZZ_ExportTest Safe",
            email="info@zz-export-safe.example",
        )
        result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest Safe",
            limit=10,
        )
        rows = _parse_csv(result.csv_text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["email"], "info@zz-export-safe.example")
        self.assertEqual(rows[0]["email_redacted_reason"], "")
        for col in DEFAULT_CSV_COLUMNS:
            self.assertIn(col, rows[0])

    def test_unsafe_email_redacted_in_csv(self) -> None:
        _insert_export_test_lead(
            name="ZZ_ExportTest Unsafe",
            email="owner@gmail.com",
        )
        result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest Unsafe",
            limit=10,
        )
        rows = _parse_csv(result.csv_text)
        self.assertEqual(rows[0]["email"], "")
        self.assertEqual(rows[0]["email_redacted_reason"], "likely_personal_or_unsafe")
        self.assertGreaterEqual(result.excluded_counts.unsafe_email_redacted, 1)

    def test_unsafe_email_included_with_flag(self) -> None:
        _insert_export_test_lead(
            name="ZZ_ExportTest Unsafe Inc",
            email="owner@gmail.com",
        )
        result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest Unsafe Inc",
            include_unsafe_emails=True,
            limit=10,
        )
        rows = _parse_csv(result.csv_text)
        self.assertEqual(rows[0]["email"], "owner@gmail.com")

    def test_do_not_contact_excluded_by_default(self) -> None:
        _insert_export_test_lead(
            name="ZZ_ExportTest DNC",
            email="info@zz-dnc.example",
            outreach_status="do_not_contact",
            contact_permission_status="do_not_contact",
        )
        result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest DNC",
            limit=10,
        )
        self.assertEqual(result.row_count, 0)
        self.assertGreaterEqual(result.excluded_counts.do_not_contact_excluded, 1)

    def test_opted_out_excluded_by_default(self) -> None:
        _insert_export_test_lead(
            name="ZZ_ExportTest OptOut",
            email="info@zz-optout.example",
            contact_permission_status="opted_out",
        )
        result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest OptOut",
            limit=10,
        )
        self.assertEqual(result.row_count, 0)

    def test_suppressed_excluded_by_default(self) -> None:
        _insert_export_test_lead(
            name="ZZ_ExportTest Suppressed",
            email="info@zz-suppressed.example",
            suppressed_at="2026-01-01T00:00:00+00:00",
        )
        result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest Suppressed",
            limit=10,
        )
        self.assertEqual(result.row_count, 0)
        self.assertGreaterEqual(result.excluded_counts.suppressed_excluded, 1)

    def test_state_filter_applied(self) -> None:
        _insert_export_test_lead(
            name="ZZ_ExportTest NSW",
            email="info@zz-nsw.example",
            state="NSW",
        )
        result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest NSW",
            state="VIC",
            limit=10,
        )
        self.assertEqual(result.row_count, 0)

    def test_raw_notes_only_with_flag(self) -> None:
        _insert_export_test_lead(
            name="ZZ_ExportTest Notes",
            email="info@zz-notes.example",
            notes="Secret internal note " * 5,
        )
        default_result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest Notes",
            limit=10,
        )
        default_rows = _parse_csv(default_result.csv_text)
        self.assertNotIn("notes", default_rows[0])
        self.assertTrue(default_rows[0]["notes_summary"])

        raw_result = export_founder_venue_leads_csv(
            search="ZZ_ExportTest Notes",
            include_raw_notes=True,
            limit=10,
        )
        raw_rows = _parse_csv(raw_result.csv_text)
        self.assertIn("notes", raw_rows[0])
        self.assertIn("Secret internal note", raw_rows[0]["notes"])

    def test_export_writes_lead_exported_event(self) -> None:
        lead_id = _insert_export_test_lead(
            name="ZZ_ExportTest Event",
            email="info@zz-event.example",
        )
        export_founder_venue_leads_csv(search="ZZ_ExportTest Event", limit=10)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT event_type FROM public.founder_venue_lead_events
                WHERE lead_id = %s::uuid
                """,
                [lead_id],
            )
            events = [row[0] for row in cursor.fetchall()]
        self.assertIn("lead_exported", events)
