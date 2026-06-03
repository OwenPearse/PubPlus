"""Email contact-safety classification for founder venue leads."""

from __future__ import annotations

from urllib.parse import urlparse

GENERIC_LOCAL_PREFIXES: frozenset[str] = frozenset(
    {
        "info",
        "hello",
        "bookings",
        "booking",
        "functions",
        "events",
        "manager",
        "contact",
        "enquiries",
        "inquiries",
        "admin",
        "reception",
        "bar",
        "pub",
    }
)

ROLE_LOCAL_PREFIXES: frozenset[str] = frozenset(
    {
        "office",
        "marketing",
        "sales",
        "hr",
        "accounts",
        "reservations",
    }
)

PERSONAL_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "hotmail.com",
        "outlook.com",
        "live.com",
        "yahoo.com",
        "icloud.com",
        "me.com",
        "protonmail.com",
        "proton.me",
    }
)


def classify_email_contact_safety(email: str | None) -> str | None:
    """
    Return contact_safety_class for an email, or None if email is empty/invalid.

    Does not block import; used for attribution and confidence adjustments.
    """
    if not email or "@" not in email:
        return None
    local, _, domain = email.partition("@")
    local = local.strip().lower()
    domain = domain.strip().lower()
    if not local or not domain:
        return None

    if domain in PERSONAL_EMAIL_DOMAINS:
        return "likely_personal_or_unsafe"

    if local in GENERIC_LOCAL_PREFIXES:
        return "generic_business_contact"

    if local in ROLE_LOCAL_PREFIXES:
        return "role_based_contact"

    if "." in local and not local.startswith("no-reply") and not local.startswith("noreply"):
        return "personal_business_contact"

    return "role_based_contact"


def is_high_confidence_business_email(email: str | None) -> bool:
    """True when email counts toward import confidence bonus."""
    safety = classify_email_contact_safety(email)
    return safety in ("generic_business_contact", "role_based_contact")
