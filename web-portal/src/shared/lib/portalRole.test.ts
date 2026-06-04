import { beforeEach, describe, expect, it, vi } from "vitest";

const internalAuthProbe = vi.fn();
const ownerAuthProbe = vi.fn();
const waitForAccessToken = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  internalAuthProbe: () => internalAuthProbe(),
  ownerAuthProbe: () => ownerAuthProbe(),
  formatApiError: (err: unknown) =>
    err && typeof err === "object" && "message" in err
      ? String((err as { message: string }).message)
      : "error",
  isApiRequestError: (err: unknown) =>
    Boolean(err && typeof err === "object" && "code" in err),
}));

vi.mock("@/shared/lib/supabase", () => ({
  waitForAccessToken: () => waitForAccessToken(),
}));

import {
  getDefaultPathForRole,
  ownerProbeRequiresMfaOnAccess,
  resolvePortalRole,
} from "@/shared/lib/portalRole";

const ownerProbeBody = {
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

describe("resolvePortalRole", () => {
  beforeEach(() => {
    internalAuthProbe.mockReset();
    ownerAuthProbe.mockReset();
    waitForAccessToken.mockReset();
    waitForAccessToken.mockResolvedValue("token");
  });

  it("returns expired when session token never appears", async () => {
    waitForAccessToken.mockResolvedValue(null);
    await expect(resolvePortalRole()).resolves.toEqual({ role: "expired" });
  });

  it("returns admin when internal probe succeeds", async () => {
    internalAuthProbe.mockResolvedValue({ status: "ok", subject: "admin" });
    ownerAuthProbe.mockResolvedValue({ status: 403, body: { owner_account_exists: false } });
    await expect(resolvePortalRole()).resolves.toEqual({ role: "admin" });
  });

  it("returns owner when admin fails and owner probe is 200", async () => {
    internalAuthProbe.mockRejectedValue({ code: "forbidden", status: 403, message: "denied" });
    ownerAuthProbe.mockResolvedValue({ status: 200, body: ownerProbeBody });
    await expect(resolvePortalRole()).resolves.toEqual({
      role: "owner",
      probe: ownerProbeBody,
    });
  });

  it("returns none with owner_not_provisioned on 403", async () => {
    internalAuthProbe.mockRejectedValue({ code: "forbidden", status: 403, message: "denied" });
    ownerAuthProbe.mockResolvedValue({
      status: 403,
      body: {
        ...ownerProbeBody,
        owner_account_exists: false,
        owner_account_id: null,
        next_step: "complete_owner_provisioning",
        error: { code: "owner_not_provisioned", message: "not provisioned" },
      },
    });
    await expect(resolvePortalRole()).resolves.toMatchObject({
      role: "none",
      reason: "owner_not_provisioned",
    });
  });

  it("returns none when both probes fail", async () => {
    internalAuthProbe.mockRejectedValue({ code: "forbidden", status: 403, message: "denied" });
    ownerAuthProbe.mockResolvedValue({
      status: 403,
      body: {
        ...ownerProbeBody,
        owner_account_exists: false,
        error: { code: "other", message: "blocked" },
      },
    });
    await expect(resolvePortalRole()).resolves.toMatchObject({
      role: "none",
      reason: "no_access",
    });
  });

  it("returns expired when owner probe is unauthorized", async () => {
    internalAuthProbe.mockRejectedValue({ code: "forbidden", status: 403, message: "denied" });
    ownerAuthProbe.mockRejectedValue({ code: "unauthorized", status: 401, message: "expired" });
    await expect(resolvePortalRole()).resolves.toEqual({ role: "expired" });
  });

  it("returns dual_access error when admin and owner both succeed", async () => {
    internalAuthProbe.mockResolvedValue({ status: "ok", subject: "admin" });
    ownerAuthProbe.mockResolvedValue({ status: 200, body: ownerProbeBody });
    await expect(resolvePortalRole()).resolves.toMatchObject({
      role: "error",
      code: "dual_access",
    });
  });
});

describe("ownerProbeRequiresMfaOnAccess", () => {
  it("never blocks owner routes (MFA optional)", () => {
    expect(
      ownerProbeRequiresMfaOnAccess({
        ...ownerProbeBody,
        next_step: "enroll_mfa",
        aal: "aal1",
      }),
    ).toBe(false);
    expect(
      ownerProbeRequiresMfaOnAccess({
        ...ownerProbeBody,
        next_step: "portal_home",
      }),
    ).toBe(false);
  });
});

describe("getDefaultPathForRole", () => {
  it("maps roles to default paths", () => {
    expect(getDefaultPathForRole({ role: "admin" })).toBe("/internal/founder-venues");
    expect(
      getDefaultPathForRole({
        role: "owner",
        probe: { ...ownerProbeBody, next_step: "portal_home" },
      }),
    ).toBe("/owner");
    expect(
      getDefaultPathForRole({
        role: "owner",
        probe: { ...ownerProbeBody, next_step: "enroll_mfa", aal: "aal1" },
      }),
    ).toBe("/owner");
  });
});
