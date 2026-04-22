from django.http import JsonResponse

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
