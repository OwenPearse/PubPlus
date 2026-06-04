import { beforeEach, describe, expect, it, vi } from "vitest";

const getAccessToken = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  getAccessToken: () => getAccessToken(),
}));

vi.mock("@/shared/lib/env", () => ({
  getApiBaseUrl: () => "http://api.test",
}));

import { ownerAuthProbe, ownerProvision } from "@/shared/lib/api";

describe("owner API wrappers", () => {
  beforeEach(() => {
    getAccessToken.mockReset();
    getAccessToken.mockResolvedValue("token-abc");
    vi.stubGlobal("fetch", vi.fn());
  });

  it("ownerProvision calls POST /api/v1/owner/provision", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          authenticated: true,
          owner_account_exists: true,
          owner_account_id: "oa-1",
          provisioned: true,
          created: true,
          next_step: "enroll_mfa",
        }),
        { status: 201, headers: { "content-type": "application/json" } },
      ),
    );

    await ownerProvision();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/owner/provision",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("ownerAuthProbe calls GET /api/v1/owner/auth-probe", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          authenticated: true,
          owner_account_exists: true,
          owner_account_active: true,
          mfa_required: true,
          aal: "aal2",
          has_active_business_membership: true,
          has_approved_managed_venue_relationship: true,
          business_count: 1,
          venue_count: 1,
          owner_account_id: "oa-1",
          next_step: "portal_home",
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const result = await ownerAuthProbe();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/owner/auth-probe",
      expect.any(Object),
    );
    expect(result.status).toBe(200);
    expect(result.body.next_step).toBe("portal_home");
  });

  it("ownerAuthProbe returns 403 body for owner_not_provisioned", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          authenticated: true,
          owner_account_exists: false,
          owner_account_active: false,
          mfa_required: true,
          aal: null,
          has_active_business_membership: false,
          has_approved_managed_venue_relationship: false,
          business_count: 0,
          venue_count: 0,
          owner_account_id: null,
          next_step: "complete_owner_provisioning",
          error: { code: "owner_not_provisioned", message: "not provisioned" },
        }),
        { status: 403, headers: { "content-type": "application/json" } },
      ),
    );

    const result = await ownerAuthProbe();
    expect(result.status).toBe(403);
    expect(result.body.error?.code).toBe("owner_not_provisioned");
  });

  it("ownerAuthProbe throws on 401", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ message: "Sign in required." }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(ownerAuthProbe()).rejects.toMatchObject({ code: "unauthorized" });
  });
});
