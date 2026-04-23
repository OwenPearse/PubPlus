from __future__ import annotations

from django.http import JsonResponse

from apps.discovery.http import (
    apply_optional_save_enrichment,
    map_discovery_error,
    parse_discovery_filters_from_request,
)
from apps.venues.public_read.card import public_venue_card_to_dict
from common.auth.guards import optional_consumer_auth
from common.auth.request_context import get_auth_context
from services.discovery import DiscoveryMode, run_discovery


@optional_consumer_auth
def search_venues(request):
    try:
        filters = parse_discovery_filters_from_request(
            request, mode=DiscoveryMode.LIST
        )
        result = run_discovery(DiscoveryMode.LIST, filters)
    except Exception as exc:  # noqa: BLE001
        return map_discovery_error(exc)

    auth_context = get_auth_context(request)
    venues = []
    for hit in result.hits:
        enriched = apply_optional_save_enrichment(hit.card, auth=auth_context)
        venues.append(public_venue_card_to_dict(enriched))

    return JsonResponse(
        {
            "data": {
                "venues": venues,
            },
            "meta": {
                "mode": result.mode,
                "count": len(venues),
                "limit": result.filters.limit,
            },
        }
    )
