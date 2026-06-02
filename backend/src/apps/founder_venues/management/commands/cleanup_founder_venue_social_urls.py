from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.founder_venues.services.social_cleanup import (
    cleanup_social_urls_in_founder_venue_leads,
)


class Command(BaseCommand):
    help = "Move Facebook/Instagram URLs out of founder venue lead website fields."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--lead-id",
            action="append",
            default=[],
            help="Lead UUID (repeatable). Comma-separated values in one flag are split.",
        )
        parser.add_argument("--state", type=str, default=None)
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--no-recompute",
            action="store_true",
            help="Skip founder-fit score recompute after cleanup.",
        )

    def handle(self, *args, **options) -> None:
        lead_ids = _expand_lead_ids(options["lead_id"])
        result = cleanup_social_urls_in_founder_venue_leads(
            lead_ids=lead_ids or None,
            state=options["state"],
            limit=options["limit"],
            dry_run=options["dry_run"],
            recompute_scores=not options["no_recompute"],
        )

        mode = "DRY RUN" if result.dry_run else "CLEANUP"
        self.stdout.write(self.style.MIGRATE_HEADING(f"Social URL cleanup ({mode})"))
        self.stdout.write(f"  Processed:                  {result.processed}")
        self.stdout.write(f"  Updated:                    {result.updated}")
        self.stdout.write(f"  Moved website -> facebook_url: {result.moved_to_facebook}")
        self.stdout.write(f"  Moved website -> instagram_url: {result.moved_to_instagram}")
        self.stdout.write(f"  Cleared social/invalid web:   {result.cleared_social_website}")
        self.stdout.write(f"  Skipped (social exists):      {result.skipped_target_exists}")
        if not result.dry_run:
            self.stdout.write(f"  Scores recomputed:            {result.scores_recomputed}")


def _expand_lead_ids(values: list[str]) -> list[str]:
    ids: list[str] = []
    for raw in values:
        for part in raw.split(","):
            part = part.strip()
            if part:
                ids.append(part)
    return ids
