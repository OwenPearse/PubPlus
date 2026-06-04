"""
Supabase MFA / authenticator assurance helpers for owner portal enforcement.

Owner protected API routes require AAL2 (`aal` JWT claim). Auth-probe returns routing
state in the response body; protected routes return 403 when AAL2 is not satisfied.
"""

from __future__ import annotations

from typing import Any

OWNER_MFA_REQUIRED = True
OWNER_REQUIRED_AAL = "aal2"


def resolve_aal(claims: dict[str, Any]) -> str:
    """Normalize Supabase JWT `aal` claim; defaults to aal1 when absent."""
    raw = claims.get("aal")
    if isinstance(raw, str) and raw in ("aal1", "aal2"):
        return raw
    return "aal1"


def is_owner_mfa_satisfied(claims: dict[str, Any]) -> bool:
    if not OWNER_MFA_REQUIRED:
        return True
    return resolve_aal(claims) == OWNER_REQUIRED_AAL


def mfa_next_step(claims: dict[str, Any]) -> str:
    """Routing hint when owner exists but MFA is not yet at AAL2."""
    if is_owner_mfa_satisfied(claims):
        return "portal_home"
    # Supabase uses aal1 until the user completes an MFA challenge after enrollment.
    return "enroll_mfa"
