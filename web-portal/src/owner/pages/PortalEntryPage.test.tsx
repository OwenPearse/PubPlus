import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PortalEntryPage } from "@/owner/pages/PortalEntryPage";

const signInWithPassword = vi.fn();
const signUpWithPassword = vi.fn();
const resolvePostAuthMfaStep = vi.fn();
const getVerifiedTotpFactorId = vi.fn();
const signOut = vi.fn();
const resolvePortalRole = vi.fn();
const ownerProvision = vi.fn();
const navigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => navigate };
});

vi.mock("@/shared/lib/supabase", () => ({
  signInWithPassword: (...args: unknown[]) => signInWithPassword(...args),
  signUpWithPassword: (...args: unknown[]) => signUpWithPassword(...args),
  resolvePostAuthMfaStep: (...args: unknown[]) => resolvePostAuthMfaStep(...args),
  getVerifiedTotpFactorId: (...args: unknown[]) => getVerifiedTotpFactorId(...args),
  signOut: (...args: unknown[]) => signOut(...args),
}));

vi.mock("@/shared/lib/api", () => ({
  ownerProvision: (...args: unknown[]) => ownerProvision(...args),
  formatApiError: (err: unknown) => (err instanceof Error ? err.message : "error"),
  isApiRequestError: () => false,
}));

vi.mock("@/shared/lib/portalRole", () => ({
  resolvePortalRole: (...args: unknown[]) => resolvePortalRole(...args),
}));

vi.mock("@/owner/components/MfaEnrollStep", () => ({
  MfaEnrollStep: ({ onSignOut }: { onSignOut: () => void }) => (
    <div data-testid="mfa-enroll-step">
      <button type="button" onClick={onSignOut}>
        MFA enroll sign out
      </button>
    </div>
  ),
}));

vi.mock("@/owner/components/MfaVerifyStep", () => ({
  MfaVerifyStep: () => <div data-testid="mfa-verify-step">MFA verify</div>,
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
    resolvePostAuthMfaStep.mockReset();
    getVerifiedTotpFactorId.mockReset();
    signOut.mockReset();
    resolvePortalRole.mockReset();
    ownerProvision.mockReset();
    navigate.mockReset();
    resolvePostAuthMfaStep.mockResolvedValue("complete");
    resolvePortalRole.mockResolvedValue({ role: "admin" });
    ownerProvision.mockResolvedValue({});
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

  it("routes to admin workspace after sign-in when role is admin", async () => {
    const user = userEvent.setup();
    signInWithPassword.mockResolvedValue({ user: { id: "u1" } });
    resolvePortalRole.mockResolvedValue({ role: "admin" });
    renderPage();

    await user.type(screen.getByLabelText("Email"), "owner@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit sign in" }));

    await waitFor(() => {
      expect(resolvePortalRole).toHaveBeenCalled();
      expect(screen.getByRole("button", { name: "Continue to operator workspace" })).toBeInTheDocument();
    });
  });

  it("transitions to MFA enroll step after sign-in when enrollment is required", async () => {
    const user = userEvent.setup();
    signInWithPassword.mockResolvedValue({ user: { id: "u1" } });
    resolvePostAuthMfaStep.mockResolvedValue("enroll");
    renderPage();

    await user.type(screen.getByLabelText("Email"), "owner@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit sign in" }));

    await waitFor(() => {
      expect(screen.getByTestId("mfa-enroll-step")).toBeInTheDocument();
    });
  });

  it("transitions to MFA verify step when verification is required", async () => {
    const user = userEvent.setup();
    signInWithPassword.mockResolvedValue({ user: { id: "u1" } });
    resolvePostAuthMfaStep.mockResolvedValue("verify");
    getVerifiedTotpFactorId.mockResolvedValue("factor-verify");
    renderPage();

    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit sign in" }));

    await waitFor(() => {
      expect(screen.getByTestId("mfa-verify-step")).toBeInTheDocument();
    });
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

  it("provisions owner on sign-up with session then resolves role", async () => {
    const user = userEvent.setup();
    signUpWithPassword.mockResolvedValue({ user: { id: "u3" }, session: { access_token: "t" } });
    resolvePostAuthMfaStep.mockResolvedValue("complete");
    resolvePortalRole.mockResolvedValue({
      role: "owner",
      probe: { next_step: "portal_home" },
    });
    renderPage();

    await user.click(screen.getByRole("tab", { name: "Create account" }));
    await user.type(screen.getByLabelText("Email"), "pending@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit create account" }));

    await waitFor(() => {
      expect(ownerProvision).toHaveBeenCalled();
      expect(resolvePortalRole).toHaveBeenCalled();
      expect(screen.getByRole("button", { name: "Continue to owner portal" })).toBeInTheDocument();
    });
  });
});
