import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerPortalEntry } from "@/owner/pages/OwnerPortalEntry";

const ownerAuthProbe = vi.fn();
const ownerProvision = vi.fn();
const ownerVenueList = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerAuthProbe: () => ownerAuthProbe(),
  ownerProvision: () => ownerProvision(),
  ownerVenueList: () => ownerVenueList(),
  referenceLocalities: vi.fn().mockResolvedValue({ data: { localities: [] } }),
  formatApiError: (err: unknown) => String(err),
  isApiRequestError: () => false,
  parseApiValidationDetails: () => ({}),
}));

vi.mock("@/shared/lib/portalBrand", () => ({
  portalBrand: { productName: "Test Portal", logoSrc: "/logo.svg", logoAlt: "Logo" },
}));

vi.mock("@/shared/lib/env", () => ({
  getPortalSupportUrl: () => null,
}));

const baseProbe = {
  authenticated: true,
  owner_account_exists: true,
  owner_account_active: true,
  mfa_required: false,
  aal: "aal2",
  has_active_business_membership: false,
  has_approved_managed_venue_relationship: false,
  business_count: 0,
  venue_count: 0,
  owner_account_id: "oa-1",
};

function renderEntry(initialPath = "/owner") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/owner" element={<OwnerPortalEntry />} />
        <Route path="/owner/venues/:venueId" element={<div data-testid="venue-hub" />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OwnerPortalEntry", () => {
  beforeEach(() => {
    ownerAuthProbe.mockReset();
    ownerProvision.mockReset();
    ownerVenueList.mockReset();
  });

  it("shows signup form immediately for awaiting membership state", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: { ...baseProbe, next_step: "owner_waiting_for_membership" },
    });
    renderEntry();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Tell us about your pub" })).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Pub name/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add or claim a venue" })).not.toBeInTheDocument();
    expect(screen.queryByText(/Awaiting business access/i)).not.toBeInTheDocument();
    expect(ownerVenueList).not.toHaveBeenCalled();
  });

  it("shows signup form immediately for awaiting venue access state", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...baseProbe,
        business_count: 1,
        has_active_business_membership: true,
        next_step: "owner_waiting_for_venue_access",
      },
    });
    renderEntry();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Tell us about your pub" })).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Pub name/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add or claim a venue" })).not.toBeInTheDocument();
    expect(ownerVenueList).not.toHaveBeenCalled();
  });

  it("calls owner venue list only for portal_home", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...baseProbe,
        business_count: 1,
        venue_count: 1,
        has_active_business_membership: true,
        has_approved_managed_venue_relationship: true,
        next_step: "portal_home",
      },
    });
    ownerVenueList.mockResolvedValue({
      data: { venues: [], meta: { total: 0, default_venue_id: null } },
    });
    renderEntry();
    await waitFor(() => {
      expect(ownerVenueList).toHaveBeenCalledTimes(1);
    });
  });

  it("redirects when one venue and default_venue_id", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...baseProbe,
        business_count: 1,
        venue_count: 1,
        has_active_business_membership: true,
        has_approved_managed_venue_relationship: true,
        next_step: "portal_home",
      },
    });
    ownerVenueList.mockResolvedValue({
      data: {
        venues: [
          {
            venue_id: "v-single",
            display_name: "Solo Pub",
            locality_name: "Carlton",
            state_code: "VIC",
            relationship_lifecycle: "approved",
            onboarding_status: "not_started",
            pending_proposal_count: 0,
            completeness_percent: 0,
            required_basics_complete: false,
          },
        ],
        meta: { total: 1, default_venue_id: "v-single" },
      },
    });
    renderEntry();
    await waitFor(() => {
      expect(screen.getByTestId("venue-hub")).toBeInTheDocument();
    });
  });

  it("shows picker when multiple venues", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...baseProbe,
        business_count: 1,
        venue_count: 2,
        has_active_business_membership: true,
        has_approved_managed_venue_relationship: true,
        next_step: "portal_home",
      },
    });
    ownerVenueList.mockResolvedValue({
      data: {
        venues: [
          {
            venue_id: "v-a",
            display_name: "Pub A",
            locality_name: "Fitzroy",
            state_code: "VIC",
            relationship_lifecycle: "approved",
            onboarding_status: "in_progress",
            pending_proposal_count: 0,
            completeness_percent: 25,
            required_basics_complete: false,
          },
          {
            venue_id: "v-b",
            display_name: "Pub B",
            locality_name: "Brunswick",
            state_code: "VIC",
            relationship_lifecycle: "approved",
            onboarding_status: "complete",
            pending_proposal_count: 1,
            completeness_percent: 100,
            required_basics_complete: true,
          },
        ],
        meta: { total: 2, default_venue_id: null },
      },
    });
    renderEntry();
    await waitFor(() => {
      expect(screen.getByText("Pub A")).toBeInTheDocument();
      expect(screen.getByText("Pub B")).toBeInTheDocument();
    });
    expect(screen.getByText(/Choose a venue/i)).toBeInTheDocument();
  });

  it("shows empty state when list is empty", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...baseProbe,
        next_step: "portal_home",
        has_active_business_membership: true,
        has_approved_managed_venue_relationship: true,
      },
    });
    ownerVenueList.mockResolvedValue({
      data: { venues: [], meta: { total: 0, default_venue_id: null } },
    });
    renderEntry();
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "No venues assigned yet" })).toBeInTheDocument();
    });
  });

  it("shows error state when list fails", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...baseProbe,
        next_step: "portal_home",
        has_active_business_membership: true,
        has_approved_managed_venue_relationship: true,
      },
    });
    ownerVenueList.mockRejectedValue(new Error("network down"));
    renderEntry();
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("network down");
    });
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("shows optional MFA prompt at AAL1 on membership empty state", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...baseProbe,
        next_step: "owner_waiting_for_membership",
        aal: "aal1",
        mfa_required: false,
        mfa_enabled: false,
      },
    });
    renderEntry();
    await waitFor(() => {
      expect(screen.getByText(/Protect your account with two-step verification/i)).toBeInTheDocument();
    });
  });
});
