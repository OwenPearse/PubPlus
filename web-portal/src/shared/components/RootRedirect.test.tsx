import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RootRedirect } from "@/shared/components/RootRedirect";

const getCurrentSession = vi.fn();
const resolvePortalRole = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  getCurrentSession: () => getCurrentSession(),
}));

vi.mock("@/shared/lib/portalRole", () => ({
  resolvePortalRole: () => resolvePortalRole(),
  getDefaultPathForRole: (result: { role: string }) => {
    if (result.role === "admin") return "/internal/founder-venues";
    if (result.role === "owner") return "/owner";
    return "/access";
  },
}));

function renderRedirect(initialEntry = "/") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/access" element={<div>Access</div>} />
        <Route path="/owner" element={<div>Owner</div>} />
        <Route path="/internal/founder-venues" element={<div>Admin</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RootRedirect", () => {
  beforeEach(() => {
    getCurrentSession.mockReset();
    resolvePortalRole.mockReset();
  });

  it("redirects logged-out users to /access", async () => {
    getCurrentSession.mockResolvedValue(null);
    renderRedirect();
    await waitFor(() => {
      expect(screen.getByText("Access")).toBeInTheDocument();
    });
  });

  it("redirects admin users to founder venues", async () => {
    getCurrentSession.mockResolvedValue({ user: { id: "a1" } });
    resolvePortalRole.mockResolvedValue({ role: "admin" });
    renderRedirect();
    await waitFor(() => {
      expect(screen.getByText("Admin")).toBeInTheDocument();
    });
  });

  it("redirects owner users to /owner", async () => {
    getCurrentSession.mockResolvedValue({ user: { id: "o1" } });
    resolvePortalRole.mockResolvedValue({
      role: "owner",
      probe: { next_step: "portal_home" },
    });
    renderRedirect();
    await waitFor(() => {
      expect(screen.getByText("Owner")).toBeInTheDocument();
    });
  });
});
