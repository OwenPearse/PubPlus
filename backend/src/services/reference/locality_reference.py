"""
Public locality reference for Profile default locality and future location UX.

Scoped to localities that have at least one discovery-eligible published venue
(same published-venue spine as Search), so IDs are always valid for discovery.
"""

from __future__ import annotations

from typing import Any

from django.db import connection


def build_locality_reference() -> dict[str, Any]:
    """
    Return ``{"localities": [...]}`` ready to wrap in API ``data``.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              l.id::text,
              l.name,
              l.geographic_region_id::text,
              gr.name AS geographic_region_name,
              COALESCE(
                CASE WHEN gr.region_level = 'state' THEN gr.region_code END,
                pgr.region_code
              ) AS state_code,
              MAX(vpl.country_code) AS country_code,
              AVG(vpm.latitude)::float8 AS latitude,
              AVG(vpm.longitude)::float8 AS longitude
            FROM public.locality l
            INNER JOIN public.geographic_region gr
              ON gr.id = l.geographic_region_id
            LEFT JOIN public.geographic_region pgr
              ON pgr.id = gr.parent_region_id
            INNER JOIN public.venue_published_location vpl
              ON vpl.locality_id = l.id
            INNER JOIN public.venue v
              ON v.id = vpl.venue_id
            INNER JOIN public.venue_published_profile vpp
              ON vpp.venue_id = v.id
             AND vpp.discovery_eligibility_status IN ('eligible', 'limited')
            INNER JOIN public.venue_published_map_point vpm
              ON vpm.venue_id = v.id
            GROUP BY
              l.id,
              l.name,
              l.geographic_region_id,
              gr.name,
              gr.region_level,
              gr.region_code,
              pgr.region_code
            ORDER BY state_code NULLS LAST, l.name ASC
            """
        )
        rows = cursor.fetchall()

    localities: list[dict[str, Any]] = []
    for (
        locality_id,
        name,
        geographic_region_id,
        geographic_region_name,
        state_code,
        country_code,
        latitude,
        longitude,
    ) in rows:
        item: dict[str, Any] = {
            "id": locality_id,
            "name": name,
            "geographic_region_id": geographic_region_id,
            "geographic_region_name": geographic_region_name,
        }
        if state_code:
            item["state"] = state_code
        if country_code:
            item["country_code"] = str(country_code).strip()
        if latitude is not None and longitude is not None:
            item["latitude"] = float(latitude)
            item["longitude"] = float(longitude)
        localities.append(item)

    return {"localities": localities}
