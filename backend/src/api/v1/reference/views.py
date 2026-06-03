from __future__ import annotations

from django.db import DatabaseError
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.discovery.http import error_response
from services.reference.locality_reference import build_locality_reference


@require_GET
def reference_localities(_request):
    try:
        payload = build_locality_reference()
    except DatabaseError:
        return error_response(
            code="db_error",
            message="Locality reference could not be loaded.",
            status=500,
        )
    response = JsonResponse({"data": payload})
    response["Cache-Control"] = "public, max-age=300"
    return response
