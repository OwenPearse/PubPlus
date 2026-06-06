import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerClaimsListPage } from "@/admin/pages/OwnerClaimsListPage";

const listOwnerClaims = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  listOwnerClaims: (...args: unknown[]) => listOwnerClaims(...args),
  formatApiError: (err: unknown) => String(err),
}));

describe("OwnerClaimsListPage", () => {
  beforeEach(() => {
    listOwnerClaims.mockReset();
    listOwnerClaims.mockResolvedValue({
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
            duplicate_candidate_count: 2,
          },
        ],
        meta: { total: 1 },
      },
    });
  });

  it("renders submitted claims in the queue", async () => {
    render(
      <MemoryRouter>
        <OwnerClaimsListPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Royal Hotel")).toBeInTheDocument();
    });
    expect(screen.getByText(/owner@example.com/i)).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(listOwnerClaims).toHaveBeenCalledWith({ status: "submitted,under_review" });
    expect(screen.queryByText(/Add or claim a venue/i)).not.toBeInTheDocument();
  });
});
