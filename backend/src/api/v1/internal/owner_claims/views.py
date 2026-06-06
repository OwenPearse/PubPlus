from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.discovery.http import error_response
from apps.internal_tools.services.moderation_write_service import (
    InternalOperatorResolutionError,
)
from apps.internal_tools.services.venue_claim_read_service import (
    VenueClaimNotFoundError,
    VenueClaimReadValidationError,
    get_owner_claim_detail,
    list_owner_claim_queue,
    parse_claim_queue_filters,
)
from apps.internal_tools.services.venue_claim_write_service import (
    VenueClaimDecisionConflictError,
    VenueClaimWriteNotFoundError,
    VenueClaimWriteValidationError,
    approve_owner_claim_existing,
    approve_owner_claim_new,
    mark_owner_claim_needs_more_info,
    reject_owner_claim,
)
from apps.internal_tools.services.moderation_write_service import (
    resolve_admin_account_for_internal_operator,
)
from common.auth.guards import require_internal_admin_auth
from common.auth.request_context import get_auth_context


def _parse_json_object_body(request):
    try:
        data = (
            json.loads(request.body)
            if isinstance(request.body, (bytes, bytearray)) and request.body
            else {}
        )
    except json.JSONDecodeError:
        raise VenueClaimWriteValidationError("Request body must be valid JSON.")
    if not isinstance(data, dict):
        raise VenueClaimWriteValidationError("Request body must be a JSON object.")
    return data


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def owner_claims_list(request):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        filters = parse_claim_queue_filters(
            {k: request.GET.get(k, "") for k in request.GET.keys()}
        )
        payload = list_owner_claim_queue(filters)
    except VenueClaimReadValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    return JsonResponse({"data": payload}, status=200)


@require_http_methods(["GET", "HEAD"])
@require_internal_admin_auth
def owner_claim_detail(request, claim_request_id: str):
    if request.method == "HEAD":
        return JsonResponse({}, status=200)
    try:
        payload = get_owner_claim_detail(claim_request_id)
    except VenueClaimReadValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except VenueClaimNotFoundError:
        return error_response(
            code="not_found",
            message="Owner claim request not found.",
            status=404,
        )
    return JsonResponse({"data": payload}, status=200)


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def owner_claim_approve_existing(request, claim_request_id: str):
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
        result = approve_owner_claim_existing(
            claim_request_id,
            venue_id=payload.get("venue_id"),
            admin_note=payload.get("admin_note"),
            operator=operator,
        )
    except VenueClaimWriteValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except VenueClaimWriteNotFoundError:
        return error_response(
            code="not_found",
            message="Owner claim request not found.",
            status=404,
        )
    except VenueClaimDecisionConflictError as exc:
        return error_response(code="conflict", message=str(exc), status=409)
    except InternalOperatorResolutionError as exc:
        return error_response(code="operator_resolution_failed", message=str(exc), status=409)
    return JsonResponse({"data": result}, status=200)


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def owner_claim_approve_new(request, claim_request_id: str):
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
        result = approve_owner_claim_new(
            claim_request_id,
            admin_note=payload.get("admin_note"),
            operator=operator,
        )
    except VenueClaimWriteValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except VenueClaimWriteNotFoundError:
        return error_response(
            code="not_found",
            message="Owner claim request not found.",
            status=404,
        )
    except VenueClaimDecisionConflictError as exc:
        return error_response(code="conflict", message=str(exc), status=409)
    except InternalOperatorResolutionError as exc:
        return error_response(code="operator_resolution_failed", message=str(exc), status=409)
    return JsonResponse({"data": result}, status=200)


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def owner_claim_reject(request, claim_request_id: str):
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
        result = reject_owner_claim(
            claim_request_id,
            admin_note=payload.get("admin_note"),
            operator=operator,
        )
    except VenueClaimWriteValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except VenueClaimWriteNotFoundError:
        return error_response(
            code="not_found",
            message="Owner claim request not found.",
            status=404,
        )
    except VenueClaimDecisionConflictError as exc:
        return error_response(code="conflict", message=str(exc), status=409)
    except InternalOperatorResolutionError as exc:
        return error_response(code="operator_resolution_failed", message=str(exc), status=409)
    return JsonResponse({"data": result}, status=200)


@require_http_methods(["POST", "HEAD"])
@require_internal_admin_auth
def owner_claim_needs_more_info(request, claim_request_id: str):
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
        result = mark_owner_claim_needs_more_info(
            claim_request_id,
            admin_note=payload.get("admin_note"),
            operator=operator,
        )
    except VenueClaimWriteValidationError as exc:
        return error_response(code="validation_error", message=exc.message, status=400)
    except VenueClaimWriteNotFoundError:
        return error_response(
            code="not_found",
            message="Owner claim request not found.",
            status=404,
        )
    except VenueClaimDecisionConflictError as exc:
        return error_response(code="conflict", message=str(exc), status=409)
    except InternalOperatorResolutionError as exc:
        return error_response(code="operator_resolution_failed", message=str(exc), status=409)
    return JsonResponse({"data": result}, status=200)
