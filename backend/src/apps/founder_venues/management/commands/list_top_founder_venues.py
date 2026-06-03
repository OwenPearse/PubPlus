from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.founder_venues.services.founder_fit_db import get_top_founder_venue_leads


class Command(BaseCommand):
    help = "List top-ranked founder venue leads by founder-fit score."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--state",
            type=str,
            default=None,
            help="Filter by state (e.g. VIC).",
        )
        parser.add_argument(
            "--suburb",
            type=str,
            default=None,
            help="Filter by suburb (case-insensitive).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum rows to return (default: 100).",
        )
        parser.add_argument(
            "--include-do-not-contact",
            action="store_true",
            help="Include suppressed outreach/permission exclusions.",
        )

    def handle(self, *args, **options) -> None:
        rows = get_top_founder_venue_leads(
            state=options["state"],
            suburb=options["suburb"],
            limit=options["limit"],
            include_do_not_contact=options["include_do_not_contact"],
        )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Top founder venues ({len(rows)} shown, limit {options['limit']})"
            )
        )
        for row in rows:
            phone = "yes" if row.get("phone") else "no"
            website = "yes" if row.get("website") else "no"
            email = "yes" if row.get("email") else "no"
            suburb = row.get("suburb") or "-"
            category = row.get("category") or "-"
            self.stdout.write(
                f"{row.get('founder_fit_score', 0):>3} | "
                f"{suburb:<14} | "
                f"{row.get('name', '-')} | "
                f"{category} | "
                f"phone {phone} | website {website} | email {email}"
            )
