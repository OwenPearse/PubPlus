import { describe, expect, it } from "vitest";

import {
  getPostAuthContinuePath,
  shouldShowAccessDenied,
} from "@/shared/lib/portalRedirect";

const ownerProbe = {
  authenticated: true,
  owner_account_exists: true,
  owner_account_active: true,
  mfa_required: false,
  aal: "aal2",
  has_active_business_membership: true,
  has_approved_managed_venue_relationship: true,
  business_count: 1,
  venue_count: 1,
  owner_account_id: "oa-1",
  next_step: "portal_home" as const,
};

describe("portalRedirect helpers", () => {
  it("getPostAuthContinuePath returns admin internal path", () => {
    expect(getPostAuthContinuePath({ role: "admin" })).toBe("/internal/founder-venues");
  });

  it("getPostAuthContinuePath returns owner path when MFA satisfied", () => {
    expect(getPostAuthContinuePath({ role: "owner", probe: ownerProbe })).toBe("/owner");
  });

  it("getPostAuthContinuePath returns owner path at AAL1 without blocking on MFA", () => {
    expect(
      getPostAuthContinuePath({
        role: "owner",
        probe: {
          ...ownerProbe,
          next_step: "owner_waiting_for_membership",
          aal: "aal1",
          mfa_required: false,
        },
      }),
    ).toBe("/owner");
  });

  it("shouldShowAccessDenied for no_access and dual_access", () => {
    expect(shouldShowAccessDenied({ role: "none", reason: "no_access" })).toBe(true);
    expect(
      shouldShowAccessDenied({
        role: "error",
        code: "dual_access",
        message: "conflict",
      }),
    ).toBe(true);
    expect(shouldShowAccessDenied({ role: "admin" })).toBe(false);
    expect(
      shouldShowAccessDenied({ role: "none", reason: "owner_not_provisioned" }),
    ).toBe(false);
  });
});
