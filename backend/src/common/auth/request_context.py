from django.http import HttpRequest

from common.auth.context import AuthContext

REQUEST_AUTH_CONTEXT_ATTR = "_pubplus_auth_context"


def set_auth_context(request: HttpRequest, context: AuthContext | None) -> None:
    setattr(request, REQUEST_AUTH_CONTEXT_ATTR, context)


def get_auth_context(request: HttpRequest) -> AuthContext | None:
    return getattr(request, REQUEST_AUTH_CONTEXT_ATTR, None)
