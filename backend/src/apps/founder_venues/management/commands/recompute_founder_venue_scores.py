from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.founder_venues.services.founder_fit_db import recompute_founder_fit_scores


class Command(BaseCommand):
    help = "Recompute founder-fit scores for venue leads."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--state",
            type=str,
            default=None,
            help="Only recompute leads in this state (e.g. VIC).",
        )
        parser.add_argument(
            "--lead-id",
            action="append",
            default=[],
            help="Specific lead UUID (repeatable). Comma-separated also accepted.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of leads to process.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Compute scores without writing to the database.",
        )
        parser.add_argument(
            "--show-top",
            action="store_true",
            help="Print top scored leads after run.",
        )
        parser.add_argument(
            "--top-limit",
            type=int,
            default=10,
            help="Number of top leads to show with --show-top (default: 10).",
        )

    def handle(self, *args, **options) -> None:
        lead_ids: list[str] = []
        for value in options["lead_id"]:
            lead_ids.extend(part.strip() for part in value.split(",") if part.strip())

        result = recompute_founder_fit_scores(
            lead_ids=lead_ids or None,
            state=options["state"],
            limit=options["limit"],
            dry_run=options["dry_run"],
        )

        mode = "DRY RUN" if result.dry_run else "RECOMPUTE"
        self.stdout.write(self.style.MIGRATE_HEADING(f"Founder-fit scoring ({mode})"))
        self.stdout.write(f"  Processed: {result.processed}")
        self.stdout.write(f"  Updated:   {result.updated}")
        self.stdout.write(f"  Skipped:   {result.skipped}")

        for err in result.errors:
            self.stdout.write(self.style.ERROR(f"  Error: {err}"))

        if options["show_top"]:
            self.stdout.write("")
            self.stdout.write("Top scores (this run):")
            for item in result.top_scores_preview[: options["top_limit"]]:
                prev = item.get("previous_score")
                prev_label = f" (was {prev})" if prev is not None else ""
                self.stdout.write(
                    f"  {item.get('founder_fit_score'):>3} | "
                    f"{item.get('suburb') or '-':<12} | "
                    f"{item.get('name')}{prev_label}"
                )

        if result.errors:
            raise CommandError("Recompute finished with errors.")
