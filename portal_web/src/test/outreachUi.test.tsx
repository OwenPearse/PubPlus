import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { ContactLegend } from "@/components/ContactLegend";
import { ExternalLink } from "@/components/ExternalLink";
import { FounderVenuesListPage } from "@/pages/FounderVenuesListPage";
import { applyQuickFilter } from "@/lib/filters";
import { DEFAULT_LIST_FILTERS } from "@/lib/types";

const listFounderVenueLeads = vi.fn();
const getFounderVenueWorkspaceSummary = vi.fn();
const patchFounderVenueLead = vi.fn();

vi.mock("@/lib/api", () => ({
  listFounderVenueLeads: (...args: unknown[]) => listFounderVenueLeads(...args),
  getFounderVenueWorkspaceSummary: (...args: unknown[]) =>
    getFounderVenueWorkspaceSummary(...args),
  patchFounderVenueLead: (...args: unknown[]) => patchFounderVenueLead(...args),
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

describe("ContactLegend", () => {
  it("renders P/W/E/S legend", () => {
    render(<ContactLegend />);
    expect(screen.getByText(/= phone/)).toBeInTheDocument();
    expect(screen.getByText(/= website/)).toBeInTheDocument();
    expect(screen.getByText(/= email/)).toBeInTheDocument();
    expect(screen.getByText(/Instagram or Facebook/)).toBeInTheDocument();
  });
});

describe("ExternalLink", () => {
  it("uses safe target and rel", () => {
    render(<ExternalLink href="https://example.com">Open</ExternalLink>);
    const link = screen.getByRole("link", { name: "Open" });
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noreferrer");
  });
});

describe("quick filters", () => {
  it("VIC 80+ not contacted sets expected filters", () => {
    const next = applyQuickFilter("vic_80_not_contacted", DEFAULT_LIST_FILTERS);
    expect(next.state).toBe("VIC");
    expect(next.score_min).toBe("80");
    expect(next.outreach_status).toBe("not_contacted");
    expect(next.sort).toBe("founder_fit_score_desc");
  });
});

describe("call-sheet mode", () => {
  beforeEach(() => {
    getFounderVenueWorkspaceSummary.mockResolvedValue({
      total_leads: 1,
      vic_leads: 1,
      vic_score_80_plus: 1,
      not_contacted: 1,
      called: 0,
      emailed: 0,
      replied: 0,
      signed_up: 0,
      rejected: 0,
      do_not_contact: 0,
      needs_review: 0,
      missing_email: 0,
      missing_website: 0,
      missing_phone: 0,
      enriched: 0,
      imported: 1,
    });
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
          last_contacted_at: "2026-05-01T10:00:00Z",
          last_contact_channel: "phone",
          notes_summary: "",
          created_at: null,
          updated_at: null,
        },
      ],
      pagination: { limit: 50, offset: 0, count: 1, total: 1, has_more: false },
    });
    patchFounderVenueLead.mockResolvedValue({
      lead: {
        id: "lead-1",
        name: "Test Pub",
        outreach_status: "called",
        last_contacted_at: "2026-06-02T12:00:00Z",
        last_contact_channel: "phone",
        contact_permission_status: "public_business_contact",
        enrichment_status: "imported",
        founder_fit_score: 92,
        confidence_score: 80,
        founder_fit_breakdown: {},
      },
      sources: [],
      field_attributions: [],
      events: [],
    });
  });

  it("shows call-sheet columns when enabled", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <FounderVenuesListPage />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Test Pub")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Call sheet mode" }));
    expect(screen.getByText("Last contact")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark called" })).toBeInTheDocument();
  });
});
