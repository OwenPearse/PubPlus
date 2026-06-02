import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FounderVenuesListPage } from "@/pages/FounderVenuesListPage";

const listFounderVenueLeads = vi.fn();

vi.mock("@/lib/api", () => ({
  listFounderVenueLeads: (...args: unknown[]) => listFounderVenueLeads(...args),
  formatApiError: (e: unknown) => String(e),
  enrichFounderVenueLead: vi.fn(),
  markLeadDoNotContact: vi.fn(),
}));

describe("FounderVenuesListPage", () => {
  beforeEach(() => {
    listFounderVenueLeads.mockResolvedValue({
      items: [
        {
          id: "lead-1",
          name: "Test Pub",
          suburb: "Fitzroy",
          state: "VIC",
          category: "Pub",
          phone: "0399999999",
          website: "https://example.com",
          email: null,
          instagram_url: null,
          facebook_url: null,
          confidence_score: 80,
          founder_fit_score: 92,
          enrichment_status: "imported",
          outreach_status: "not_contacted",
          contact_permission_status: "public_business_contact",
          created_at: null,
          updated_at: null,
        },
      ],
      pagination: { limit: 50, offset: 0, count: 1, total: 1, has_more: false },
    });
  });

  it("renders lead rows from mocked API", async () => {
    render(
      <MemoryRouter>
        <FounderVenuesListPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Test Pub")).toBeInTheDocument();
    });
    expect(screen.getByText("Fitzroy, VIC")).toBeInTheDocument();
    expect(screen.getByText("92")).toBeInTheDocument();
  });

  it("calls list API with default VIC filters", async () => {
    render(
      <MemoryRouter>
        <FounderVenuesListPage />
      </MemoryRouter>,
    );

    await waitFor(() => expect(listFounderVenueLeads).toHaveBeenCalled());
    const filters = listFounderVenueLeads.mock.calls[0][0];
    expect(filters.state).toBe("VIC");
    expect(filters.sort).toBe("founder_fit_score_desc");
    expect(filters.limit).toBe(50);
  });
});
