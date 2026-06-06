import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NoVenueAccessState } from "@/owner/components/NoVenueAccessState";

const ownerCurrentVenueClaim = vi.fn();

vi.mock("@/owner/pages/OwnerVenueClaimEntry", () => ({
  OwnerVenueClaimEntry: () => <div data-testid="claim-entry-form">Signup form</div>,
}));

vi.mock("@/shared/lib/api", () => ({
  ownerCurrentVenueClaim: () => ownerCurrentVenueClaim(),
  formatApiError: (err: unknown) => String(err),
}));

describe("NoVenueAccessState", () => {
  beforeEach(() => {
    ownerCurrentVenueClaim.mockReset();
  });

  it("renders signup form when owner has no claim", async () => {
    ownerCurrentVenueClaim.mockResolvedValue({ data: null });
    render(<NoVenueAccessState />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Tell us about your pub" })).toBeInTheDocument();
    });
    expect(screen.getByTestId("claim-entry-form")).toBeInTheDocument();
  });

  it("shows claim status instead of blank form when open claim exists", async () => {
    ownerCurrentVenueClaim.mockResolvedValue({
      data: {
        claim_request_id: "claim-1",
        claim_lifecycle_status: "submitted",
        submitted_venue_name: "Royal Hotel",
        submitted_address_line_1: "1 Main St",
        locality_name: "Fitzroy",
        submitted_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    });
    render(<NoVenueAccessState />);
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Your venue request is under review" }),
      ).toBeInTheDocument();
    });
    expect(screen.queryByTestId("claim-entry-form")).not.toBeInTheDocument();
    expect(screen.queryByText(/duplicate/i)).not.toBeInTheDocument();
  });
});
