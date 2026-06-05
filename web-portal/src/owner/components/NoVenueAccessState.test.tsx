import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NoVenueAccessState } from "@/owner/components/NoVenueAccessState";

vi.mock("@/owner/pages/OwnerVenueClaimEntry", () => ({
  OwnerVenueClaimEntry: () => <div data-testid="claim-entry-form">Claim form</div>,
}));

vi.mock("@/shared/lib/api", () => ({
  referenceLocalities: vi.fn().mockResolvedValue({ data: { localities: [] } }),
  formatApiError: (err: unknown) => String(err),
  isApiRequestError: () => false,
  parseApiValidationDetails: () => ({}),
}));

describe("NoVenueAccessState", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders add or claim copy for membership waiting state", () => {
    render(<NoVenueAccessState variant="membership" businessCount={0} />);
    expect(screen.getByRole("heading", { name: "Add or claim your venue" })).toBeInTheDocument();
    expect(screen.getByText(/Tell us which pub you manage/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add or claim a venue" })).toBeInTheDocument();
  });

  it("renders add or claim copy for venue waiting state", () => {
    render(<NoVenueAccessState variant="venue" businessCount={1} venueCount={0} />);
    expect(screen.getByRole("heading", { name: "Add or claim your venue" })).toBeInTheDocument();
    expect(screen.getByText(/Businesses: 1/)).toBeInTheDocument();
    expect(screen.getByText(/Approved venues: 0/)).toBeInTheDocument();
  });

  it("shows claim form after CTA click", async () => {
    const user = userEvent.setup();
    render(<NoVenueAccessState variant="membership" businessCount={0} />);
    await user.click(screen.getByRole("button", { name: "Add or claim a venue" }));
    expect(screen.getByTestId("claim-entry-form")).toBeInTheDocument();
  });
});
