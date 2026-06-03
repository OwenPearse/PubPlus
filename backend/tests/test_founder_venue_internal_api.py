from __future__ import annotations

from unittest.mock import patch

from django.test import Client, SimpleTestCase, TestCase

from apps.founder_venues.services.import_service import FounderVenueImportResult
from apps.founder_venues.services.lead_validation import LeadValidationError
from common.auth.context import AuthContext


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


LEAD_ID = "00000000-0000-4000-8000-000000000001"


class FounderVenueInternalApiAuthTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_list_requires_internal_admin(self) -> None:
        self.assertEqual(
            self.client.get("/api/v1/internal/founder-venues/leads").status_code,
            401,
        )

    def test_consumer_rejected_for_list(self) -> None:
        with patch("common.auth.guards.verify_supabase_jwt", return_value=_consumer_ctx()):
            r = self.client.get(
                "/api/v1/internal/founder-venues/leads",
                HTTP_AUTHORIZATION="Bearer token",
            )
        self.assertEqual(r.status_code, 403)

    def test_consumer_rejected_for_import(self) -> None:
        with patch("common.auth.guards.verify_supabase_jwt", return_value=_consumer_ctx()):
            r = self.client.post(
                "/api/v1/internal/founder-venues/import",
                data='{"csv_text":"name\\nPub"}',
                content_type="application/json",
                HTTP_AUTHORIZATION="Bearer token",
            )
        self.assertEqual(r.status_code, 403)


class FounderVenueInternalApiValidationTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.list_founder_venue_leads")
    def test_list_validates_limit_max(self, mock_list, _jwt) -> None:
        r = self.client.get(
            "/api/v1/internal/founder-venues/leads?limit=500",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 400)
        mock_list.assert_not_called()

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.import_founder_venue_leads_csv")
    def test_import_validates_source_type(self, mock_import, _jwt) -> None:
        r = self.client.post(
            "/api/v1/internal/founder-venues/import",
            data='{"csv_text":"business_name\\nX","source_type":"bad"}',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 400)
        mock_import.assert_not_called()

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.recompute_founder_fit_scores")
    def test_recompute_requires_constraint(self, mock_recompute, _jwt) -> None:
        r = self.client.post(
            "/api/v1/internal/founder-venues/recompute-scores",
            data="{}",
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 400)
        mock_recompute.assert_not_called()


class FounderVenueInternalApiEndpointTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.list_founder_venue_leads")
    def test_list_filters_passed_to_service(self, mock_list, _jwt) -> None:
        mock_list.return_value = {
            "items": [],
            "pagination": {
                "limit": 50,
                "offset": 0,
                "count": 0,
                "total": 0,
                "has_more": False,
            },
        }
        r = self.client.get(
            "/api/v1/internal/founder-venues/leads?state=VIC&search=pub",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        mock_list.assert_called_once()
        filters = mock_list.call_args[0][0]
        self.assertEqual(filters.state, "VIC")
        self.assertEqual(filters.search, "pub")

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.get_founder_venue_lead_detail")
    def test_detail_returns_payload(self, mock_detail, _jwt) -> None:
        mock_detail.return_value = {
            "lead": {"id": LEAD_ID, "name": "Test"},
            "sources": [],
            "field_attributions": [],
            "events": [],
        }
        r = self.client.get(
            f"/api/v1/internal/founder-venues/leads/{LEAD_ID}",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("lead", body)
        self.assertIn("sources", body)

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.import_founder_venue_leads_csv")
    def test_import_returns_summary(self, mock_import, _jwt) -> None:
        mock_import.return_value = FounderVenueImportResult(
            rows_processed=1,
            leads_created=1,
        )
        r = self.client.post(
            "/api/v1/internal/founder-venues/import",
            data='{"csv_text":"business_name\\nPub","source_type":"csv_import"}',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["leads_created"], 1)
        mock_import.assert_called_once()

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.recompute_founder_fit_scores")
    def test_recompute_calls_service(self, mock_recompute, _jwt) -> None:
        from apps.founder_venues.services.founder_fit_db import FounderFitRecomputeResult

        mock_recompute.return_value = FounderFitRecomputeResult(processed=2, updated=2)
        r = self.client.post(
            "/api/v1/internal/founder-venues/recompute-scores",
            data='{"state":"VIC","limit":100,"dry_run":true}',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        mock_recompute.assert_called_once()

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.get_top_founder_venue_leads")
    def test_top_returns_items(self, mock_top, _jwt) -> None:
        mock_top.return_value = [{"id": LEAD_ID, "founder_fit_score": 80}]
        r = self.client.get(
            "/api/v1/internal/founder-venues/top?state=VIC",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["items"]), 1)

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    def test_patch_rejects_unknown_fields(self, _jwt) -> None:
        r = self.client.patch(
            f"/api/v1/internal/founder-venues/leads/{LEAD_ID}",
            data='{"founder_fit_score":99}',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "validation_error")

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.mark_lead_do_not_contact")
    def test_mark_do_not_contact(self, mock_mark, _jwt) -> None:
        mock_mark.return_value = {
            "lead": {"outreach_status": "do_not_contact"},
            "sources": [],
            "field_attributions": [],
            "events": [],
        }
        r = self.client.post(
            f"/api/v1/internal/founder-venues/leads/{LEAD_ID}/mark-do-not-contact",
            data='{"reason":"Requested"}',
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        mock_mark.assert_called_once()


class LeadValidationUnitTests(SimpleTestCase):
    def test_parse_list_filters_sort(self) -> None:
        from apps.founder_venues.services.lead_queries import parse_list_filters

        f = parse_list_filters({"sort": "name_asc"})
        self.assertEqual(f.sort, "name_asc")

    def test_parse_list_filters_invalid_sort(self) -> None:
        from apps.founder_venues.services.lead_queries import parse_list_filters

        with self.assertRaises(LeadValidationError):
            parse_list_filters({"sort": "DROP TABLE"})

    def test_parse_list_filters_outreach_status_in(self) -> None:
        from apps.founder_venues.services.lead_queries import parse_list_filters

        f = parse_list_filters({"outreach_status_in": "called,emailed"})
        self.assertEqual(f.outreach_status_in, ("called", "emailed"))
        self.assertIsNone(f.outreach_status)

    def test_parse_list_filters_contacted_before_iso(self) -> None:
        from apps.founder_venues.services.lead_queries import parse_list_filters

        f = parse_list_filters({"contacted_before": "2026-01-01T00:00:00Z"})
        self.assertIsNotNone(f.contacted_before)

    def test_parse_list_filters_invalid_contacted_before(self) -> None:
        from apps.founder_venues.services.lead_queries import parse_list_filters

        with self.assertRaises(LeadValidationError):
            parse_list_filters({"contacted_before": "not-a-date"})


class FounderVenueListDtoTests(SimpleTestCase):
    def test_lead_list_item_dto_includes_last_contact_fields(self) -> None:
        from apps.founder_venues.services.lead_queries import lead_list_item_dto

        dto = lead_list_item_dto(
            {
                "id": LEAD_ID,
                "name": "Test Pub",
                "notes": "A" * 250,
                "last_contacted_at": None,
                "last_contact_channel": "phone",
                "confidence_score": 1,
                "founder_fit_score": 2,
                "enrichment_status": "imported",
                "outreach_status": "called",
                "contact_permission_status": "public_business_contact",
            }
        )
        self.assertIn("last_contacted_at", dto)
        self.assertEqual(dto["last_contact_channel"], "phone")
        self.assertTrue(dto["notes_summary"].endswith("..."))


class FounderVenueSummaryEndpointTests(SimpleTestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_summary_requires_internal_admin(self) -> None:
        self.assertEqual(
            self.client.get("/api/v1/internal/founder-venues/summary").status_code,
            401,
        )

    @patch("common.auth.guards.verify_supabase_jwt", return_value=_internal_ctx())
    @patch("api.v1.internal.founder_venues.views.get_founder_venue_workspace_summary")
    def test_summary_returns_expected_keys(self, mock_summary, _jwt) -> None:
        mock_summary.return_value = {
            "total_leads": 100,
            "vic_leads": 40,
            "vic_score_80_plus": 10,
            "not_contacted": 50,
            "called": 5,
            "emailed": 3,
            "replied": 2,
            "signed_up": 1,
            "rejected": 1,
            "do_not_contact": 0,
            "needs_review": 2,
            "missing_email": 20,
            "missing_website": 15,
            "missing_phone": 5,
            "enriched": 8,
            "imported": 90,
        }
        r = self.client.get(
            "/api/v1/internal/founder-venues/summary",
            HTTP_AUTHORIZATION="Bearer token",
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["vic_leads"], 40)
        self.assertEqual(body["not_contacted"], 50)
