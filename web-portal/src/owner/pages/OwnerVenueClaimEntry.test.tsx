import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenueClaimEntry } from "@/owner/pages/OwnerVenueClaimEntry";

const ownerVenueClaimCandidates = vi.fn();
const ownerVenueClaimRequest = vi.fn();
const referenceLocalities = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerVenueClaimCandidates: (...args: unknown[]) => ownerVenueClaimCandidates(...args),
  ownerVenueClaimRequest: (...args: unknown[]) => ownerVenueClaimRequest(...args),
  referenceLocalities: () => referenceLocalities(),
  formatApiError: (err: unknown) => String(err),
  isApiRequestError: () => false,
  parseApiValidationDetails: () => ({}),
}));

const localities = {
  data: {
    localities: [
      {
        id: "loc-1",
        name: "Fitzroy",
        state: "VIC",
        geographic_region_id: "reg-1",
        geographic_region_name: "Melbourne",
      },
    ],
  },
};

const candidate = {
  venue_id: "v-1",
  display_name: "Royal Hotel",
  locality_name: "Fitzroy",
  state_code: "VIC",
  address_line_1: "1 Main St",
  match_reason: "Exact name match; Same locality",
  match_score: 95,
};

describe("OwnerVenueClaimEntry", () => {
  beforeEach(() => {
    ownerVenueClaimCandidates.mockReset();
    ownerVenueClaimRequest.mockReset();
    referenceLocalities.mockReset();
    referenceLocalities.mockResolvedValue(localities);
  });

  it("renders claim form and loads locality picker", async () => {
    render(<OwnerVenueClaimEntry />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Venue name/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Suburb \/ locality/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("option", { name: /Fitzroy/i })).toBeInTheDocument();
    });
  });

  it("displays likely match and claims existing venue", async () => {
    const user = userEvent.setup();
    ownerVenueClaimCandidates.mockResolvedValue({
      data: {
        candidates: [candidate],
        best_match: candidate,
        has_good_match: true,
      },
    });
    ownerVenueClaimRequest.mockResolvedValue({
      data: {
        claim_request_id: "claim-1",
        status: "submitted",
        message: "Claim request submitted.",
      },
    });

    render(<OwnerVenueClaimEntry />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Venue name/i)).toBeInTheDocument();
    });
    await user.type(screen.getByLabelText(/Venue name/i), "Royal Hotel");
    await user.click(screen.getByRole("button", { name: "Add or claim a venue" }));

    await waitFor(() => {
      expect(screen.getByText(/This looks like your venue/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/google_place_id/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Request to claim this listing" }));
    await waitFor(() => {
      expect(ownerVenueClaimRequest).toHaveBeenCalledWith({
        mode: "claim_existing",
        venue_id: "v-1",
        claimant_note: undefined,
      });
    });
    expect(
      screen.getByRole("heading", { name: "Claim request submitted" }),
    ).toBeInTheDocument();
  });

  it("submits new venue when no good match", async () => {
    const user = userEvent.setup();
    ownerVenueClaimCandidates.mockResolvedValue({
      data: { candidates: [], best_match: null, has_good_match: false },
    });
    ownerVenueClaimRequest.mockResolvedValue({
      data: {
        claim_request_id: "claim-2",
        status: "submitted",
        message: "Claim request submitted.",
      },
    });

    render(<OwnerVenueClaimEntry />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Venue name/i)).toBeInTheDocument();
    });
    await user.type(screen.getByLabelText(/Venue name/i), "Brand New Pub");
    await user.click(screen.getByRole("button", { name: "Add or claim a venue" }));

    await waitFor(() => {
      expect(screen.getByText(/couldn't find a matching listing/i)).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "Submit as a new venue for review" }));

    await waitFor(() => {
      expect(ownerVenueClaimRequest).toHaveBeenCalledWith({
        mode: "submit_new",
        venue_name: "Brand New Pub",
        address_line_1: undefined,
        locality_id: undefined,
        claimant_note: undefined,
      });
    });
  });
});
