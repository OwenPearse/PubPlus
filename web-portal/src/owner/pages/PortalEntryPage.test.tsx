import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PortalEntryPage } from "@/owner/pages/PortalEntryPage";

const signInWithPassword = vi.fn();
const signUpWithPassword = vi.fn();
const resolvePostAuthMfaStep = vi.fn();
const getVerifiedTotpFactorId = vi.fn();
const sendPasswordResetEmail = vi.fn();
const updatePassword = vi.fn();
const signOut = vi.fn();
const resolvePortalRole = vi.fn();
const ownerProvision = vi.fn();
const navigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => navigate };
});

vi.mock("@/shared/lib/supabase", async () => {
  const actual = await vi.importActual<typeof import("@/shared/lib/supabase")>("@/shared/lib/supabase");
  return {
    ...actual,
    signInWithPassword: (...args: unknown[]) => signInWithPassword(...args),
    signUpWithPassword: (...args: unknown[]) => signUpWithPassword(...args),
    resolvePostAuthMfaStep: (...args: unknown[]) => resolvePostAuthMfaStep(...args),
    getVerifiedTotpFactorId: (...args: unknown[]) => getVerifiedTotpFactorId(...args),
    sendPasswordResetEmail: (...args: unknown[]) => sendPasswordResetEmail(...args),
    updatePassword: (...args: unknown[]) => updatePassword(...args),
    signOut: (...args: unknown[]) => signOut(...args),
  };
});

vi.mock("@/shared/lib/api", () => ({
  ownerProvision: (...args: unknown[]) => ownerProvision(...args),
  formatApiError: (err: unknown) => (err instanceof Error ? err.message : "error"),
  isApiRequestError: () => false,
}));

vi.mock("@/shared/lib/portalRole", () => ({
  resolvePortalRole: (...args: unknown[]) => resolvePortalRole(...args),
}));

vi.mock("@/owner/components/MfaEnrollStep", () => ({
  MfaEnrollStep: ({
    onSignOut,
    onNeedVerify,
  }: {
    onSignOut: () => void;
    onNeedVerify: (factorId: string) => void;
  }) => (
    <div data-testid="mfa-enroll-step">
      <button type="button" onClick={() => onNeedVerify("from-enroll")}>
        MFA route verify
      </button>
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

function renderPage(initialEntry = "/access") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/access" element={<PortalEntryPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("PortalEntryPage", () => {
  beforeEach(() => {
    signInWithPassword.mockReset();
    signUpWithPassword.mockReset();
    resolvePostAuthMfaStep.mockReset();
    getVerifiedTotpFactorId.mockReset();
    sendPasswordResetEmail.mockReset();
    updatePassword.mockReset();
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

  it("shows forgot password link on sign-in form", async () => {
    renderPage();
    expect(screen.getByRole("button", { name: "Forgot password?" })).toBeInTheDocument();
  });

  it("submits forgot password email with non-enumerating success copy", async () => {
    const user = userEvent.setup();
    sendPasswordResetEmail.mockResolvedValue(undefined);
    renderPage();

    await user.click(screen.getByRole("button", { name: "Forgot password?" }));
    await user.type(screen.getByLabelText("Email"), "reset@example.com");
    await user.click(screen.getByRole("button", { name: "Send reset email" }));

    await waitFor(() => {
      expect(sendPasswordResetEmail).toHaveBeenCalledWith("reset@example.com");
      expect(
        screen.getByText(/If an account exists for this email, we'll send password reset instructions/i),
      ).toBeInTheDocument();
    });
  });

  it("shows error when forgot password submit fails", async () => {
    const user = userEvent.setup();
    sendPasswordResetEmail.mockRejectedValue(new Error("Rate limit exceeded"));
    renderPage();

    await user.click(screen.getByRole("button", { name: "Forgot password?" }));
    await user.type(screen.getByLabelText("Email"), "reset@example.com");
    await user.click(screen.getByRole("button", { name: "Send reset email" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Rate limit exceeded");
    });
  });

  it("renders set-new-password form when mode=reset", () => {
    renderPage("/access?mode=reset");
    expect(screen.getByRole("heading", { name: "Set a new password" })).toBeInTheDocument();
    expect(screen.getByLabelText("New password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Update password" })).toBeInTheDocument();
  });

  it("shows validation error when reset passwords do not match", async () => {
    const user = userEvent.setup();
    renderPage("/access?mode=reset");

    await user.type(screen.getByLabelText("New password"), "secret12");
    await user.type(screen.getByLabelText("Confirm password"), "different");
    await user.click(screen.getByRole("button", { name: "Update password" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Passwords do not match.");
    });
    expect(updatePassword).not.toHaveBeenCalled();
  });

  it("calls updatePassword and shows success state on reset submit", async () => {
    const user = userEvent.setup();
    updatePassword.mockResolvedValue({ id: "user-1" });
    renderPage("/access?mode=reset");

    await user.type(screen.getByLabelText("New password"), "newpass12");
    await user.type(screen.getByLabelText("Confirm password"), "newpass12");
    await user.click(screen.getByRole("button", { name: "Update password" }));

    await waitFor(() => {
      expect(updatePassword).toHaveBeenCalledWith("newpass12");
      expect(
        screen.getByText(/Your password has been updated. You can now continue signing in/i),
      ).toBeInTheDocument();
    });
  });

  it("shows friendly error when updatePassword fails", async () => {
    const user = userEvent.setup();
    updatePassword.mockRejectedValue(new Error("Auth session missing"));
    renderPage("/access?mode=reset");

    await user.type(screen.getByLabelText("New password"), "newpass12");
    await user.type(screen.getByLabelText("Confirm password"), "newpass12");
    await user.click(screen.getByRole("button", { name: "Update password" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /invalid or has expired|Could not update your password/i,
      );
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
