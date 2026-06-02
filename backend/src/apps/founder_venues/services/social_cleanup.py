"""Move social URLs out of founder venue lead website fields."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from django.db import connection, transaction

from apps.founder_venues.services.founder_fit_db import recompute_founder_fit_scores
from apps.founder_venues.services.lead_validation import parse_uuid
from apps.founder_venues.services.url_classification import (
    classify_url_kind,
    normalize_social_url,
)

SOCIAL_WEBSITE_KINDS = frozenset({"facebook", "instagram", "other_social", "invalid"})


@dataclass
class LeadSocialCleanupChange:
    lead_id: str
    action: str
    website_before: str | None
    website_after: str | None
    facebook_url_after: str | None
    instagram_url_after: str | None


@dataclass
class SocialCleanupResult:
    processed: int = 0
    updated: int = 0
    moved_to_facebook: int = 0
    moved_to_instagram: int = 0
    cleared_social_website: int = 0
    skipped_target_exists: int = 0
    scores_recomputed: int = 0
    dry_run: bool = False
    changes: list[LeadSocialCleanupChange] = field(default_factory=list)


def _find_leads_for_cleanup(
    *,
    lead_ids: list[str] | None,
    state: str | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    clauses = [
        "l.website IS NOT NULL",
        "btrim(l.website) <> ''",
    ]
    params: list[Any] = []

    if lead_ids:
        valid = [parse_uuid(lid, field_name="lead_id") for lid in lead_ids]
        placeholders = ", ".join(["%s::uuid"] * len(valid))
        clauses.append(f"l.id IN ({placeholders})")
        params.extend(valid)

    if state:
        clauses.append("l.state = %s")
        params.append(state.strip().upper())

    sql = f"""
        SELECT
          l.id::text,
          l.website,
          l.facebook_url,
          l.instagram_url
        FROM public.founder_venue_leads l
        WHERE {' AND '.join(clauses)}
        ORDER BY l.updated_at DESC, l.name ASC
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    candidates: list[dict[str, Any]] = []
    for row in rows:
        if classify_url_kind(row.get("website")) in SOCIAL_WEBSITE_KINDS:
            candidates.append(row)
            if limit is not None and len(candidates) >= limit:
                break
    return candidates


def _plan_change(row: dict[str, Any]) -> LeadSocialCleanupChange:
    website = (row.get("website") or "").strip()
    kind = classify_url_kind(website)
    fb = (row.get("facebook_url") or "").strip() or None
    ig = (row.get("instagram_url") or "").strip() or None
    social_norm = normalize_social_url(website)

    new_website = None
    new_fb = fb
    new_ig = ig
    action = "cleared_social_website"

    if kind == "facebook":
        if fb:
            action = "skipped_target_exists"
        elif social_norm:
            new_fb = social_norm
            action = "moved_to_facebook"
    elif kind == "instagram":
        if ig:
            action = "skipped_target_exists"
        elif social_norm:
            new_ig = social_norm
            action = "moved_to_instagram"

    return LeadSocialCleanupChange(
        lead_id=row["id"],
        action=action,
        website_before=website,
        website_after=new_website,
        facebook_url_after=new_fb,
        instagram_url_after=new_ig,
    )


def _apply_change(change: LeadSocialCleanupChange) -> None:
    metadata = json.dumps(
        {
            "action": change.action,
            "website_before": change.website_before,
            "website_after": change.website_after,
            "facebook_url_after": change.facebook_url_after,
            "instagram_url_after": change.instagram_url_after,
        }
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE public.founder_venue_leads
            SET website = %s,
                facebook_url = %s,
                instagram_url = %s,
                updated_at = now()
            WHERE id = %s::uuid
            """,
            [
                change.website_after,
                change.facebook_url_after,
                change.instagram_url_after,
                change.lead_id,
            ],
        )

        cursor.execute(
            """
            INSERT INTO public.founder_venue_lead_sources (
              lead_id, source_type, source_name, raw_payload, confidence
            ) VALUES (
              %s::uuid, 'manual', 'social_url_cleanup',
              %s::jsonb, 90
            )
            RETURNING id::text
            """,
            [
                change.lead_id,
                json.dumps({"website_before": change.website_before}),
            ],
        )
        source_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO public.founder_venue_lead_field_attributions (
              lead_id, source_id, field_name, source_type,
              confidence, raw_value, normalized_value
            ) VALUES (
              %s::uuid, %s::uuid, 'website', 'manual',
              90, %s, NULL
            )
            """,
            [change.lead_id, source_id, change.website_before],
        )

        if change.action == "moved_to_facebook" and change.facebook_url_after:
            cursor.execute(
                """
                INSERT INTO public.founder_venue_lead_field_attributions (
                  lead_id, source_id, field_name, source_type,
                  confidence, raw_value, normalized_value
                ) VALUES (
                  %s::uuid, %s::uuid, 'facebook_url', 'manual',
                  90, %s, %s
                )
                """,
                [
                    change.lead_id,
                    source_id,
                    change.website_before,
                    change.facebook_url_after,
                ],
            )
        elif change.action == "moved_to_instagram" and change.instagram_url_after:
            cursor.execute(
                """
                INSERT INTO public.founder_venue_lead_field_attributions (
                  lead_id, source_id, field_name, source_type,
                  confidence, raw_value, normalized_value
                ) VALUES (
                  %s::uuid, %s::uuid, 'instagram_url', 'manual',
                  90, %s, %s
                )
                """,
                [
                    change.lead_id,
                    source_id,
                    change.website_before,
                    change.instagram_url_after,
                ],
            )

        cursor.execute(
            """
            INSERT INTO public.founder_venue_lead_events (
              lead_id, event_type, metadata
            ) VALUES (%s::uuid, %s, %s::jsonb)
            """,
            [change.lead_id, "social_url_cleanup_applied", metadata],
        )


def cleanup_social_urls_in_founder_venue_leads(
    *,
    lead_ids: list[str] | None = None,
    state: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    recompute_scores: bool = True,
) -> SocialCleanupResult:
    rows = _find_leads_for_cleanup(lead_ids=lead_ids, state=state, limit=limit)
    result = SocialCleanupResult(dry_run=dry_run)
    changes: list[LeadSocialCleanupChange] = []

    for row in rows:
        result.processed += 1
        change = _plan_change(row)
        changes.append(change)
        result.updated += 1

        if change.action == "moved_to_facebook":
            result.moved_to_facebook += 1
        elif change.action == "moved_to_instagram":
            result.moved_to_instagram += 1
        elif change.action == "cleared_social_website":
            result.cleared_social_website += 1
        elif change.action == "skipped_target_exists":
            result.skipped_target_exists += 1

    result.changes = changes

    if not dry_run and changes:
        with transaction.atomic():
            for change in changes:
                _apply_change(change)

        if recompute_scores:
            recompute = recompute_founder_fit_scores(
                lead_ids=[c.lead_id for c in changes]
            )
            result.scores_recomputed = recompute.updated

    return result
