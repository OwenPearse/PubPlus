import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerClaimDetailPage } from "@/admin/pages/OwnerClaimDetailPage";

const getOwnerClaim = vi.fn();
const approveOwnerClaimExisting = vi.fn();
const rejectOwnerClaim = vi.fn();
const approveOwnerClaimNew = vi.fn();
const markOwnerClaimNeedsMoreInfo = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  getOwnerClaim: (...args: unknown[]) => getOwnerClaim(...args),
  approveOwnerClaimExisting: (...args: unknown[]) => approveOwnerClaimExisting(...args),
  approveOwnerClaimNew: (...args: unknown[]) => approveOwnerClaimNew(...args),
  rejectOwnerClaim: (...args: unknown[]) => rejectOwnerClaim(...args),
  markOwnerClaimNeedsMoreInfo: (...args: unknown[]) => markOwnerClaimNeedsMoreInfo(...args),
  formatApiError: (err: unknown) => String(err),
}));

const claimDetail = {
  claim_request_id: "claim-1",
  status: "submitted",
  submitted_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  venue_id: "stub-v-1",
  business_id: "biz-1",
  owner_account_id: "owner-1",
  resulting_relationship_id: null,
  claimant_email: "owner@example.com",
  business_display_name: "Pending business",
  submitted: {
    mode: "submit_new_or_claim",
    venue_name: "Royal Hotel",
    address_line_1: "1 Main St",
    locality_id: "loc-1",
    locality_name: "Fitzroy",
    state_code: "VIC",
    claimant_note: "I manage this pub.",
  },
  possible_duplicate_venue_ids: ["v-existing"],
  duplicate_candidates: [
    {
      venue_id: "v-existing",
      display_name: "Royal Hotel Fitzroy",
      address_line_1: "1 Main St",
      locality_name: "Fitzroy",
      state_code: "VIC",
      match_score: 95,
      match_reason: "Exact name match",
    },
  ],
};

function renderDetail() {
  return render(
    <MemoryRouter initialEntries={["/internal/owner-claims/claim-1"]}>
      <Routes>
        <Route path="/internal/owner-claims/:claimRequestId" element={<OwnerClaimDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OwnerClaimDetailPage", () => {
  beforeEach(() => {
    getOwnerClaim.mockReset();
    approveOwnerClaimExisting.mockReset();
    rejectOwnerClaim.mockReset();
    approveOwnerClaimNew.mockReset();
    markOwnerClaimNeedsMoreInfo.mockReset();
    getOwnerClaim.mockResolvedValue({ data: claimDetail });
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  it("renders submitted pub details and duplicate candidates", async () => {
    renderDetail();
    await waitFor(() => {
      expect(screen.getByText("Royal Hotel")).toBeInTheDocument();
    });
    expect(screen.getByText(/I manage this pub/i)).toBeInTheDocument();
    expect(screen.getByText(/Royal Hotel Fitzroy/i)).toBeInTheDocument();
    expect(screen.getByText(/Exact name match/i)).toBeInTheDocument();
    expect(screen.queryByText(/google_place_id/i)).not.toBeInTheDocument();
  });

  it("approve existing calls the correct API", async () => {
    const user = userEvent.setup();
    approveOwnerClaimExisting.mockResolvedValue({
      data: { claim_request_id: "claim-1", status: "closed", message: "Approved" },
    });
    getOwnerClaim
      .mockResolvedValueOnce({ data: claimDetail })
      .mockResolvedValueOnce({
        data: { ...claimDetail, status: "closed" },
      });

    renderDetail();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Approve against this venue" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Approve against this venue" }));

    await waitFor(() => {
      expect(approveOwnerClaimExisting).toHaveBeenCalledWith("claim-1", {
        venue_id: "v-existing",
        admin_note: undefined,
      });
    });
  });

  it("reject calls the correct API", async () => {
    const user = userEvent.setup();
    rejectOwnerClaim.mockResolvedValue({
      data: { claim_request_id: "claim-1", status: "denied", message: "Rejected" },
    });
    getOwnerClaim
      .mockResolvedValueOnce({ data: claimDetail })
      .mockResolvedValueOnce({
        data: { ...claimDetail, status: "denied" },
      });

    renderDetail();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Reject" }));

    await waitFor(() => {
      expect(rejectOwnerClaim).toHaveBeenCalledWith("claim-1", {
        admin_note: undefined,
      });
    });
  });
});
