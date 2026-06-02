import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ExternalLink } from "@/components/ExternalLink";
import { FounderVenueDetailPage } from "@/pages/FounderVenueDetailPage";

const getFounderVenueLead = vi.fn();
const patchFounderVenueLead = vi.fn();
const enrichFounderVenueLead = vi.fn();
const markLeadDoNotContact = vi.fn();

vi.mock("@/lib/api", () => ({
  getFounderVenueLead: (...args: unknown[]) => getFounderVenueLead(...args),
  patchFounderVenueLead: (...args: unknown[]) => patchFounderVenueLead(...args),
  enrichFounderVenueLead: (...args: unknown[]) => enrichFounderVenueLead(...args),
  markLeadDoNotContact: (...args: unknown[]) => markLeadDoNotContact(...args),
  formatApiError: (e: unknown) => String(e),
}));

const mockDetail = {
  lead: {
    id: "lead-1",
    name: "Detail Pub",
    suburb: "Richmond",
    state: "VIC",
    postcode: "3121",
    category: "Pub",
    phone: "0399999999",
    website: "https://example.com",
    email: "hello@example.com",
    instagram_url: null,
    facebook_url: null,
    confidence_score: 80,
    founder_fit_score: 90,
    enrichment_status: "imported",
    outreach_status: "not_contacted",
    contact_permission_status: "public_business_contact",
    created_at: null,
    updated_at: null,
    venue_id: null,
    normalized_name: null,
    address_line: null,
    country: "AU",
    latitude: null,
    longitude: null,
    contact_name: null,
    contact_role: null,
    source_summary: null,
    notes: "Initial note",
    founder_fit_breakdown: {
      components: { location: 20, category: 15 },
      positive_signals: ["Strong category match"],
      negative_signals: [],
      warnings: ["Imported data only"],
    },
    last_contacted_at: null,
    last_contact_channel: null,
    unsubscribe_at: null,
    unsubscribe_source: null,
    suppressed_at: null,
    suppression_reason: null,
  },
  sources: [],
  field_attributions: [],
  events: [],
};

function renderDetail() {
  return render(
    <MemoryRouter initialEntries={["/internal/founder-venues/lead-1"]}>
      <Routes>
        <Route path="/internal/founder-venues/:leadId" element={<FounderVenueDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("FounderVenueDetailPage", () => {
  beforeEach(() => {
    getFounderVenueLead.mockResolvedValue(mockDetail);
    patchFounderVenueLead.mockResolvedValue({
      ...mockDetail,
      lead: { ...mockDetail.lead, notes: "Updated note" },
    });
    enrichFounderVenueLead.mockResolvedValue({
      lead_id: "lead-1",
      fetched_urls: ["https://example.com"],
      candidates: [{ field_name: "email", raw_value: "a@b.com", normalized_value: "a@b.com", source_url: "https://example.com", confidence: 70, contact_safety_class: "public_business_contact" }],
      product_signals: ["menu"],
      warnings: [],
      errors: [],
      fields_promoted: [],
      enrichment_status: null,
      dry_run: true,
    });
    markLeadDoNotContact.mockResolvedValue({
      ...mockDetail,
      lead: { ...mockDetail.lead, outreach_status: "do_not_contact" },
    });
  });

  it("renders score breakdown", async () => {
    renderDetail();
    await waitFor(() => expect(screen.getByText("Detail Pub")).toBeInTheDocument());
    expect(screen.getByText("Score breakdown")).toBeInTheDocument();
    expect(screen.getByText("Strong category match")).toBeInTheDocument();
  });

  it("Save notes PATCHes notes field", async () => {
    const user = userEvent.setup();
    renderDetail();
    await waitFor(() => expect(screen.getByDisplayValue("Initial note")).toBeInTheDocument());
    const notes = screen.getByDisplayValue("Initial note");
    await user.clear(notes);
    await user.type(notes, "Updated note");
    await user.click(screen.getByRole("button", { name: "Save notes" }));
    await waitFor(() => expect(patchFounderVenueLead).toHaveBeenCalled());
    const [, body] = patchFounderVenueLead.mock.calls[0];
    expect(body).toEqual({ notes: "Updated note" });
  });

  it("enrich dry-run calls endpoint and shows candidates", async () => {
    const user = userEvent.setup();
    renderDetail();
    await waitFor(() => expect(screen.getByText("Website enrichment")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Dry-run" }));
    await waitFor(() => expect(enrichFounderVenueLead).toHaveBeenCalledWith("lead-1", true));
    expect(screen.getByText("Candidates")).toBeInTheDocument();
    expect(screen.getByText("a@b.com")).toBeInTheDocument();
  });

  it("mark do-not-contact calls correct endpoint", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "prompt").mockReturnValue("");
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderDetail();
    await waitFor(() => expect(screen.getByText("Detail Pub")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Mark DNC" }));
    await waitFor(() =>
      expect(markLeadDoNotContact).toHaveBeenCalledWith("lead-1", undefined),
    );
  });

  it("outreach panel renders on detail page", async () => {
    renderDetail();
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Outreach" })).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Mark called" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark emailed" })).toBeInTheDocument();
  });

  it("DNC warning is visible", async () => {
    renderDetail();
    await waitFor(() =>
      expect(
        screen.getByText(/removes this venue from normal outreach queues/i),
      ).toBeInTheDocument(),
    );
  });
});

describe("ExternalLink on detail", () => {
  it("renders with noreferrer", () => {
    render(<ExternalLink href="https://example.com">Open website</ExternalLink>);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("rel", "noreferrer");
    expect(link).toHaveAttribute("target", "_blank");
  });
});
