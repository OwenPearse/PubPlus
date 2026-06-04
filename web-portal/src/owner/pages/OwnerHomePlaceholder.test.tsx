import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerHomePlaceholder } from "@/owner/pages/OwnerHomePlaceholder";

const ownerAuthProbe = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerAuthProbe: () => ownerAuthProbe(),
  ownerProvision: vi.fn(),
  formatApiError: (err: unknown) => String(err),
}));

vi.mock("@/shared/lib/portalBrand", () => ({
  portalBrand: { productName: "Test Portal", logoSrc: "/logo.svg", logoAlt: "Logo" },
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

describe("OwnerHomePlaceholder", () => {
  beforeEach(() => {
    ownerAuthProbe.mockReset();
  });

  it("shows awaiting membership state", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: { ...baseProbe, next_step: "owner_waiting_for_membership" },
    });
    render(
      <MemoryRouter>
        <OwnerHomePlaceholder />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Awaiting business access" })).toBeInTheDocument();
    });
  });

  it("shows awaiting venue access state", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...baseProbe,
        business_count: 1,
        has_active_business_membership: true,
        next_step: "owner_waiting_for_venue_access",
      },
    });
    render(
      <MemoryRouter>
        <OwnerHomePlaceholder />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Awaiting venue access" })).toBeInTheDocument();
    });
  });

  it("shows portal home placeholder", async () => {
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
    render(
      <MemoryRouter>
        <OwnerHomePlaceholder />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText(/venue management features will appear here/i)).toBeInTheDocument();
    });
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
    render(
      <MemoryRouter>
        <OwnerHomePlaceholder />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText(/Protect your account with two-step verification/i)).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Set up 2FA" })).toHaveAttribute("href", "/access");
    });
  });
});
