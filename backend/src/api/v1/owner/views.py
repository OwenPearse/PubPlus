from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.discovery.http import error_response
from apps.owner.services.owner_access_service import (
    OwnerProvisioningDisallowedError,
    build_provision_payload,
    provision_owner_account,
    resolve_owner_auth_probe,
)
from apps.owner.services.owner_claim_service import (
    get_current_owner_claim_status,
    search_venue_claim_candidates,
    submit_venue_claim_request,
)
from apps.owner.services.owner_venue_service import (
    create_or_update_owner_core_details_proposal,
    create_owner_restricted_change_request,
    create_owner_venue_meal_special,
    create_owner_venue_tap_list_item,
    deactivate_owner_venue_meal_special,
    deactivate_owner_venue_tap_list_item,
    get_owner_venue_detail,
    get_owner_venue_features,
    get_owner_venue_meal_specials,
    get_owner_venue_tap_list,
    list_owner_venues,
    patch_owner_operational_profile,
    patch_owner_venue_features,
    patch_owner_venue_hours,
    patch_owner_venue_meal_special,
    patch_owner_venue_tap_list_item,
)
from common.auth.guards import require_consumer_auth_api, require_owner_portal_auth
from common.auth.request_context import get_auth_context
from common.owner_account import admin_account_exists_for_auth


def _validation_error(
    message: str = "Please check the highlighted fields.",
    details: dict[str, list[str]] | None = None,
) -> JsonResponse:
    err: dict[str, Any] = {
        "code": "validation_error",
        "message": message,
    }
    if details:
        err["details"] = details
    return JsonResponse({"error": err}, status=400)


def _map_venue_scope_error(code: str) -> JsonResponse:
    if code == "not_found":
        return error_response(
            code="not_found",
            message="Venue not found.",
            status=404,
        )
    if code == "admin_forbidden":
        return error_response(
            code="forbidden",
            message="Admin identities must use internal tools, not owner venue APIs.",
            status=403,
        )
    if code == "missing_capability":
        return error_response(
            code="forbidden",
            message=(
                "Direct listing edits are not enabled for your account. "
                "Contact support if you manage this venue."
            ),
            status=403,
        )
    if code == "missing_restricted_capability":
        return error_response(
            code="forbidden",
            message=(
                "Change requests are not enabled for your account. "
                "Contact support if you manage this venue."
            ),
            status=403,
        )
    return error_response(
        code="forbidden",
        message="You do not have permission to manage this venue.",
        status=403,
    )


@require_http_methods(["POST"])
@require_consumer_auth_api
def owner_provision(request: HttpRequest) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None
    try:
        owner_id, created = provision_owner_account(auth)
    except OwnerProvisioningDisallowedError as exc:
        return error_response(
            code="owner_provisioning_disallowed",
            message=str(exc),
            status=403,
        )
    payload = build_provision_payload(
        owner_account_id=owner_id,
        created=created,
        claims=auth.claims or {},
    )
    return JsonResponse(payload, status=201 if created else 200)


@require_http_methods(["GET", "HEAD"])
@require_consumer_auth_api
def owner_auth_probe(request: HttpRequest) -> JsonResponse:
    if request.method == "HEAD":
        return JsonResponse({}, status=200)

    auth = get_auth_context(request)
    assert auth is not None
    body, status = resolve_owner_auth_probe(auth)
    if status == 403:
        return JsonResponse(
            {
                **body,
                "error": {
                    "code": "owner_not_provisioned",
                    "message": "Owner account is not provisioned for this identity.",
                },
            },
            status=403,
        )
    return JsonResponse(body, status=status)


@require_http_methods(["GET", "HEAD"])
@require_owner_portal_auth
def owner_venue_claim_candidates(request: HttpRequest) -> JsonResponse:
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    auth = get_auth_context(request)
    assert auth is not None
    if admin_account_exists_for_auth(auth):
        return _map_venue_scope_error("admin_forbidden")

    result, code, details = search_venue_claim_candidates(
        auth,
        name=request.GET.get("name"),
        locality_id=request.GET.get("locality_id"),
        q=request.GET.get("q"),
        address_line_1=request.GET.get("address_line_1"),
    )
    if code == "ok" and result is not None:
        return JsonResponse({"data": result}, status=200)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code == "admin_forbidden":
        return _map_venue_scope_error("admin_forbidden")
    if code == "forbidden":
        return error_response(
            code="forbidden",
            message="Owner account is not provisioned for this identity.",
            status=403,
        )
    return error_response(
        code="owner_claim_search_error",
        message="Could not search venue candidates.",
        status=500,
    )


@require_http_methods(["GET", "HEAD", "POST"])
@require_owner_portal_auth
def owner_venue_claim_requests(request: HttpRequest) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None
    if admin_account_exists_for_auth(auth):
        return _map_venue_scope_error("admin_forbidden")

    if request.method in ("GET", "HEAD"):
        if request.method == "HEAD":
            return JsonResponse({}, status=200)
        result, code, details = get_current_owner_claim_status(auth)
        if code == "ok":
            return JsonResponse({"data": result}, status=200)
        if code == "admin_forbidden":
            return _map_venue_scope_error("admin_forbidden")
        if code == "forbidden":
            return error_response(
                code="forbidden",
                message="Owner account is not provisioned for this identity.",
                status=403,
            )
        return error_response(
            code="owner_claim_status_error",
            message="Could not load your claim request status.",
            status=500,
        )

    body, err_resp = _parse_json_object_body(request)
    if err_resp is not None:
        return err_resp
    assert body is not None

    result, code, details = submit_venue_claim_request(auth, body)
    if code in ("ok", "duplicate_open") and result:
        status = 200 if code == "duplicate_open" else 201
        return JsonResponse({"data": result}, status=status)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code == "not_found":
        return error_response(
            code="not_found",
            message="Venue not found.",
            status=404,
        )
    if code == "admin_forbidden":
        return _map_venue_scope_error("admin_forbidden")
    if code == "forbidden":
        return error_response(
            code="forbidden",
            message="Owner account is not provisioned for this identity.",
            status=403,
        )
    return error_response(
        code="owner_claim_request_error",
        message="Could not submit your claim request.",
        status=500,
    )


@require_http_methods(["GET", "HEAD"])
@require_owner_portal_auth
def owner_venues_list(request: HttpRequest) -> JsonResponse:
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    auth = get_auth_context(request)
    assert auth is not None
    if admin_account_exists_for_auth(auth):
        return _map_venue_scope_error("admin_forbidden")
    payload = list_owner_venues(auth)
    return JsonResponse({"data": payload}, status=200)


@require_http_methods(["GET", "HEAD"])
@require_owner_portal_auth
def owner_venue_detail(request: HttpRequest, venue_id) -> JsonResponse:
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    auth = get_auth_context(request)
    assert auth is not None
    detail, code = get_owner_venue_detail(auth, str(venue_id))
    if detail is None:
        return _map_venue_scope_error(code)
    return JsonResponse({"data": detail}, status=200)


@require_http_methods(["POST"])
@require_owner_portal_auth
def owner_venue_proposals(request: HttpRequest, venue_id) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None
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

    section = data.get("section")
    intent = data.get("intent")
    payload = data.get("payload")
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return _validation_error(
            details={"payload": ["payload must be a JSON object."]}
        )

    result, code, details = create_or_update_owner_core_details_proposal(
        auth,
        str(venue_id),
        section=str(section) if section is not None else "",
        intent=str(intent) if intent is not None else "",
        payload=payload,
    )
    if code == "ok" and result:
        return JsonResponse({"data": result}, status=201)
    if code == "already_in_review" and result:
        return JsonResponse({"data": result}, status=200)
    if code == "proposal_already_in_review":
        return error_response(
            code="proposal_already_in_review",
            message="Your latest changes are already submitted for review.",
            status=409,
        )
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code in ("forbidden", "not_found", "admin_forbidden"):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_proposal_error",
        message="Could not save your proposal.",
        status=500,
    )


def _parse_json_object_body(request: HttpRequest) -> tuple[dict[str, Any] | None, JsonResponse | None]:
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, (bytes, bytearray)) and request.body
            else {}
        )
    except json.JSONDecodeError:
        return None, _validation_error("Request body must be valid JSON.")
    if not isinstance(data, dict):
        return None, _validation_error("Request body must be a JSON object.")
    return data, None


@require_http_methods(["PATCH"])
@require_owner_portal_auth
def owner_venue_operational_profile_patch(
    request: HttpRequest, venue_id
) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None
    body, err_resp = _parse_json_object_body(request)
    if err_resp is not None:
        return err_resp
    assert body is not None

    result, code, details = patch_owner_operational_profile(
        auth, str(venue_id), body
    )
    if code == "ok" and result:
        return JsonResponse({"data": result}, status=200)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code in ("forbidden", "not_found", "admin_forbidden", "missing_capability"):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_direct_edit_error",
        message="Could not save your changes.",
        status=500,
    )


@require_http_methods(["PATCH"])
@require_owner_portal_auth
def owner_venue_hours_patch(request: HttpRequest, venue_id) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None
    body, err_resp = _parse_json_object_body(request)
    if err_resp is not None:
        return err_resp
    assert body is not None

    result, code, details = patch_owner_venue_hours(auth, str(venue_id), body)
    if code == "ok" and result:
        return JsonResponse({"data": result}, status=200)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code in ("forbidden", "not_found", "admin_forbidden", "missing_capability"):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_direct_edit_error",
        message="Could not save opening hours.",
        status=500,
    )


@require_http_methods(["GET", "HEAD", "PATCH"])
@require_owner_portal_auth
def owner_venue_features(request: HttpRequest, venue_id) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None

    if request.method in ("GET", "HEAD"):
        if request.method == "HEAD":
            return JsonResponse({}, status=200)
        result, code = get_owner_venue_features(auth, str(venue_id))
        if result is None:
            return _map_venue_scope_error(code)
        return JsonResponse({"data": result}, status=200)

    body, err_resp = _parse_json_object_body(request)
    if err_resp is not None:
        return err_resp
    assert body is not None

    result, code, details = patch_owner_venue_features(auth, str(venue_id), body)
    if code == "ok" and result:
        return JsonResponse({"data": result}, status=200)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code in ("forbidden", "not_found", "admin_forbidden", "missing_capability"):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_direct_edit_error",
        message="Could not save venue features.",
        status=500,
    )


@require_http_methods(["GET", "HEAD", "POST"])
@require_owner_portal_auth
def owner_venue_meal_specials(request: HttpRequest, venue_id) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None

    if request.method in ("GET", "HEAD"):
        if request.method == "HEAD":
            return JsonResponse({}, status=200)
        result, code = get_owner_venue_meal_specials(auth, str(venue_id))
        if result is None:
            return _map_venue_scope_error(code)
        return JsonResponse({"data": result}, status=200)

    body, err_resp = _parse_json_object_body(request)
    if err_resp is not None:
        return err_resp
    assert body is not None

    result, code, details = create_owner_venue_meal_special(
        auth, str(venue_id), body
    )
    if code == "ok" and result:
        return JsonResponse({"data": result}, status=201)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code in ("forbidden", "not_found", "admin_forbidden", "missing_capability"):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_direct_edit_error",
        message="Could not save meal special.",
        status=500,
    )


@require_http_methods(["PATCH", "DELETE"])
@require_owner_portal_auth
def owner_venue_meal_special_detail(
    request: HttpRequest, venue_id, special_id
) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None

    if request.method == "DELETE":
        result, code, details = deactivate_owner_venue_meal_special(
            auth, str(venue_id), str(special_id)
        )
    else:
        body, err_resp = _parse_json_object_body(request)
        if err_resp is not None:
            return err_resp
        assert body is not None
        result, code, details = patch_owner_venue_meal_special(
            auth, str(venue_id), str(special_id), body
        )

    if code == "ok" and result:
        return JsonResponse({"data": result}, status=200)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code == "not_found":
        return error_response(
            code="not_found",
            message="Meal special not found.",
            status=404,
        )
    if code in ("forbidden", "admin_forbidden", "missing_capability"):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_direct_edit_error",
        message="Could not update meal special.",
        status=500,
    )


@require_http_methods(["GET", "HEAD", "POST"])
@require_owner_portal_auth
def owner_venue_tap_list(request: HttpRequest, venue_id) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None

    if request.method in ("GET", "HEAD"):
        if request.method == "HEAD":
            return JsonResponse({}, status=200)
        result, code = get_owner_venue_tap_list(auth, str(venue_id))
        if result is None:
            return _map_venue_scope_error(code)
        return JsonResponse({"data": result}, status=200)

    body, err_resp = _parse_json_object_body(request)
    if err_resp is not None:
        return err_resp
    assert body is not None

    result, code, details = create_owner_venue_tap_list_item(
        auth, str(venue_id), body
    )
    if code == "ok" and result:
        return JsonResponse({"data": result}, status=201)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code in ("forbidden", "not_found", "admin_forbidden", "missing_capability"):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_direct_edit_error",
        message="Could not save tap list item.",
        status=500,
    )


@require_http_methods(["PATCH", "DELETE"])
@require_owner_portal_auth
def owner_venue_tap_list_detail(
    request: HttpRequest, venue_id, item_id
) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None

    if request.method == "DELETE":
        result, code, details = deactivate_owner_venue_tap_list_item(
            auth, str(venue_id), str(item_id)
        )
    else:
        body, err_resp = _parse_json_object_body(request)
        if err_resp is not None:
            return err_resp
        assert body is not None
        result, code, details = patch_owner_venue_tap_list_item(
            auth, str(venue_id), str(item_id), body
        )

    if code == "ok" and result:
        return JsonResponse({"data": result}, status=200)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code == "not_found":
        return error_response(
            code="not_found",
            message="Tap list item not found.",
            status=404,
        )
    if code in ("forbidden", "admin_forbidden", "missing_capability"):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_direct_edit_error",
        message="Could not update tap list item.",
        status=500,
    )


@require_http_methods(["POST"])
@require_owner_portal_auth
def owner_venue_restricted_change_request(
    request: HttpRequest, venue_id
) -> JsonResponse:
    auth = get_auth_context(request)
    assert auth is not None
    body, err_resp = _parse_json_object_body(request)
    if err_resp is not None:
        return err_resp
    assert body is not None

    section = body.get("section")
    payload = body.get("payload")
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return _validation_error(
            details={"payload": ["payload must be a JSON object."]}
        )

    result, code, details = create_owner_restricted_change_request(
        auth,
        str(venue_id),
        section=str(section) if section is not None else "",
        payload=payload,
    )
    if code == "ok" and result:
        return JsonResponse({"data": result}, status=201)
    if code == "already_in_review" and result:
        return JsonResponse({"data": result}, status=200)
    if code == "validation_error" and details:
        return _validation_error(details=details)
    if code == "validation_error":
        return _validation_error()
    if code in (
        "forbidden",
        "not_found",
        "admin_forbidden",
        "missing_restricted_capability",
    ):
        return _map_venue_scope_error(code)
    return error_response(
        code="owner_restricted_change_error",
        message="Could not submit your change request.",
        status=500,
    )
