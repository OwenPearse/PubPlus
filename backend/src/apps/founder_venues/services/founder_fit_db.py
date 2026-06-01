"""
Database persistence for founder-fit scoring and ranking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from django.db import connection, transaction

from apps.founder_venues.services.scoring import compute_founder_fit_score


@dataclass
class FounderFitRecomputeResult:
    processed: int = 0
    updated: int = 0
    skipped: int = 0
    dry_run: bool = False
    top_scores_preview: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _bad_uuid(value: str) -> bool:
    try:
        UUID(value)
    except (ValueError, TypeError):
        return True
    return False


def _row_to_lead_dict(columns: list[str], row: tuple[Any, ...]) -> dict[str, Any]:
    lead = dict(zip(columns, row, strict=True))
    if lead.get("founder_fit_breakdown") and isinstance(
        lead["founder_fit_breakdown"], str
    ):
        lead["founder_fit_breakdown"] = json.loads(lead["founder_fit_breakdown"])
    return lead


def _load_leads(
    *,
    lead_ids: list[str] | None = None,
    state: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []

    if lead_ids:
        valid_ids = [lid for lid in lead_ids if not _bad_uuid(lid)]
        if not valid_ids:
            return []
        placeholders = ", ".join(["%s::uuid"] * len(valid_ids))
        clauses.append(f"l.id IN ({placeholders})")
        params.extend(valid_ids)

    if state:
        clauses.append("l.state = %s")
        params.append(state.strip().upper())

    sql = f"""
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
          l.latitude,
          l.longitude,
          l.suppressed_at,
          (SELECT COUNT(*)::int FROM public.founder_venue_lead_sources s
           WHERE s.lead_id = l.id) AS source_count
        FROM public.founder_venue_leads l
        WHERE {' AND '.join(clauses)}
        ORDER BY l.updated_at DESC, l.name ASC
    """
    if limit is not None:
        sql += " LIMIT %s"
        params.append(limit)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        return [_row_to_lead_dict(columns, row) for row in cursor.fetchall()]


def recompute_founder_fit_scores(
    *,
    lead_ids: list[str] | None = None,
    state: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> FounderFitRecomputeResult:
    result = FounderFitRecomputeResult(dry_run=dry_run)
    leads = _load_leads(lead_ids=lead_ids, state=state, limit=limit)

    updates: list[tuple[str, int, dict[str, Any], int | None]] = []

    for lead in leads:
        result.processed += 1
        lead_id = lead["id"]
        previous_score = lead.get("founder_fit_score")
        computed = compute_founder_fit_score(lead)

        if dry_run:
            result.updated += 1
            updates.append((lead_id, computed.score, computed.breakdown, previous_score))
            continue

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE public.founder_venue_leads
                        SET founder_fit_score = %s,
                            founder_fit_breakdown = %s::jsonb,
                            updated_at = now()
                        WHERE id = %s::uuid
                        """,
                        [
                            computed.score,
                            json.dumps(computed.breakdown),
                            lead_id,
                        ],
                    )
                    if cursor.rowcount == 0:
                        result.skipped += 1
                        continue

                    cursor.execute(
                        """
                        INSERT INTO public.founder_venue_lead_events (
                          lead_id, event_type, metadata
                        ) VALUES (%s::uuid, %s, %s::jsonb)
                        """,
                        [
                            lead_id,
                            "founder_fit_score_recomputed",
                            json.dumps(
                                {
                                    "previous_score": previous_score,
                                    "new_score": computed.score,
                                    "components": computed.breakdown.get(
                                        "components", {}
                                    ),
                                }
                            ),
                        ],
                    )
            result.updated += 1
            updates.append((lead_id, computed.score, computed.breakdown, previous_score))
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{lead_id}: {exc}")
            result.skipped += 1

    lead_by_id = {lead["id"]: lead for lead in leads}
    preview = sorted(updates, key=lambda x: x[1], reverse=True)[:10]
    result.top_scores_preview = [
        {
            "id": lead_id,
            "name": lead_by_id.get(lead_id, {}).get("name"),
            "suburb": lead_by_id.get(lead_id, {}).get("suburb"),
            "state": lead_by_id.get(lead_id, {}).get("state"),
            "founder_fit_score": score,
            "previous_score": prev,
        }
        for lead_id, score, _breakdown, prev in preview
    ]
    return result


def get_top_founder_venue_leads(
    *,
    state: str | None = None,
    suburb: str | None = None,
    limit: int = 100,
    include_do_not_contact: bool = False,
) -> list[dict[str, Any]]:
    clauses = ["l.suppressed_at IS NULL"]
    params: list[Any] = []

    if not include_do_not_contact:
        clauses.append("l.outreach_status <> 'do_not_contact'")
        clauses.append(
            "l.contact_permission_status NOT IN ('opted_out', 'do_not_contact')"
        )

    if state:
        clauses.append("l.state = %s")
        params.append(state.strip().upper())

    if suburb:
        clauses.append("lower(l.suburb) = lower(%s)")
        params.append(suburb.strip())

    params.append(limit)

    sql = f"""
        SELECT
          l.id::text,
          l.name,
          l.suburb,
          l.state,
          l.category,
          l.phone,
          l.website,
          l.email,
          l.instagram_url,
          l.facebook_url,
          l.confidence_score,
          l.founder_fit_score,
          l.founder_fit_breakdown,
          l.enrichment_status,
          l.outreach_status,
          l.contact_permission_status
        FROM public.founder_venue_leads l
        WHERE {' AND '.join(clauses)}
        ORDER BY
          l.founder_fit_score DESC,
          l.confidence_score DESC,
          l.updated_at DESC,
          l.name ASC
        LIMIT %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = []
        for row in cursor.fetchall():
            item = dict(zip(columns, row, strict=True))
            if isinstance(item.get("founder_fit_breakdown"), str):
                item["founder_fit_breakdown"] = json.loads(
                    item["founder_fit_breakdown"]
                )
            rows.append(item)
        return rows
