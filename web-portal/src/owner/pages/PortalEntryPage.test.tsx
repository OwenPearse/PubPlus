import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PortalEntryPage } from "@/owner/pages/PortalEntryPage";

const signInWithPassword = vi.fn();
const signUpWithPassword = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  signInWithPassword: (...args: unknown[]) => signInWithPassword(...args),
  signUpWithPassword: (...args: unknown[]) => signUpWithPassword(...args),
}));

vi.mock("@/shared/lib/env", () => ({
  hasSupabaseAuthConfig: () => true,
  getPortalSupportUrl: () => null,
}));

vi.mock("@/shared/lib/portalBrand", () => ({
  portalBrand: {
    productName: "Test Venue Portal",
    tagline: "",
    logoSrc: "/brand/placeholder-mark.svg",
    logoAlt: "Portal",
  },
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <PortalEntryPage />
    </MemoryRouter>,
  );
}

describe("PortalEntryPage", () => {
  beforeEach(() => {
    signInWithPassword.mockReset();
    signUpWithPassword.mockReset();
  });

  it("renders portalBrand product name and sign-in mode by default", () => {
    renderPage();
    expect(screen.getByRole("heading", { name: "Test Venue Portal" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Sign in", selected: true })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit sign in" })).toBeInTheDocument();
  });

  it("switches to create-account mode", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("tab", { name: "Create account" }));
    expect(screen.getByRole("heading", { name: "Create your account" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit create account" })).toBeInTheDocument();
  });

  it("calls signInWithPassword on sign-in submit", async () => {
    const user = userEvent.setup();
    signInWithPassword.mockResolvedValue({ user: { id: "u1" } });
    renderPage();

    await user.type(screen.getByLabelText("Email"), "owner@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit sign in" }));

    await waitFor(() => {
      expect(signInWithPassword).toHaveBeenCalledWith("owner@example.com", "secret12");
    });
    expect(screen.getByRole("heading", { name: "Signed in" })).toBeInTheDocument();
  });

  it("calls signUpWithPassword on create-account submit", async () => {
    const user = userEvent.setup();
    signUpWithPassword.mockResolvedValue({ user: { id: "u2" }, session: null });
    renderPage();

    await user.click(screen.getByRole("tab", { name: "Create account" }));
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit create account" }));

    await waitFor(() => {
      expect(signUpWithPassword).toHaveBeenCalledWith("new@example.com", "secret12");
    });
    expect(screen.getByRole("heading", { name: "Check your email" })).toBeInTheDocument();
  });

  it("shows loading then error on failed sign-in", async () => {
    const user = userEvent.setup();
    signInWithPassword.mockRejectedValue(new Error("Invalid login credentials"));
    renderPage();

    await user.type(screen.getByLabelText("Email"), "bad@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Submit sign in" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Invalid login credentials");
    });
  });

  it("shows sign-up pending copy when session is returned", async () => {
    const user = userEvent.setup();
    signUpWithPassword.mockResolvedValue({ user: { id: "u3" }, session: { access_token: "t" } });
    renderPage();

    await user.click(screen.getByRole("tab", { name: "Create account" }));
    await user.type(screen.getByLabelText("Email"), "pending@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit create account" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Account created" })).toBeInTheDocument();
    });
    expect(screen.getByText(/may require approval or provisioning/i)).toBeInTheDocument();
  });
});
