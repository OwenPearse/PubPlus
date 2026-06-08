"""
Owner venue photo/media direct-edit (Stage 8).

Metadata in venue_published_media; files in Supabase Storage venue-media bucket.
Upload paths are backend-issued via owner_venue_media_upload_intent rows.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from django.conf import settings
from django.db import connection, transaction

from apps.owner.services.owner_venue_service import (
    _write_owner_direct_edit_audit,
    assert_owner_can_direct_edit,
)
from common.auth.context import AuthContext
from common.storage import public_storage_object_url
from common.storage.supabase_storage import (
    SupabaseStorageError,
    create_signed_upload_url,
    storage_object_exists,
)

_MEDIA_BUCKET_SETTING = "SUPABASE_STORAGE_BUCKET_VENUE_MEDIA"
_DEFAULT_MEDIA_BUCKET = "venue-media"
_MEDIA_KIND = "image"
_ALLOWED_PURPOSES = frozenset({"profile", "gallery"})
_ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
_CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
_MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
_MAX_CAPTION_LEN = 200
_MAX_ALT_TEXT_LEN = 200
_MAX_SORT_ORDER = 999
_UPLOAD_INTENT_TTL_SECONDS = 600
_STORAGE_PATH_RE = re.compile(
    r"^venues/[0-9a-f-]{36}/(profile|gallery)/[0-9a-f-]{36}\.(jpg|jpeg|png|webp)$",
    re.IGNORECASE,
)

_UPLOAD_INTENT_ALLOWED_KEYS = frozenset(
    {"purpose", "file_name", "content_type", "file_size_bytes"}
)
_CREATE_ALLOWED_KEYS = frozenset(
    {
        "media_id",
        "purpose",
        "storage_bucket",
        "storage_path",
        "caption",
        "alt_text",
        "sort_order",
    }
)
_PATCH_ALLOWED_KEYS = frozenset(
    {"caption", "alt_text", "sort_order", "purpose", "active"}
)


def media_bucket_name() -> str:
    return str(getattr(settings, _MEDIA_BUCKET_SETTING, _DEFAULT_MEDIA_BUCKET))


def _public_media_url(storage_bucket: str, storage_path: str) -> str:
    return public_storage_object_url(
        str(settings.SUPABASE_URL),
        storage_bucket,
        storage_path,
    )


def _extension_for_content_type(content_type: str) -> str | None:
    return _CONTENT_TYPE_EXTENSIONS.get(content_type)


def _build_storage_path(venue_id: str, purpose: str, media_id: str, ext: str) -> str:
    return f"venues/{venue_id}/{purpose}/{media_id}.{ext}"


def _media_row_to_public(row: tuple) -> dict[str, Any]:
    (
        media_id,
        purpose,
        media_kind,
        storage_bucket,
        storage_path,
        caption,
        alt_text,
        sort_order,
        catalog_status,
    ) = row
    return {
        "id": str(media_id),
        "purpose": purpose,
        "media_kind": media_kind,
        "url": _public_media_url(storage_bucket, storage_path),
        "storage_bucket": storage_bucket,
        "storage_path": storage_path,
        "caption": caption,
        "alt_text": alt_text,
        "sort_order": int(sort_order),
        "active": catalog_status == "active",
    }


def _load_owner_media_rows(venue_id: str, *, active_only: bool = True) -> list[tuple]:
    status_clause = "AND catalog_record_status = 'active'" if active_only else ""
    with connection.cursor() as c:
        c.execute(
            f"""
            SELECT
              id,
              purpose,
              media_kind,
              storage_bucket,
              storage_path,
              caption,
              alt_text,
              sort_order,
              catalog_record_status
            FROM public.venue_published_media
            WHERE venue_id = %s::uuid
              {status_clause}
            ORDER BY
              CASE purpose WHEN 'profile' THEN 0 ELSE 1 END,
              sort_order,
              created_at
            """,
            [venue_id],
        )
        return list(c.fetchall())


def _build_media_response(venue_id: str) -> dict[str, Any]:
    rows = _load_owner_media_rows(venue_id)
    return {
        "venue_id": venue_id,
        "media": [_media_row_to_public(row) for row in rows],
    }


def _snapshot_media_for_audit(venue_id: str) -> list[dict[str, Any]]:
    return [_media_row_to_public(row) for row in _load_owner_media_rows(venue_id)]


def _validate_upload_intent_body(
    body: Any,
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(body, dict):
        return None, {"body": ["Request body must be a JSON object."]}

    unknown = sorted(set(body.keys()) - _UPLOAD_INTENT_ALLOWED_KEYS)
    details: dict[str, list[str]] = {}
    for key in unknown:
        details[key] = ["Unknown field."]

    purpose = body.get("purpose")
    if purpose not in _ALLOWED_PURPOSES:
        details["purpose"] = ["Must be profile or gallery."]

    content_type = body.get("content_type")
    if content_type not in _ALLOWED_CONTENT_TYPES:
        details["content_type"] = ["Must be image/jpeg, image/png, or image/webp."]

    file_size = body.get("file_size_bytes")
    if not isinstance(file_size, int) or isinstance(file_size, bool):
        details["file_size_bytes"] = ["Must be an integer."]
    elif file_size <= 0 or file_size > _MAX_FILE_SIZE_BYTES:
        details["file_size_bytes"] = [
            f"Must be between 1 and {_MAX_FILE_SIZE_BYTES} bytes."
        ]

    file_name = body.get("file_name")
    if not isinstance(file_name, str) or not file_name.strip():
        details["file_name"] = ["file_name is required."]
    else:
        trimmed = file_name.strip()
        if len(trimmed) > 255:
            details["file_name"] = ["Must be at most 255 characters."]
        if content_type in _ALLOWED_CONTENT_TYPES:
            ext = _extension_for_content_type(content_type)
            lower = trimmed.lower()
            if ext and not lower.endswith(f".{ext}") and not lower.endswith(".jpeg"):
                if content_type == "image/jpeg" and not lower.endswith(".jpg"):
                    details["file_name"] = [
                        "File extension must match content type (jpg/jpeg, png, or webp)."
                    ]
                elif content_type != "image/jpeg":
                    details["file_name"] = [
                        "File extension must match content type (jpg/jpeg, png, or webp)."
                    ]

    if details:
        return None, details
    assert isinstance(file_name, str)
    assert isinstance(content_type, str)
    assert isinstance(file_size, int)
    return {
        "purpose": purpose,
        "file_name": file_name.strip(),
        "content_type": content_type,
        "file_size_bytes": file_size,
    }, None


def _validate_create_body(
    body: Any,
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(body, dict):
        return None, {"body": ["Request body must be a JSON object."]}

    unknown = sorted(set(body.keys()) - _CREATE_ALLOWED_KEYS)
    details: dict[str, list[str]] = {}
    for key in unknown:
        details[key] = ["Unknown field."]

    media_id = body.get("media_id")
    if not isinstance(media_id, str) or not media_id.strip():
        details["media_id"] = ["media_id is required."]
    else:
        try:
            UUID(media_id.strip())
        except ValueError:
            details["media_id"] = ["Must be a valid UUID."]

    purpose = body.get("purpose")
    if purpose not in _ALLOWED_PURPOSES:
        details["purpose"] = ["Must be profile or gallery."]

    storage_bucket = body.get("storage_bucket")
    expected_bucket = media_bucket_name()
    if storage_bucket != expected_bucket:
        details["storage_bucket"] = [f"Must be {expected_bucket}."]

    storage_path = body.get("storage_path")
    if not isinstance(storage_path, str) or not storage_path.strip():
        details["storage_path"] = ["storage_path is required."]
    elif not _STORAGE_PATH_RE.match(storage_path.strip()):
        details["storage_path"] = ["storage_path is not a valid venue media path."]

    for key, max_len in (("caption", _MAX_CAPTION_LEN), ("alt_text", _MAX_ALT_TEXT_LEN)):
        if key not in body:
            continue
        val = body[key]
        if val is None:
            continue
        if not isinstance(val, str):
            details[key] = ["Must be a string or null."]
        elif len(val.strip()) > max_len:
            details[key] = [f"Must be at most {max_len} characters."]

    sort_order = body.get("sort_order", 0)
    if sort_order is not None:
        if not isinstance(sort_order, int) or isinstance(sort_order, bool):
            details["sort_order"] = ["Must be an integer."]
        elif sort_order < 0 or sort_order > _MAX_SORT_ORDER:
            details["sort_order"] = [f"Must be between 0 and {_MAX_SORT_ORDER}."]

    if details:
        return None, details

    out: dict[str, Any] = {
        "media_id": str(media_id).strip(),
        "purpose": purpose,
        "storage_bucket": expected_bucket,
        "storage_path": storage_path.strip(),
        "sort_order": int(sort_order) if sort_order is not None else 0,
    }
    for key in ("caption", "alt_text"):
        if key in body:
            val = body[key]
            out[key] = val.strip() if isinstance(val, str) and val.strip() else None
    return out, None


def _validate_patch_body(
    body: Any,
) -> tuple[dict[str, Any] | None, dict[str, list[str]] | None]:
    if not isinstance(body, dict):
        return None, {"body": ["Request body must be a JSON object."]}

    unknown = sorted(set(body.keys()) - _PATCH_ALLOWED_KEYS)
    details: dict[str, list[str]] = {}
    for key in unknown:
        details[key] = ["Unknown field."]

    if not _PATCH_ALLOWED_KEYS.intersection(body.keys()):
        details["body"] = ["At least one updatable field must be provided."]

    if "purpose" in body and body["purpose"] not in _ALLOWED_PURPOSES:
        details["purpose"] = ["Must be profile or gallery."]

    for key, max_len in (("caption", _MAX_CAPTION_LEN), ("alt_text", _MAX_ALT_TEXT_LEN)):
        if key not in body:
            continue
        val = body[key]
        if val is None:
            continue
        if not isinstance(val, str):
            details[key] = ["Must be a string or null."]
        elif len(val.strip()) > max_len:
            details[key] = [f"Must be at most {max_len} characters."]

    if "sort_order" in body:
        sort_order = body["sort_order"]
        if not isinstance(sort_order, int) or isinstance(sort_order, bool):
            details["sort_order"] = ["Must be an integer."]
        elif sort_order < 0 or sort_order > _MAX_SORT_ORDER:
            details["sort_order"] = [f"Must be between 0 and {_MAX_SORT_ORDER}."]

    if "active" in body and not isinstance(body["active"], bool):
        details["active"] = ["Must be a boolean."]

    if details:
        return None, details

    out: dict[str, Any] = {}
    for key in _PATCH_ALLOWED_KEYS:
        if key in body:
            val = body[key]
            if key in ("caption", "alt_text") and isinstance(val, str):
                out[key] = val.strip() or None
            else:
                out[key] = val
    return out, None


def _load_upload_intent(
    *,
    media_id: str,
    venue_id: str,
    owner_account_id: UUID,
) -> dict[str, Any] | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              id::text,
              venue_id::text,
              owner_account_id::text,
              purpose,
              storage_bucket,
              storage_path,
              content_type,
              expires_at,
              committed_at
            FROM public.owner_venue_media_upload_intent
            WHERE id = %s::uuid
              AND venue_id = %s::uuid
              AND owner_account_id = %s::uuid
            """,
            [media_id, venue_id, str(owner_account_id)],
        )
        row = c.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "venue_id": row[1],
        "owner_account_id": row[2],
        "purpose": row[3],
        "storage_bucket": row[4],
        "storage_path": row[5],
        "content_type": row[6],
        "expires_at": row[7],
        "committed_at": row[8],
    }


def _retire_active_profile_images(venue_id: str, *, exclude_id: str | None = None) -> None:
    with connection.cursor() as c:
        if exclude_id:
            c.execute(
                """
                UPDATE public.venue_published_media
                SET catalog_record_status = 'retired', updated_at = now()
                WHERE venue_id = %s::uuid
                  AND purpose = 'profile'
                  AND catalog_record_status = 'active'
                  AND id <> %s::uuid
                """,
                [venue_id, exclude_id],
            )
        else:
            c.execute(
                """
                UPDATE public.venue_published_media
                SET catalog_record_status = 'retired', updated_at = now()
                WHERE venue_id = %s::uuid
                  AND purpose = 'profile'
                  AND catalog_record_status = 'active'
                """,
                [venue_id],
            )


def get_owner_venue_media(
    auth: AuthContext, venue_id: str
) -> tuple[dict[str, Any] | None, str]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err
    return _build_media_response(venue_id), "ok"


@transaction.atomic
def create_owner_venue_media_upload_intent(
    auth: AuthContext,
    venue_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    parsed, val_err = _validate_upload_intent_body(body)
    if val_err:
        return None, "validation_error", val_err
    assert parsed is not None

    bucket = media_bucket_name()
    ext = _extension_for_content_type(parsed["content_type"])
    assert ext is not None
    media_id = str(uuid4())
    storage_path = _build_storage_path(venue_id, parsed["purpose"], media_id, ext)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=_UPLOAD_INTENT_TTL_SECONDS)

    try:
        signed = create_signed_upload_url(
            bucket,
            storage_path,
            expires_in_seconds=_UPLOAD_INTENT_TTL_SECONDS,
        )
    except SupabaseStorageError as exc:
        return None, "storage_error", {"storage": [str(exc)]}

    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.owner_venue_media_upload_intent (
                id,
                venue_id,
                owner_account_id,
                purpose,
                storage_bucket,
                storage_path,
                content_type,
                expires_at
            ) VALUES (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s)
            """,
            [
                media_id,
                venue_id,
                str(access.owner_account_id),
                parsed["purpose"],
                bucket,
                storage_path,
                parsed["content_type"],
                expires_at,
            ],
        )

    return {
        "media_id": media_id,
        "storage_bucket": bucket,
        "storage_path": storage_path,
        "signed_upload_url": signed.signed_upload_url,
        "expires_in_seconds": _UPLOAD_INTENT_TTL_SECONDS,
    }, "ok", None


@transaction.atomic
def create_owner_venue_media(
    auth: AuthContext,
    venue_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    parsed, val_err = _validate_create_body(body)
    if val_err:
        return None, "validation_error", val_err
    assert parsed is not None

    intent = _load_upload_intent(
        media_id=parsed["media_id"],
        venue_id=venue_id,
        owner_account_id=access.owner_account_id,
    )
    if intent is None:
        return None, "validation_error", {
            "media_id": ["Upload intent not found for this venue."]
        }

    if intent["committed_at"] is not None:
        return None, "validation_error", {
            "media_id": ["Upload intent has already been used."]
        }

    now = datetime.now(timezone.utc)
    expires_at = intent["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        return None, "validation_error", {"media_id": ["Upload intent has expired."]}

    if intent["storage_path"] != parsed["storage_path"]:
        return None, "validation_error", {
            "storage_path": ["storage_path does not match issued upload intent."]
        }
    if intent["purpose"] != parsed["purpose"]:
        return None, "validation_error", {
            "purpose": ["purpose does not match upload intent."]
        }
    if intent["storage_bucket"] != parsed["storage_bucket"]:
        return None, "validation_error", {
            "storage_bucket": ["storage_bucket does not match upload intent."]
        }

    if f"venues/{venue_id}/" not in parsed["storage_path"]:
        return None, "validation_error", {
            "storage_path": ["storage_path must be scoped to this venue."]
        }

    if not storage_object_exists(parsed["storage_bucket"], parsed["storage_path"]):
        return None, "validation_error", {
            "storage_path": ["Uploaded file was not found in storage."]
        }

    before = _snapshot_media_for_audit(venue_id)

    if parsed["purpose"] == "profile":
        _retire_active_profile_images(venue_id)

    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.venue_published_media (
                id,
                venue_id,
                storage_bucket,
                storage_path,
                media_kind,
                purpose,
                caption,
                alt_text,
                sort_order,
                catalog_record_status,
                uploaded_by_owner_account_id
            ) VALUES (
                %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, 'active', %s::uuid
            )
            ON CONFLICT (storage_bucket, storage_path) DO UPDATE SET
                purpose = EXCLUDED.purpose,
                caption = EXCLUDED.caption,
                alt_text = EXCLUDED.alt_text,
                sort_order = EXCLUDED.sort_order,
                catalog_record_status = 'active',
                uploaded_by_owner_account_id = EXCLUDED.uploaded_by_owner_account_id,
                updated_at = now()
            RETURNING id::text
            """,
            [
                parsed["media_id"],
                venue_id,
                parsed["storage_bucket"],
                parsed["storage_path"],
                _MEDIA_KIND,
                parsed["purpose"],
                parsed.get("caption"),
                parsed.get("alt_text"),
                parsed.get("sort_order", 0),
                str(access.owner_account_id),
            ],
        )
        row = c.fetchone()
        c.execute(
            """
            UPDATE public.owner_venue_media_upload_intent
            SET committed_at = now()
            WHERE id = %s::uuid
            """,
            [parsed["media_id"]],
        )
    assert row is not None
    saved_id = row[0]

    after = _snapshot_media_for_audit(venue_id)
    saved = next(item for item in after if item["id"] == saved_id)

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_published_media",
        field_family="media",
        endpoint=f"/api/v1/owner/venues/{venue_id}/media",
        before={"media": before},
        after={"media": after},
    )

    return {
        "venue_id": venue_id,
        "media_item": saved,
        "message": "Photo saved. These updates are now reflected on your listing.",
    }, "ok", None


def _media_belongs_to_venue(venue_id: str, media_id: str) -> bool:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM public.venue_published_media
            WHERE id = %s::uuid AND venue_id = %s::uuid
            """,
            [media_id, venue_id],
        )
        return c.fetchone() is not None


def _load_single_media_row(venue_id: str, media_id: str) -> dict[str, Any] | None:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              id,
              purpose,
              media_kind,
              storage_bucket,
              storage_path,
              caption,
              alt_text,
              sort_order,
              catalog_record_status
            FROM public.venue_published_media
            WHERE id = %s::uuid AND venue_id = %s::uuid
            """,
            [media_id, venue_id],
        )
        row = c.fetchone()
    return _media_row_to_public(row) if row else None


@transaction.atomic
def patch_owner_venue_media(
    auth: AuthContext,
    venue_id: str,
    media_id: str,
    body: dict[str, Any],
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    access, err = assert_owner_can_direct_edit(auth, venue_id)
    if access is None:
        return None, err, None

    if not _media_belongs_to_venue(venue_id, media_id):
        return None, "not_found", None

    parsed, val_err = _validate_patch_body(body)
    if val_err:
        return None, "validation_error", val_err
    assert parsed is not None

    before = _snapshot_media_for_audit(venue_id)
    current = next((m for m in before if m["id"] == media_id), None)
    if current is None:
        return None, "not_found", None

    merged = {**current, **parsed}
    if parsed.get("purpose") == "profile" and merged.get("active", True):
        _retire_active_profile_images(venue_id, exclude_id=media_id)

    catalog_status = "active" if merged.get("active", current["active"]) else "retired"
    caption = merged.get("caption", current.get("caption"))
    alt_text = merged.get("alt_text", current.get("alt_text"))
    sort_order = merged.get("sort_order", current.get("sort_order", 0))
    purpose = merged.get("purpose", current.get("purpose"))

    with connection.cursor() as c:
        c.execute(
            """
            UPDATE public.venue_published_media
            SET purpose = %s,
                caption = %s,
                alt_text = %s,
                sort_order = %s,
                catalog_record_status = %s,
                updated_at = now()
            WHERE id = %s::uuid AND venue_id = %s::uuid
            """,
            [
                purpose,
                caption,
                alt_text,
                sort_order,
                catalog_status,
                media_id,
                venue_id,
            ],
        )

    after = _snapshot_media_for_audit(venue_id)
    saved = _load_single_media_row(venue_id, media_id)
    if saved is None:
        return None, "not_found", None

    _write_owner_direct_edit_audit(
        owner_account_id=access.owner_account_id,
        venue_id=venue_id,
        entity_table="venue_published_media",
        field_family="media",
        endpoint=f"/api/v1/owner/venues/{venue_id}/media/{media_id}",
        before={"media": before},
        after={"media": after},
    )

    return {
        "venue_id": venue_id,
        "media_item": saved,
        "message": "Photo saved. These updates are now reflected on your listing.",
    }, "ok", None


@transaction.atomic
def deactivate_owner_venue_media(
    auth: AuthContext,
    venue_id: str,
    media_id: str,
) -> tuple[dict[str, Any] | None, str, dict[str, list[str]] | None]:
    return patch_owner_venue_media(
        auth,
        venue_id,
        media_id,
        {"active": False},
    )
