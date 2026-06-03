from functools import lru_cache
from typing import Any

import jwt
from django.conf import settings

from common.auth.context import AuthContext
from common.auth.errors import InvalidTokenError


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url)


def verify_supabase_jwt(token: str) -> AuthContext:
    try:
        jwks_client = _jwks_client(settings.SUPABASE_JWT_JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=[settings.SUPABASE_JWT_ALGORITHM],
            audience=settings.SUPABASE_JWT_AUDIENCE,
            issuer=settings.SUPABASE_JWT_ISSUER,
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Token verification failed.") from exc
    except Exception as exc:
        raise InvalidTokenError("Token verification failed.") from exc

    subject = claims.get("sub")
    if not subject:
        raise InvalidTokenError("Token missing required 'sub' claim.")

    return AuthContext(
        subject=subject,
        audience=claims.get("aud", settings.SUPABASE_JWT_AUDIENCE),
        issuer=claims.get("iss", settings.SUPABASE_JWT_ISSUER),
        role=claims.get("role"),
        email=claims.get("email"),
        claims=claims,
    )
