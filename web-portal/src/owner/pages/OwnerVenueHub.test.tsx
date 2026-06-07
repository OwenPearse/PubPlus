import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenueHub } from "@/owner/pages/OwnerVenueHub";

const ownerVenueDetail = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerVenueDetail: (id: string) => ownerVenueDetail(id),
  formatApiError: (err: unknown) => String(err),
  isApiRequestError: (err: unknown) =>
    Boolean(err && typeof err === "object" && "code" in err),
}));

function baseDetail(overrides: Record<string, unknown> = {}) {
  return {
    venue_id: "v-1",
    display_name: "Harbour Hotel",
    listing: { discovery_eligibility_status: "eligible", operational_status: "open" },
    relationship: {
      lifecycle: "approved",
      business_id: "b-1",
      capabilities: [],
    },
    published: {
      profile: { display_name: "Harbour Hotel", slug: "harbour", operational_status: "open" },
      location: {
        locality_id: "loc-1",
        locality_name: "Docklands",
        state_code: "VIC",
        address_line_1: "1 Pier St",
        address_line_2: null,
        postal_code: "3008",
        country_code: "AU",
        latitude: null,
        longitude: null,
      },
      descriptions: { short_description: "Waterfront.", long_description: null },
      hours: { uncertainty_level: "resolved_confident", regular: [], exceptions: [] },
      contact: { supported: false, phone: null, email: null, website: null },
    },
    draft: {
      proposal_id: null,
      lifecycle_status: null,
      last_saved_at: null,
      payload_preview: { display_name: null, address_line_1: null, locality_id: null },
      core_details_payload: null,
    },
    pending_review: {
      proposal_id: null,
      lifecycle_status: null,
      submitted_at: null,
      reviewed_at: null,
      review_outcome: null,
    },
    completeness: {
      percent: 40,
      required_basics_complete: false,
      sections: [
        {
          key: "core_details",
          label: "Pub details",
          status: "partial",
          required: true,
          available: true,
        },
        {
          key: "features",
          label: "Features",
          status: "missing",
          required: false,
          available: true,
        },
        {
          key: "events",
          label: "Events",
          status: "deferred",
          required: false,
          available: false,
        },
        {
          key: "photos",
          label: "Photos",
          status: "deferred",
          required: false,
          available: false,
        },
      ],
    },
    sections_available: {
      core_details: true,
      events: false,
      meal_specials: false,
      tap_list: false,
      features: true,
      photos: false,
    },
    ...overrides,
  };
}

describe("OwnerVenueHub", () => {
  beforeEach(() => {
    ownerVenueDetail.mockReset();
  });

  it("loads venue detail and shows checklist", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1"]}>
        <Routes>
          <Route path="/owner/venues/:venueId" element={<OwnerVenueHub />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Harbour Hotel" })).toBeInTheDocument();
    });
    expect(screen.getByText(/Docklands, VIC/)).toBeInTheDocument();
    expect(screen.getByText("40%")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Edit pub details" })).toHaveAttribute(
      "href",
      "/owner/venues/v-1/basics",
    );
    expect(screen.getByRole("link", { name: "Edit features" })).toHaveAttribute(
      "href",
      "/owner/venues/v-1/features",
    );
  });

  it("keeps deferred sections disabled", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1"]}>
        <Routes>
          <Route path="/owner/venues/:venueId" element={<OwnerVenueHub />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("link", { name: "Edit features" })).toBeInTheDocument();
    });
    expect(screen.getAllByText(/Coming later/i).length).toBeGreaterThan(0);
    expect(screen.queryByRole("link", { name: /meal specials/i })).not.toBeInTheDocument();
  });

  it("shows deferred sections as disabled", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1"]}>
        <Routes>
          <Route path="/owner/venues/:venueId" element={<OwnerVenueHub />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getAllByText(/Coming later/i).length).toBeGreaterThan(0);
    });
  });

  it("shows submitted for review message", async () => {
    ownerVenueDetail.mockResolvedValue({
      data: baseDetail({
        pending_review: {
          proposal_id: "p-1",
          lifecycle_status: "in_review",
          submitted_at: "2026-01-01T00:00:00Z",
          reviewed_at: null,
          review_outcome: null,
        },
      }),
    });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-1"]}>
        <Routes>
          <Route path="/owner/venues/:venueId" element={<OwnerVenueHub />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(
        screen.getByText(/Name\/address change pending review/i),
      ).toBeInTheDocument();
    });
  });

  it("does not render google_place_id or contact inputs", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    const { container } = render(
      <MemoryRouter initialEntries={["/owner/venues/v-1"]}>
        <Routes>
          <Route path="/owner/venues/:venueId" element={<OwnerVenueHub />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Harbour Hotel" })).toBeInTheDocument();
    });
    expect(container.textContent).not.toMatch(/google_place_id/i);
    expect(screen.queryByLabelText(/phone/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/website/i)).not.toBeInTheDocument();
  });

  it("shows not found state", async () => {
    ownerVenueDetail.mockRejectedValue({ code: "not_found", message: "missing", status: 404 });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-missing"]}>
        <Routes>
          <Route path="/owner/venues/:venueId" element={<OwnerVenueHub />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Venue not found" })).toBeInTheDocument();
    });
  });

  it("shows forbidden state", async () => {
    ownerVenueDetail.mockRejectedValue({ code: "forbidden", message: "denied", status: 403 });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-other"]}>
        <Routes>
          <Route path="/owner/venues/:venueId" element={<OwnerVenueHub />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Access denied" })).toBeInTheDocument();
    });
  });

  it("renders sparse approve-new venue without crashing", async () => {
    ownerVenueDetail.mockResolvedValue({
      data: baseDetail({
        display_name: "Sparse Pub",
        published: {
          profile: {
            display_name: "Sparse Pub",
            slug: "sparse-pub",
            operational_status: null,
          },
          location: {
            locality_id: "loc-1",
            locality_name: "Carlton",
            state_code: "VIC",
            address_line_1: "1 Sparse St",
            address_line_2: null,
            postal_code: null,
            country_code: "AU",
            latitude: null,
            longitude: null,
          },
          descriptions: { short_description: null, long_description: null },
          hours: { uncertainty_level: "resolved_confident", regular: [], exceptions: [] },
          contact: { supported: false, phone: null, email: null, website: null },
        },
      }),
    });
    render(
      <MemoryRouter initialEntries={["/owner/venues/v-sparse"]}>
        <Routes>
          <Route path="/owner/venues/:venueId" element={<OwnerVenueHub />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Sparse Pub" })).toBeInTheDocument();
    });
    expect(screen.getByText(/Carlton, VIC/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Edit pub details" })).toBeInTheDocument();
  });
});
