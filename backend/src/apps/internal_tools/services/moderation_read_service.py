from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from django.db import connection
from django.utils.dateparse import parse_datetime

from apps.venues.services.published_venue_read import load_published_venue_read_bundle

ALLOWED_STATUSES = frozenset(
    {"staged", "in_review", "approved", "rejected", "withdrawn", "superseded"}
)
OPEN_STATUSES = ("staged", "in_review")
API_DOMAIN_TO_DB = {
    "profile": "profile",
    "location": "geo",
    "geo": "geo",
    "attributes": "attributes",
    "hours": "hours",
    "whole_venue": "whole_venue",
}


class ModerationReadValidationError(ValueError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ModerationItemNotFoundError(LookupError):
    pass


class VenueNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class ModerationQueueFilters:
    statuses: tuple[str, ...]
    domains: tuple[str, ...] | None
    venue_id: str | None
    created_before: datetime | None
    created_after: datetime | None


def _parse_uuid(value: str, *, key: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError) as exc:
        raise ModerationReadValidationError(
            f"{key} must be a valid UUID."
        ) from exc


def _parse_csv_values(value: str) -> tuple[str, ...]:
    out: list[str] = []
    for raw in value.split(","):
        item = raw.strip()
        if item:
            out.append(item)
    return tuple(out)


def parse_queue_filters(raw: dict[str, str]) -> ModerationQueueFilters:
    allowed = {"status", "domain", "venue_id", "created_before", "created_after"}
    unknown = sorted(set(raw.keys()) - allowed)
    if unknown:
        raise ModerationReadValidationError(
            f"Unsupported query parameter(s): {', '.join(unknown)}."
        )

    statuses: tuple[str, ...]
    raw_status = raw.get("status", "").strip()
    if raw_status:
        vals = _parse_csv_values(raw_status)
        if not vals:
            raise ModerationReadValidationError("status filter cannot be empty.")
        bad = sorted(v for v in vals if v not in ALLOWED_STATUSES)
        if bad:
            raise ModerationReadValidationError(
                f"status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}."
            )
        statuses = vals
    else:
        statuses = OPEN_STATUSES

    domains: tuple[str, ...] | None = None
    raw_domain = raw.get("domain", "").strip()
    if raw_domain:
        vals = _parse_csv_values(raw_domain)
        if not vals:
            raise ModerationReadValidationError("domain filter cannot be empty.")
        mapped: list[str] = []
        for v in vals:
            key = v.strip().lower()
            if key not in API_DOMAIN_TO_DB:
                raise ModerationReadValidationError(
                    "domain must be one of: profile, location, attributes, hours, whole_venue."
                )
            mapped.append(API_DOMAIN_TO_DB[key])
        domains = tuple(mapped)

    venue_id: str | None = None
    raw_venue_id = raw.get("venue_id", "").strip()
    if raw_venue_id:
        venue_id = _parse_uuid(raw_venue_id, key="venue_id")

    created_before: datetime | None = None
    raw_created_before = raw.get("created_before", "").strip()
    if raw_created_before:
        created_before = parse_datetime(raw_created_before)
        if created_before is None:
            raise ModerationReadValidationError(
                "created_before must be an ISO-8601 datetime."
            )

    created_after: datetime | None = None
    raw_created_after = raw.get("created_after", "").strip()
    if raw_created_after:
        created_after = parse_datetime(raw_created_after)
        if created_after is None:
            raise ModerationReadValidationError(
                "created_after must be an ISO-8601 datetime."
            )

    return ModerationQueueFilters(
        statuses=statuses,
        domains=domains,
        venue_id=venue_id,
        created_before=created_before,
        created_after=created_after,
    )


def list_moderation_queue(filters: ModerationQueueFilters) -> dict[str, Any]:
    where = ["p.lifecycle_status = ANY(%s)"]
    params: list[Any] = [list(filters.statuses)]

    if filters.venue_id:
        where.append("p.venue_id = %s::uuid")
        params.append(filters.venue_id)
    if filters.domains:
        where.append(
            """
            EXISTS (
                SELECT 1
                FROM public.venue_proposal_target tf
                WHERE tf.venue_change_proposal_id = p.id
                  AND tf.target_family = ANY(%s)
            )
            """
        )
        params.append(list(filters.domains))
    if filters.created_before:
        where.append("COALESCE(p.submitted_at, p.created_at) <= %s")
        params.append(filters.created_before)
    if filters.created_after:
        where.append("COALESCE(p.submitted_at, p.created_at) >= %s")
        params.append(filters.created_after)

    sql = f"""
        SELECT
          p.id::text,
          p.venue_id::text,
          p.lifecycle_status::text,
          p.proposal_kind::text,
          p.channel::text,
          p.submitted_at,
          p.created_at,
          p.actor_type::text,
          p.actor_consumer_account_id::text,
          cse.app_surface,
          COALESCE(vpp.display_name, vpsp.proposed_display_name) AS venue_label,
          COALESCE(
            array_agg(DISTINCT t.target_family::text)
              FILTER (WHERE t.target_family IS NOT NULL),
            '{{}}'
          ) AS target_families
        FROM public.venue_change_proposal p
        LEFT JOIN public.venue_proposal_target t
          ON t.venue_change_proposal_id = p.id
        LEFT JOIN public.venue_published_profile vpp
          ON vpp.venue_id = p.venue_id
        LEFT JOIN public.venue_proposal_staging_profile vpsp
          ON vpsp.venue_change_proposal_id = p.id
        LEFT JOIN public.consumer_submission_extension cse
          ON cse.venue_change_proposal_id = p.id
        WHERE {' AND '.join(where)}
        GROUP BY
          p.id, p.venue_id, p.lifecycle_status, p.proposal_kind, p.channel,
          p.submitted_at, p.created_at, p.actor_type, p.actor_consumer_account_id,
          cse.app_surface, vpp.display_name, vpsp.proposed_display_name
        ORDER BY COALESCE(p.submitted_at, p.created_at) DESC, p.created_at DESC, p.id DESC
    """

    items: list[dict[str, Any]] = []
    with connection.cursor() as c:
        c.execute(sql, params)
        for row in c.fetchall():
            items.append(
                {
                    "item_id": row[0],
                    "venue_id": row[1],
                    "status": row[2],
                    "proposal_kind": row[3],
                    "channel": row[4],
                    "submitted_at": row[5].isoformat() if row[5] else None,
                    "created_at": row[6].isoformat() if row[6] else None,
                    "domain_tags": list(row[11] or []),
                    "venue_label": row[10],
                    "submitter": {
                        "actor_type": row[7],
                        "consumer_account_id": row[8],
                        "app_surface": row[9],
                    },
                }
            )
    return {"items": items}


def _load_targets(proposal_id: str) -> list[str]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT target_family::text
            FROM public.venue_proposal_target
            WHERE venue_change_proposal_id = %s::uuid
            ORDER BY target_family
            """,
            [proposal_id],
        )
        return [str(r[0]) for r in c.fetchall()]


def _load_staging(proposal_id: str) -> dict[str, Any]:
    staging: dict[str, Any] = {
        "profile": None,
        "location": None,
        "attributes": [],
        "hours": None,
    }
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              proposed_display_name,
              proposed_slug,
              proposed_discovery_eligibility_status,
              proposed_operational_status,
              proposed_short_description,
              proposed_long_description
            FROM public.venue_proposal_staging_profile
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        row = c.fetchone()
        if row:
            staging["profile"] = {
                "display_name": row[0],
                "slug": row[1],
                "discovery_eligibility_status": row[2],
                "operational_status": row[3],
                "short_description": row[4],
                "long_description": row[5],
            }

        c.execute(
            """
            SELECT
              proposed_locality_id::text,
              proposed_address_line_1,
              proposed_address_line_2,
              proposed_postal_code,
              proposed_country_code,
              proposed_latitude,
              proposed_longitude
            FROM public.venue_proposal_staging_location
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        row = c.fetchone()
        if row:
            staging["location"] = {
                "locality_id": row[0],
                "address_line_1": row[1],
                "address_line_2": row[2],
                "postal_code": row[3],
                "country_code": row[4],
                "latitude": row[5],
                "longitude": row[6],
            }

        c.execute(
            """
            SELECT
              attribute_definition_id::text,
              allowed_value_id::text,
              value_boolean,
              value_numeric
            FROM public.venue_proposal_staging_attribute
            WHERE venue_change_proposal_id = %s::uuid
            ORDER BY id
            """,
            [proposal_id],
        )
        staging["attributes"] = [
            {
                "attribute_definition_id": r[0],
                "allowed_value_id": r[1],
                "value_boolean": r[2],
                "value_numeric": r[3],
            }
            for r in c.fetchall()
        ]

        c.execute(
            """
            SELECT
              proposed_uncertainty_level,
              regular_hours_json,
              exceptions_json,
              notes
            FROM public.venue_proposal_staging_hours
            WHERE venue_change_proposal_id = %s::uuid
            """,
            [proposal_id],
        )
        row = c.fetchone()
        if row:
            staging["hours"] = {
                "uncertainty_level": row[0],
                "regular_hours_json": row[1],
                "exceptions_json": row[2],
                "notes": row[3],
            }
    return staging


def _load_reviews(proposal_id: str) -> list[dict[str, Any]]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              id::text,
              reviewer_admin_account_id::text,
              review_sequence,
              review_outcome::text,
              reason_code,
              decision_reason_text,
              reviewed_at
            FROM public.proposal_review
            WHERE venue_change_proposal_id = %s::uuid
            ORDER BY review_sequence ASC, reviewed_at ASC
            """,
            [proposal_id],
        )
        out: list[dict[str, Any]] = []
        for r in c.fetchall():
            out.append(
                {
                    "id": r[0],
                    "reviewer_admin_account_id": r[1],
                    "review_sequence": r[2],
                    "review_outcome": r[3],
                    "reason_code": r[4],
                    "decision_reason_text": r[5],
                    "reviewed_at": r[6].isoformat() if r[6] else None,
                }
            )
        return out


def _load_internal_notes(proposal_id: str) -> list[dict[str, Any]]:
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              ae.id::text,
              ae.actor_admin_account_id::text,
              ae.occurred_at,
              ae.detail
            FROM public.audit_event ae
            WHERE ae.entity_table = 'venue_change_proposal'
              AND ae.entity_id = %s::uuid
              AND ae.action = 'internal_note'
            ORDER BY ae.occurred_at ASC, ae.id ASC
            """,
            [proposal_id],
        )
        out: list[dict[str, Any]] = []
        for r in c.fetchall():
            detail = r[3] if isinstance(r[3], dict) else {}
            out.append(
                {
                    "id": r[0],
                    "actor_admin_account_id": r[1],
                    "body": detail.get("body"),
                    "created_at": r[2].isoformat() if r[2] else None,
                }
            )
        return out


def _load_published_context(venue_id: str) -> dict[str, Any] | None:
    bundle = load_published_venue_read_bundle(venue_id)
    if bundle is None:
        return None
    core = bundle.core
    return {
        "display_name": core.display_name,
        "operational_status": core.operational_status,
        "suburb": core.suburb_name,
        "address_line_1": core.address_line_1,
        "address_line_2": core.address_line_2,
        "postal_code": core.postal_code,
        "country_code": core.country_code,
        "latitude": core.latitude,
        "longitude": core.longitude,
    }


def get_moderation_item_detail(item_id: str) -> dict[str, Any]:
    proposal_id = _parse_uuid(item_id, key="item_id")
    with connection.cursor() as c:
        c.execute(
            """
            SELECT
              p.id::text,
              p.venue_id::text,
              p.actor_type::text,
              p.actor_consumer_account_id::text,
              p.channel::text,
              p.proposal_kind::text,
              p.lifecycle_status::text,
              p.created_at,
              p.submitted_at,
              p.closed_at,
              cse.app_surface,
              cse.client_correlation_id
            FROM public.venue_change_proposal p
            LEFT JOIN public.consumer_submission_extension cse
              ON cse.venue_change_proposal_id = p.id
            WHERE p.id = %s::uuid
            """,
            [proposal_id],
        )
        row = c.fetchone()
    if not row:
        raise ModerationItemNotFoundError

    venue_id = str(row[1])
    return {
        "item_id": str(row[0]),
        "venue_id": venue_id,
        "status": row[6],
        "proposal_kind": row[5],
        "channel": row[4],
        "created_at": row[7].isoformat() if row[7] else None,
        "submitted_at": row[8].isoformat() if row[8] else None,
        "closed_at": row[9].isoformat() if row[9] else None,
        "target_families": _load_targets(proposal_id),
        "staging": _load_staging(proposal_id),
        "published_context": _load_published_context(venue_id),
        "submitter": {
            "actor_type": row[2],
            "consumer_account_id": row[3],
            "app_surface": row[10],
            "client_correlation_id": row[11],
        },
        "reviews": _load_reviews(proposal_id),
        "internal_notes": _load_internal_notes(proposal_id),
    }


def get_internal_venue_detail(venue_id: str) -> dict[str, Any]:
    vid = _parse_uuid(venue_id, key="venue_id")
    with connection.cursor() as c:
        c.execute("SELECT id::text, created_at FROM public.venue WHERE id = %s::uuid", [vid])
        vrow = c.fetchone()
    if not vrow:
        raise VenueNotFoundError

    published = _load_published_context(vid)
    with connection.cursor() as c:
        c.execute(
            """
            SELECT count(*)::int
            FROM public.venue_change_proposal
            WHERE venue_id = %s::uuid
              AND lifecycle_status = ANY(%s)
            """,
            [vid, list(OPEN_STATUSES)],
        )
        open_count = int(c.fetchone()[0])
        c.execute(
            """
            SELECT id::text
            FROM public.venue_change_proposal
            WHERE venue_id = %s::uuid
              AND lifecycle_status = ANY(%s)
            ORDER BY COALESCE(submitted_at, created_at) DESC, created_at DESC, id DESC
            LIMIT 1
            """,
            [vid, list(OPEN_STATUSES)],
        )
        latest_open = c.fetchone()
    latest_open_id = str(latest_open[0]) if latest_open else None

    shell_fallback: dict[str, Any] | None = None
    if published is None:
        with connection.cursor() as c:
            c.execute(
                """
                SELECT
                  p.id::text,
                  p.proposal_kind::text,
                  p.lifecycle_status::text,
                  p.submitted_at,
                  sp.proposed_display_name,
                  sl.proposed_address_line_1,
                  sl.proposed_address_line_2,
                  sl.proposed_postal_code,
                  sl.proposed_country_code,
                  sl.proposed_latitude,
                  sl.proposed_longitude
                FROM public.venue_change_proposal p
                LEFT JOIN public.venue_proposal_staging_profile sp
                  ON sp.venue_change_proposal_id = p.id
                LEFT JOIN public.venue_proposal_staging_location sl
                  ON sl.venue_change_proposal_id = p.id
                WHERE p.venue_id = %s::uuid
                ORDER BY COALESCE(p.submitted_at, p.created_at) DESC, p.created_at DESC, p.id DESC
                LIMIT 1
                """,
                [vid],
            )
            row = c.fetchone()
        if row:
            shell_fallback = {
                "source_proposal_id": row[0],
                "proposal_kind": row[1],
                "proposal_status": row[2],
                "proposal_submitted_at": row[3].isoformat() if row[3] else None,
                "display_name": row[4],
                "address_line_1": row[5],
                "address_line_2": row[6],
                "postal_code": row[7],
                "country_code": row[8],
                "latitude": row[9],
                "longitude": row[10],
            }

    return {
        "venue_id": str(vrow[0]),
        "venue_created_at": vrow[1].isoformat() if vrow[1] else None,
        "published": published,
        "shell_fallback": shell_fallback,
        "workflow_summary": {
            "open_proposal_count": open_count,
            "latest_open_proposal_id": latest_open_id,
        },
    }
