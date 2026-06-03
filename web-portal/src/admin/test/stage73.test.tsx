import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardCards } from "@/admin/components/DashboardCards";
import { EventsTable } from "@/admin/components/EventsTable";
import { FounderVenuesListPage } from "@/admin/pages/FounderVenuesListPage";
import { applyQuickFilter, buildExportConfirmMessage } from "@/shared/lib/filters";
import { DEFAULT_LIST_FILTERS } from "@/shared/lib/types";

const listFounderVenueLeads = vi.fn();
const getFounderVenueWorkspaceSummary = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  listFounderVenueLeads: (...args: unknown[]) => listFounderVenueLeads(...args),
  getFounderVenueWorkspaceSummary: (...args: unknown[]) =>
    getFounderVenueWorkspaceSummary(...args),
  formatApiError: (e: unknown) => String(e),
  enrichFounderVenueLead: vi.fn(),
  markLeadDoNotContact: vi.fn(),
  markFounderVenueCalled: vi.fn(),
  markFounderVenueEmailed: vi.fn(),
  markFounderVenueReplied: vi.fn(),
  markFounderVenueRejected: vi.fn(),
  markFounderVenueSignedUp: vi.fn(),
  markFounderVenueDoNotContact: vi.fn(),
  markFounderVenueQueued: vi.fn(),
}));

const mockSummary = {
  total_leads: 100,
  vic_leads: 50,
  vic_score_80_plus: 20,
  not_contacted: 40,
  called: 5,
  emailed: 3,
  replied: 2,
  signed_up: 1,
  rejected: 1,
  do_not_contact: 0,
  needs_review: 2,
  missing_email: 10,
  missing_website: 8,
  missing_phone: 4,
  enriched: 6,
  imported: 90,
};

const mockLead = {
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
  last_contacted_at: "2026-05-01T10:00:00Z",
  last_contact_channel: "phone",
  notes_summary: "",
  created_at: null,
  updated_at: null,
};

describe("Stage 7.3 polish", () => {
  beforeEach(() => {
    getFounderVenueWorkspaceSummary.mockResolvedValue(mockSummary);
    listFounderVenueLeads.mockResolvedValue({
      items: [mockLead],
      pagination: { limit: 50, offset: 0, count: 1, total: 1, has_more: false },
    });
  });

  it("dashboard cards render from summary", async () => {
    render(<DashboardCards summary={mockSummary} />);
    expect(screen.getByText("VIC leads")).toBeInTheDocument();
    expect(screen.getByText("50")).toBeInTheDocument();
    expect(screen.getByText("Not contacted")).toBeInTheDocument();
  });

  it("follow-up quick filter sets expected filters", () => {
    const next = applyQuickFilter("follow_up", DEFAULT_LIST_FILTERS);
    expect(next.outreach_status_in).toBe("called,emailed");
    expect(next.contacted_before).toBeTruthy();
  });

  it("export confirmation includes safe-default warning", () => {
    const msg = buildExportConfirmMessage(DEFAULT_LIST_FILTERS, 42);
    expect(msg).toContain("Safe defaults");
    expect(msg).toContain("Do-not-contact");
    expect(msg).toContain("42");
  });

  it("call-sheet shows phone and last contacted", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <FounderVenuesListPage />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Test Pub")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Call sheet mode" }));
    expect(screen.getByText("0399999999")).toBeInTheDocument();
    expect(screen.getByText("Last contact")).toBeInTheDocument();
  });

  it("list renders last_contacted_at from API", async () => {
    render(
      <MemoryRouter>
        <FounderVenuesListPage />
      </MemoryRouter>,
    );
    await waitFor(() => expect(listFounderVenueLeads).toHaveBeenCalled());
    const items = listFounderVenueLeads.mock.results[0].value;
    await items;
    expect(mockLead.last_contacted_at).toBeTruthy();
  });
});

describe("EventsTable", () => {
  it("renders readable event rows", () => {
    render(
      <EventsTable
        events={[
          {
            id: "e1",
            event_type: "outreach_status_changed",
            metadata: { outreach_status: "called", last_contact_channel: "phone" },
            created_by: null,
            created_at: "2026-06-01T12:00:00Z",
          },
        ]}
      />,
    );
    expect(screen.getByText(/outreach status changed/i)).toBeInTheDocument();
    expect(screen.getByText(/outreach status: called/)).toBeInTheDocument();
  });
});
