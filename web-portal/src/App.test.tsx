import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "@/App";

vi.mock("@/owner/pages/PortalEntryPage", () => ({
  PortalEntryPage: () => <div data-testid="portal-entry-page">Portal entry</div>,
}));

vi.mock("@/owner/pages/AccessDeniedPage", () => ({
  AccessDeniedPage: () => <div data-testid="access-denied-page">Access denied</div>,
}));

vi.mock("@/admin/components/AdminRouteGuard", () => ({
  AdminRouteGuard: ({ children }: { children: ReactNode }) => (
    <div data-testid="admin-route-guard">
      <div data-testid="admin-route-children">{children}</div>
    </div>
  ),
}));

vi.mock("@/owner/components/OwnerRouteGuard", () => ({
  OwnerRouteGuard: ({ children }: { children: ReactNode }) => (
    <div data-testid="owner-route-guard">{children}</div>
  ),
}));

vi.mock("@/shared/components/RootRedirect", () => ({
  RootRedirect: () => <div data-testid="root-redirect">Root redirect</div>,
}));

vi.mock("@/admin/pages/FounderVenuesListPage", () => ({
  FounderVenuesListPage: () => <div>Founder list</div>,
}));

vi.mock("@/admin/pages/FounderVenueDetailPage", () => ({
  FounderVenueDetailPage: () => <div>Founder detail</div>,
}));

vi.mock("@/owner/pages/OwnerHomePlaceholder", () => ({
  OwnerHomePlaceholder: () => <div data-testid="owner-home">Owner home</div>,
}));

describe("App routing", () => {
  it("renders /access without route guards", () => {
    render(
      <MemoryRouter initialEntries={["/access"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("portal-entry-page")).toBeInTheDocument();
    expect(screen.queryByTestId("admin-route-guard")).not.toBeInTheDocument();
    expect(screen.queryByTestId("owner-route-guard")).not.toBeInTheDocument();
  });

  it("wraps internal routes in AdminRouteGuard", () => {
    render(
      <MemoryRouter initialEntries={["/internal/founder-venues"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("admin-route-guard")).toBeInTheDocument();
    expect(screen.getByTestId("admin-route-children")).toBeInTheDocument();
    expect(screen.getByText("Founder list")).toBeInTheDocument();
  });

  it("wraps owner routes in OwnerRouteGuard", () => {
    render(
      <MemoryRouter initialEntries={["/owner"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("owner-route-guard")).toBeInTheDocument();
    expect(screen.getByTestId("owner-home")).toBeInTheDocument();
  });
});
