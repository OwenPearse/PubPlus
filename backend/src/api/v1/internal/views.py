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
from apps.internal_tools.services.moderation_write_service import (
    InternalOperatorResolutionError,
    ModerationDecisionConflictError,
    ModerationWriteNotFoundError,
    ModerationWriteValidationError,
    add_moderation_note,
    decide_moderation_item,
    resolve_admin_account_for_internal_operator,
)
from common.auth.guards import require_internal_admin_auth
from common.auth.request_context import get_auth_context
import json


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


def _parse_json_object_body(request):
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, (bytes, bytearray)) and request.body
            else {}
        )
    except json.JSONDecodeError:
        raise ModerationWriteValidationError("Request body must be valid JSON.")
    if not isinstance(data, dict):
        raise ModerationWriteValidationError("Request body must be a JSON object.")
    return data


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def moderation_item_decision(request, item_id: str):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    auth = get_auth_context(request)
    if auth is None:
        return error_response(
            code="unauthorized",
            message="Authentication required.",
            status=401,
        )
    try:
        payload = _parse_json_object_body(request)
        operator = resolve_admin_account_for_internal_operator(auth)
        response_payload = decide_moderation_item(
            item_id=item_id,
            decision=payload.get("decision"),
            reason=payload.get("reason"),
            operator=operator,
        )
    except ModerationWriteValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except ModerationWriteNotFoundError:
        return error_response(
            code="not_found",
            message="Moderation item not found.",
            status=404,
        )
    except ModerationDecisionConflictError as exc:
        return error_response(code="conflict", message=str(exc), status=409)
    except InternalOperatorResolutionError as exc:
        return error_response(code="operator_resolution_failed", message=str(exc), status=409)
    return JsonResponse(response_payload, status=200)


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def moderation_item_notes(request, item_id: str):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    auth = get_auth_context(request)
    if auth is None:
        return error_response(
            code="unauthorized",
            message="Authentication required.",
            status=401,
        )
    try:
        payload = _parse_json_object_body(request)
        operator = resolve_admin_account_for_internal_operator(auth)
        response_payload = add_moderation_note(
            item_id=item_id,
            body=payload.get("body"),
            operator=operator,
        )
    except ModerationWriteValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except ModerationWriteNotFoundError:
        return error_response(
            code="not_found",
            message="Moderation item not found.",
            status=404,
        )
    except InternalOperatorResolutionError as exc:
        return error_response(code="operator_resolution_failed", message=str(exc), status=409)
    return JsonResponse(response_payload, status=201)
