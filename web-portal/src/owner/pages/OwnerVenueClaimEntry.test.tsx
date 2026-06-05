import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenueClaimEntry } from "@/owner/pages/OwnerVenueClaimEntry";

const ownerVenueClaimRequest = vi.fn();
const referenceLocalities = vi.fn();

vi.mock("@/shared/lib/api", () => ({
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

describe("OwnerVenueClaimEntry", () => {
  beforeEach(() => {
    ownerVenueClaimRequest.mockReset();
    referenceLocalities.mockReset();
    referenceLocalities.mockResolvedValue(localities);
  });

  it("renders signup form and loads locality picker", async () => {
    render(<OwnerVenueClaimEntry />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Pub name/i)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Suburb \/ locality/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("option", { name: /Fitzroy/i })).toBeInTheDocument();
    });
    expect(screen.queryByText(/duplicate/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/google_place_id/i)).not.toBeInTheDocument();
  });

  it("submits pub details for admin review without duplicate selection UI", async () => {
    const user = userEvent.setup();
    ownerVenueClaimRequest.mockResolvedValue({
      data: {
        claim_request_id: "claim-1",
        status: "submitted",
        message:
          "Thanks — your venue details have been submitted for review. We'll check the details and let you know when you can manage the listing.",
      },
    });

    render(<OwnerVenueClaimEntry />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Pub name/i)).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText(/Pub name/i), "Royal Hotel");
    await user.type(screen.getByLabelText(/^Address$/i), "1 Main St");
    await user.selectOptions(screen.getByLabelText(/Suburb \/ locality/i), "loc-1");
    await user.type(
      screen.getByLabelText(/Tell us your role/i),
      "I am the licensee.",
    );
    await user.click(screen.getByRole("button", { name: "Submit for review" }));

    await waitFor(() => {
      expect(ownerVenueClaimRequest).toHaveBeenCalledWith({
        mode: "submit_new_or_claim",
        venue_name: "Royal Hotel",
        address_line_1: "1 Main St",
        locality_id: "loc-1",
        claimant_note: "I am the licensee.",
      });
    });
    expect(
      screen.getByRole("heading", { name: "Submitted for review" }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/This looks like your venue/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Request to claim/i)).not.toBeInTheDocument();
  });

  it("validates required fields before submit", async () => {
    const user = userEvent.setup();
    render(<OwnerVenueClaimEntry />);
    await waitFor(() => {
      expect(screen.getByLabelText(/Pub name/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Submit for review" }));

    expect(screen.getByText("Pub name is required.")).toBeInTheDocument();
    expect(screen.getByText("Address is required.")).toBeInTheDocument();
    expect(screen.getByText("Suburb / locality is required.")).toBeInTheDocument();
    expect(ownerVenueClaimRequest).not.toHaveBeenCalled();
  });
});
