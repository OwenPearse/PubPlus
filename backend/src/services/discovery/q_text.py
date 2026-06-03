"""MVP text search (`q`) normalization and SQL ILIKE patterns."""

from __future__ import annotations

from services.discovery.errors import DiscoveryFilterError

MAX_Q_LENGTH = 100


def normalize_discovery_q(raw: str | None) -> str | None:
    """Trim whitespace; return None when empty; reject overlong values."""
    if raw is None:
        return None
    term = raw.strip()
    if not term:
        return None
    if len(term) > MAX_Q_LENGTH:
        raise DiscoveryFilterError(
            "invalid_q",
            f"q must be at most {MAX_Q_LENGTH} characters.",
        )
    return term


def sql_ilike_pattern(term: str) -> str:
    """Build a parameterized ILIKE pattern; caller must use ESCAPE '\\'."""
    escaped = (
        term.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"
