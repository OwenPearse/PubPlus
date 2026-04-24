from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse

from apps.discovery.http import error_response
from apps.saved.services.saved_venues_service import (
    add_venue_to_default_list,
    list_default_saved_venue_payloads,
    parse_venue_id_from_request_body,
    parse_venue_id_path,
    remove_venue_from_default_list,
)
from common.auth.guards import require_consumer_auth
from common.auth.request_context import get_auth_context


def _validation_error(*, code: str, message: str, field_errors: dict | None = None) -> JsonResponse:
    err: dict = {"code": code, "message": message}
    if field_errors:
        err["details"] = field_errors
    return JsonResponse({"error": err}, status=400)


@require_consumer_auth
def saved_venues(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return _get_saved_venues(request)
    if request.method == "POST":
        return _post_saved_venue(request)
    return error_response(
        code="method_not_allowed",
        message="Method not allowed.",
        status=405,
    )


def _get_saved_venues(request: HttpRequest) -> HttpResponse:
    auth = get_auth_context(request)
    venues, err = list_default_saved_venue_payloads(auth=auth)
    if err == "invalid_auth_subject":
        return _validation_error(
            code="validation_error",
            message="Authenticated subject could not be mapped to a consumer account.",
        )
    if err is not None:
        return error_response(
            code="saved_venues_unavailable",
            message="Could not load saved venues.",
            status=500,
        )
    return JsonResponse({"data": {"venues": venues}})


def _post_saved_venue(request: HttpRequest) -> HttpResponse:
    auth = get_auth_context(request)
    venue_id, perr = parse_venue_id_from_request_body(request.body)
    if perr == "malformed_json":
        return _validation_error(
            code="validation_error",
            message="Request body must be valid JSON.",
        )
    if perr == "invalid_body":
        return _validation_error(
            code="validation_error",
            message="Request body must be a JSON object.",
        )
    if perr == "missing_venue_id":
        return _validation_error(
            code="validation_error",
            message="Field venue_id is required.",
            field_errors={"venue_id": ["This field is required."]},
        )
    if perr == "invalid_venue_id" or venue_id is None:
        return _validation_error(
            code="validation_error",
            message="Field venue_id must be a valid UUID.",
            field_errors={"venue_id": ["Must be a valid UUID."]},
        )

    try:
        result = add_venue_to_default_list(auth=auth, venue_id=venue_id)
    except ValueError:
        return _validation_error(
            code="validation_error",
            message="Authenticated subject could not be mapped to a consumer account.",
        )
    except Exception:  # noqa: BLE001
        return error_response(
            code="save_failed",
            message="Could not save venue.",
            status=500,
        )

    if result is None:
        return error_response(
            code="venue_not_found",
            message="Venue not found.",
            status=404,
        )
    return JsonResponse(
        {
            "data": {
                "venue_id": result.venue_id,
                "saved": result.saved,
            }
        }
    )


@require_consumer_auth
def remove_saved_venue(request: HttpRequest, venue_id: str) -> HttpResponse:
    if request.method != "DELETE":
        return error_response(
            code="method_not_allowed",
            message="Method not allowed.",
            status=405,
        )
    auth = get_auth_context(request)
    vid, perr = parse_venue_id_path(venue_id)
    if perr or vid is None:
        return _validation_error(
            code="validation_error",
            message="venue_id must be a valid UUID.",
            field_errors={"venue_id": ["Must be a valid UUID."]},
        )
    try:
        remove_venue_from_default_list(auth=auth, venue_id=vid)
    except Exception:  # noqa: BLE001
        return error_response(
            code="unsave_failed",
            message="Could not update saved state.",
            status=500,
        )
    return HttpResponse(status=204)
