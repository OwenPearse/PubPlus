import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerRouteGuard } from "@/owner/components/OwnerRouteGuard";

const waitForSession = vi.fn();
const onAuthStateChange = vi.fn();
const ownerAuthProbe = vi.fn();
const signOut = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  waitForSession: () => waitForSession(),
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
  mfa_required: false,
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
  const ownerSession = { user: { id: "owner-1", email: "owner@example.com" } };

  beforeEach(() => {
    waitForSession.mockReset();
    ownerAuthProbe.mockReset();
    onAuthStateChange.mockReset();
    waitForSession.mockResolvedValue(ownerSession);
    onAuthStateChange.mockImplementation((cb: (s: unknown) => void) => {
      cb(ownerSession);
      return vi.fn();
    });
    ownerAuthProbe.mockResolvedValue({ status: 200, body: portalHomeProbe });
  });

  it("redirects logged-out users to /access", async () => {
    waitForSession.mockResolvedValue(null);
    onAuthStateChange.mockImplementation((cb: (s: unknown) => void) => {
      cb(null);
      return vi.fn();
    });
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

  it("allows owner shell when probe is AAL1 with legacy enroll_mfa next_step", async () => {
    ownerAuthProbe.mockResolvedValue({
      status: 200,
      body: {
        ...portalHomeProbe,
        next_step: "enroll_mfa",
        aal: "aal1",
        mfa_required: false,
        mfa_enabled: false,
      },
    });
    renderGuard();
    await waitFor(() => {
      expect(screen.getByTestId("owner-shell")).toBeInTheDocument();
      expect(screen.getByText("Owner content")).toBeInTheDocument();
    });
  });

  it("redirects to /access with session_expired when probe returns unauthorized", async () => {
    ownerAuthProbe.mockRejectedValue({ code: "unauthorized", status: 401, message: "expired" });
    renderGuard();
    await waitFor(() => {
      expect(screen.getByText("Access page")).toBeInTheDocument();
    });
  });

  it("redirects to /access/denied when probe fails with a non-auth error", async () => {
    ownerAuthProbe.mockRejectedValue({ code: "network_error", status: null, message: "offline" });
    renderGuard();
    await waitFor(() => {
      expect(screen.getByText("Denied page")).toBeInTheDocument();
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
