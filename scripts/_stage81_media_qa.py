#!/usr/bin/env python3
"""Stage 8.1 media deployment + manual upload QA. Do not commit secrets."""
from __future__ import annotations

import json
import os
import struct
import sys
import urllib.error
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
BACKEND_SRC = BACKEND / "src"
for path in (BACKEND, BACKEND_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.conf import settings
from django.db import connection

DEMO_EMAIL = os.environ.get("QA_OWNER_EMAIL", "owner1@demo.pubplus.local")
DEMO_PASSWORD = "demo-password-123"
DEMO_VENUE_ID = "f1111111-1111-4111-8111-111111111101"
API_BASE = "http://localhost:8000"
SUPABASE_URL = settings.SUPABASE_URL
ANON_KEY = settings.SUPABASE_ANON_KEY

results: list[tuple[str, bool, str]] = []
profile_media_id: str | None = None
gallery_media_id: str | None = None
profile_storage_path: str | None = None


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line, flush=True)


def http_json(
    url: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    token: str | None = None,
    apikey: str | None = None,
    raw_body: bytes | None = None,
    content_type: str | None = None,
) -> tuple[int, dict | bytes | str]:
    headers = {"Accept": "application/json"}
    data = raw_body
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif content_type:
        headers["Content-Type"] = content_type
    if apikey:
        headers["apikey"] = apikey
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            ct = resp.headers.get("Content-Type", "")
            if "json" in ct:
                return resp.status, json.loads(raw.decode("utf-8"))
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            payload = raw.decode("utf-8", errors="replace")
        return exc.code, payload


def make_png() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xfc\x00\x00\x00\x00\x00\x01"))
    iend = chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


def sign_in(email: str) -> str:
    status, body = http_json(
        f"{SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password",
        method="POST",
        body={"email": email, "password": DEMO_PASSWORD},
        apikey=ANON_KEY,
    )
    if status != 200 or not isinstance(body, dict):
        raise RuntimeError(f"sign_in_failed email={email} status={status} body={body}")
    token = body.get("access_token")
    if not token:
        raise RuntimeError(f"sign_in_no_token email={email}")
    return str(token)


def verify_db_and_audit() -> None:
    global profile_media_id, gallery_media_id, profile_storage_path
    with connection.cursor() as c:
        if profile_media_id:
            c.execute(
                """
                SELECT storage_bucket, storage_path, purpose, catalog_record_status,
                       uploaded_by_owner_account_id IS NOT NULL
                FROM public.venue_published_media
                WHERE id = %s::uuid
                """,
                [profile_media_id],
            )
            row = c.fetchone()
            check(
                "postgres profile row",
                row is not None
                and row[0] == "venue-media"
                and row[2] == "profile"
                and row[3] == "active"
                and row[4],
                str(row) if row else "missing",
            )
            if row:
                profile_storage_path = row[1]

        c.execute(
            """
            SELECT COUNT(*)::int FROM public.audit_event
            WHERE action = 'owner_direct_edit'
              AND entity_table = 'venue_published_media'
              AND detail->>'field_family' = 'media'
              AND entity_id = %s::uuid
            """,
            [DEMO_VENUE_ID],
        )
        audit_count = c.fetchone()[0]
        check("audit_event media rows", audit_count >= 1, f"count={audit_count}")

        if gallery_media_id:
            c.execute(
                """
                SELECT catalog_record_status FROM public.venue_published_media
                WHERE id = %s::uuid
                """,
                [gallery_media_id],
            )
            g_row = c.fetchone()
            check(
                "postgres gallery retired",
                g_row is not None and g_row[0] == "retired",
                str(g_row[0]) if g_row else "missing",
            )


def main() -> int:
    global profile_media_id, gallery_media_id

    check("SUPABASE_SERVICE_ROLE_KEY configured", bool(settings.SUPABASE_SERVICE_ROLE_KEY))
    check(
        "SUPABASE_STORAGE_BUCKET_VENUE_MEDIA",
        settings.SUPABASE_STORAGE_BUCKET_VENUE_MEDIA == "venue-media",
        settings.SUPABASE_STORAGE_BUCKET_VENUE_MEDIA,
    )

    token = sign_in(DEMO_EMAIL)
    check("owner_sign_in", True, DEMO_EMAIL)

    status, body = http_json(
        f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media", token=token
    )
    check("GET media", status == 200, f"status={status}")

    status, _ = http_json(
        f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media/upload-intent",
        method="POST",
        token=token,
        body={
            "purpose": "profile",
            "file_name": "x.gif",
            "content_type": "image/gif",
            "file_size_bytes": 100,
        },
    )
    check("upload-intent rejects gif", status == 400, f"status={status}")

    status, _ = http_json(
        f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media/upload-intent",
        method="POST",
        token=token,
        body={
            "purpose": "profile",
            "file_name": "big.png",
            "content_type": "image/png",
            "file_size_bytes": 6_000_000,
        },
    )
    check("upload-intent rejects oversized", status == 400, f"status={status}")

    png = make_png()
    status, intent_body = http_json(
        f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media/upload-intent",
        method="POST",
        token=token,
        body={
            "purpose": "profile",
            "file_name": "qa-profile.png",
            "content_type": "image/png",
            "file_size_bytes": len(png),
        },
    )
    check("upload-intent profile", status in (200, 201), f"status={status}")
    if status >= 400 or not isinstance(intent_body, dict):
        print(json.dumps(intent_body, indent=2))
        return 1

    intent = intent_body["data"]
    check("signed URL issued", bool(intent.get("signed_upload_url")))
    check(
        "storage path format",
        str(intent["storage_path"]).startswith(f"venues/{DEMO_VENUE_ID}/profile/"),
        intent["storage_path"],
    )

    signed = intent["signed_upload_url"]
    if signed.startswith("/"):
        signed = SUPABASE_URL.rstrip("/") + signed
    put_status, _ = http_json(
        signed, method="PUT", raw_body=png, content_type="image/png"
    )
    check("PUT to signed URL", put_status in (200, 201), f"status={put_status}")

    status, _ = http_json(
        f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media",
        method="POST",
        token=token,
        body={
            "media_id": intent["media_id"],
            "purpose": "profile",
            "storage_bucket": "venue-media",
            "storage_path": f"venues/{DEMO_VENUE_ID}/profile/evil.jpg",
        },
    )
    check("reject arbitrary path", status == 400, f"status={status}")

    status, commit_body = http_json(
        f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media",
        method="POST",
        token=token,
        body={
            "media_id": intent["media_id"],
            "purpose": "profile",
            "storage_bucket": "venue-media",
            "storage_path": intent["storage_path"],
            "caption": "QA profile",
            "alt_text": "QA alt",
        },
    )
    check("POST media commit profile", status in (200, 201), f"status={status}")
    if isinstance(commit_body, dict):
        profile_media_id = commit_body.get("data", {}).get("media_item", {}).get("id")

    status, g_intent_body = http_json(
        f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media/upload-intent",
        method="POST",
        token=token,
        body={
            "purpose": "gallery",
            "file_name": "qa-gallery.png",
            "content_type": "image/png",
            "file_size_bytes": len(png),
        },
    )
    if status >= 400 or not isinstance(g_intent_body, dict):
        check("upload-intent gallery", False, f"status={status}")
    else:
        g_intent = g_intent_body["data"]
        signed_g = g_intent["signed_upload_url"]
        if signed_g.startswith("/"):
            signed_g = SUPABASE_URL.rstrip("/") + signed_g
        http_json(signed_g, method="PUT", raw_body=png, content_type="image/png")
        status, g_commit = http_json(
            f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media",
            method="POST",
            token=token,
            body={
                "media_id": g_intent["media_id"],
                "purpose": "gallery",
                "storage_bucket": "venue-media",
                "storage_path": g_intent["storage_path"],
                "caption": "Gallery QA",
            },
        )
        check("gallery upload commit", status in (200, 201), f"status={status}")
        if isinstance(g_commit, dict):
            gallery_media_id = g_commit.get("data", {}).get("media_item", {}).get("id")

    if gallery_media_id:
        status, _ = http_json(
            f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media/{gallery_media_id}",
            method="PATCH",
            token=token,
            body={"caption": "Updated gallery caption", "alt_text": "Updated alt"},
        )
        check("PATCH caption/alt", status == 200, f"status={status}")

        status, _ = http_json(
            f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media/{gallery_media_id}",
            method="DELETE",
            token=token,
        )
        check("DELETE/deactivate gallery", status == 200, f"status={status}")

    status, list2 = http_json(
        f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media", token=token
    )
    active_ids: list[str] = []
    if status == 200 and isinstance(list2, dict):
        active_ids = [m["id"] for m in list2.get("data", {}).get("media", [])]
    check(
        "deactivated gallery hidden",
        gallery_media_id is None or gallery_media_id not in active_ids,
    )
    check(
        "profile persists in GET",
        profile_media_id is not None and profile_media_id in active_ids,
    )

    try:
        token2 = sign_in("owner2@demo.pubplus.local")
        status, _ = http_json(
            f"{API_BASE}/api/v1/owner/venues/{DEMO_VENUE_ID}/media/upload-intent",
            method="POST",
            token=token2,
            body={
                "purpose": "profile",
                "file_name": "x.png",
                "content_type": "image/png",
                "file_size_bytes": 100,
            },
        )
        check("missing capability 403", status == 403, f"status={status}")
    except RuntimeError as exc:
        check("missing capability 403", False, str(exc))

    verify_db_and_audit()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\nSUMMARY: {passed}/{total} passed")
    failed = [name for name, ok, _ in results if not ok]
    if failed:
        print("FAILED:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
