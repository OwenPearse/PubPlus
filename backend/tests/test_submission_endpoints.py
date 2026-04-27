from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

from django.db import connection, transaction
from django.test import TestCase, override_settings
from django.test.client import Client

from common.auth.context import AuthContext

from tests.support.submissions_e2e_data import (
    count_proposals_for_venue,
    get_latest_proposal_id_for_venue,
    try_install_submissions_e2e_fixtures,
)


def _auth_headers() -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": "Bearer test-token"}


def _ctx(sub: str) -> AuthContext:
    return AuthContext(
        subject=sub,
        audience="authenticated",
        issuer="https://example.supabase.co/auth/v1",
        role="authenticated",
        email="e2e-submissions@pubplus.test",
        claims={"sub": sub},
    )


@override_settings(
    SUPABASE_JWT_JWKS_URL="https://example.supabase.co/auth/v1/keys"
)
class SubmissionIntakeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.csrf_client = Client(enforce_csrf_checks=True)

    def _delete_workflow_for_venue(self, venue_id: str) -> None:
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM public.venue_change_proposal WHERE venue_id = %s::uuid",
                [venue_id],
            )

    def test_unauthenticated_corrections(self) -> None:
        r = self.client.post(
            "/api/v1/submissions/corrections",
            data='{"venue_id":"%s","domain":"profile","proposed_values":{"display_name":"X"}}' % str(uuid4()),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    def test_unauthenticated_new_venues(self) -> None:
        r = self.client.post(
            "/api/v1/submissions/new-venues",
            data='{"name":"A","address_line_1":"1 St"}',
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 401)

    def test_malformed_json(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        ctx = _ctx(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.post(
                "/api/v1/submissions/corrections",
                data="not json",
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r2 = self.client.post(
                "/api/v1/submissions/new-venues",
                data="not json",
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r2.status_code, 400)

    def test_submission_mutations_with_bearer_do_not_require_csrf(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        ctx = _ctx(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            correction = self.csrf_client.post(
                "/api/v1/submissions/corrections",
                data=json.dumps(
                    {
                        "venue_id": e2e.venue_id,
                        "domain": "profile",
                        "proposed_values": {"display_name": "CSRF test name"},
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertNotEqual(correction.status_code, 403, correction.content)

        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            suggestion = self.csrf_client.post(
                "/api/v1/submissions/new-venues",
                data=json.dumps(
                    {
                        "name": "CSRF Test Venue",
                        "address_line_1": "1 CSRF Street",
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertNotEqual(suggestion.status_code, 403, suggestion.content)

    def test_unsupported_domain_rejected(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        with transaction.atomic():
            self._delete_workflow_for_venue(e2e.venue_id)
        ctx = _ctx(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.post(
                "/api/v1/submissions/corrections",
                data=json.dumps(
                    {
                        "venue_id": e2e.venue_id,
                        "domain": "specials",
                        "proposed_values": {"x": 1},
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)

    def test_invalid_venue_rejected(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        ctx = _ctx(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.post(
                "/api/v1/submissions/corrections",
                data=json.dumps(
                    {
                        "venue_id": str(uuid4()),
                        "domain": "profile",
                        "proposed_values": {"display_name": "X"},
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 404)

    def test_profile_correction(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        with transaction.atomic():
            self._delete_workflow_for_venue(e2e.venue_id)
        n0 = count_proposals_for_venue(e2e.venue_id)
        ctx = _ctx(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.post(
                "/api/v1/submissions/corrections",
                data=json.dumps(
                    {
                        "venue_id": e2e.venue_id,
                        "domain": "profile",
                        "proposed_values": {"display_name": "E2E correction name"},
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 201, r.content)
        b = r.json()
        self.assertEqual(b.get("status"), "received")
        self.assertIn("message", b)
        self.assertEqual(
            count_proposals_for_venue(e2e.venue_id), n0 + 1, "expected proposal row"
        )

    def test_location_attributes_hours_corrections(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        with transaction.atomic():
            self._delete_workflow_for_venue(e2e.venue_id)
        ctx = _ctx(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r1 = self.client.post(
                "/api/v1/submissions/corrections",
                data=json.dumps(
                    {
                        "venue_id": e2e.venue_id,
                        "domain": "location",
                        "proposed_values": {"address_line_1": "2 Test Rd"},
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r1.status_code, 201)
        with transaction.atomic():
            self._delete_workflow_for_venue(e2e.venue_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r2 = self.client.post(
                "/api/v1/submissions/corrections",
                data=json.dumps(
                    {
                        "venue_id": e2e.venue_id,
                        "domain": "attributes",
                        "proposed_values": {
                            "items": [
                                {
                                    "attribute_definition_id": e2e.attribute_definition_id,
                                    "value_boolean": True,
                                }
                            ]
                        },
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r2.status_code, 201)
        with transaction.atomic():
            self._delete_workflow_for_venue(e2e.venue_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r3 = self.client.post(
                "/api/v1/submissions/corrections",
                data=json.dumps(
                    {
                        "venue_id": e2e.venue_id,
                        "domain": "hours",
                        "proposed_values": {
                            "regular_hours_json": [{"dow": 0, "periods": []}]
                        },
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r3.status_code, 201)
        prop = get_latest_proposal_id_for_venue(e2e.venue_id)
        self.assertIsNotNone(prop)
        with connection.cursor() as c:
            c.execute(
                """
                SELECT actor_type::text, channel::text, proposal_kind::text, lifecycle_status::text
                FROM public.venue_change_proposal WHERE id = %s::uuid
                """,
                [str(prop)],
            )
            row = c.fetchone()
        self.assertEqual(
            row,
            ("consumer", "app_consumer", "field_family", "staged"),
        )

    def test_new_venue_suggestion(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        ctx = _ctx(e2e.auth_user_id)
        with connection.cursor() as c:
            c.execute("SELECT count(*)::int FROM public.venue")
            n_before = int(c.fetchone()[0])
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.post(
                "/api/v1/submissions/new-venues",
                data=json.dumps(
                    {
                        "name": "Suggested Pub",
                        "address_line_1": "1 New Street",
                        "locality_id": e2e.locality_id,
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 201, r.content)
        b = r.json()
        self.assertEqual(b.get("status"), "received", "safe acknowledgement only")
        self.assertIn("reviewed", b.get("message", ""))
        with connection.cursor() as c:
            c.execute("SELECT count(*)::int FROM public.venue")
            n_after = int(c.fetchone()[0])
        self.assertEqual(n_after, n_before + 1, "shell venue created for proposal chain only")
        with connection.cursor() as c:
            c.execute(
                """
                SELECT p.venue_id::text, p.proposal_kind::text
                FROM public.venue_change_proposal p
                WHERE p.proposal_kind = 'whole_record' AND p.channel = 'app_consumer'
                ORDER BY p.created_at DESC
                LIMIT 1
                """
            )
            row = c.fetchone()
        self.assertIsNotNone(row, "new-venue flow creates a whole_record proposal")
        v_id, pk = str(row[0]), str(row[1])
        self.assertNotEqual(
            v_id, e2e.venue_id, "new shell must be distinct from the E2E published test venue"
        )
        self.assertEqual(pk, "whole_record", "suggestion is staged, not a straight publish")
        with connection.cursor() as c:
            c.execute(
                """
                SELECT array_agg(target_family::text ORDER BY target_family) AS t
                FROM public.venue_proposal_target
                WHERE venue_change_proposal_id = (
                    SELECT p.id
                    FROM public.venue_change_proposal p
                    WHERE p.venue_id = %s::uuid
                    LIMIT 1
                )
                """,
                [v_id],
            )
            ts = c.fetchone()[0]
        self.assertIsNotNone(ts, "proposal must list staging targets")
        self.assertIn("geo", ts, ts)
        self.assertIn("profile", ts, ts)
        with connection.cursor() as c:
            c.execute(
                """
                SELECT 1
                FROM public.venue v
                LEFT JOIN public.venue_published_profile vpp ON vpp.venue_id = v.id
                WHERE v.id = %s::uuid AND vpp.venue_id IS NULL
                """,
                [v_id],
            )
            published_missing = c.fetchone()
        self.assertTrue(
            published_missing is not None,
            "suggested venue must not be published in venue_published_profile (discovery truth separate)",
        )

    def test_new_venue_rejects_missing_required(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        ctx = _ctx(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.post(
                "/api/v1/submissions/new-venues",
                data=json.dumps(
                    {
                        "name": "OnlyName",
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)

    def test_new_venue_rejects_bad_fk(self) -> None:
        e2e = try_install_submissions_e2e_fixtures()
        if e2e is None:
            self.skipTest("PubPlus workflow schema not available in test database.")
        ctx = _ctx(e2e.auth_user_id)
        with patch("common.auth.guards.verify_supabase_jwt", return_value=ctx):
            r = self.client.post(
                "/api/v1/submissions/new-venues",
                data=json.dumps(
                    {
                        "name": "X",
                        "address_line_1": "1 St",
                        "locality_id": str(uuid4()),
                    }
                ),
                content_type="application/json",
                **_auth_headers(),
            )
        self.assertEqual(r.status_code, 400)
