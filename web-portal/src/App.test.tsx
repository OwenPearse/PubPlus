import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "@/App";

vi.mock("@/owner/pages/PortalEntryPage", () => ({
  PortalEntryPage: () => <div data-testid="portal-entry-page">Portal entry</div>,
}));

vi.mock("@/shared/components/AuthGate", () => ({
  AuthGate: ({ children }: { children: ReactNode }) => (
    <div data-testid="auth-gate">{children}</div>
  ),
}));

vi.mock("@/admin/pages/FounderVenuesListPage", () => ({
  FounderVenuesListPage: () => <div>Founder list</div>,
}));

vi.mock("@/admin/pages/FounderVenueDetailPage", () => ({
  FounderVenueDetailPage: () => <div>Founder detail</div>,
}));

describe("App routing", () => {
  it("renders /access without AuthGate", () => {
    render(
      <MemoryRouter initialEntries={["/access"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("portal-entry-page")).toBeInTheDocument();
    expect(screen.queryByTestId("auth-gate")).not.toBeInTheDocument();
  });

  it("wraps internal routes in AuthGate", () => {
    render(
      <MemoryRouter initialEntries={["/internal/founder-venues"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("auth-gate")).toBeInTheDocument();
    expect(screen.queryByTestId("portal-entry-page")).not.toBeInTheDocument();
  });
});
