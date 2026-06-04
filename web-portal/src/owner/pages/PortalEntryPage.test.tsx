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

vi.mock("@/shared/lib/supabase", () => ({
  signInWithPassword: (...args: unknown[]) => signInWithPassword(...args),
  signUpWithPassword: (...args: unknown[]) => signUpWithPassword(...args),
  resolvePostAuthMfaStep: (...args: unknown[]) => resolvePostAuthMfaStep(...args),
  getVerifiedTotpFactorId: (...args: unknown[]) => getVerifiedTotpFactorId(...args),
  signOut: (...args: unknown[]) => signOut(...args),
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
    resolvePostAuthMfaStep.mockResolvedValue("complete");
    getVerifiedTotpFactorId.mockResolvedValue("factor-1");
    signOut.mockResolvedValue(undefined);
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

  it("shows MFA complete state after sign-in when MFA is satisfied", async () => {
    const user = userEvent.setup();
    signInWithPassword.mockResolvedValue({ user: { id: "u1" } });
    resolvePostAuthMfaStep.mockResolvedValue("complete");
    renderPage();

    await user.type(screen.getByLabelText("Email"), "owner@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit sign in" }));

    await waitFor(() => {
      expect(signInWithPassword).toHaveBeenCalledWith("owner@example.com", "secret12");
      expect(resolvePostAuthMfaStep).toHaveBeenCalled();
    });
    expect(
      screen.getByRole("heading", { name: "Two-step verification complete" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/may still require account approval or provisioning/i)).toBeInTheDocument();
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

  it("starts MFA flow when sign-up returns a session", async () => {
    const user = userEvent.setup();
    signUpWithPassword.mockResolvedValue({ user: { id: "u3" }, session: { access_token: "t" } });
    resolvePostAuthMfaStep.mockResolvedValue("enroll");
    renderPage();

    await user.click(screen.getByRole("tab", { name: "Create account" }));
    await user.type(screen.getByLabelText("Email"), "pending@example.com");
    await user.type(screen.getByLabelText("Password"), "secret12");
    await user.click(screen.getByRole("button", { name: "Submit create account" }));

    await waitFor(() => {
      expect(resolvePostAuthMfaStep).toHaveBeenCalled();
      expect(screen.getByTestId("mfa-enroll-step")).toBeInTheDocument();
    });
  });
});
