import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AccessDeniedPage } from "@/owner/pages/AccessDeniedPage";

const signOut = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  signOut: () => signOut(),
}));

vi.mock("@/shared/lib/portalBrand", () => ({
  portalBrand: {
    productName: "Test Venue Portal",
    logoSrc: "/brand/placeholder-mark.svg",
    logoAlt: "Portal",
  },
}));

describe("AccessDeniedPage", () => {
  it("renders placeholder brand and default denied copy", () => {
    render(
      <MemoryRouter>
        <AccessDeniedPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Test Venue Portal" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Access not available" })).toBeInTheDocument();
    expect(screen.getByText(/not available for your account/i)).toBeInTheDocument();
  });

  it("shows custom message from navigation state", () => {
    render(
      <MemoryRouter
        initialEntries={[{ pathname: "/access/denied", state: { message: "Custom denied reason" } }]}
      >
        <Routes>
          <Route path="/access/denied" element={<AccessDeniedPage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("Custom denied reason")).toBeInTheDocument();
  });

  it("links back to sign-in and supports sign out", async () => {
    const user = userEvent.setup();
    signOut.mockResolvedValue(undefined);
    render(
      <MemoryRouter>
        <AccessDeniedPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("link", { name: "Back to sign-in" })).toHaveAttribute("href", "/access");
    await user.click(screen.getByRole("button", { name: "Sign out" }));
    expect(signOut).toHaveBeenCalled();
  });
});
