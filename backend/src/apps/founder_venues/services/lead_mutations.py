"""Write operations for founder venue lead internal API."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from django.db import connection, transaction

from apps.founder_venues.services.contact_safety import classify_email_contact_safety
from apps.founder_venues.services.founder_fit_db import recompute_founder_fit_scores
from apps.founder_venues.services.lead_queries import get_founder_venue_lead_detail
from apps.founder_venues.services.lead_validation import (
    CONTACT_PERMISSION_STATUSES,
    ENRICHMENT_STATUSES,
    LAST_CONTACT_CHANNELS,
    OUTREACH_STATUSES,
    LeadNotFoundError,
    LeadValidationError,
    parse_uuid,
)
from apps.founder_venues.services.normalization import (
    normalize_email,
    normalize_phone_au,
    normalize_postcode,
    normalize_state,
    normalize_venue_name,
    normalize_website_url,
)
from apps.founder_venues.services.normalization import build_soft_dedupe_key

PATCHABLE_FIELDS = frozenset(
    {
        "name",
        "category",
        "address_line",
        "suburb",
        "state",
        "postcode",
        "phone",
        "website",
        "email",
        "instagram_url",
        "facebook_url",
        "contact_name",
        "contact_role",
        "notes",
        "enrichment_status",
        "outreach_status",
        "contact_permission_status",
        "last_contacted_at",
        "last_contact_channel",
    }
)

_NORMALIZERS = {
    "name": lambda v: v.strip() if isinstance(v, str) else v,
    "state": normalize_state,
    "postcode": normalize_postcode,
    "phone": normalize_phone_au,
    "website": normalize_website_url,
    "email": normalize_email,
}


def _normalize_patch_field(field: str, value: Any) -> Any:
    if value is None:
        return None
    if field in _NORMALIZERS:
        return _NORMALIZERS[field](value)
    if isinstance(value, str):
        return value.strip() or None
    return value


def _validate_patch_field(field: str, value: Any) -> Any:
    if field == "enrichment_status" and value not in ENRICHMENT_STATUSES:
        raise LeadValidationError(f"Invalid enrichment_status: {value}")
    if field == "outreach_status" and value not in OUTREACH_STATUSES:
        raise LeadValidationError(f"Invalid outreach_status: {value}")
    if field == "contact_permission_status" and value not in CONTACT_PERMISSION_STATUSES:
        raise LeadValidationError(f"Invalid contact_permission_status: {value}")
    if field == "last_contact_channel" and value is not None:
        if value not in LAST_CONTACT_CHANNELS:
            raise LeadValidationError(f"Invalid last_contact_channel: {value}")
    if field == "last_contacted_at" and value is not None:
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise LeadValidationError(
                    "last_contacted_at must be ISO-8601 datetime."
                ) from exc
    return value


def _recompute_dedupe_key(cursor: Any, lead_id: str) -> None:
    cursor.execute(
        """
        SELECT normalized_name, postcode, website, phone, email
        FROM public.founder_venue_leads WHERE id = %s::uuid
        """,
        [lead_id],
    )
    row = cursor.fetchone()
    if not row:
        return
    dedupe_key = build_soft_dedupe_key(
        normalized_name=row[0],
        postcode=row[1],
        website=row[2],
        phone=row[3],
        email=row[4],
    )
    cursor.execute(
        """
        UPDATE public.founder_venue_leads
        SET dedupe_key = %s, updated_at = now()
        WHERE id = %s::uuid
        """,
        [dedupe_key, lead_id],
    )


def patch_founder_venue_lead(
    lead_id: str,
    payload: dict[str, Any],
    *,
    admin_account_id: str | None,
) -> dict[str, Any]:
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")
    if not isinstance(payload, dict):
        raise LeadValidationError("Request body must be a JSON object.")

    unknown = set(payload.keys()) - PATCHABLE_FIELDS
    if unknown:
        raise LeadValidationError(
            f"Fields not allowed for patch: {', '.join(sorted(unknown))}."
        )
    if not payload:
        raise LeadValidationError("At least one field is required for patch.")

    updates: dict[str, Any] = {}
    raw_for_attribution: dict[str, tuple[Any, Any, str | None]] = {}

    for field, raw in payload.items():
        _validate_patch_field(field, raw)
        normalized = _normalize_patch_field(field, raw)
        if field == "name" and normalized:
            updates["normalized_name"] = normalize_venue_name(str(normalized))
        updates[field] = normalized
        safety = None
        if field == "email" and normalized:
            safety = classify_email_contact_safety(str(normalized))
        raw_for_attribution[field] = (raw, normalized, safety)

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM public.founder_venue_leads WHERE id = %s::uuid",
                [lead_uuid],
            )
            if not cursor.fetchone():
                raise LeadNotFoundError

            sets = [f"{col} = %s" for col in updates]
            sets.append("updated_at = now()")
            cursor.execute(
                f"""
                UPDATE public.founder_venue_leads
                SET {', '.join(sets)}
                WHERE id = %s::uuid
                """,
                [*updates.values(), lead_uuid],
            )

            if any(f in updates for f in ("name", "postcode", "website", "phone", "email")):
                _recompute_dedupe_key(cursor, lead_uuid)

            cursor.execute(
                """
                INSERT INTO public.founder_venue_lead_sources (
                  lead_id, source_type, source_name, raw_payload, confidence
                ) VALUES (%s::uuid, 'manual', 'API patch', %s::jsonb, 80)
                RETURNING id::text
                """,
                [lead_uuid, json.dumps({"fields": list(payload.keys())})],
            )
            source_id = cursor.fetchone()[0]

            for field, (raw_val, norm_val, safety) in raw_for_attribution.items():
                cursor.execute(
                    """
                    INSERT INTO public.founder_venue_lead_field_attributions (
                      lead_id, source_id, field_name, source_type,
                      confidence, raw_value, normalized_value, contact_safety_class
                    ) VALUES (%s::uuid, %s::uuid, %s, 'manual', 80, %s, %s, %s)
                    """,
                    [
                        lead_uuid,
                        source_id,
                        field,
                        str(raw_val) if raw_val is not None else None,
                        str(norm_val) if norm_val is not None else None,
                        safety,
                    ],
                )

            cursor.execute(
                """
                INSERT INTO public.founder_venue_lead_events (
                  lead_id, event_type, metadata, created_by
                ) VALUES (%s::uuid, %s, %s::jsonb, %s)
                """,
                [
                    lead_uuid,
                    "lead_manual_patch",
                    json.dumps({"changed_fields": list(payload.keys())}),
                    admin_account_id,
                ],
            )

    recompute_founder_fit_scores(lead_ids=[lead_uuid])
    return get_founder_venue_lead_detail(lead_uuid)


def mark_lead_do_not_contact(
    lead_id: str,
    *,
    reason: str | None,
    admin_account_id: str | None,
) -> dict[str, Any]:
    """
    Mark lead as do-not-contact via outreach and permission status only.

    Does not set suppressed_at — leads remain visible in internal lists unless
    filtered by outreach/permission status (see list defaults).
    """
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")
    reason_text = (reason or "").strip() or None

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.founder_venue_leads
                SET outreach_status = 'do_not_contact',
                    contact_permission_status = 'do_not_contact',
                    updated_at = now()
                WHERE id = %s::uuid
                """,
                [lead_uuid],
            )
            if cursor.rowcount == 0:
                raise LeadNotFoundError

            cursor.execute(
                """
                INSERT INTO public.founder_venue_lead_events (
                  lead_id, event_type, metadata, created_by
                ) VALUES (%s::uuid, %s, %s::jsonb, %s)
                """,
                [
                    lead_uuid,
                    "lead_marked_do_not_contact",
                    json.dumps({"reason": reason_text}),
                    admin_account_id,
                ],
            )

    recompute_founder_fit_scores(lead_ids=[lead_uuid])
    return get_founder_venue_lead_detail(lead_uuid)
