from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.discovery.http import error_response
from apps.submissions.services import submission_intake_service
from common.auth.guards import require_consumer_auth
from common.auth.request_context import get_auth_context


def _validation_error(
    message: str, details: dict[str, list[str]] | None = None
) -> JsonResponse:
    err: dict[str, Any] = {
        "code": "validation_error",
        "message": message,
    }
    if details:
        err["details"] = details
    return JsonResponse({"error": err}, status=400)


def _ack_response() -> JsonResponse:
    return JsonResponse(
        {
            "status": "received",
            "message": "Your submission has been received and will be reviewed.",
        },
        status=201,
    )


@require_http_methods(["POST", "HEAD"])
@require_consumer_auth
def submit_correction(request: HttpRequest) -> HttpResponse:
    if request.method == "HEAD":
        return HttpResponse(status=200)
    auth = get_auth_context(request)
    if auth is None:
        return error_response(
            code="unauthorized", message="Authentication required.", status=401
        )
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, (bytes, bytearray)) and request.body
            else {}
        )
    except json.JSONDecodeError:
        return _validation_error("Request body must be valid JSON.")
    if not isinstance(data, dict):
        return _validation_error("Request body must be a JSON object.")

    result, code, details = submission_intake_service.submit_consumer_correction(
        auth, data
    )
    if code == "ok" and result:
        return _ack_response()
    if code == "invalid_auth_subject":
        return _validation_error(
            "Authenticated subject could not be mapped to a consumer account."
        )
    if code == "venue_not_found":
        return error_response(
            code="not_found", message="Venue not found.", status=404
        )
    if code == "validation_error" and details:
        return _validation_error("One or more fields are invalid.", details=details)
    if code == "validation_error":
        return _validation_error("One or more fields are invalid.")
    return error_response(
        code="submission_intake_error",
        message="Could not record your submission.",
        status=500,
    )


@require_http_methods(["POST", "HEAD"])
@require_consumer_auth
def submit_new_venue(request: HttpRequest) -> HttpResponse:
    if request.method == "HEAD":
        return HttpResponse(status=200)
    auth = get_auth_context(request)
    if auth is None:
        return error_response(
            code="unauthorized", message="Authentication required.", status=401
        )
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, (bytes, bytearray)) and request.body
            else {}
        )
    except json.JSONDecodeError:
        return _validation_error("Request body must be valid JSON.")
    if not isinstance(data, dict):
        return _validation_error("Request body must be a JSON object.")

    result, code, details = (
        submission_intake_service.submit_new_venue_suggestion(auth, data)
    )
    if code == "ok" and result:
        return _ack_response()
    if code == "invalid_auth_subject":
        return _validation_error(
            "Authenticated subject could not be mapped to a consumer account."
        )
    if code == "validation_error" and details:
        return _validation_error("One or more fields are invalid.", details=details)
    if code == "validation_error":
        return _validation_error("One or more fields are invalid.")
    return error_response(
        code="submission_intake_error",
        message="Could not record your submission.",
        status=500,
    )
