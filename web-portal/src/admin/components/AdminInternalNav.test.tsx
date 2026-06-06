import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminInternalNav } from "@/admin/components/AdminInternalNav";

const getOwnerClaimsSummary = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  getOwnerClaimsSummary: () => getOwnerClaimsSummary(),
}));

describe("AdminInternalNav", () => {
  beforeEach(() => {
    getOwnerClaimsSummary.mockReset();
    getOwnerClaimsSummary.mockResolvedValue({
      data: { open_count: 4, submitted_count: 3, under_review_count: 1 },
    });
  });

  it("renders founder venues and owner claims links", async () => {
    render(
      <MemoryRouter initialEntries={["/internal/founder-venues"]}>
        <AdminInternalNav />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: /Founder venues/i })).toHaveAttribute(
      "href",
      "/internal/founder-venues",
    );
    expect(screen.getByRole("link", { name: /Owner claims/i })).toHaveAttribute(
      "href",
      "/internal/owner-claims",
    );
  });

  it("shows open claim count badge when count is positive", async () => {
    render(
      <MemoryRouter initialEntries={["/internal/founder-venues"]}>
        <AdminInternalNav />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText("4")).toBeInTheDocument();
    });
  });
});
