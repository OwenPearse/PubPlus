from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse

from common.auth.errors import InvalidTokenError, MissingBearerTokenError
from common.auth.jwt_verifier import verify_supabase_jwt
from common.auth.request_context import set_auth_context
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
