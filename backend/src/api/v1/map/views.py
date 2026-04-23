from __future__ import annotations

from django.http import JsonResponse

from apps.discovery.http import (
    apply_optional_save_enrichment,
    map_discovery_error,
    parse_discovery_filters_from_request,
)
from common.auth.guards import optional_consumer_auth
from common.auth.request_context import get_auth_context
from services.discovery import DiscoveryMode, run_discovery


def _map_marker_payload(card) -> dict:
    return {
        "id": card.id,
        "name": card.name,
        "latitude": card.latitude,
        "longitude": card.longitude,
        "suburb": card.suburb,
        "hero_photo_url": card.hero_photo_url,
        "open_now": card.open_now,
        "open_now_uncomputed": card.open_now_uncomputed,
        "is_saved": card.is_saved,
    }


@optional_consumer_auth
def map_venues(request):
    try:
        filters = parse_discovery_filters_from_request(
            request, mode=DiscoveryMode.MAP
        )
        result = run_discovery(DiscoveryMode.MAP, filters)
    except Exception as exc:  # noqa: BLE001
        return map_discovery_error(exc)

    auth_context = get_auth_context(request)
    markers = []
    for hit in result.hits:
        enriched = apply_optional_save_enrichment(hit.card, auth=auth_context)
        markers.append(_map_marker_payload(enriched))

    return JsonResponse(
        {
            "data": {
                "venues": markers,
            },
            "meta": {
                "mode": result.mode,
                "count": len(markers),
                "limit": result.filters.limit,
            },
        }
    )
