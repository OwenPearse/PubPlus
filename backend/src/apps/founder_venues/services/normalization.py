"""
Normalization helpers for founder venue lead import, dedupe, and enrichment.

Pure functions only. Database writes belong in import/enrichment services (Stage 2+).
"""

from __future__ import annotations

import re
from typing import Final
from urllib.parse import urlparse

_AU_STATE_MAP: Final[dict[str, str]] = {
    "australian capital territory": "ACT",
    "act": "ACT",
    "new south wales": "NSW",
    "nsw": "NSW",
    "northern territory": "NT",
    "nt": "NT",
    "queensland": "QLD",
    "qld": "QLD",
    "south australia": "SA",
    "sa": "SA",
    "tasmania": "TAS",
    "tas": "TAS",
    "victoria": "VIC",
    "vic": "VIC",
    "western australia": "WA",
    "wa": "WA",
}

_NAME_LEGAL_SUFFIXES: Final[tuple[str, ...]] = (
    "pty ltd",
    "pty. ltd.",
    "pty limited",
    "limited",
    "ltd",
)

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_PHONE_DIGITS_RE = re.compile(r"\d+")


def normalize_venue_name(value: str | None) -> str | None:
    """Lowercase, trim legal suffixes, collapse punctuation for soft matching."""
    if value is None:
        return None
    text = _WHITESPACE_RE.sub(" ", value.strip().lower())
    if not text:
        return None
    for suffix in _NAME_LEGAL_SUFFIXES:
        if text.endswith(f" {suffix}"):
            text = text[: -len(suffix)].strip()
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or None


def normalize_state(value: str | None) -> str | None:
    """Map Australian state names/abbreviations to standard codes (ACT–WA)."""
    if value is None:
        return None
    key = value.strip().lower()
    if not key:
        return None
    return _AU_STATE_MAP.get(key)


def normalize_website_url(value: str | None) -> str | None:
    """Normalize http(s) URL; strip www; drop trailing slash on path."""
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if "://" not in text:
        text = f"https://{text}"
    parsed = urlparse(text)
    if not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/") if parsed.path and parsed.path != "/" else ""
    scheme = (parsed.scheme or "https").lower()
    if scheme not in ("http", "https"):
        return None
    return f"{scheme}://{host}{path}"


def website_host(value: str | None) -> str | None:
    """Normalized website hostname for dedupe (no www prefix)."""
    normalized = normalize_website_url(value)
    if not normalized:
        return None
    return urlparse(normalized).netloc or None


def normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    if not text or "@" not in text:
        return None
    return text


def normalize_phone_au(value: str | None) -> str | None:
    """Conservative AU E.164 (+61…) normalization; returns None if not 10-digit national."""
    if value is None:
        return None
    digits = "".join(_PHONE_DIGITS_RE.findall(value))
    if not digits:
        return None
    if digits.startswith("61") and len(digits) >= 11:
        national = digits[2:]
    elif digits.startswith("0"):
        national = digits[1:]
    else:
        national = digits
    if len(national) == 9:
        national = f"0{national}"
    if len(national) != 10:
        return None
    return f"+61{national[1:]}"


def normalize_postcode(value: str | int | float | None) -> str | None:
    """TODO: expand validation for AU postcode ranges in Stage 2 import."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "." in text:
        text = text.split(".", 1)[0]
    if len(text) == 4 and text.isdigit():
        return text
    return None


def build_soft_dedupe_key(
    *,
    normalized_name: str | None = None,
    postcode: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    email: str | None = None,
) -> str | None:
    """
    Stable fingerprint for soft dedupe (not a hard UNIQUE constraint).

    Prefers strong identifiers (website host, phone, email) over name+postcode.
    """
    parts: list[str] = []
    host = website_host(website)
    if host:
        parts.append(f"web:{host}")
    if phone:
        parts.append(f"phone:{phone}")
    if email:
        parts.append(f"email:{email}")
    if normalized_name and postcode:
        parts.append(f"namepc:{normalized_name}|{postcode}")
    if not parts:
        return None
    return "|".join(parts)
