"""
Consumer-private profile and notification preferences (schema-backed fields only).

Read/write: `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings`.
Does not touch public venue truth, moderation, or saved lists.
"""

from __future__ import annotations

import json
import re
from datetime import time
from typing import Any
from uuid import UUID

from django.db import DatabaseError, connection, transaction

from common.auth.context import AuthContext
from common.consumer_account import get_or_create_consumer_account_id

# PATCH body: only these top-level keys are accepted (all others => 400).
PATCH_ALLOWED_KEYS = frozenset(
    {
        "display_name",
        "avatar_storage_ref",
        "default_locality_id",
        "default_geographic_region_id",
        "email_marketing_opt_in",
        "email_transactional_opt_in",
        "push_notifications_opt_in",
        "sms_marketing_opt_in",
        "sms_transactional_opt_in",
        "quiet_hours_start_local",
        "quiet_hours_end_local",
    }
)

# Defaults when `consumer_notification_settings` row is absent (matches DB defaults, migration 0010).
_NOTIF_DEFAULTS: dict[str, Any] = {
    "email_marketing_opt_in": False,
    "email_transactional_opt_in": True,
    "push_notifications_opt_in": True,
    "sms_marketing_opt_in": False,
    "sms_transactional_opt_in": True,
    "quiet_hours_start_local": None,
    "quiet_hours_end_local": None,
}

_TIME_RE = re.compile(
    r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$"
)


def _parse_time_value(raw: object) -> time:
    """Parse HH:MM or HH:MM:SS (1–2 digit hours allowed; matches check constraint on DB)."""
    if not isinstance(raw, str) or not _TIME_RE.match(raw):
        raise ValueError("not_a_time")
    parts = str(raw).strip().split(":")
    h = int(parts[0])
    m = int(parts[1])
    s = int(parts[2]) if len(parts) > 2 else 0
    if h > 23 or m > 59 or s > 59:
        raise ValueError("not_a_time")
    return time(h, m, s)


def _time_to_api(t: time | None) -> str | None:
    if t is None:
        return None
    s = t.isoformat(timespec="seconds")
    return s


def _load_profile(consumer_id: UUID) -> tuple[str | None, str | None]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT display_name, avatar_storage_ref
            FROM public.consumer_profile
            WHERE consumer_account_id = %s::uuid
            """,
            [str(consumer_id)],
        )
        row = c.fetchone()
        if not row:
            return (None, None)
        return (row[0], row[1])


def _load_location(consumer_id: UUID) -> tuple[UUID | None, UUID | None]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT default_locality_id, default_geographic_region_id
            FROM public.consumer_default_location_preference
            WHERE consumer_account_id = %s::uuid
            """,
            [str(consumer_id)],
        )
        row = c.fetchone()
        if not row:
            return (None, None)
        dloc, dreg = row[0], row[1]
        return (
            UUID(str(dloc)) if dloc is not None else None,
            UUID(str(dreg)) if dreg is not None else None,
        )


def _load_notification(consumer_id: UUID) -> dict[str, Any]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
                email_marketing_opt_in,
                email_transactional_opt_in,
                push_notifications_opt_in,
                sms_marketing_opt_in,
                sms_transactional_opt_in,
                quiet_hours_start_local,
                quiet_hours_end_local
            FROM public.consumer_notification_settings
            WHERE consumer_account_id = %s::uuid
            """,
            [str(consumer_id)],
        )
        row = c.fetchone()
        if not row:
            return dict(_NOTIF_DEFAULTS)
        return {
            "email_marketing_opt_in": bool(row[0]),
            "email_transactional_opt_in": bool(row[1]),
            "push_notifications_opt_in": bool(row[2]),
            "sms_marketing_opt_in": bool(row[3]),
            "sms_transactional_opt_in": bool(row[4]),
            "quiet_hours_start_local": row[5],
            "quiet_hours_end_local": row[6],
        }


def _row_exists_in_table(*, table: str, id_obj: object) -> bool:
    allowed = {"locality", "geographic_region"}
    if table not in allowed:
        raise ValueError("Unexpected table in FK check.")
    with connection.cursor() as c:
        if table == "locality":
            c.execute(
                "SELECT 1 FROM public.locality WHERE id = %s::uuid LIMIT 1",
                [str(id_obj)],
            )
        else:
            c.execute(
                "SELECT 1 FROM public.geographic_region WHERE id = %s::uuid LIMIT 1",
                [str(id_obj)],
            )
        return c.fetchone() is not None


def build_response_payload(consumer_id: UUID) -> dict[str, Any]:
    """Assemble JSON-ready profile document (flat shape)."""
    dname, avatar = _load_profile(consumer_id)
    dloc, dreg = _load_location(consumer_id)
    n = _load_notification(consumer_id)
    return {
        "display_name": dname,
        "avatar_storage_ref": avatar,
        "default_locality_id": str(dloc) if dloc is not None else None,
        "default_geographic_region_id": str(dreg) if dreg is not None else None,
        "email_marketing_opt_in": n["email_marketing_opt_in"],
        "email_transactional_opt_in": n["email_transactional_opt_in"],
        "push_notifications_opt_in": n["push_notifications_opt_in"],
        "sms_marketing_opt_in": n["sms_marketing_opt_in"],
        "sms_transactional_opt_in": n["sms_transactional_opt_in"],
        "quiet_hours_start_local": _time_to_api(n["quiet_hours_start_local"]),
        "quiet_hours_end_local": _time_to_api(n["quiet_hours_end_local"]),
    }


def get_profile_state(*, auth: AuthContext) -> tuple[dict[str, Any] | None, str | None]:
    try:
        cid = get_or_create_consumer_account_id(auth)
    except (ValueError, RuntimeError):
        return None, "invalid_auth_subject"
    except DatabaseError:
        return None, "db_error"
    return build_response_payload(cid), None


def parse_request_json(body: bytes | str) -> tuple[dict | None, str | None]:
    if isinstance(body, str):
        rawb = body.encode("utf-8")
    else:
        rawb = body
    if not rawb or not rawb.strip():
        return None, "empty_body"
    try:
        o = json.loads(rawb.decode("utf-8"))
    except json.JSONDecodeError:
        return None, "malformed_json"
    if not isinstance(o, dict):
        return None, "not_object"
    return o, None


def _coerce_str_or_null(key: str, v: object) -> tuple[object, str | None]:
    if v is None:
        return None, None
    if isinstance(v, str):
        return v, None
    return None, f"Field {key} must be a string or null."


def _coerce_uuid_or_null(key: str, v: object) -> tuple[object, str | None]:
    if v is None:
        return None, None
    if not isinstance(v, str) or not v.strip():
        return None, f"Field {key} must be a UUID string or null."
    try:
        return UUID(v), None
    except (ValueError, TypeError):
        return None, f"Field {key} must be a valid UUID or null."


def _coerce_bool(key: str, v: object) -> tuple[bool, str | None]:
    if isinstance(v, bool):
        return v, None
    return False, f"Field {key} must be a boolean (true or false), not a number or string."


def _coerce_time_or_null(key: str, v: object) -> tuple[time | object | None, str | None]:
    if v is None:
        return None, None
    try:
        return _parse_time_value(v), None
    except (ValueError, TypeError):
        return None, f"Field {key} must be a time string (HH:MM or HH:MM:SS) or null."


def _validate_typed_payload(payload: dict[str, Any]) -> dict[str, Any] | str:
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if k == "display_name" or k == "avatar_storage_ref":
            val, err = _coerce_str_or_null(k, v)
            if err:
                return err
            out[k] = val
        elif k in (
            "default_locality_id",
            "default_geographic_region_id",
        ):
            val, err = _coerce_uuid_or_null(k, v)
            if err:
                return err
            out[k] = val
        elif k in (
            "email_marketing_opt_in",
            "email_transactional_opt_in",
            "push_notifications_opt_in",
            "sms_marketing_opt_in",
            "sms_transactional_opt_in",
        ):
            b, err = _coerce_bool(k, v)
            if err:
                return err
            out[k] = b
        else:
            t, err = _coerce_time_or_null(k, v)
            if err:
                return err
            out[k] = t
    return out


def _quiet_pair_ok(start: time | object | None, end: time | object | None) -> bool:
    s_null = start is None
    e_null = end is None
    return s_null == e_null


def _validate_fk_locality(v: UUID) -> str | None:
    if not _row_exists_in_table(table="locality", id_obj=v):
        return "default_locality_id does not match an existing locality."
    return None


def _validate_fk_region(v: UUID) -> str | None:
    if not _row_exists_in_table(table="geographic_region", id_obj=v):
        return "default_geographic_region_id does not match an existing geographic region."
    return None


PROFILE_KEY_SET = frozenset({"display_name", "avatar_storage_ref"})
LOCATION_KEY_SET = frozenset({"default_locality_id", "default_geographic_region_id"})
NOTIFICATION_KEY_SET = PATCH_ALLOWED_KEYS - PROFILE_KEY_SET - LOCATION_KEY_SET


def _upsert_profile_row(
    consumer_id: UUID, display_name: str | None, avatar: str | None
) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.consumer_profile (
                consumer_account_id, display_name, avatar_storage_ref
            )
            VALUES (%s::uuid, %s, %s)
            ON CONFLICT (consumer_account_id) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                avatar_storage_ref = EXCLUDED.avatar_storage_ref,
                updated_at = now()
            """,
            [str(consumer_id), display_name, avatar],
        )


def _upsert_location_row(
    consumer_id: UUID,
    *,
    default_locality_id: UUID | None,
    default_geographic_region_id: UUID | None,
) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.consumer_default_location_preference (
                consumer_account_id, default_locality_id, default_geographic_region_id
            )
            VALUES (%s::uuid, %s::uuid, %s::uuid)
            ON CONFLICT (consumer_account_id) DO UPDATE SET
                default_locality_id = EXCLUDED.default_locality_id,
                default_geographic_region_id = EXCLUDED.default_geographic_region_id,
                updated_at = now()
            """,
            [
                str(consumer_id),
                str(default_locality_id) if default_locality_id is not None else None,
                str(default_geographic_region_id) if default_geographic_region_id is not None else None,
            ],
        )


def _upsert_notification_row(consumer_id: UUID, n: dict[str, Any]) -> None:
    with connection.cursor() as c:
        c.execute(
            """
            INSERT INTO public.consumer_notification_settings (
                consumer_account_id,
                email_marketing_opt_in,
                email_transactional_opt_in,
                push_notifications_opt_in,
                sms_marketing_opt_in,
                sms_transactional_opt_in,
                quiet_hours_start_local,
                quiet_hours_end_local
            )
            VALUES (
                %s::uuid, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (consumer_account_id) DO UPDATE SET
                email_marketing_opt_in = EXCLUDED.email_marketing_opt_in,
                email_transactional_opt_in = EXCLUDED.email_transactional_opt_in,
                push_notifications_opt_in = EXCLUDED.push_notifications_opt_in,
                sms_marketing_opt_in = EXCLUDED.sms_marketing_opt_in,
                sms_transactional_opt_in = EXCLUDED.sms_transactional_opt_in,
                quiet_hours_start_local = EXCLUDED.quiet_hours_start_local,
                quiet_hours_end_local = EXCLUDED.quiet_hours_end_local,
                updated_at = now()
            """,
            [
                str(consumer_id),
                n["email_marketing_opt_in"],
                n["email_transactional_opt_in"],
                n["push_notifications_opt_in"],
                n["sms_marketing_opt_in"],
                n["sms_transactional_opt_in"],
                n["quiet_hours_start_local"],
                n["quiet_hours_end_local"],
            ],
        )


@transaction.atomic
def apply_profile_patch(
    *, auth: AuthContext, body: bytes | str
) -> tuple[dict[str, Any] | None, str | None, dict | None]:
    """
    Return (data, err_code, field_errors).
    err_code: invalid_auth_subject, malformed_json, validation_error, db_error
    """
    try:
        consumer_id = get_or_create_consumer_account_id(auth)
    except (ValueError, RuntimeError):
        return None, "invalid_auth_subject", None
    except DatabaseError:
        return None, "db_error", None

    raw, perr = parse_request_json(body)
    if perr is not None:
        if perr == "malformed_json":
            return None, "malformed_json", None
        if perr == "empty_body":
            return None, "validation_error", {
                "_body": ["Request body must be a non-empty JSON object (use {} for a no-op)."],
            }
        if perr == "not_object":
            return None, "validation_error", {
                "_body": ["Request body must be a JSON object, not a list or primitive."],
            }

    assert raw is not None
    if raw.keys() - PATCH_ALLOWED_KEYS:
        extra = ", ".join(sorted(k for k in (raw.keys() - PATCH_ALLOWED_KEYS)))
        return None, "validation_error", {
            "_unknown": [f"Unknown or unsupported fields: {extra}."],
        }

    typed = _validate_typed_payload({k: raw[k] for k in raw})
    if isinstance(typed, str):
        return None, "validation_error", {"_general": [typed]}

    if not typed:
        return build_response_payload(consumer_id), None, None

    dname, avatar = _load_profile(consumer_id)
    dloc, dreg = _load_location(consumer_id)
    notif = _load_notification(consumer_id)

    if "display_name" in typed:
        dname = typed["display_name"]
    if "avatar_storage_ref" in typed:
        avatar = typed["avatar_storage_ref"]
    if "default_locality_id" in typed:
        dloc = typed["default_locality_id"]
    if "default_geographic_region_id" in typed:
        dreg = typed["default_geographic_region_id"]

    for k in NOTIFICATION_KEY_SET:
        if k in typed:
            notif[k] = typed[k]

    if dloc is not None:
        err = _validate_fk_locality(dloc)
        if err:
            return None, "validation_error", {"default_locality_id": [err]}

    if dreg is not None:
        err = _validate_fk_region(dreg)
        if err:
            return None, "validation_error", {"default_geographic_region_id": [err]}

    if not _quiet_pair_ok(notif["quiet_hours_start_local"], notif["quiet_hours_end_local"]):
        return None, "validation_error", {
            "quiet_hours": [
                "quiet_hours_start_local and quiet_hours_end_local must both be null, "
                "or both be set to valid times; partial quiet hours are not allowed.",
            ]
        }

    try:
        if PROFILE_KEY_SET & typed.keys():
            _upsert_profile_row(consumer_id, dname, avatar)
        if LOCATION_KEY_SET & typed.keys():
            _upsert_location_row(consumer_id, dloc, dreg)
        if NOTIFICATION_KEY_SET & typed.keys():
            _upsert_notification_row(consumer_id, notif)
    except DatabaseError:
        return None, "db_error", None

    return build_response_payload(consumer_id), None, None