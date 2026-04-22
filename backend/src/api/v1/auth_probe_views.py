from django.http import JsonResponse

from common.auth.guards import optional_consumer_auth, require_consumer_auth
from common.auth.request_context import get_auth_context


@require_consumer_auth
def private_consumer_probe(request):
    auth_context = get_auth_context(request)
    return JsonResponse(
        {
            "status": "ok",
            "subject": auth_context.subject,
        }
    )


@optional_consumer_auth
def public_probe(request):
    auth_context = get_auth_context(request)
    return JsonResponse(
        {
            "status": "ok",
            "authenticated": auth_context is not None,
        }
    )
