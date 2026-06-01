"""
CSV import for founder venue leads (Stage 2).

Uses raw SQL via django.db.connection; no ORM.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from django.db import connection, transaction

from apps.founder_venues.services.contact_safety import (
    classify_email_contact_safety,
    is_high_confidence_business_email,
)
from apps.founder_venues.services.csv_mapping import (
    build_header_map,
    map_row_to_lead_fields,
    parse_csv_rows,
)
from apps.founder_venues.services.normalization import (
    build_soft_dedupe_key,
    normalize_email,
    normalize_phone_au,
    normalize_postcode,
    normalize_state,
    normalize_venue_name,
    normalize_website_url,
    website_host,
)

VALID_SOURCE_TYPES = frozenset(
    {
        "csv_import",
        "purchased_dataset",
        "venue_website",
        "business_directory",
        "open_data",
        "google_places",
        "osm",
        "manual",
        "other",
    }
)

LEAD_WRITABLE_FIELDS = (
    "name",
    "normalized_name",
    "category",
    "address_line",
    "suburb",
    "state",
    "postcode",
    "country",
    "latitude",
    "longitude",
    "phone",
    "website",
    "email",
    "instagram_url",
    "facebook_url",
    "contact_name",
    "contact_role",
    "dedupe_key",
    "confidence_score",
    "enrichment_status",
    "contact_permission_status",
)

ATTRIBUTION_FIELDS = frozenset(
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
        "latitude",
        "longitude",
    }
)


@dataclass
class RowError:
    row_number: int
    message: str


@dataclass
class DuplicateReview:
    row_number: int
    reason: str
    existing_lead_id: str | None
    name: str | None


@dataclass
class FounderVenueImportResult:
    rows_processed: int = 0
    leads_created: int = 0
    leads_updated: int = 0
    duplicates_skipped: int = 0
    duplicates_needing_review: list[DuplicateReview] = field(default_factory=list)
    invalid_rows: list[RowError] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = False


@dataclass
class _NormalizedRow:
    row_number: int
    raw_fields: dict[str, str | None]
    raw_row: dict[str, Any]
    name: str
    normalized_name: str | None
    category: str | None
    address_line: str | None
    suburb: str | None
    state: str | None
    postcode: str | None
    latitude: float | None
    longitude: float | None
    phone: str | None
    website: str | None
    email: str | None
    instagram_url: str | None
    facebook_url: str | None
    contact_name: str | None
    contact_role: str | None
    dedupe_key: str | None
    website_host_value: str | None
    confidence_score: int
    enrichment_status: str
    contact_permission_status: str
    email_safety: str | None
    probable_duplicate: DuplicateReview | None = None


def _bad_uuid(value: str | None) -> bool:
    if not value:
        return True
    try:
        UUID(value)
    except (ValueError, TypeError):
        return True
    return False


def _parse_coordinate(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def compute_import_confidence(
    *,
    source_type: str,
    phone: str | None,
    website: str | None,
    email: str | None,
    instagram_url: str | None,
    facebook_url: str | None,
    address_line: str | None,
    suburb: str | None,
    state: str | None,
    latitude: float | None,
    longitude: float | None,
) -> int:
    score = 30
    if phone:
        score += 10
    if website:
        score += 10
    if email and is_high_confidence_business_email(email):
        score += 10
    if instagram_url or facebook_url:
        score += 5
    if address_line and suburb and state:
        score += 10
    if latitude is not None and longitude is not None:
        score += 10
    cap = 80
    if source_type == "purchased_dataset" and not phone and not website:
        cap = 70
    return min(score, cap)


def _default_contact_permission(
    phone: str | None, email: str | None
) -> str:
    if phone or email:
        return "public_business_contact"
    return "unknown"


def normalize_import_row(
    row_number: int,
    raw_fields: dict[str, str | None],
    raw_row: dict[str, Any],
    *,
    source_type: str,
) -> _NormalizedRow | RowError:
    name = (raw_fields.get("name") or "").strip()
    if not name:
        return RowError(row_number=row_number, message="Missing required venue name.")

    state_raw = raw_fields.get("state")
    state = normalize_state(state_raw) if state_raw else None
    if state_raw and state_raw.strip() and not state:
        state = state_raw.strip()

    normalized = _NormalizedRow(
        row_number=row_number,
        raw_fields=raw_fields,
        raw_row=raw_row,
        name=name,
        normalized_name=normalize_venue_name(name),
        category=raw_fields.get("category"),
        address_line=raw_fields.get("address_line"),
        suburb=raw_fields.get("suburb"),
        state=state,
        postcode=normalize_postcode(raw_fields.get("postcode")),
        latitude=_parse_coordinate(raw_fields.get("latitude")),
        longitude=_parse_coordinate(raw_fields.get("longitude")),
        phone=normalize_phone_au(raw_fields.get("phone")),
        website=normalize_website_url(raw_fields.get("website")),
        email=normalize_email(raw_fields.get("email")),
        instagram_url=raw_fields.get("instagram_url"),
        facebook_url=raw_fields.get("facebook_url"),
        contact_name=raw_fields.get("contact_name"),
        contact_role=raw_fields.get("contact_role"),
        website_host_value=None,
        dedupe_key=None,
        confidence_score=0,
        enrichment_status="imported",
        contact_permission_status="unknown",
        email_safety=None,
    )
    normalized.website_host_value = website_host(normalized.website)
    normalized.email_safety = classify_email_contact_safety(normalized.email)
    normalized.dedupe_key = build_soft_dedupe_key(
        normalized_name=normalized.normalized_name,
        postcode=normalized.postcode,
        website=normalized.website,
        phone=normalized.phone,
        email=normalized.email,
    )
    normalized.confidence_score = compute_import_confidence(
        source_type=source_type,
        phone=normalized.phone,
        website=normalized.website,
        email=normalized.email,
        instagram_url=normalized.instagram_url,
        facebook_url=normalized.facebook_url,
        address_line=normalized.address_line,
        suburb=normalized.suburb,
        state=normalized.state,
        latitude=normalized.latitude,
        longitude=normalized.longitude,
    )
    normalized.contact_permission_status = _default_contact_permission(
        normalized.phone, normalized.email
    )
    return normalized


def _find_strong_duplicate_lead_id(
    cursor: Any,
    *,
    dedupe_key: str | None,
    phone: str | None,
    email: str | None,
    host: str | None,
) -> tuple[str | None, str | None]:
    if dedupe_key:
        cursor.execute(
            """
            SELECT id::text FROM public.founder_venue_leads
            WHERE dedupe_key = %s AND suppressed_at IS NULL
            LIMIT 1
            """,
            [dedupe_key],
        )
        row = cursor.fetchone()
        if row:
            return row[0], "dedupe_key"

    if phone:
        cursor.execute(
            """
            SELECT id::text FROM public.founder_venue_leads
            WHERE phone = %s AND suppressed_at IS NULL
            LIMIT 1
            """,
            [phone],
        )
        row = cursor.fetchone()
        if row:
            return row[0], "phone"

    if email:
        cursor.execute(
            """
            SELECT id::text FROM public.founder_venue_leads
            WHERE email = %s AND suppressed_at IS NULL
            LIMIT 1
            """,
            [email],
        )
        row = cursor.fetchone()
        if row:
            return row[0], "email"

    if host:
        cursor.execute(
            """
            SELECT id::text, website FROM public.founder_venue_leads
            WHERE website IS NOT NULL AND suppressed_at IS NULL
            """,
        )
        for lead_id, website in cursor.fetchall():
            if website_host(website) == host:
                return lead_id, "website_host"

    return None, None


def _find_probable_duplicate_lead_id(
    cursor: Any,
    *,
    normalized_name: str | None,
    postcode: str | None,
    suburb: str | None,
    state: str | None,
) -> tuple[str | None, str | None]:
    if normalized_name and postcode:
        cursor.execute(
            """
            SELECT id::text FROM public.founder_venue_leads
            WHERE normalized_name = %s AND postcode = %s AND suppressed_at IS NULL
            LIMIT 1
            """,
            [normalized_name, postcode],
        )
        row = cursor.fetchone()
        if row:
            return row[0], "normalized_name_postcode"

    if normalized_name and suburb and state:
        cursor.execute(
            """
            SELECT id::text FROM public.founder_venue_leads
            WHERE normalized_name = %s AND lower(suburb) = lower(%s)
              AND state = %s AND suppressed_at IS NULL
            LIMIT 1
            """,
            [normalized_name, suburb, state],
        )
        row = cursor.fetchone()
        if row:
            return row[0], "normalized_name_suburb_state"

    return None, None


def _lead_values_for_insert(row: _NormalizedRow) -> dict[str, Any]:
    return {
        "name": row.name,
        "normalized_name": row.normalized_name,
        "category": row.category,
        "address_line": row.address_line,
        "suburb": row.suburb,
        "state": row.state,
        "postcode": row.postcode,
        "country": "AU",
        "latitude": row.latitude,
        "longitude": row.longitude,
        "phone": row.phone,
        "website": row.website,
        "email": row.email,
        "instagram_url": row.instagram_url,
        "facebook_url": row.facebook_url,
        "contact_name": row.contact_name,
        "contact_role": row.contact_role,
        "dedupe_key": row.dedupe_key,
        "confidence_score": row.confidence_score,
        "enrichment_status": row.enrichment_status,
        "contact_permission_status": row.contact_permission_status,
    }


def _insert_lead(cursor: Any, values: dict[str, Any]) -> str:
    cursor.execute(
        """
        INSERT INTO public.founder_venue_leads (
          name, normalized_name, category, address_line, suburb, state, postcode,
          country, latitude, longitude, phone, website, email,
          instagram_url, facebook_url, contact_name, contact_role,
          dedupe_key, confidence_score, enrichment_status, contact_permission_status
        ) VALUES (
          %(name)s, %(normalized_name)s, %(category)s, %(address_line)s, %(suburb)s,
          %(state)s, %(postcode)s, %(country)s, %(latitude)s, %(longitude)s,
          %(phone)s, %(website)s, %(email)s, %(instagram_url)s, %(facebook_url)s,
          %(contact_name)s, %(contact_role)s, %(dedupe_key)s, %(confidence_score)s,
          %(enrichment_status)s, %(contact_permission_status)s
        )
        RETURNING id::text
        """,
        values,
    )
    return cursor.fetchone()[0]


def _update_lead_empty_fields(
    cursor: Any, lead_id: str, values: dict[str, Any]
) -> list[str]:
    cursor.execute(
        """
        SELECT name, normalized_name, category, address_line, suburb, state, postcode,
               latitude, longitude, phone, website, email, instagram_url, facebook_url,
               contact_name, contact_role, dedupe_key, confidence_score,
               enrichment_status, contact_permission_status
        FROM public.founder_venue_leads
        WHERE id = %s::uuid
        """,
        [lead_id],
    )
    current = cursor.fetchone()
    if not current:
        return []
    columns = [
        "name",
        "normalized_name",
        "category",
        "address_line",
        "suburb",
        "state",
        "postcode",
        "latitude",
        "longitude",
        "phone",
        "website",
        "email",
        "instagram_url",
        "facebook_url",
        "contact_name",
        "contact_role",
        "dedupe_key",
        "confidence_score",
        "enrichment_status",
        "contact_permission_status",
    ]
    changed: list[str] = []
    sets: list[str] = []
    params: list[Any] = []
    for idx, col in enumerate(columns):
        new_val = values.get(col)
        old_val = current[idx]
        if new_val is None:
            continue
        if old_val is None or (isinstance(old_val, str) and not str(old_val).strip()):
            sets.append(f"{col} = %s")
            params.append(new_val)
            changed.append(col)
        elif col == "confidence_score" and isinstance(new_val, int) and new_val > (
            old_val or 0
        ):
            sets.append(f"{col} = %s")
            params.append(new_val)
            changed.append(col)
    if not sets:
        return []
    sets.append("updated_at = now()")
    params.append(lead_id)
    cursor.execute(
        f"UPDATE public.founder_venue_leads SET {', '.join(sets)} WHERE id = %s::uuid",
        params,
    )
    return changed


def _insert_source(
    cursor: Any,
    *,
    lead_id: str,
    source_type: str,
    source_name: str | None,
    source_url: str | None,
    raw_payload: dict[str, Any],
    confidence: int,
) -> str:
    cursor.execute(
        """
        INSERT INTO public.founder_venue_lead_sources (
          lead_id, source_type, source_url, source_name, raw_payload, confidence
        ) VALUES (%s::uuid, %s, %s, %s, %s::jsonb, %s)
        RETURNING id::text
        """,
        [
            lead_id,
            source_type,
            source_url,
            source_name,
            json.dumps(raw_payload),
            confidence,
        ],
    )
    return cursor.fetchone()[0]


def _insert_attributions(
    cursor: Any,
    *,
    lead_id: str,
    source_id: str,
    source_type: str,
    source_url: str | None,
    row: _NormalizedRow,
    confidence: int,
) -> None:
    field_pairs: list[tuple[str, str | None, str | None, str | None]] = [
        ("name", row.raw_fields.get("name"), row.name, None),
        ("category", row.raw_fields.get("category"), row.category, None),
        ("address_line", row.raw_fields.get("address_line"), row.address_line, None),
        ("suburb", row.raw_fields.get("suburb"), row.suburb, None),
        ("state", row.raw_fields.get("state"), row.state, None),
        ("postcode", row.raw_fields.get("postcode"), row.postcode, None),
        ("phone", row.raw_fields.get("phone"), row.phone, None),
        ("website", row.raw_fields.get("website"), row.website, None),
        ("email", row.raw_fields.get("email"), row.email, row.email_safety),
        (
            "instagram_url",
            row.raw_fields.get("instagram_url"),
            row.instagram_url,
            None,
        ),
        (
            "facebook_url",
            row.raw_fields.get("facebook_url"),
            row.facebook_url,
            None,
        ),
        ("contact_name", row.raw_fields.get("contact_name"), row.contact_name, None),
        ("contact_role", row.raw_fields.get("contact_role"), row.contact_role, None),
        (
            "latitude",
            row.raw_fields.get("latitude"),
            str(row.latitude) if row.latitude is not None else None,
            None,
        ),
        (
            "longitude",
            row.raw_fields.get("longitude"),
            str(row.longitude) if row.longitude is not None else None,
            None,
        ),
    ]
    for field_name, raw_value, normalized_value, safety in field_pairs:
        if raw_value is None and normalized_value is None:
            continue
        cursor.execute(
            """
            INSERT INTO public.founder_venue_lead_field_attributions (
              lead_id, source_id, field_name, source_type, source_url,
              confidence, raw_value, normalized_value, contact_safety_class
            ) VALUES (
              %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            [
                lead_id,
                source_id,
                field_name,
                source_type,
                source_url,
                confidence,
                raw_value,
                normalized_value,
                safety,
            ],
        )


def _insert_event(
    cursor: Any,
    *,
    lead_id: str,
    event_type: str,
    metadata: dict[str, Any],
    created_by: str | None,
) -> None:
    cursor.execute(
        """
        INSERT INTO public.founder_venue_lead_events (
          lead_id, event_type, metadata, created_by
        ) VALUES (%s::uuid, %s, %s::jsonb, %s)
        """,
        [
            lead_id,
            event_type,
            json.dumps(metadata),
            created_by if created_by and not _bad_uuid(created_by) else None,
        ],
    )


def _process_row(
    cursor: Any,
    row: _NormalizedRow,
    *,
    source_type: str,
    source_name: str | None,
    source_url: str | None,
    imported_by_admin_account_id: str | None,
    update_existing: bool,
    result: FounderVenueImportResult,
) -> None:
    strong_id, strong_reason = _find_strong_duplicate_lead_id(
        cursor,
        dedupe_key=row.dedupe_key,
        phone=row.phone,
        email=row.email,
        host=row.website_host_value,
    )

    if strong_id:
        if update_existing:
            values = _lead_values_for_insert(row)
            changed = _update_lead_empty_fields(cursor, strong_id, values)
            source_id = _insert_source(
                cursor,
                lead_id=strong_id,
                source_type=source_type,
                source_name=source_name,
                source_url=source_url,
                raw_payload=row.raw_row,
                confidence=row.confidence_score,
            )
            _insert_attributions(
                cursor,
                lead_id=strong_id,
                source_id=source_id,
                source_type=source_type,
                source_url=source_url,
                row=row,
                confidence=row.confidence_score,
            )
            _insert_event(
                cursor,
                lead_id=strong_id,
                event_type="import_updated",
                metadata={
                    "source_type": source_type,
                    "source_name": source_name,
                    "row_number": row.row_number,
                    "duplicate_reason": strong_reason,
                    "changed_fields": changed,
                },
                created_by=imported_by_admin_account_id,
            )
            result.leads_updated += 1
        else:
            _insert_event(
                cursor,
                lead_id=strong_id,
                event_type="import_duplicate_skipped",
                metadata={
                    "source_type": source_type,
                    "source_name": source_name,
                    "row_number": row.row_number,
                    "duplicate_reason": strong_reason,
                    "incoming_name": row.name,
                },
                created_by=imported_by_admin_account_id,
            )
            result.duplicates_skipped += 1
        return

    probable_id, probable_reason = _find_probable_duplicate_lead_id(
        cursor,
        normalized_name=row.normalized_name,
        postcode=row.postcode,
        suburb=row.suburb,
        state=row.state,
    )
    if probable_id:
        row.enrichment_status = "needs_review"
        review = DuplicateReview(
            row_number=row.row_number,
            reason=probable_reason or "probable_duplicate",
            existing_lead_id=probable_id,
            name=row.name,
        )
        row.probable_duplicate = review
        result.duplicates_needing_review.append(review)

    values = _lead_values_for_insert(row)
    lead_id = _insert_lead(cursor, values)
    source_id = _insert_source(
        cursor,
        lead_id=lead_id,
        source_type=source_type,
        source_name=source_name,
        source_url=source_url,
        raw_payload=row.raw_row,
        confidence=row.confidence_score,
    )
    _insert_attributions(
        cursor,
        lead_id=lead_id,
        source_id=source_id,
        source_type=source_type,
        source_url=source_url,
        row=row,
        confidence=row.confidence_score,
    )
    event_type = (
        "import_needs_review" if row.probable_duplicate else "import_created"
    )
    _insert_event(
        cursor,
        lead_id=lead_id,
        event_type=event_type,
        metadata={
            "source_type": source_type,
            "source_name": source_name,
            "row_number": row.row_number,
            "probable_duplicate": (
                row.probable_duplicate.reason if row.probable_duplicate else None
            ),
            "existing_lead_id": (
                row.probable_duplicate.existing_lead_id
                if row.probable_duplicate
                else None
            ),
        },
        created_by=imported_by_admin_account_id,
    )
    result.leads_created += 1


def import_founder_venue_leads_csv(
    csv_text: str,
    *,
    source_type: str = "csv_import",
    source_name: str | None = None,
    source_url: str | None = None,
    imported_by_admin_account_id: str | None = None,
    update_existing: bool = False,
    dry_run: bool = False,
    limit: int | None = None,
) -> FounderVenueImportResult:
    """
    Import founder venue leads from CSV text.

    When dry_run=True, no database writes occur; counts reflect planned actions.
    """
    result = FounderVenueImportResult(dry_run=dry_run)

    if source_type not in VALID_SOURCE_TYPES:
        result.errors.append(f"Invalid source_type: {source_type}")
        return result

    if imported_by_admin_account_id and _bad_uuid(imported_by_admin_account_id):
        result.errors.append("imported_by_admin_account_id must be a valid UUID.")
        return result

    headers, raw_rows = parse_csv_rows(csv_text)
    if not headers:
        result.errors.append("CSV has no header row.")
        return result

    header_map = build_header_map(headers)
    if "name" not in header_map.values():
        result.errors.append(
            "CSV must include a venue name column (name, business_name, venue_name, etc.)."
        )
        return result

    normalized_rows: list[_NormalizedRow] = []
    for idx, raw_row in enumerate(raw_rows, start=2):
        if limit is not None and result.rows_processed >= limit:
            break
        result.rows_processed += 1
        raw_fields = map_row_to_lead_fields(raw_row, header_map)
        parsed = normalize_import_row(
            idx, raw_fields, raw_row, source_type=source_type
        )
        if isinstance(parsed, RowError):
            result.invalid_rows.append(parsed)
            continue
        normalized_rows.append(parsed)

    if dry_run:
        with connection.cursor() as cursor:
            for row in normalized_rows:
                strong_id, strong_reason = _find_strong_duplicate_lead_id(
                    cursor,
                    dedupe_key=row.dedupe_key,
                    phone=row.phone,
                    email=row.email,
                    host=row.website_host_value,
                )
                if strong_id:
                    if update_existing:
                        result.leads_updated += 1
                    else:
                        result.duplicates_skipped += 1
                    continue
                probable_id, probable_reason = _find_probable_duplicate_lead_id(
                    cursor,
                    normalized_name=row.normalized_name,
                    postcode=row.postcode,
                    suburb=row.suburb,
                    state=row.state,
                )
                if probable_id:
                    result.duplicates_needing_review.append(
                        DuplicateReview(
                            row_number=row.row_number,
                            reason=probable_reason or "probable_duplicate",
                            existing_lead_id=probable_id,
                            name=row.name,
                        )
                    )
                result.leads_created += 1
        return result

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                for row in normalized_rows:
                    _process_row(
                        cursor,
                        row,
                        source_type=source_type,
                        source_name=source_name,
                        source_url=source_url,
                        imported_by_admin_account_id=imported_by_admin_account_id,
                        update_existing=update_existing,
                        result=result,
                    )
    except Exception as exc:  # noqa: BLE001 — surface DB errors in summary
        result.errors.append(str(exc))

    return result
