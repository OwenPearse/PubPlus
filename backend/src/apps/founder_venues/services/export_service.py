"""CSV export for founder venue leads (safe outreach / CRM import)."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from django.db import connection, transaction

from apps.founder_venues.services.contact_safety import classify_email_contact_safety
from apps.founder_venues.services.lead_queries import (
    ListLeadsFilters,
    build_founder_venue_lead_filter_where,
)
from apps.founder_venues.services.lead_validation import (
    EXPORT_DEFAULT_LIMIT,
    EXPORT_MAX_LIMIT,
    LeadValidationError,
    parse_bool_param,
    parse_int_param,
)

NOTES_SUMMARY_MAX_LEN = 200

UNSAFE_EMAIL_SAFETY_CLASSES = frozenset(
    {"personal_business_contact", "likely_personal_or_unsafe"}
)

DEFAULT_CSV_COLUMNS: tuple[str, ...] = (
    "founder_venue_lead_id",
    "venue_name",
    "suburb",
    "state",
    "postcode",
    "category",
    "phone",
    "email",
    "email_redacted_reason",
    "website",
    "instagram_url",
    "facebook_url",
    "founder_fit_score",
    "confidence_score",
    "enrichment_status",
    "outreach_status",
    "contact_permission_status",
    "source_summary",
    "notes_summary",
    "last_contacted_at",
    "last_contact_channel",
)

_EXPORT_SORT_SQL = (
    "l.founder_fit_score DESC, l.confidence_score DESC, l.updated_at DESC, l.name ASC"
)


@dataclass
class ExportExcludedCounts:
    do_not_contact_excluded: int = 0
    unsafe_email_redacted: int = 0
    suppressed_excluded: int = 0


@dataclass
class FounderVenueExportResult:
    csv_text: str
    row_count: int
    filters_applied: dict[str, Any]
    excluded_counts: ExportExcludedCounts
    generated_at: str


@dataclass
class ExportLeadsFilters:
    state: str | None = None
    suburb: str | None = None
    postcode: str | None = None
    search: str | None = None
    enrichment_status: str | None = None
    outreach_status: str | None = None
    contact_permission_status: str | None = None
    score_min: int | None = None
    confidence_min: int | None = None
    missing_email: bool = False
    missing_phone: bool = False
    missing_website: bool = False
    needs_review: bool = False
    include_do_not_contact: bool = False
    include_suppressed: bool = False
    include_unsafe_emails: bool = False
    include_raw_notes: bool = False
    limit: int = EXPORT_DEFAULT_LIMIT
    offset: int = 0


def truncate_notes_summary(notes: str | None, *, max_len: int = NOTES_SUMMARY_MAX_LEN) -> str:
    if not notes:
        return ""
    collapsed = " ".join(str(notes).split())
    if len(collapsed) <= max_len:
        return collapsed
    return collapsed[: max_len - 3] + "..."


def resolve_export_email(
    *,
    email: str | None,
    email_safety_class: str | None,
    outreach_status: str | None,
    contact_permission_status: str | None,
    suppressed_at: Any,
    include_unsafe_emails: bool,
) -> tuple[str, str]:
    """
    Return (email_for_csv, email_redacted_reason).

    Status-based redaction applies even when DNC/suppressed rows are included.
    """
    if outreach_status == "do_not_contact":
        return "", "do_not_contact"
    if contact_permission_status == "opted_out":
        return "", "opted_out"
    if contact_permission_status == "do_not_contact":
        return "", "do_not_contact"
    if suppressed_at is not None:
        return "", "suppressed"

    raw = (email or "").strip()
    if not raw:
        return "", ""

    safety = email_safety_class or classify_email_contact_safety(raw)
    if not include_unsafe_emails and safety in UNSAFE_EMAIL_SAFETY_CLASSES:
        return "", safety or ""

    return raw, ""


def _filters_applied_dict(
    filters: ExportLeadsFilters,
    *,
    exported_by_admin_account_id: str | None,
) -> dict[str, Any]:
    payload = asdict(filters)
    if exported_by_admin_account_id:
        payload["exported_by_admin_account_id"] = exported_by_admin_account_id
    return payload


def _to_list_filters(filters: ExportLeadsFilters) -> ListLeadsFilters:
    return ListLeadsFilters(
        state=filters.state,
        suburb=filters.suburb,
        postcode=filters.postcode,
        search=filters.search,
        enrichment_status=filters.enrichment_status,
        outreach_status=filters.outreach_status,
        contact_permission_status=filters.contact_permission_status,
        score_min=filters.score_min,
        confidence_min=filters.confidence_min,
        missing_email=filters.missing_email,
        missing_phone=filters.missing_phone,
        missing_website=filters.missing_website,
        needs_review=filters.needs_review,
        include_suppressed=filters.include_suppressed,
        include_do_not_contact=filters.include_do_not_contact,
        sort="founder_fit_score_desc",
        limit=filters.limit,
        offset=filters.offset,
    )


def parse_export_filters(query: dict[str, str]) -> ExportLeadsFilters:
    def _optional_int(key: str) -> int | None:
        raw = query.get(key)
        if raw in (None, ""):
            return None
        try:
            return int(raw)
        except (TypeError, ValueError) as exc:
            raise LeadValidationError(f"{key} must be an integer.") from exc

    return ExportLeadsFilters(
        state=(query.get("state") or "").strip().upper() or None,
        suburb=(query.get("suburb") or "").strip() or None,
        postcode=(query.get("postcode") or "").strip() or None,
        search=(query.get("search") or "").strip() or None,
        enrichment_status=(query.get("enrichment_status") or "").strip() or None,
        outreach_status=(query.get("outreach_status") or "").strip() or None,
        contact_permission_status=(
            (query.get("contact_permission_status") or "").strip() or None
        ),
        score_min=_optional_int("score_min"),
        confidence_min=_optional_int("confidence_min"),
        missing_email=parse_bool_param(query.get("missing_email")),
        missing_phone=parse_bool_param(query.get("missing_phone")),
        missing_website=parse_bool_param(query.get("missing_website")),
        needs_review=parse_bool_param(query.get("needs_review")),
        include_do_not_contact=parse_bool_param(query.get("include_do_not_contact")),
        include_suppressed=parse_bool_param(query.get("include_suppressed")),
        include_unsafe_emails=parse_bool_param(query.get("include_unsafe_emails")),
        include_raw_notes=parse_bool_param(query.get("include_raw_notes")),
        limit=parse_int_param(
            query.get("limit"),
            default=EXPORT_DEFAULT_LIMIT,
            minimum=1,
            maximum=EXPORT_MAX_LIMIT,
            field_name="limit",
        ),
        offset=parse_int_param(
            query.get("offset"),
            default=0,
            minimum=0,
            maximum=10_000,
            field_name="offset",
        ),
    )


def _iso_export(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _csv_columns(filters: ExportLeadsFilters) -> list[str]:
    columns = list(DEFAULT_CSV_COLUMNS)
    if filters.include_raw_notes:
        columns.append("notes")
    return columns


def _row_to_csv_dict(
    row: dict[str, Any],
    *,
    filters: ExportLeadsFilters,
) -> dict[str, str]:
    export_email, redaction_reason = resolve_export_email(
        email=row.get("email"),
        email_safety_class=row.get("email_safety_class"),
        outreach_status=row.get("outreach_status"),
        contact_permission_status=row.get("contact_permission_status"),
        suppressed_at=row.get("suppressed_at"),
        include_unsafe_emails=filters.include_unsafe_emails,
    )
    out: dict[str, str] = {
        "founder_venue_lead_id": row.get("id") or "",
        "venue_name": row.get("name") or "",
        "suburb": row.get("suburb") or "",
        "state": row.get("state") or "",
        "postcode": row.get("postcode") or "",
        "category": row.get("category") or "",
        "phone": row.get("phone") or "",
        "email": export_email,
        "email_redacted_reason": redaction_reason,
        "website": row.get("website") or "",
        "instagram_url": row.get("instagram_url") or "",
        "facebook_url": row.get("facebook_url") or "",
        "founder_fit_score": str(row.get("founder_fit_score") or 0),
        "confidence_score": str(row.get("confidence_score") or 0),
        "enrichment_status": row.get("enrichment_status") or "",
        "outreach_status": row.get("outreach_status") or "",
        "contact_permission_status": row.get("contact_permission_status") or "",
        "source_summary": row.get("source_summary") or "",
        "notes_summary": truncate_notes_summary(row.get("notes")),
        "last_contacted_at": _iso_export(row.get("last_contacted_at")),
        "last_contact_channel": row.get("last_contact_channel") or "",
    }
    if filters.include_raw_notes:
        out["notes"] = row.get("notes") or ""
    return out


def _count_excluded_leads(filters: ExportLeadsFilters) -> ExportExcludedCounts:
    """Count leads excluded only by default DNC/suppression filters."""
    counts = ExportExcludedCounts()
    with connection.cursor() as cursor:
        if not filters.include_do_not_contact:
            relaxed = _to_list_filters(filters)
            relaxed.include_do_not_contact = True
            where_sql, params = build_founder_venue_lead_filter_where(relaxed)
            cursor.execute(
                f"""
                SELECT COUNT(*)::int FROM public.founder_venue_leads l
                WHERE {where_sql}
                  AND (
                    l.outreach_status = 'do_not_contact'
                    OR l.contact_permission_status IN ('opted_out', 'do_not_contact')
                  )
                """,
                params,
            )
            counts.do_not_contact_excluded = cursor.fetchone()[0]

        if not filters.include_suppressed:
            relaxed = _to_list_filters(filters)
            relaxed.include_suppressed = True
            where_sql, params = build_founder_venue_lead_filter_where(relaxed)
            cursor.execute(
                f"""
                SELECT COUNT(*)::int FROM public.founder_venue_leads l
                WHERE {where_sql} AND l.suppressed_at IS NOT NULL
                """,
                params,
            )
            counts.suppressed_excluded = cursor.fetchone()[0]

    return counts


def _write_export_events(
    lead_ids: list[str],
    *,
    filters: ExportLeadsFilters,
    exported_by_admin_account_id: str | None,
) -> None:
    if not lead_ids:
        return

    metadata = json.dumps(
        {
            "export_type": "csv",
            "filters_applied": asdict(filters),
            "include_unsafe_emails": filters.include_unsafe_emails,
            "include_do_not_contact": filters.include_do_not_contact,
            "include_suppressed": filters.include_suppressed,
        }
    )
    rows = [
        (lead_id, "lead_exported", metadata, exported_by_admin_account_id)
        for lead_id in lead_ids
    ]
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO public.founder_venue_lead_events (
              lead_id, event_type, metadata, created_by
            ) VALUES (%s::uuid, %s, %s::jsonb, %s::uuid)
            """,
            rows,
        )


def export_founder_venue_leads_csv(
    *,
    state: str | None = None,
    suburb: str | None = None,
    postcode: str | None = None,
    search: str | None = None,
    enrichment_status: str | None = None,
    outreach_status: str | None = None,
    contact_permission_status: str | None = None,
    score_min: int | None = None,
    confidence_min: int | None = None,
    missing_email: bool | None = None,
    missing_phone: bool | None = None,
    missing_website: bool | None = None,
    needs_review: bool | None = None,
    include_do_not_contact: bool = False,
    include_suppressed: bool = False,
    include_unsafe_emails: bool = False,
    include_raw_notes: bool = False,
    limit: int = EXPORT_DEFAULT_LIMIT,
    offset: int = 0,
    exported_by_admin_account_id: str | None = None,
) -> FounderVenueExportResult:
    filters = ExportLeadsFilters(
        state=state,
        suburb=suburb,
        postcode=postcode,
        search=search,
        enrichment_status=enrichment_status,
        outreach_status=outreach_status,
        contact_permission_status=contact_permission_status,
        score_min=score_min,
        confidence_min=confidence_min,
        missing_email=bool(missing_email),
        missing_phone=bool(missing_phone),
        missing_website=bool(missing_website),
        needs_review=bool(needs_review),
        include_do_not_contact=include_do_not_contact,
        include_suppressed=include_suppressed,
        include_unsafe_emails=include_unsafe_emails,
        include_raw_notes=include_raw_notes,
        limit=min(max(limit, 1), EXPORT_MAX_LIMIT),
        offset=max(offset, 0),
    )
    list_filters = _to_list_filters(filters)
    where_sql, params = build_founder_venue_lead_filter_where(list_filters)

    export_sql = f"""
        SELECT
          l.id::text,
          l.name,
          l.suburb,
          l.state,
          l.postcode,
          l.category,
          l.phone,
          l.email,
          l.website,
          l.instagram_url,
          l.facebook_url,
          l.confidence_score,
          l.founder_fit_score,
          l.enrichment_status,
          l.outreach_status,
          l.contact_permission_status,
          l.source_summary,
          l.notes,
          l.last_contacted_at,
          l.last_contact_channel,
          l.suppressed_at,
          email_attr.contact_safety_class AS email_safety_class
        FROM public.founder_venue_leads l
        LEFT JOIN LATERAL (
          SELECT a.contact_safety_class
          FROM public.founder_venue_lead_field_attributions a
          WHERE a.lead_id = l.id AND a.field_name = 'email'
          ORDER BY a.created_at DESC
          LIMIT 1
        ) email_attr ON true
        WHERE {where_sql}
        ORDER BY {_EXPORT_SORT_SQL}
        LIMIT %s OFFSET %s
    """

    generated_at = datetime.now(timezone.utc).isoformat()
    excluded_counts = ExportExcludedCounts()

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(export_sql, [*params, filters.limit, filters.offset])
            columns = [col[0] for col in cursor.description]
            db_rows = [
                dict(zip(columns, row, strict=True)) for row in cursor.fetchall()
            ]

        csv_rows: list[dict[str, str]] = []
        lead_ids: list[str] = []
        for row in db_rows:
            csv_row = _row_to_csv_dict(row, filters=filters)
            reason = csv_row.get("email_redacted_reason") or ""
            if row.get("email") and reason in UNSAFE_EMAIL_SAFETY_CLASSES:
                excluded_counts.unsafe_email_redacted += 1
            csv_rows.append(csv_row)
            lead_ids.append(row["id"])

        _write_export_events(
            lead_ids,
            filters=filters,
            exported_by_admin_account_id=exported_by_admin_account_id,
        )

    extra_excluded = _count_excluded_leads(filters)
    excluded_counts.do_not_contact_excluded = extra_excluded.do_not_contact_excluded
    excluded_counts.suppressed_excluded = extra_excluded.suppressed_excluded

    columns = _csv_columns(filters)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(csv_rows)

    return FounderVenueExportResult(
        csv_text=buffer.getvalue(),
        row_count=len(csv_rows),
        filters_applied=_filters_applied_dict(
            filters, exported_by_admin_account_id=exported_by_admin_account_id
        ),
        excluded_counts=excluded_counts,
        generated_at=generated_at,
    )
