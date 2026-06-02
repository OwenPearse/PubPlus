"""Persist founder venue lead enrichment from venue websites."""

from __future__ import annotations

import json
from typing import Any

from django.db import connection, transaction

from apps.founder_venues.services.enrichment.extractors import (
    extract_contact_page_url,
    extract_emails_from_html,
    extract_phones_from_html,
    extract_product_signals_from_html,
    extract_social_links_from_html,
    is_email_auto_promotable,
)
from apps.founder_venues.services.enrichment.result import (
    WebsiteEnrichmentCandidate,
    WebsiteEnrichmentResult,
)
from apps.founder_venues.services.enrichment.website import (
    FetchedPage,
    PageFetcher,
    fetch_venue_website_pages,
)
from apps.founder_venues.services.url_classification import (
    is_social_profile_url,
    website_url_is_fetchable,
)
from apps.founder_venues.services.founder_fit_db import recompute_founder_fit_scores
from apps.founder_venues.services.import_service import compute_import_confidence
from apps.founder_venues.services.lead_validation import LeadNotFoundError, parse_uuid
from apps.founder_venues.services.normalization import (
    normalize_website_url,
    website_host,
)

PROMOTABLE_FIELDS = frozenset({"email", "phone", "instagram_url", "facebook_url"})


def _is_contact_page(url: str) -> bool:
    path = (url or "").lower()
    return any(
        kw in path
        for kw in ("contact", "about", "bookings", "book", "functions", "events")
    )


def _extract_from_pages(
    pages: list[FetchedPage],
    *,
    venue_host: str | None,
) -> tuple[list[WebsiteEnrichmentCandidate], list[str]]:
    candidates: list[WebsiteEnrichmentCandidate] = []
    signals: list[str] = []
    seen_signals: set[str] = set()

    for page in pages:
        contact_page = _is_contact_page(page.url)
        candidates.extend(
            extract_emails_from_html(
                page.html,
                source_url=page.url,
                venue_host=venue_host,
                contact_page=contact_page,
            )
        )
        candidates.extend(
            extract_phones_from_html(
                page.html,
                source_url=page.url,
                contact_page=contact_page,
            )
        )
        candidates.extend(
            extract_social_links_from_html(page.html, source_url=page.url)
        )
        contact_url = extract_contact_page_url(
            page.html, source_url=page.url, venue_host=venue_host
        )
        if contact_url:
            candidates.append(contact_url)
        for signal in extract_product_signals_from_html(page.html):
            if signal not in seen_signals:
                seen_signals.add(signal)
                signals.append(signal)

    return candidates, signals


def _best_candidates(
    candidates: list[WebsiteEnrichmentCandidate],
) -> dict[str, WebsiteEnrichmentCandidate]:
    best: dict[str, WebsiteEnrichmentCandidate] = {}
    for candidate in candidates:
        key = candidate.field_name
        if key == "contact_page_url":
            continue
        existing = best.get(key)
        if existing is None or candidate.confidence > existing.confidence:
            best[key] = candidate
    return best


def _load_lead_row(lead_id: str) -> dict[str, Any]:
    lead_uuid = parse_uuid(lead_id, field_name="lead_id")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              l.id::text,
              l.name,
              l.website,
              l.email,
              l.phone,
              l.instagram_url,
              l.facebook_url,
              l.source_summary,
              l.notes,
              l.confidence_score,
              l.enrichment_status,
              l.address_line,
              l.suburb,
              l.state,
              l.postcode,
              l.latitude,
              l.longitude
            FROM public.founder_venue_leads l
            WHERE l.id = %s::uuid
            """,
            [lead_uuid],
        )
        row = cursor.fetchone()
        if not row:
            raise LeadNotFoundError
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row, strict=True))


def _values_conflict(existing: str | None, new_value: str | None) -> bool:
    if not existing or not new_value:
        return False
    return existing.strip().lower() != new_value.strip().lower()


def _decide_promotions(
    lead: dict[str, Any],
    best: dict[str, WebsiteEnrichmentCandidate],
) -> tuple[dict[str, str], bool, list[str]]:
    """Return field updates, needs_review flag, promoted field names."""
    updates: dict[str, str] = {}
    promoted: list[str] = []
    needs_review = False

    for field_name, candidate in best.items():
        if field_name not in PROMOTABLE_FIELDS:
            continue
        normalized = candidate.normalized_value
        if not normalized:
            continue

        current = lead.get(field_name)
        if field_name == "email":
            if not is_email_auto_promotable(candidate.contact_safety_class):
                if normalized and candidate.contact_safety_class:
                    needs_review = True
                continue
            if _values_conflict(current, normalized):
                needs_review = True
                continue
            if current:
                continue
            updates[field_name] = normalized
            promoted.append(field_name)
            continue

        if _values_conflict(current, normalized):
            needs_review = True
            continue
        if current:
            continue
        updates[field_name] = normalized
        promoted.append(field_name)

    return updates, needs_review, promoted


def _append_product_signals_summary(
    existing: str | None,
    signals: list[str],
) -> str | None:
    if not signals:
        return existing
    snippet = "Website signals: " + ", ".join(signals[:12])
    if existing and snippet in existing:
        return existing
    if existing:
        combined = f"{existing.strip()}; {snippet}"
    else:
        combined = snippet
    return combined[:500]


def _compute_enriched_confidence(lead: dict[str, Any], updates: dict[str, str]) -> int:
    merged = {**lead, **updates}
    return compute_import_confidence(
        source_type="venue_website",
        phone=merged.get("phone"),
        website=merged.get("website"),
        email=merged.get("email"),
        instagram_url=merged.get("instagram_url"),
        facebook_url=merged.get("facebook_url"),
        address_line=lead.get("address_line"),
        suburb=lead.get("suburb"),
        state=lead.get("state"),
        latitude=lead.get("latitude"),
        longitude=lead.get("longitude"),
    )


def enrich_founder_venue_lead_from_website(
    lead_id: str,
    *,
    requested_by_admin_account_id: str | None = None,
    dry_run: bool = False,
    page_fetcher: PageFetcher | None = None,
) -> WebsiteEnrichmentResult:
    lead = _load_lead_row(lead_id)
    lead_uuid = lead["id"]
    website = lead.get("website")
    if not website or not str(website).strip():
        return WebsiteEnrichmentResult(
            lead_id=lead_uuid,
            warnings=["No website available on lead; enrichment skipped."],
            errors=["no_website"],
            dry_run=dry_run,
        )

    if not website_url_is_fetchable(website):
        warning = (
            "Lead website is a social profile URL; fetch skipped (not a venue-owned site)."
            if is_social_profile_url(website)
            else "Lead website URL is not fetchable."
        )
        return WebsiteEnrichmentResult(
            lead_id=lead_uuid,
            warnings=[warning],
            errors=["website_not_fetchable"],
            dry_run=dry_run,
        )

    venue_host = website_host(website)
    pages, fetched_urls, fetch_errors = fetch_venue_website_pages(
        website,
        page_fetcher=page_fetcher,
    )

    if not pages:
        result = WebsiteEnrichmentResult(
            lead_id=lead_uuid,
            fetched_urls=fetched_urls,
            errors=fetch_errors or ["No pages could be fetched"],
            warnings=["Website fetch failed; lead not updated."],
            dry_run=dry_run,
        )
        if not dry_run:
            _write_failed_event(lead_uuid, result, requested_by_admin_account_id)
        return result

    candidates, product_signals = _extract_from_pages(pages, venue_host=venue_host)
    best = _best_candidates(candidates)
    field_updates, needs_review, promoted = _decide_promotions(lead, best)

    unsafe_only = any(
        c.field_name == "email"
        and c.contact_safety_class
        and not is_email_auto_promotable(c.contact_safety_class)
        for c in candidates
    )
    if unsafe_only and not field_updates.get("email"):
        needs_review = True

    source_summary = _append_product_signals_summary(
        lead.get("source_summary"), product_signals
    )
    if source_summary and source_summary != lead.get("source_summary"):
        field_updates["source_summary"] = source_summary
        if "source_summary" not in promoted:
            promoted.append("source_summary")

    enrichment_status = "needs_review" if needs_review else "enriched"
    warnings: list[str] = []
    if needs_review:
        warnings.append("Conflicting or unsafe contact data requires manual review.")
    if fetch_errors:
        warnings.append("Some secondary pages could not be fetched.")

    result = WebsiteEnrichmentResult(
        lead_id=lead_uuid,
        fetched_urls=fetched_urls,
        candidates=candidates,
        product_signals=product_signals,
        warnings=warnings,
        errors=fetch_errors,
        fields_promoted=promoted,
        enrichment_status=enrichment_status,
        dry_run=dry_run,
    )

    if dry_run:
        return result

    with transaction.atomic():
        source_id = _insert_enrichment_source(
            lead_uuid,
            fetched_urls=fetched_urls,
            product_signals=product_signals,
        )
        _insert_field_attributions(lead_uuid, source_id, candidates)
        confidence = _compute_enriched_confidence(lead, field_updates)
        _apply_lead_updates(
            lead_uuid,
            field_updates=field_updates,
            enrichment_status=enrichment_status,
            confidence_score=confidence,
        )
        _insert_completed_event(
            lead_uuid,
            result,
            requested_by_admin_account_id=requested_by_admin_account_id,
        )

    recompute_founder_fit_scores(lead_ids=[lead_uuid])
    return result


def _insert_enrichment_source(
    lead_id: str,
    *,
    fetched_urls: list[str],
    product_signals: list[str],
) -> str:
    payload = json.dumps(
        {
            "fetched_urls": fetched_urls,
            "product_signals": product_signals,
        }
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.founder_venue_lead_sources (
              lead_id, source_type, source_name, raw_payload, confidence
            ) VALUES (%s::uuid, 'venue_website', 'website_enrichment', %s::jsonb, 70)
            RETURNING id::text
            """,
            [lead_id, payload],
        )
        return cursor.fetchone()[0]


def _insert_field_attributions(
    lead_id: str,
    source_id: str,
    candidates: list[WebsiteEnrichmentCandidate],
) -> None:
    if not candidates:
        return
    rows = [
        (
            lead_id,
            source_id,
            c.field_name,
            c.confidence,
            c.raw_value,
            c.normalized_value,
            c.contact_safety_class,
            c.source_url,
        )
        for c in candidates
    ]
    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO public.founder_venue_lead_field_attributions (
              lead_id, source_id, field_name, source_type,
              confidence, raw_value, normalized_value,
              contact_safety_class, source_url
            ) VALUES (
              %s::uuid, %s::uuid, %s, 'venue_website',
              %s, %s, %s, %s, %s
            )
            """,
            rows,
        )


def _apply_lead_updates(
    lead_id: str,
    *,
    field_updates: dict[str, str],
    enrichment_status: str,
    confidence_score: int,
) -> None:
    set_parts = [
        "enrichment_status = %s",
        "confidence_score = %s",
        "updated_at = now()",
    ]
    params: list[Any] = [enrichment_status, confidence_score]

    column_map = {
        "email": "email",
        "phone": "phone",
        "instagram_url": "instagram_url",
        "facebook_url": "facebook_url",
        "website": "website",
        "source_summary": "source_summary",
    }
    for key, column in column_map.items():
        if key in field_updates:
            set_parts.append(f"{column} = %s")
            params.append(field_updates[key])

    params.append(lead_id)
    sql = f"""
        UPDATE public.founder_venue_leads
        SET {', '.join(set_parts)}
        WHERE id = %s::uuid
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, params)


def _insert_completed_event(
    lead_id: str,
    result: WebsiteEnrichmentResult,
    *,
    requested_by_admin_account_id: str | None,
) -> None:
    metadata = json.dumps(
        {
            "fetched_urls": result.fetched_urls,
            "fields_promoted": result.fields_promoted,
            "product_signals": result.product_signals,
            "candidate_count": len(result.candidates),
            "enrichment_status": result.enrichment_status,
            "warnings": result.warnings,
        }
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.founder_venue_lead_events (
              lead_id, event_type, metadata, created_by
            ) VALUES (%s::uuid, %s, %s::jsonb, %s::uuid)
            """,
            [
                lead_id,
                "website_enrichment_completed",
                metadata,
                requested_by_admin_account_id,
            ],
        )


def _write_failed_event(
    lead_id: str,
    result: WebsiteEnrichmentResult,
    requested_by_admin_account_id: str | None,
) -> None:
    metadata = json.dumps(
        {
            "errors": result.errors,
            "warnings": result.warnings,
            "fetched_urls": result.fetched_urls,
        }
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO public.founder_venue_lead_events (
              lead_id, event_type, metadata, created_by
            ) VALUES (%s::uuid, %s, %s::jsonb, %s::uuid)
            """,
            [
                lead_id,
                "website_enrichment_failed",
                metadata,
                requested_by_admin_account_id,
            ],
        )


def list_leads_for_website_enrichment(
    *,
    lead_ids: list[str] | None = None,
    state: str | None = None,
    suburb: str | None = None,
    missing_email: bool = False,
    missing_phone: bool = False,
    missing_socials: bool = False,
    score_min: int | None = None,
    limit: int = 10,
) -> list[str]:
    clauses = [
        "l.website IS NOT NULL",
        "btrim(l.website) <> ''",
        "l.website NOT ILIKE '%%facebook.com%%'",
        "l.website NOT ILIKE '%%instagram.com%%'",
        "l.suppressed_at IS NULL",
        "l.outreach_status <> 'do_not_contact'",
        "l.contact_permission_status NOT IN ('opted_out', 'do_not_contact')",
    ]
    params: list[Any] = []

    if lead_ids:
        placeholders = ", ".join(["%s::uuid"] * len(lead_ids))
        clauses.append(f"l.id IN ({placeholders})")
        params.extend(lead_ids)

    if state:
        clauses.append("l.state = %s")
        params.append(state.strip().upper())
    if suburb:
        clauses.append("lower(l.suburb) = lower(%s)")
        params.append(suburb.strip())
    if missing_email:
        clauses.append("(l.email IS NULL OR btrim(l.email) = '')")
    if missing_phone:
        clauses.append("(l.phone IS NULL OR btrim(l.phone) = '')")
    if missing_socials:
        clauses.append(
            "(l.instagram_url IS NULL OR btrim(l.instagram_url) = '')"
        )
        clauses.append(
            "(l.facebook_url IS NULL OR btrim(l.facebook_url) = '')"
        )
    if score_min is not None:
        clauses.append("l.founder_fit_score >= %s")
        params.append(score_min)

    sql = f"""
        SELECT l.id::text
        FROM public.founder_venue_leads l
        WHERE {' AND '.join(clauses)}
        ORDER BY l.founder_fit_score DESC, l.confidence_score DESC, l.updated_at DESC
        LIMIT %s
    """
    params.append(limit)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return [row[0] for row in cursor.fetchall()]
