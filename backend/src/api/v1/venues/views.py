from __future__ import annotations

from django.http import JsonResponse

from apps.discovery.http import error_response
from apps.venues.services.venue_read_service import public_venue_detail_dict
from common.auth.guards import optional_consumer_auth
from common.auth.request_context import get_auth_context


@optional_consumer_auth
def venue_detail(request, venue_id: str):
    auth_context = get_auth_context(request)
    detail = public_venue_detail_dict(venue_id, auth=auth_context)
    if detail is None:
        return error_response(
            code="venue_not_found",
            message="Venue not found.",
            status=404,
        )
    return JsonResponse({"data": detail})
