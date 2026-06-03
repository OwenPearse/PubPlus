"""Shared validation for founder venue lead API and mutations."""

from __future__ import annotations

from uuid import UUID

ENRICHMENT_STATUSES = frozenset(
    {
        "imported",
        "pending_enrichment",
        "enriched",
        "needs_review",
        "rejected",
    }
)

OUTREACH_STATUSES = frozenset(
    {
        "not_contacted",
        "queued",
        "called",
        "emailed",
        "replied",
        "signed_up",
        "rejected",
        "do_not_contact",
    }
)

CONTACT_PERMISSION_STATUSES = frozenset(
    {
        "unknown",
        "public_business_contact",
        "requested_info_by_phone",
        "requested_info_by_dm",
        "opted_in",
        "opted_out",
        "do_not_contact",
    }
)

LAST_CONTACT_CHANNELS = frozenset(
    {
        "phone",
        "email",
        "instagram",
        "facebook",
        "website_form",
        "in_person",
        "other",
    }
)

SORT_OPTIONS = frozenset(
    {
        "founder_fit_score_desc",
        "confidence_score_desc",
        "updated_at_desc",
        "created_at_desc",
        "name_asc",
    }
)

DEFAULT_LIMIT = 50
MAX_LIMIT = 200
EXPORT_DEFAULT_LIMIT = 1000
EXPORT_MAX_LIMIT = 5000
MAX_RECOMPUTE_LIMIT = 1000
MAX_CSV_BYTES = 5 * 1024 * 1024


class LeadValidationError(ValueError):
    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LeadNotFoundError(LookupError):
    pass


def parse_uuid(value: str, *, field_name: str = "id") -> str:
    try:
        return str(UUID(str(value).strip()))
    except (ValueError, TypeError) as exc:
        raise LeadValidationError(f"{field_name} must be a valid UUID.") from exc


def parse_optional_iso_datetime(
    value: str | None,
    *,
    field_name: str,
) -> "datetime | None":
    from datetime import datetime

    if value in (None, ""):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise LeadValidationError(
            f"{field_name} must be a valid ISO 8601 datetime."
        ) from exc


def parse_bool_param(value: str | None, *, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    lowered = value.strip().lower()
    if lowered in ("true", "1", "yes"):
        return True
    if lowered in ("false", "0", "no"):
        return False
    raise LeadValidationError(f"Invalid boolean value: {value!r}")


def parse_int_param(
    value: str | None,
    *,
    default: int,
    minimum: int,
    maximum: int,
    field_name: str,
) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise LeadValidationError(f"{field_name} must be an integer.") from exc
    if parsed < minimum or parsed > maximum:
        raise LeadValidationError(
            f"{field_name} must be between {minimum} and {maximum}."
        )
    return parsed
