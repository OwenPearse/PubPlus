"""Read queries and DTO shaping for founder venue lead internal API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.db import connection

from apps.founder_venues.services.lead_validation import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    SORT_OPTIONS,
    LeadNotFoundError,
    LeadValidationError,
    parse_bool_param,
    parse_int_param,
    parse_uuid,
)

_SORT_SQL = {
    "founder_fit_score_desc": "l.founder_fit_score DESC, l.confidence_score DESC, l.updated_at DESC, l.name ASC",
    "confidence_score_desc": "l.confidence_score DESC, l.founder_fit_score DESC, l.updated_at DESC, l.name ASC",
    "updated_at_desc": "l.updated_at DESC, l.founder_fit_score DESC, l.name ASC",
    "created_at_desc": "l.created_at DESC, l.founder_fit_score DESC, l.name ASC",
    "name_asc": "l.name ASC, l.founder_fit_score DESC",
}


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return value


def lead_list_item_dto(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "suburb": row.get("suburb"),
        "state": row.get("state"),
        "category": row.get("category"),
        "phone": row.get("phone"),
        "website": row.get("website"),
        "email": row.get("email"),
        "instagram_url": row.get("instagram_url"),
        "facebook_url": row.get("facebook_url"),
        "confidence_score": row.get("confidence_score"),
        "founder_fit_score": row.get("founder_fit_score"),
        "enrichment_status": row.get("enrichment_status"),
        "outreach_status": row.get("outreach_status"),
        "contact_permission_status": row.get("contact_permission_status"),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
    }


def lead_detail_core_dto(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **lead_list_item_dto(row),
        "venue_id": row.get("venue_id"),
        "normalized_name": row.get("normalized_name"),
        "address_line": row.get("address_line"),
        "postcode": row.get("postcode"),
        "country": row.get("country"),
        "latitude": float(row["latitude"]) if row.get("latitude") is not None else None,
        "longitude": float(row["longitude"]) if row.get("longitude") is not None else None,
        "contact_name": row.get("contact_name"),
        "contact_role": row.get("contact_role"),
        "source_summary": row.get("source_summary"),
        "notes": row.get("notes"),
        "founder_fit_breakdown": _json_field(row.get("founder_fit_breakdown")) or {},
        "last_contacted_at": _iso(row.get("last_contacted_at")),
        "last_contact_channel": row.get("last_contact_channel"),
        "unsubscribe_at": _iso(row.get("unsubscribe_at")),
        "unsubscribe_source": row.get("unsubscribe_source"),
        "suppressed_at": _iso(row.get("suppressed_at")),
        "suppression_reason": row.get("suppression_reason"),
    }


@dataclass
class ListLeadsFilters:
    state: str | None = None
    suburb: str | None = None
    postcode: str | None = None
    search: str | None = None
    enrichment_status: str | None = None
    outreach_status: str | None = None
    contact_permission_status: str | None = None
    score_min: int | None = None
    score_max: int | None = None
    confidence_min: int | None = None
    missing_email: bool = False
    missing_phone: bool = False
    missing_website: bool = False
    needs_review: bool = False
    include_suppressed: bool = False
    include_do_not_contact: bool = False
    sort: str = "founder_fit_score_desc"
    limit: int = DEFAULT_LIMIT
    offset: int = 0


def parse_list_filters(query: dict[str, str]) -> ListLeadsFilters:
    sort = (query.get("sort") or "founder_fit_score_desc").strip()
    if sort not in SORT_OPTIONS:
        raise LeadValidationError(
            f"sort must be one of: {', '.join(sorted(SORT_OPTIONS))}."
        )

    def _optional_int(key: str) -> int | None:
        raw = query.get(key)
        if raw in (None, ""):
            return None
        try:
            return int(raw)
        except (TypeError, ValueError) as exc:
            raise LeadValidationError(f"{key} must be an integer.") from exc

    return ListLeadsFilters(
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
        score_max=_optional_int("score_max"),
        confidence_min=_optional_int("confidence_min"),
        missing_email=parse_bool_param(query.get("missing_email")),
        missing_phone=parse_bool_param(query.get("missing_phone")),
        missing_website=parse_bool_param(query.get("missing_website")),
        needs_review=parse_bool_param(query.get("needs_review")),
        include_suppressed=parse_bool_param(query.get("include_suppressed")),
        include_do_not_contact=parse_bool_param(query.get("include_do_not_contact")),
        sort=sort,
        limit=parse_int_param(
            query.get("limit"),
            default=DEFAULT_LIMIT,
            minimum=1,
            maximum=MAX_LIMIT,
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


def build_founder_venue_lead_filter_where(
    filters: ListLeadsFilters,
) -> tuple[str, list[Any]]:
    """Shared WHERE clause for list and export queries."""
    return _build_list_where(filters)


def _build_list_where(filters: ListLeadsFilters) -> tuple[str, list[Any]]:
    clauses = ["1=1"]
    params: list[Any] = []

    if not filters.include_suppressed:
        clauses.append("l.suppressed_at IS NULL")

    if not filters.include_do_not_contact:
        clauses.append("l.outreach_status <> 'do_not_contact'")
        clauses.append(
            "l.contact_permission_status NOT IN ('opted_out', 'do_not_contact')"
        )

    if filters.state:
        clauses.append("l.state = %s")
        params.append(filters.state)
    if filters.suburb:
        clauses.append("lower(l.suburb) = lower(%s)")
        params.append(filters.suburb)
    if filters.postcode:
        clauses.append("l.postcode = %s")
        params.append(filters.postcode)
    if filters.enrichment_status:
        clauses.append("l.enrichment_status = %s")
        params.append(filters.enrichment_status)
    if filters.outreach_status:
        clauses.append("l.outreach_status = %s")
        params.append(filters.outreach_status)
    if filters.contact_permission_status:
        clauses.append("l.contact_permission_status = %s")
        params.append(filters.contact_permission_status)
    if filters.score_min is not None:
        clauses.append("l.founder_fit_score >= %s")
        params.append(filters.score_min)
    if filters.score_max is not None:
        clauses.append("l.founder_fit_score <= %s")
        params.append(filters.score_max)
    if filters.confidence_min is not None:
        clauses.append("l.confidence_score >= %s")
        params.append(filters.confidence_min)
    if filters.missing_email:
        clauses.append("(l.email IS NULL OR btrim(l.email) = '')")
    if filters.missing_phone:
        clauses.append("(l.phone IS NULL OR btrim(l.phone) = '')")
    if filters.missing_website:
        clauses.append("(l.website IS NULL OR btrim(l.website) = '')")
    if filters.needs_review:
        clauses.append("l.enrichment_status = 'needs_review'")
    if filters.search:
        clauses.append(
            "(l.name ILIKE %s OR l.suburb ILIKE %s OR l.category ILIKE %s)"
        )
        pattern = f"%{filters.search}%"
        params.extend([pattern, pattern, pattern])

    return " AND ".join(clauses), params


def list_founder_venue_leads(filters: ListLeadsFilters) -> dict[str, Any]:
    where_sql, params = build_founder_venue_lead_filter_where(filters)
    order_sql = _SORT_SQL[filters.sort]

    count_sql = f"""
        SELECT COUNT(*)::int FROM public.founder_venue_leads l WHERE {where_sql}
    """
    list_sql = f"""
        SELECT
          l.id::text,
          l.venue_id::text,
          l.name,
          l.normalized_name,
          l.category,
          l.address_line,
          l.suburb,
          l.state,
          l.postcode,
          l.country,
          l.latitude,
          l.longitude,
          l.phone,
          l.website,
          l.email,
          l.instagram_url,
          l.facebook_url,
          l.contact_name,
          l.contact_role,
          l.source_summary,
          l.notes,
          l.confidence_score,
          l.founder_fit_score,
          l.founder_fit_breakdown,
          l.enrichment_status,
          l.outreach_status,
          l.contact_permission_status,
          l.last_contacted_at,
          l.last_contact_channel,
          l.unsubscribe_at,
          l.unsubscribe_source,
          l.suppressed_at,
          l.suppression_reason,
          l.created_at,
          l.updated_at
        FROM public.founder_venue_leads l
        WHERE {where_sql}
        ORDER BY {order_sql}
        LIMIT %s OFFSET %s
    """

    with connection.cursor() as cursor:
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]
        cursor.execute(list_sql, [*params, filters.limit, filters.offset])
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    items = [lead_list_item_dto(row) for row in rows]
    returned = len(items)
    return {
        "items": items,
        "pagination": {
            "limit": filters.limit,
            "offset": filters.offset,
            "count": returned,
            "total": total,
            "has_more": filters.offset + returned < total,
        },
    }


def get_founder_venue_lead_detail(lead_id: str) -> dict[str, Any]:
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              l.id::text,
              l.venue_id::text,
              l.name,
              l.normalized_name,
              l.category,
              l.address_line,
              l.suburb,
              l.state,
              l.postcode,
              l.country,
              l.latitude,
              l.longitude,
              l.phone,
              l.website,
              l.email,
              l.instagram_url,
              l.facebook_url,
              l.contact_name,
              l.contact_role,
              l.source_summary,
              l.notes,
              l.confidence_score,
              l.founder_fit_score,
              l.founder_fit_breakdown,
              l.enrichment_status,
              l.outreach_status,
              l.contact_permission_status,
              l.last_contacted_at,
              l.last_contact_channel,
              l.unsubscribe_at,
              l.unsubscribe_source,
              l.suppressed_at,
              l.suppression_reason,
              l.created_at,
              l.updated_at
            FROM public.founder_venue_leads l
            WHERE l.id = %s::uuid
            """,
            [lead_uuid],
        )
        row = cursor.fetchone()
        if not row:
            raise LeadNotFoundError

        columns = [col[0] for col in cursor.description]
        lead_row = dict(zip(columns, row, strict=True))

        cursor.execute(
            """
            SELECT
              s.id::text,
              s.source_type,
              s.source_url,
              s.source_name,
              s.fetched_at,
              s.confidence,
              s.created_at
            FROM public.founder_venue_lead_sources s
            WHERE s.lead_id = %s::uuid
            ORDER BY s.created_at DESC
            """,
            [lead_uuid],
        )
        source_cols = [c[0] for c in cursor.description]
        sources = []
        for r in cursor.fetchall():
            item = dict(zip(source_cols, r, strict=True))
            sources.append(
                {
                    "id": item["id"],
                    "source_type": item["source_type"],
                    "source_url": item["source_url"],
                    "source_name": item["source_name"],
                    "fetched_at": _iso(item["fetched_at"]),
                    "confidence": item["confidence"],
                    "created_at": _iso(item["created_at"]),
                }
            )

        cursor.execute(
            """
            SELECT
              a.id::text,
              a.field_name,
              a.source_type,
              a.source_url,
              a.confidence,
              a.raw_value,
              a.normalized_value,
              a.contact_safety_class,
              a.fetched_at,
              a.created_at
            FROM public.founder_venue_lead_field_attributions a
            WHERE a.lead_id = %s::uuid
            ORDER BY a.created_at DESC
            """,
            [lead_uuid],
        )
        attr_cols = [c[0] for c in cursor.description]
        attributions = []
        for r in cursor.fetchall():
            item = dict(zip(attr_cols, r, strict=True))
            attributions.append(
                {
                    "id": item["id"],
                    "field_name": item["field_name"],
                    "source_type": item["source_type"],
                    "source_url": item["source_url"],
                    "confidence": item["confidence"],
                    "raw_value": item["raw_value"],
                    "normalized_value": item["normalized_value"],
                    "contact_safety_class": item["contact_safety_class"],
                    "fetched_at": _iso(item["fetched_at"]),
                    "created_at": _iso(item["created_at"]),
                }
            )

        cursor.execute(
            """
            SELECT
              e.id::text,
              e.event_type,
              e.metadata,
              e.created_by::text,
              e.created_at
            FROM public.founder_venue_lead_events e
            WHERE e.lead_id = %s::uuid
            ORDER BY e.created_at DESC
            """,
            [lead_uuid],
        )
        event_cols = [c[0] for c in cursor.description]
        events = []
        for r in cursor.fetchall():
            item = dict(zip(event_cols, r, strict=True))
            events.append(
                {
                    "id": item["id"],
                    "event_type": item["event_type"],
                    "metadata": _json_field(item["metadata"]) or {},
                    "created_by": item["created_by"],
                    "created_at": _iso(item["created_at"]),
                }
            )

    return {
        "lead": lead_detail_core_dto(lead_row),
        "sources": sources,
        "field_attributions": attributions,
        "events": events,
    }
