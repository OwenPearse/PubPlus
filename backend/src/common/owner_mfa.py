"""
Supabase MFA / authenticator assurance helpers for owner portal.

Normal owner portal access allows AAL1. Optional MFA raises the session to AAL2.
Stricter guards (e.g. require_owner_portal_auth_aal2) apply AAL2 for sensitive actions.
"""

from __future__ import annotations

from typing import Any

OWNER_MFA_REQUIRED = False
OWNER_REQUIRED_AAL = "aal2"


def resolve_aal(claims: dict[str, Any]) -> str:
    """Normalize Supabase JWT `aal` claim; defaults to aal1 when absent."""
    raw = claims.get("aal")
    if isinstance(raw, str) and raw in ("aal1", "aal2"):
        return raw
    return "aal1"


def is_owner_mfa_satisfied(claims: dict[str, Any]) -> bool:
    """True when JWT is at AAL2 (MFA challenge completed for this session)."""
    return resolve_aal(claims) == OWNER_REQUIRED_AAL


def is_owner_mfa_enabled(claims: dict[str, Any]) -> bool:
    """Posture hint: session has completed MFA (AAL2)."""
    return is_owner_mfa_satisfied(claims)


def mfa_next_step(claims: dict[str, Any]) -> str:
    """Legacy routing hint; MFA is optional — prefer membership/venue next_step."""
    if is_owner_mfa_satisfied(claims):
        return "portal_home"
    return "enroll_mfa"
