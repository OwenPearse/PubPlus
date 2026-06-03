from __future__ import annotations

from dataclasses import asdict

from django.core.management.base import BaseCommand

from apps.founder_venues.services.export_service import export_founder_venue_leads_csv


class Command(BaseCommand):
    help = "Export founder venue leads to CSV for outreach or CRM import."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--state", type=str, default=None)
        parser.add_argument("--suburb", type=str, default=None)
        parser.add_argument("--postcode", type=str, default=None)
        parser.add_argument("--search", type=str, default=None)
        parser.add_argument("--enrichment-status", type=str, default=None)
        parser.add_argument("--outreach-status", type=str, default=None)
        parser.add_argument(
            "--contact-permission-status",
            type=str,
            default=None,
        )
        parser.add_argument("--score-min", type=int, default=None)
        parser.add_argument("--confidence-min", type=int, default=None)
        parser.add_argument("--missing-email", action="store_true")
        parser.add_argument("--missing-phone", action="store_true")
        parser.add_argument("--missing-website", action="store_true")
        parser.add_argument("--needs-review", action="store_true")
        parser.add_argument("--include-do-not-contact", action="store_true")
        parser.add_argument("--include-suppressed", action="store_true")
        parser.add_argument("--include-unsafe-emails", action="store_true")
        parser.add_argument("--include-raw-notes", action="store_true")
        parser.add_argument("--limit", type=int, default=1000)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Write CSV to this path; stdout if omitted.",
        )

    def handle(self, *args, **options) -> None:
        result = export_founder_venue_leads_csv(
            state=options["state"],
            suburb=options["suburb"],
            postcode=options["postcode"],
            search=options["search"],
            enrichment_status=options["enrichment_status"],
            outreach_status=options["outreach_status"],
            contact_permission_status=options["contact_permission_status"],
            score_min=options["score_min"],
            confidence_min=options["confidence_min"],
            missing_email=options["missing_email"] or None,
            missing_phone=options["missing_phone"] or None,
            missing_website=options["missing_website"] or None,
            needs_review=options["needs_review"] or None,
            include_do_not_contact=options["include_do_not_contact"],
            include_suppressed=options["include_suppressed"],
            include_unsafe_emails=options["include_unsafe_emails"],
            include_raw_notes=options["include_raw_notes"],
            limit=options["limit"],
            offset=options["offset"],
        )

        output_path = options["output"]
        if output_path:
            with open(output_path, "w", encoding="utf-8", newline="") as handle:
                handle.write(result.csv_text)
            self.stdout.write(self.style.SUCCESS(f"Wrote {output_path}"))
        else:
            self.stdout.write(result.csv_text)

        excluded = asdict(result.excluded_counts)
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Rows exported: {result.row_count} (generated {result.generated_at})"
            )
        )
        self.stdout.write(f"Filters: {result.filters_applied}")
        self.stdout.write(f"Exclusions/redactions: {excluded}")
