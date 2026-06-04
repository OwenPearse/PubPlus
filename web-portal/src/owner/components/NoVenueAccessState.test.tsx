import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { NoVenueAccessState } from "@/owner/components/NoVenueAccessState";

describe("NoVenueAccessState", () => {
  it("renders awaiting membership copy", () => {
    render(<NoVenueAccessState variant="membership" businessCount={0} />);
    expect(screen.getByRole("heading", { name: "Awaiting business access" })).toBeInTheDocument();
    expect(screen.getByText(/not linked to a business/i)).toBeInTheDocument();
  });

  it("renders awaiting venue access with counts", () => {
    render(<NoVenueAccessState variant="venue" businessCount={1} venueCount={0} />);
    expect(screen.getByRole("heading", { name: "Awaiting venue access" })).toBeInTheDocument();
    expect(screen.getByText(/Businesses: 1/)).toBeInTheDocument();
    expect(screen.getByText(/Approved venues: 0/)).toBeInTheDocument();
  });
});
