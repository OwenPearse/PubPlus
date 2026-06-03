from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.founder_venues.services.enrichment_service import (
    enrich_founder_venue_lead_from_website,
    list_leads_for_website_enrichment,
)

DEFAULT_LIMIT = 10
MAX_LIMIT = 100


class Command(BaseCommand):
    help = "Enrich founder venue leads from their own websites (conservative fetch)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--lead-id",
            action="append",
            default=[],
            help="Lead UUID (repeatable). Comma-separated values in one flag are split.",
        )
        parser.add_argument("--state", type=str, default=None)
        parser.add_argument("--suburb", type=str, default=None)
        parser.add_argument("--missing-email", action="store_true")
        parser.add_argument("--missing-phone", action="store_true")
        parser.add_argument("--missing-socials", action="store_true")
        parser.add_argument("--score-min", type=int, default=None)
        parser.add_argument(
            "--limit",
            type=int,
            default=DEFAULT_LIMIT,
            help=f"Max leads to process (default {DEFAULT_LIMIT}, max {MAX_LIMIT}).",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options) -> None:
        limit = min(max(options["limit"], 1), MAX_LIMIT)
        lead_ids = _expand_lead_ids(options["lead_id"])

        if lead_ids:
            targets = lead_ids[:limit]
        else:
            targets = list_leads_for_website_enrichment(
                state=options["state"],
                suburb=options["suburb"],
                missing_email=options["missing_email"],
                missing_phone=options["missing_phone"],
                missing_socials=options["missing_socials"],
                score_min=options["score_min"],
                limit=limit,
            )

        stats = {
            "processed": 0,
            "enriched": 0,
            "failed": 0,
            "needs_review": 0,
            "fields_promoted": 0,
            "candidates_found": 0,
            "warnings": [],
        }

        for lead_id in targets:
            stats["processed"] += 1
            result = enrich_founder_venue_lead_from_website(
                lead_id,
                dry_run=options["dry_run"],
            )
            stats["candidates_found"] += len(result.candidates)
            stats["fields_promoted"] += len(result.fields_promoted)
            stats["warnings"].extend(result.warnings)

            if result.errors and not result.fetched_urls:
                stats["failed"] += 1
            elif result.enrichment_status == "enriched":
                stats["enriched"] += 1
            elif result.enrichment_status == "needs_review":
                stats["needs_review"] += 1
            elif result.warnings and "No website" in result.warnings[0]:
                stats["failed"] += 1

            self.stdout.write(
                f"{lead_id}: status={result.enrichment_status or 'skipped'} "
                f"promoted={result.fields_promoted} "
                f"candidates={len(result.candidates)} "
                f"fetched={len(result.fetched_urls)}"
            )

        self.stdout.write(self.style.MIGRATE_HEADING("Website enrichment summary"))
        for key, value in stats.items():
            if key == "warnings":
                unique = sorted(set(value))
                self.stdout.write(f"warnings ({len(unique)} unique): {unique[:10]}")
            else:
                self.stdout.write(f"{key}: {value}")


def _expand_lead_ids(values: list[str]) -> list[str]:
    ids: list[str] = []
    for raw in values:
        for part in raw.split(","):
            part = part.strip()
            if part:
                ids.append(part)
    return ids
