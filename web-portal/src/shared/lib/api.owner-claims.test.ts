import { beforeEach, describe, expect, it, vi } from "vitest";

const waitForAccessToken = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  waitForAccessToken: () => waitForAccessToken(),
}));

vi.mock("@/shared/lib/env", () => ({
  getApiBaseUrl: () => "http://api.test",
}));

import {
  approveOwnerClaimExisting,
  getOwnerClaim,
  listOwnerClaims,
  rejectOwnerClaim,
} from "@/shared/lib/api";

describe("owner claims API client", () => {
  beforeEach(() => {
    waitForAccessToken.mockResolvedValue("test-token");
    vi.stubGlobal("fetch", vi.fn());
  });

  it("listOwnerClaims sends GET with status filter", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          data: {
            items: [
              {
                claim_request_id: "claim-1",
                status: "submitted",
                submitted_at: "2026-01-01T00:00:00Z",
                owner_account_id: "owner-1",
                claimant_email: "owner@example.com",
                venue_name: "Royal Hotel",
                address_line_1: "1 Main St",
                locality_id: "loc-1",
                locality_name: "Fitzroy",
                state_code: "VIC",
                claimant_note: "Licensee",
                duplicate_candidate_count: 1,
              },
            ],
            meta: { total: 1 },
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    await listOwnerClaims({ status: "submitted,under_review" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/internal/owner-claims/?status=submitted%2Cunder_review",
      expect.any(Object),
    );
  });

  it("getOwnerClaim fetches claim detail", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          data: {
            claim_request_id: "claim-1",
            status: "submitted",
            duplicate_candidates: [
              {
                venue_id: "v-1",
                display_name: "Royal Hotel",
                match_score: 95,
                match_reason: "Exact name match",
              },
            ],
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const result = await getOwnerClaim("claim-1");
    expect(result.data.claim_request_id).toBe("claim-1");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/internal/owner-claims/claim-1",
      expect.any(Object),
    );
  });

  it("approveOwnerClaimExisting posts venue_id", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          data: {
            claim_request_id: "claim-1",
            status: "closed",
            message: "Approved",
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    await approveOwnerClaimExisting("claim-1", {
      venue_id: "v-1",
      admin_note: "Verified",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/internal/owner-claims/claim-1/approve-existing",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ venue_id: "v-1", admin_note: "Verified" }),
      }),
    );
  });

  it("rejectOwnerClaim posts reject action", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          data: {
            claim_request_id: "claim-1",
            status: "denied",
            message: "Rejected",
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    await rejectOwnerClaim("claim-1", { admin_note: "Insufficient proof" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/internal/owner-claims/claim-1/reject",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ admin_note: "Insufficient proof" }),
      }),
    );
  });
});
