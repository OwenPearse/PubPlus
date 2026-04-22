class AuthError(Exception):
    pass


class MissingBearerTokenError(AuthError):
    pass


class InvalidTokenError(AuthError):
    pass
