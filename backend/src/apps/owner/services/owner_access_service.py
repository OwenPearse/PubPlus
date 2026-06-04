"""
Owner portal access resolution: provisioning and auth-probe state.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from django.conf import settings
from django.db import connection

from common.auth.context import AuthContext
from common.owner_account import (
    admin_account_exists_for_auth,
    get_or_create_owner_account_id,
    get_owner_account_id,
)
from common.owner_mfa import (
    OWNER_MFA_REQUIRED,
    is_owner_mfa_enabled,
    resolve_aal,
)


class OwnerProvisioningDisallowedError(Exception):
    """Valid JWT but this identity may not receive an owner_account row."""


@dataclass(frozen=True)
class OwnerAccessCounts:
    business_count: int
    venue_count: int

    @property
    def has_active_business_membership(self) -> bool:
        return self.business_count > 0

    @property
    def has_approved_managed_venue_relationship(self) -> bool:
        return self.venue_count > 0


def _owner_provision_disabled() -> bool:
    return bool(getattr(settings, "PUBPLUS_OWNER_PROVISION_DISABLED", False))


def assert_owner_provisioning_allowed(auth: AuthContext) -> None:
    if _owner_provision_disabled():
        raise OwnerProvisioningDisallowedError("Owner provisioning is disabled.")
    if admin_account_exists_for_auth(auth):
        raise OwnerProvisioningDisallowedError(
            "Auth subject is already linked to an admin_account; owner provisioning is not allowed."
        )


def provision_owner_account(auth: AuthContext) -> tuple[UUID, bool]:
    """
    Create or confirm owner_account for the authenticated subject.

    Returns (owner_account_id, created).
    """
    assert_owner_provisioning_allowed(auth)
    return get_or_create_owner_account_id(auth)


def load_owner_access_counts(owner_account_id: UUID) -> OwnerAccessCounts:
    """
    Count active business memberships and distinct approved managed venues.

    Venue access requires an approved business_venue_management_relationship on a
    business where the owner has active membership — not membership alone.
    """
    with connection.cursor() as c:
        c.execute(
            """
            SELECT COUNT(*)::int
            FROM public.owner_business_membership obm
            WHERE obm.owner_account_id = %s::uuid
              AND obm.membership_status = 'active'
            """,
            [str(owner_account_id)],
        )
        business_count = int(c.fetchone()[0])

        c.execute(
            """
            SELECT COUNT(DISTINCT bvmr.venue_id)::int
            FROM public.owner_business_membership obm
            INNER JOIN public.business_venue_management_relationship bvmr
              ON bvmr.business_id = obm.business_id
            WHERE obm.owner_account_id = %s::uuid
              AND obm.membership_status = 'active'
              AND bvmr.relationship_lifecycle = 'approved'
            """,
            [str(owner_account_id)],
        )
        venue_count = int(c.fetchone()[0])

    return OwnerAccessCounts(
        business_count=business_count,
        venue_count=venue_count,
    )


def resolve_owner_next_step(
    *,
    claims: dict,
    counts: OwnerAccessCounts,
) -> str:
    if counts.business_count == 0:
        return "owner_waiting_for_membership"
    if counts.venue_count == 0:
        return "owner_waiting_for_venue_access"
    return "portal_home"


def build_provision_payload(
    *,
    owner_account_id: UUID,
    created: bool,
    claims: dict,
) -> dict:
    counts = load_owner_access_counts(owner_account_id)
    return {
        "authenticated": True,
        "owner_account_exists": True,
        "owner_account_id": str(owner_account_id),
        "provisioned": True,
        "created": created,
        "mfa_required": OWNER_MFA_REQUIRED,
        "mfa_enabled": is_owner_mfa_enabled(claims),
        "aal": resolve_aal(claims),
        "next_step": resolve_owner_next_step(claims=claims, counts=counts),
    }


def build_auth_probe_payload(
    *,
    owner_account_id: UUID,
    claims: dict,
    counts: OwnerAccessCounts,
) -> dict:
    aal = resolve_aal(claims)
    next_step = resolve_owner_next_step(claims=claims, counts=counts)
    return {
        "authenticated": True,
        "owner_account_exists": True,
        "owner_account_active": True,
        "mfa_required": OWNER_MFA_REQUIRED,
        "mfa_enabled": is_owner_mfa_enabled(claims),
        "aal": aal,
        "has_active_business_membership": counts.has_active_business_membership,
        "has_approved_managed_venue_relationship": counts.has_approved_managed_venue_relationship,
        "business_count": counts.business_count,
        "venue_count": counts.venue_count,
        "owner_account_id": str(owner_account_id),
        "next_step": next_step,
    }


def build_auth_probe_no_owner_payload() -> dict:
    return {
        "authenticated": True,
        "owner_account_exists": False,
        "owner_account_active": False,
        "mfa_required": OWNER_MFA_REQUIRED,
        "mfa_enabled": False,
        "aal": None,
        "has_active_business_membership": False,
        "has_approved_managed_venue_relationship": False,
        "business_count": 0,
        "venue_count": 0,
        "owner_account_id": None,
        "next_step": "complete_owner_provisioning",
    }


def resolve_owner_auth_probe(auth: AuthContext) -> tuple[dict, int]:
    """
    Return (response_body, http_status) for GET /api/v1/owner/auth-probe.
    """
    owner_id = get_owner_account_id(auth)
    if owner_id is None:
        return build_auth_probe_no_owner_payload(), 403

    counts = load_owner_access_counts(owner_id)
    body = build_auth_probe_payload(
        owner_account_id=owner_id,
        claims=auth.claims or {},
        counts=counts,
    )
    return body, 200
