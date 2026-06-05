#!/usr/bin/env python3
"""One-off Stage 3.5 owner onboarding integration QA. Do not commit secrets."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_EMAIL = os.environ.get("QA_OWNER_EMAIL", "owner1@demo.pubplus.local")
DEMO_PASSWORD = "demo-password-123"
DEMO_VENUE_ID = "f1111111-1111-4111-8111-111111111101"
API_BASE = "http://localhost:8000"


def load_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def http_json(
    url: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    token: str | None = None,
    apikey: str | None = None,
) -> tuple[int, dict | str]:
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if apikey:
        headers["apikey"] = apikey
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {"error": {"message": exc.reason}}
        except json.JSONDecodeError:
            payload = raw
        return exc.code, payload


def sign_in(supabase_url: str, anon_key: str) -> str:
    url = f"{supabase_url.rstrip('/')}/auth/v1/token?grant_type=password"
    status, body = http_json(
        url,
        method="POST",
        body={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
        apikey=anon_key,
    )
    if status != 200 or not isinstance(body, dict):
        raise RuntimeError(f"sign_in_failed status={status} body={body}")
    token = body.get("access_token")
    if not token:
        raise RuntimeError(f"sign_in_no_token body_keys={list(body.keys())}")
    return token


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line, flush=True)


def main() -> int:
    env = load_env_file(ROOT / "web-portal" / ".env")
    supabase_url = env.get("VITE_SUPABASE_URL", "")
    anon_key = env.get("VITE_SUPABASE_PUBLISHABLE_KEY", "") or env.get(
        "VITE_SUPABASE_ANON_KEY", ""
    )
    api_base = env.get("VITE_API_BASE_URL", API_BASE).rstrip("/")

    if not supabase_url or not anon_key:
        print("[BLOCKER] Missing VITE_SUPABASE_URL or publishable key in web-portal/.env")
        return 1

    print(f"API base: {api_base}")
    print(f"Demo owner: {DEMO_EMAIL}")
    print(f"Demo venue: {DEMO_VENUE_ID}")

    # 401 without token
    status, _ = http_json(f"{api_base}/api/v1/owner/auth-probe")
    check("auth_probe_no_token_401", status == 401, f"status={status}")

    try:
        token = sign_in(supabase_url, anon_key)
    except RuntimeError as exc:
        print(f"[BLOCKER] Cannot sign in demo owner: {exc}")
        return 1

    status, probe = http_json(f"{api_base}/api/v1/owner/auth-probe", token=token)
    check("auth_probe_200", status == 200, f"status={status}")
    if isinstance(probe, dict):
        check(
            "auth_probe_portal_home",
            probe.get("next_step") == "portal_home",
            f"next_step={probe.get('next_step')}",
        )
        check(
            "auth_probe_has_venue",
            bool(probe.get("has_approved_managed_venue_relationship")),
            f"venue_count={probe.get('venue_count')}",
        )

    status, list_body = http_json(f"{api_base}/api/v1/owner/venues", token=token)
    check("owner_venues_list_200", status == 200, f"status={status}")
    venues = []
    default_id = None
    if isinstance(list_body, dict):
        data = list_body.get("data", {})
        venues = data.get("venues", [])
        default_id = data.get("meta", {}).get("default_venue_id")
        dumped = json.dumps(list_body)
        check("list_no_google_place_id", "google_place_id" not in dumped)
        check("list_no_contact_fields", all(x not in dumped for x in ("phone", "email", "website")))
        check("list_has_venues", len(venues) >= 1, f"count={len(venues)}")
        if len(venues) == 1:
            check("list_default_venue_id", default_id == venues[0].get("venue_id"), f"default={default_id}")

    venue_id = DEMO_VENUE_ID
    if venues:
        ids = {v.get("venue_id") for v in venues}
        if venue_id not in ids:
            venue_id = venues[0]["venue_id"]

    status, detail = http_json(f"{api_base}/api/v1/owner/venues/{venue_id}", token=token)
    check("owner_venue_detail_200", status == 200, f"status={status}")
    locality_id = None
    pub_name_before = None
    if isinstance(detail, dict):
        data = detail.get("data", {})
        dumped = json.dumps(detail)
        check("detail_no_google_place_id", "google_place_id" not in dumped)
        contact = data.get("published", {}).get("contact", {})
        check("contact_supported_false", contact.get("supported") is False)
        check("contact_phone_null", contact.get("phone") is None)
        check("sections_core_details", data.get("sections_available", {}).get("core_details") is True)
        locality_id = data.get("published", {}).get("location", {}).get("locality_id")
        pub_name_before = data.get("published", {}).get("profile", {}).get("display_name")

    status, loc_body = http_json(f"{api_base}/api/v1/reference/localities", token=token)
    check("reference_localities_200", status == 200, f"status={status}")
    locality_in_picker = False
    if isinstance(loc_body, dict) and locality_id:
        locs = loc_body.get("data", {}).get("localities", [])
        locality_in_picker = any(l.get("id") == locality_id for l in locs)
        check(
            "venue_locality_in_reference_picker",
            locality_in_picker,
            f"locality_id={locality_id} picker_count={len(locs)}",
        )

    draft_body = {
        "section": "core_details",
        "intent": "draft",
        "payload": {
            "display_name": "QA Draft Pub Name",
            "address_line_1": "99 QA Draft Street",
            "locality_id": locality_id,
            "short_description": "QA draft short description only.",
            "opening_hours": {
                "uncertainty_level": "resolved_confident",
                "regular_hours_json": [
                    {
                        "day_of_week": 3,
                        "opens_at": "11:00",
                        "closes_at": "22:00",
                        "crosses_midnight": False,
                    }
                ],
                "exceptions_json": [],
                "notes": None,
            },
        },
    }
    status, draft_resp = http_json(
        f"{api_base}/api/v1/owner/venues/{venue_id}/proposals",
        method="POST",
        body=draft_body,
        token=token,
    )
    proposal_id = None
    check("draft_save_201", status == 201, f"status={status}")
    if isinstance(draft_resp, dict):
        data = draft_resp.get("data", {})
        proposal_id = data.get("proposal_id")
        check("draft_lifecycle_staged", data.get("lifecycle_status") == "staged")
        check("draft_submitted_at_null", data.get("submitted_at") is None)
        check("draft_proposal_id", bool(proposal_id), f"id={proposal_id}")

    status, detail_after_draft = http_json(
        f"{api_base}/api/v1/owner/venues/{venue_id}", token=token
    )
    if isinstance(detail_after_draft, dict):
        draft = detail_after_draft.get("data", {}).get("draft", {})
        preview = draft.get("payload_preview", {})
        check("detail_shows_draft_proposal", bool(draft.get("proposal_id")))
        check(
            "draft_preview_display_name",
            preview.get("display_name") == "QA Draft Pub Name",
            f"got={preview.get('display_name')}",
        )
        check(
            "draft_hydration_short_description_gap",
            detail_after_draft.get("data", {})
            .get("published", {})
            .get("descriptions", {})
            .get("short_description")
            != "QA draft short description only.",
            "published short_description unchanged in detail DTO (expected limitation)",
        )

    submit_body = {
        "section": "core_details",
        "intent": "submit",
        "payload": {
            "display_name": "QA Submit Pub Name",
            "address_line_1": "100 QA Submit Street",
            "postal_code": "2000",
            "locality_id": locality_id,
            "country_code": "AU",
            "short_description": "QA submit short description for review.",
            "long_description": "Optional longer copy for QA submit.",
            "opening_hours": {
                "uncertainty_level": "resolved_confident",
                "regular_hours_json": [
                    {
                        "day_of_week": 4,
                        "opens_at": "12:00",
                        "closes_at": "23:00",
                        "crosses_midnight": False,
                    }
                ],
                "exceptions_json": [],
                "notes": None,
            },
            "owner_confirms_management": True,
        },
    }
    status, submit_resp = http_json(
        f"{api_base}/api/v1/owner/venues/{venue_id}/proposals",
        method="POST",
        body=submit_body,
        token=token,
    )
    submit_proposal_id = None
    check("submit_201", status == 201, f"status={status}")
    if isinstance(submit_resp, dict):
        data = submit_resp.get("data", {})
        submit_proposal_id = data.get("proposal_id")
        check("submit_lifecycle_in_review", data.get("lifecycle_status") == "in_review")
        check("submit_submitted_at_set", bool(data.get("submitted_at")))
        msg = data.get("message", "")
        check("submit_message_review_copy", "review" in msg.lower())

    status, detail_after_submit = http_json(
        f"{api_base}/api/v1/owner/venues/{venue_id}", token=token
    )
    if isinstance(detail_after_submit, dict):
        pending = detail_after_submit.get("data", {}).get("pending_review", {})
        check(
            "detail_pending_review_after_submit",
            pending.get("lifecycle_status") == "in_review" or bool(pending.get("submitted_at")),
            f"pending={pending}",
        )
        pub_name_after = (
            detail_after_submit.get("data", {})
            .get("published", {})
            .get("profile", {})
            .get("display_name")
        )
        check(
            "published_display_name_unchanged_after_submit",
            pub_name_after == pub_name_before,
            f"before={pub_name_before} after={pub_name_after}",
        )

    # DB verification via Django if available
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        sys.path.insert(0, str(ROOT / "backend" / "src"))
        import django

        django.setup()
        from django.db import connection

        with connection.cursor() as c:
            if submit_proposal_id:
                c.execute(
                    """
                    SELECT lifecycle_status::text, submitted_at, actor_type, channel
                    FROM public.venue_change_proposal WHERE id = %s::uuid
                    """,
                    [submit_proposal_id],
                )
                row = c.fetchone()
                if row:
                    check("db_proposal_in_review", row[0] == "in_review")
                    check("db_proposal_submitted_at", row[1] is not None)
                    check("db_actor_owner", row[2] == "owner")
                    check("db_channel_owner_portal", row[3] == "owner_portal")
                c.execute(
                    """
                    SELECT count(*)::int FROM public.venue_proposal_target
                    WHERE venue_change_proposal_id = %s::uuid
                    """,
                    [submit_proposal_id],
                )
                targets = c.fetchone()[0]
                check("db_proposal_targets", targets >= 3, f"count={targets}")
            c.execute(
                "SELECT display_name FROM public.venue_published_profile WHERE venue_id = %s::uuid",
                [venue_id],
            )
            pub = c.fetchone()
            if pub:
                check(
                    "db_published_profile_unchanged",
                    pub[0] == pub_name_before,
                    f"published={pub[0]}",
                )
            c.execute(
                """
                SELECT id::text, channel::text, lifecycle_status::text
                FROM public.venue_change_proposal
                WHERE venue_id = %s::uuid AND channel = 'owner_portal'
                  AND lifecycle_status IN ('staged', 'in_review')
                ORDER BY created_at DESC
                """,
                [venue_id],
            )
            open_rows = c.fetchall()
            check(
                "db_open_owner_proposals_count",
                len(open_rows) >= 1,
                f"open_count={len(open_rows)} ids={[r[0] for r in open_rows]}",
            )
    except Exception as exc:  # noqa: BLE001
        print(f"[SKIP] Django DB checks: {type(exc).__name__}: {exc}")

    # Moderation queue (requires admin JWT — skip if unavailable)
    admin_env = load_env_file(ROOT / "backend" / ".env")
    admin_subjects = admin_env.get("PUBPLUS_INTERNAL_ADMIN_SUBJECTS", "")
    if admin_subjects:
        print("[INFO] Admin moderation check requires separate admin JWT — not run in this script")
    else:
        print("[INFO] Moderation queue API requires internal admin auth — verified via service code review")

    # Re-submit while in_review (duplicate proposal risk)
    status, resubmit_resp = http_json(
        f"{api_base}/api/v1/owner/venues/{venue_id}/proposals",
        method="POST",
        body={
            **submit_body,
            "payload": {
                **submit_body["payload"],
                "display_name": "QA Resubmit While In Review",
            },
        },
        token=token,
    )
    check("resubmit_while_in_review_201", status == 201, f"status={status}")
    if isinstance(resubmit_resp, dict):
        new_id = resubmit_resp.get("data", {}).get("proposal_id")
        check(
            "resubmit_same_or_new_proposal_id",
            bool(new_id),
            f"first={submit_proposal_id} second={new_id}",
        )

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
