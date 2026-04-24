from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.discovery.http import error_response
from apps.internal_tools.services.moderation_read_service import (
    ModerationItemNotFoundError,
    ModerationReadValidationError,
    VenueNotFoundError,
    get_internal_venue_detail,
    get_moderation_item_detail,
    list_moderation_queue,
    parse_queue_filters,
)
from common.auth.guards import require_internal_admin_auth
from common.auth.request_context import get_auth_context


@require_internal_admin_auth
def internal_auth_probe(request):
    auth_context = get_auth_context(request)
    return JsonResponse(
        {
            "status": "ok",
            "subject": auth_context.subject,
        }
    )


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def moderation_queue(request):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        filters = parse_queue_filters(
            {k: request.GET.get(k, "") for k in request.GET.keys()}
        )
        payload = list_moderation_queue(filters)
    except ModerationReadValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    return JsonResponse(payload)


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def moderation_item_detail(request, item_id: str):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        payload = get_moderation_item_detail(item_id)
    except ModerationReadValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except ModerationItemNotFoundError:
        return error_response(
            code="not_found",
            message="Moderation item not found.",
            status=404,
        )
    return JsonResponse(payload)


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def internal_venue_detail(request, venue_id: str):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        payload = get_internal_venue_detail(venue_id)
    except ModerationReadValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except VenueNotFoundError:
        return error_response(code="not_found", message="Venue not found.", status=404)
    return JsonResponse(payload)
