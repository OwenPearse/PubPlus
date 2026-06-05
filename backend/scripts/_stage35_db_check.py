import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

django.setup()
from django.db import connection

venue_id = "f1111111-1111-4111-8111-111111111101"

with connection.cursor() as c:
    c.execute(
        """
        SELECT id::text, lifecycle_status::text, channel::text, submitted_at IS NOT NULL
        FROM public.venue_change_proposal
        WHERE venue_id = %s::uuid AND channel = 'owner_portal'
          AND lifecycle_status IN ('staged', 'in_review')
        ORDER BY created_at DESC
        """,
        [venue_id],
    )
    open_rows = c.fetchall()
    print("open_owner_proposals", open_rows)
    if open_rows:
        proposal_id = open_rows[0][0]
        c.execute(
            """
            SELECT target_family::text FROM public.venue_proposal_target
            WHERE venue_change_proposal_id = %s::uuid ORDER BY target_family
            """,
            [proposal_id],
        )
        print("targets", [r[0] for r in c.fetchall()])
        for table in (
            "venue_proposal_staging_profile",
            "venue_proposal_staging_location",
            "venue_proposal_staging_hours",
        ):
            c.execute(
                f"SELECT count(*)::int FROM public.{table} WHERE venue_change_proposal_id = %s::uuid",
                [proposal_id],
            )
            print(table, c.fetchone()[0])
    c.execute(
        "SELECT display_name FROM public.venue_published_profile WHERE venue_id = %s::uuid",
        [venue_id],
    )
    print("published_name", c.fetchone()[0])
    c.execute(
        """
        SELECT p.id::text, p.channel::text, p.lifecycle_status::text,
               COALESCE(vpp.display_name, vpsp.proposed_display_name)
        FROM public.venue_change_proposal p
        LEFT JOIN public.venue_published_profile vpp ON vpp.venue_id = p.venue_id
        LEFT JOIN public.venue_proposal_staging_profile vpsp
          ON vpsp.venue_change_proposal_id = p.id
        WHERE p.lifecycle_status IN ('staged', 'in_review')
          AND p.channel = 'owner_portal'
          AND p.venue_id = %s::uuid
        ORDER BY COALESCE(p.submitted_at, p.created_at) DESC
        """,
        [venue_id],
    )
    print("moderation_queue_rows", c.fetchall())
