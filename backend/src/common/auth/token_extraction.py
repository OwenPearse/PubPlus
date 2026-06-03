from django.http import HttpRequest


def extract_bearer_token(request: HttpRequest) -> str | None:
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header:
        return None

    token_type, _, token = auth_header.partition(" ")
    if token_type.lower() != "bearer" or not token.strip():
        return None

    return token.strip()
