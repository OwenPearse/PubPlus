from collections.abc import Callable
from functools import wraps
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from common.auth.errors import InvalidTokenError, MissingBearerTokenError
from common.auth.jwt_verifier import verify_supabase_jwt
from common.auth.request_context import get_auth_context, set_auth_context
from common.auth.token_extraction import extract_bearer_token


def _unauthorized_response() -> JsonResponse:
    return JsonResponse(
        {
            "error": {
                "code": "unauthorized",
                "message": "Missing or invalid authentication token.",
            }
        },
        status=401,
    )


def _forbidden_response() -> JsonResponse:
    return JsonResponse(
        {
            "error": {
                "code": "forbidden",
                "message": "Authenticated identity is not authorized for this endpoint.",
            }
        },
        status=403,
    )


def _resolve_auth_context(request: HttpRequest, required: bool) -> bool:
    token = extract_bearer_token(request)
    if not token:
        if required:
            raise MissingBearerTokenError("Bearer token is required.")
        set_auth_context(request, None)
        return False

    context = verify_supabase_jwt(token)
    set_auth_context(request, context)
    return True


def _is_internal_admin_context(request: HttpRequest) -> bool:
    auth_context = get_auth_context(request)
    if auth_context is None:
        return False

    allowed_subjects = set(getattr(settings, "PUBPLUS_INTERNAL_ADMIN_SUBJECTS", []))
    if auth_context.subject in allowed_subjects:
        return True

    claims = auth_context.claims or {}
    return bool(claims.get("pubplus_internal_admin") is True)


def require_consumer_auth(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    def wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            _resolve_auth_context(request, required=True)
        except (MissingBearerTokenError, InvalidTokenError):
            return _unauthorized_response()
        return view_func(request, *args, **kwargs)

    return wrapped


def require_consumer_auth_api(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """
    Bearer-token API wrapper for mobile/web clients.

    CSRF is for cookie-backed browser sessions; these endpoints use Authorization: Bearer.
    """
    return csrf_exempt(require_consumer_auth(view_func))


def require_internal_admin_auth(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    def wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            _resolve_auth_context(request, required=True)
        except (MissingBearerTokenError, InvalidTokenError):
            return _unauthorized_response()

        if not _is_internal_admin_context(request):
            return _forbidden_response()

        return view_func(request, *args, **kwargs)

    # These endpoints use Authorization: Bearer <Supabase JWT> for auth, not
    # cookie-backed browser sessions. Exempt CSRF so the portal can call them
    # without needing a CSRF cookie.
    return csrf_exempt(wrapped)


def optional_consumer_auth(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    def wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            _resolve_auth_context(request, required=False)
        except InvalidTokenError:
            set_auth_context(request, None)
        return view_func(request, *args, **kwargs)

    return wrapped
