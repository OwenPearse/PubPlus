from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.founder_venues.services.import_service import import_founder_venue_leads_csv


class Command(BaseCommand):
    help = "Import founder venue leads from a CSV file."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "csv_path",
            type=str,
            help="Path to the CSV file to import.",
        )
        parser.add_argument(
            "--source-type",
            type=str,
            default="csv_import",
            help="founder_venue_lead_sources.source_type (default: csv_import).",
        )
        parser.add_argument(
            "--source-name",
            type=str,
            default=None,
            help="Human-readable source label stored on source rows.",
        )
        parser.add_argument(
            "--source-url",
            type=str,
            default=None,
            help="Optional source URL for provenance.",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Fill empty fields on strong duplicates instead of skipping.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Compute import summary without writing to the database.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of CSV data rows to process.",
        )

    def handle(self, *args, **options) -> None:
        csv_path = Path(options["csv_path"])
        if not csv_path.is_file():
            raise CommandError(f"CSV file not found: {csv_path}")

        csv_text = csv_path.read_text(encoding="utf-8-sig")
        result = import_founder_venue_leads_csv(
            csv_text,
            source_type=options["source_type"],
            source_name=options["source_name"],
            source_url=options["source_url"],
            update_existing=options["update_existing"],
            dry_run=options["dry_run"],
            limit=options["limit"],
        )

        mode = "DRY RUN" if result.dry_run else "IMPORT"
        self.stdout.write(self.style.MIGRATE_HEADING(f"Founder venue lead import ({mode})"))
        self.stdout.write(f"  Rows processed:        {result.rows_processed}")
        self.stdout.write(f"  Leads created:       {result.leads_created}")
        self.stdout.write(f"  Leads updated:       {result.leads_updated}")
        self.stdout.write(f"  Duplicates skipped:  {result.duplicates_skipped}")
        self.stdout.write(f"  Needs review:        {len(result.duplicates_needing_review)}")
        self.stdout.write(f"  Invalid rows:        {len(result.invalid_rows)}")

        for review in result.duplicates_needing_review:
            self.stdout.write(
                f"    - row {review.row_number}: {review.reason} "
                f"(existing={review.existing_lead_id}, name={review.name!r})"
            )

        for invalid in result.invalid_rows:
            self.stdout.write(f"    - row {invalid.row_number}: {invalid.message}")

        for err in result.errors:
            self.stdout.write(self.style.ERROR(f"  Error: {err}"))

        if result.errors:
            raise CommandError("Import finished with errors.")
