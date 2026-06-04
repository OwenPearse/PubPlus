from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.discovery.http import error_response
from apps.owner.services.owner_access_service import (
    OwnerProvisioningDisallowedError,
    build_provision_payload,
    provision_owner_account,
    resolve_owner_auth_probe,
)
from common.auth.guards import require_consumer_auth_api
from common.auth.request_context import get_auth_context


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
    payload = build_provision_payload(owner_account_id=owner_id, created=created)
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
