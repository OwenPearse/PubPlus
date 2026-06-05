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
from apps.owner.services.owner_venue_service import (
    create_or_update_owner_core_details_proposal,
    get_owner_venue_detail,
    list_owner_venues,
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
