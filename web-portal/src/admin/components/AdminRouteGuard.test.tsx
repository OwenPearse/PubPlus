import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminRouteGuard } from "@/admin/components/AdminRouteGuard";

const getCurrentSession = vi.fn();
const onAuthStateChange = vi.fn();
const internalAuthProbe = vi.fn();
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
  internalAuthProbe: () => internalAuthProbe(),
  formatApiError: (err: unknown) => String(err),
}));

vi.mock("@/shared/lib/env", () => ({
  hasSupabaseAuthConfig: () => true,
}));

vi.mock("@/shared/components/PortalShell", () => ({
  PortalShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="portal-shell">{children}</div>
  ),
}));

function renderGuard(initialEntry = "/internal/founder-venues") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/access" element={<div>Access page</div>} />
        <Route path="/access/denied" element={<div>Denied page</div>} />
        <Route
          path="/internal/*"
          element={
            <AdminRouteGuard>
              <div>Admin content</div>
            </AdminRouteGuard>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("AdminRouteGuard", () => {
  beforeEach(() => {
    getCurrentSession.mockReset();
    internalAuthProbe.mockReset();
    getCurrentSession.mockResolvedValue({ user: { email: "admin@example.com" } });
    internalAuthProbe.mockResolvedValue({ status: "ok", subject: "admin" });
  });

  it("redirects logged-out users to /access", async () => {
    getCurrentSession.mockResolvedValue(null);
    renderGuard();
    await waitFor(() => {
      expect(screen.getByText("Access page")).toBeInTheDocument();
    });
  });

  it("renders children when admin probe succeeds", async () => {
    renderGuard();
    await waitFor(() => {
      expect(screen.getByTestId("portal-shell")).toBeInTheDocument();
      expect(screen.getByText("Admin content")).toBeInTheDocument();
    });
  });

  it("redirects to access denied when admin probe fails", async () => {
    internalAuthProbe.mockRejectedValue({ code: "forbidden", message: "denied", status: 403 });
    renderGuard();
    await waitFor(() => {
      expect(screen.getByText("Denied page")).toBeInTheDocument();
    });
  });
});
