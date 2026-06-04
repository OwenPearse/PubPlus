from __future__ import annotations

from django.db import DatabaseError
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.discovery.http import (
    apply_optional_save_enrichment_batch,
    error_response,
    map_discovery_error,
    parse_discovery_filters_from_request,
)
from apps.venues.public_read.card import public_venue_card_to_dict
from common.auth.guards import optional_consumer_auth
from common.auth.request_context import get_auth_context
from services.discovery import DiscoveryMode, run_discovery
from services.discovery.filter_reference import build_search_filter_reference


@require_GET
def search_filters(_request):
    try:
        payload = build_search_filter_reference()
    except DatabaseError:
        return error_response(
            code="db_error",
            message="Filter reference could not be loaded.",
            status=500,
        )
    return JsonResponse({"data": payload})


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
    cards = [hit.card for hit in result.hits]
    enriched = apply_optional_save_enrichment_batch(cards, auth=auth_context)
    venues = [public_venue_card_to_dict(card) for card in enriched]

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
