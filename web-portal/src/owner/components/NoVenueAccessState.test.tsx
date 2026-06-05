import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NoVenueAccessState } from "@/owner/components/NoVenueAccessState";

vi.mock("@/owner/pages/OwnerVenueClaimEntry", () => ({
  OwnerVenueClaimEntry: () => <div data-testid="claim-entry-form">Signup form</div>,
}));

describe("NoVenueAccessState", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders signup heading and form immediately without intermediate CTA", () => {
    render(<NoVenueAccessState />);
    expect(screen.getByRole("heading", { name: "Tell us about your pub" })).toBeInTheDocument();
    expect(
      screen.getByText(/Add the basic details for the pub you manage/i),
    ).toBeInTheDocument();
    expect(screen.getByTestId("claim-entry-form")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add or claim a venue" })).not.toBeInTheDocument();
    expect(screen.queryByText(/Awaiting business access/i)).not.toBeInTheDocument();
  });
});
