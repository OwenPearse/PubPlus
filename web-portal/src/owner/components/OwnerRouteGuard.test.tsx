import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerRouteGuard } from "@/owner/components/OwnerRouteGuard";

const getCurrentSession = vi.fn();
const onAuthStateChange = vi.fn();
const ownerAuthProbe = vi.fn();
const signOut = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  getCurrentSession: () => getCurrentSession(),
  onAuthStateChange: (cb: (s: unknown) => void) => {
    onAuthStateChange(cb);
    return vi.fn();
  },
  signOut: () => signOut(),
}));

vi.mock("@/shared/lib/api", () => ({
  ownerAuthProbe: () => ownerAuthProbe(),
  formatApiError: (err: unknown) =>
    err && typeof err === "object" && "message" in err
      ? String((err as { message: string }).message)
      : "error",
  isApiRequestError: (err: unknown) =>
    Boolean(err && typeof err === "object" && "code" in err),
}));

vi.mock("@/shared/lib/env", () => ({
  hasSupabaseAuthConfig: () => true,
}));

vi.mock("@/shared/components/PortalShell", () => ({
  PortalShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="owner-shell">{children}</div>
  ),
}));

const portalHomeProbe = {
  authenticated: true,
  owner_account_exists: true,
  owner_account_active: true,
  mfa_required: true,
  aal: "aal2",
  has_active_business_membership: true,
  has_approved_managed_venue_relationship: true,
  business_count: 1,
  venue_count: 1,
  owner_account_id: "oa-1",
  next_step: "portal_home",
};

function renderGuard() {
  return render(
    <MemoryRouter initialEntries={["/owner"]}>
      <Routes>
        <Route path="/access" element={<div>Access page</div>} />
        <Route path="/access/denied" element={<div>Denied page</div>} />
        <Route
          path="/owner/*"
          element={
            <OwnerRouteGuard>
              <div>Owner content</div>
            </OwnerRouteGuard>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OwnerRouteGuard", () => {
  beforeEach(() => {
    getCurrentSession.mockReset();
    ownerAuthProbe.mockReset();
    getCurrentSession.mockResolvedValue({ user: { email: "owner@example.com" } });
    ownerAuthProbe.mockResolvedValue({ status: 200, body: portalHomeProbe });
  });

  it("redirects logged-out users to /access", async () => {
    getCurrentSession.mockResolvedValue(null);
    renderGuard();
    await waitFor(() => {
      expect(screen.getByText("Access page")).toBeInTheDocument();
    });
  });

  it("renders children when owner probe allows portal_home", async () => {
    renderGuard();
    await waitFor(() => {
      expect(screen.getByTestId("owner-shell")).toBeInTheDocument();
      expect(screen.getByText("Owner content")).toBeInTheDocument();
    });
  });

  it("redirects to /access when MFA enrollment is required", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: { ...portalHomeProbe, next_step: "enroll_mfa", aal: "aal1" },
    });
    renderGuard();
    await waitFor(() => {
      expect(screen.getByText("Access page")).toBeInTheDocument();
    });
  });

  it("redirects to /access when owner is not provisioned", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 403,
      body: {
        ...portalHomeProbe,
        owner_account_exists: false,
        next_step: "complete_owner_provisioning",
        error: { code: "owner_not_provisioned", message: "not provisioned" },
      },
    });
    renderGuard();
    await waitFor(() => {
      expect(screen.getByText("Access page")).toBeInTheDocument();
    });
  });
});
