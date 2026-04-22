from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthContext:
    subject: str
    audience: str | list[str]
    issuer: str
    role: str | None
    email: str | None
    claims: dict[str, Any]
