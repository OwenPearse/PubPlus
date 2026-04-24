from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.discovery.http import error_response
from apps.profile.services import profile_service
from common.auth.guards import require_consumer_auth
from common.auth.request_context import get_auth_context


def _validation_error(
    *, message: str, details: dict[str, list[str]] | None = None
) -> JsonResponse:
    err: dict = {
        "code": "validation_error",
        "message": message,
    }
    if details:
        err["details"] = details
    return JsonResponse({"error": err}, status=400)


def _map_validation_details(
    details: dict[str, list[str]] | None,
) -> dict[str, list[str]] | None:
    if not details:
        return None
    out: dict[str, list[str]] = {}
    for k, v in details.items():
        if k == "_body":
            out["body"] = v
        elif k == "_unknown":
            out["unknown"] = v
        elif k == "_general":
            out["fields"] = v
        elif k == "quiet_hours":
            out["quiet_hours"] = v
        else:
            out[k] = v
    return out or None


@require_http_methods(["GET", "HEAD", "PATCH"])
@require_consumer_auth
def consumer_profile(request: HttpRequest) -> HttpResponse:
    if request.method == "HEAD":
        return HttpResponse(status=200)
    if request.method == "GET":
        return _get_profile(request)
    if request.method == "PATCH":
        return _patch_profile(request)
    return error_response(
        code="method_not_allowed", message="Method not allowed.", status=405
    )


def _get_profile(request: HttpRequest) -> HttpResponse:
    auth = get_auth_context(request)
    data, err = profile_service.get_profile_state(auth=auth)
    if err == "invalid_auth_subject":
        return _validation_error(
            message="Authenticated subject could not be mapped to a consumer account.",
        )
    if err is not None:
        return error_response(
            code="profile_unavailable",
            message="Could not load profile.",
            status=500,
        )
    return JsonResponse({"data": data})


def _patch_profile(request: HttpRequest) -> HttpResponse:
    auth = get_auth_context(request)
    data, err, details = profile_service.apply_profile_patch(auth=auth, body=request.body)
    if err == "invalid_auth_subject":
        return _validation_error(
            message="Authenticated subject could not be mapped to a consumer account.",
        )
    if err == "malformed_json":
        return _validation_error(message="Request body must be valid JSON.")
    if err == "validation_error":
        if details and "_unknown" in details:
            return _validation_error(
                message=details["_unknown"][0],
                details=_map_validation_details(details),
            )
        if details and "_body" in details:
            return _validation_error(
                message=details["_body"][0],
                details=_map_validation_details(details),
            )
        if details and "_general" in details:
            return _validation_error(
                message=details["_general"][0],
                details=_map_validation_details(details),
            )
        return _validation_error(
            message="One or more fields are invalid.",
            details=_map_validation_details(details),
        )
    if err is not None:
        return error_response(
            code="profile_update_failed",
            message="Could not update profile.",
            status=500,
        )
    return JsonResponse({"data": data})
