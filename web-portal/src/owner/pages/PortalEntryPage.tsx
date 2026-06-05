import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { MfaEnrollStep } from "@/owner/components/MfaEnrollStep";
import { MfaVerifyStep } from "@/owner/components/MfaVerifyStep";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerProvision,
} from "@/shared/lib/api";
import { getPortalSupportUrl, hasSupabaseAuthConfig } from "@/shared/lib/env";
import { portalBrand } from "@/shared/lib/portalBrand";
import {
  getPostAuthContinuePath,
  shouldShowAccessDenied,
} from "@/shared/lib/portalRedirect";
import { resolvePortalRole, type ResolvePortalRoleResult } from "@/shared/lib/portalRole";
import {
  getVerifiedTotpFactorId,
  resolvePostAuthMfaStep,
  formatPasswordUpdateError,
  sendPasswordResetEmail,
  signInWithPassword,
  signOut,
  signUpWithPassword,
  updatePassword,
  waitForSession,
} from "@/shared/lib/supabase";

type EntryMode = "sign-in" | "sign-up";
type CredentialView =
  | "form"
  | "forgot-password"
  | "forgot-password-sent"
  | "reset-password"
  | "reset-password-success";

function initialCredentialView(searchParams: URLSearchParams): CredentialView {
  return searchParams.get("mode") === "reset" ? "reset-password" : "form";
}

type PortalPhase =
  | { kind: "credentials" }
  | { kind: "mfa-loading" }
  | { kind: "mfa-enroll" }
  | { kind: "mfa-verify"; factorId: string }
  | { kind: "routing-loading" }
  | { kind: "post-auth"; roleResult: ResolvePortalRoleResult }
  | { kind: "sign-up-confirm" };

export function PortalEntryPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<EntryMode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [provisioning, setProvisioning] = useState(false);
  const [error, setError] = useState("");
  const [phase, setPhase] = useState<PortalPhase>({ kind: "credentials" });
  const [credentialView, setCredentialView] = useState<CredentialView>(() =>
    initialCredentialView(searchParams),
  );
  const [resetEmail, setResetEmail] = useState("");

  const supportUrl = getPortalSupportUrl();

  useEffect(() => {
    const state = location.state as { setupMfa?: boolean } | null;
    if (state?.setupMfa) {
      void beginOptionalMfaSetup();
      navigate(location.pathname + location.search, { replace: true, state: {} });
    }
  }, [location.pathname, location.search, location.state, navigate]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const session = await waitForSession();
      if (!session || cancelled) return;
      await routeAfterSignIn();
    })();
    return () => {
      cancelled = true;
    };
    // Resume post-auth when /access loads with an existing Supabase session (e.g. guard bounce).
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount-only session restore
  }, []);

  async function beginOptionalMfaSetup() {
    setPhase({ kind: "mfa-loading" });
    setError("");
    try {
      const step = await resolvePostAuthMfaStep();
      if (step === "complete") {
        setPhase({ kind: "credentials" });
        setError("Two-step verification is already enabled for this account.");
        return;
      }
      if (step === "verify") {
        const factorId = await getVerifiedTotpFactorId();
        if (factorId) {
          setPhase({ kind: "mfa-verify", factorId });
          return;
        }
      }
      setPhase({ kind: "mfa-enroll" });
    } catch (err) {
      setPhase({ kind: "credentials" });
      setError(
        err instanceof Error
          ? err.message
          : "Could not start two-step verification setup. Please try again.",
      );
    }
  }

  async function routeAfterSignIn() {
    setPhase({ kind: "routing-loading" });
    setError("");
    try {
      if (mode === "sign-up") {
        try {
          await ownerProvision();
        } catch (provisionErr) {
          if (!isApiRequestError(provisionErr) || provisionErr.code !== "forbidden") {
            throw provisionErr;
          }
        }
      }
      const roleResult = await resolvePortalRole();
      setPhase({ kind: "post-auth", roleResult });
    } catch (err) {
      setPhase({ kind: "credentials" });
      setError(formatApiError(err));
    }
  }

  async function beginMfaFlow() {
    setPhase({ kind: "mfa-loading" });
    setError("");
    try {
      const step = await resolvePostAuthMfaStep();
      if (step === "complete") {
        await completeMfaAndRoute();
        return;
      }
      if (step === "verify") {
        const factorId = await getVerifiedTotpFactorId();
        if (factorId) {
          setPhase({ kind: "mfa-verify", factorId });
          return;
        }
      }
      setPhase({ kind: "mfa-enroll" });
    } catch (err) {
      setPhase({ kind: "credentials" });
      setError(
        err instanceof Error
          ? err.message
          : "Could not check two-step verification status. Please try again.",
      );
    }
  }

  async function completeMfaAndRoute() {
    setPhase({ kind: "routing-loading" });
    setError("");
    try {
      if (mode === "sign-up") {
        try {
          await ownerProvision();
        } catch (provisionErr) {
          if (!isApiRequestError(provisionErr) || provisionErr.code !== "forbidden") {
            throw provisionErr;
          }
        }
      }
      const roleResult = await resolvePortalRole();
      setPhase({ kind: "post-auth", roleResult });
    } catch (err) {
      setPhase({ kind: "credentials" });
      setError(formatApiError(err));
    }
  }

  async function handleRetryOwnerProvision() {
    setProvisioning(true);
    setError("");
    try {
      await ownerProvision();
      const roleResult = await resolvePortalRole();
      setPhase({ kind: "post-auth", roleResult });
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setProvisioning(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "sign-in") {
        await signInWithPassword(email.trim(), password);
        await routeAfterSignIn();
      } else {
        const data = await signUpWithPassword(email.trim(), password);
        if (data.session) {
          await routeAfterSignIn();
        } else {
          setPhase({ kind: "sign-up-confirm" });
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSignOutFromMfa() {
    await signOut();
    setPhase({ kind: "credentials" });
    setPassword("");
    setError("");
  }

  function resetToCredentials() {
    setPhase({ kind: "credentials" });
    setCredentialView("form");
    setPassword("");
    setError("");
  }

  async function handleForgotPasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await sendPasswordResetEmail(resetEmail.trim());
      setCredentialView("forgot-password-sent");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not send password reset email. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleResetPasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await updatePassword(newPassword);
      setNewPassword("");
      setConfirmPassword("");
      setCredentialView("reset-password-success");
      navigate("/access", { replace: true });
    } catch (err) {
      setError(
        formatPasswordUpdateError(
          err,
          "Could not update your password. Please try again or request a new reset link.",
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  function goToSignInAfterReset() {
    setCredentialView("form");
    setMode("sign-in");
    setError("");
    setNewPassword("");
    setConfirmPassword("");
    void signOut();
  }

  function handleContinueAfterAuth(roleResult: ResolvePortalRoleResult) {
    const path = getPostAuthContinuePath(roleResult);
    if (path) {
      navigate(path);
      return;
    }
    if (shouldShowAccessDenied(roleResult)) {
      const message =
        roleResult.role === "error"
          ? roleResult.message
          : "Your account is signed in but does not have portal access yet.";
      navigate("/access/denied", { state: { message } });
    }
  }

  if (!hasSupabaseAuthConfig()) {
    return (
      <div className="mx-auto max-w-lg p-8">
        <p className="text-red-700">
          Supabase is not configured. Copy <code>.env.example</code> to <code>.env</code> and set{" "}
          <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_PUBLISHABLE_KEY</code>.
        </p>
      </div>
    );
  }

  if (phase.kind !== "credentials") {
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center p-6">
        <PortalEntryHeader />
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          {phase.kind === "sign-up-confirm" ? (
            <>
              <h2 className="text-lg font-semibold text-slate-900">Check your email</h2>
              <p className="mt-2 text-sm text-slate-600">
                We sent a confirmation link to <strong>{email}</strong>. After you confirm, sign in
                here. Venue portal access may require account approval before you can manage a venue.
              </p>
              <button
                type="button"
                className="mt-4 text-sm text-slate-600 underline"
                onClick={resetToCredentials}
              >
                Back to sign in
              </button>
            </>
          ) : phase.kind === "mfa-loading" || phase.kind === "routing-loading" ? (
            <p className="text-sm text-slate-600" role="status">
              {phase.kind === "mfa-loading"
                ? "Checking two-step verification…"
                : "Checking your portal access…"}
            </p>
          ) : phase.kind === "mfa-enroll" ? (
            <MfaEnrollStep
              onComplete={() => void completeMfaAndRoute()}
              onSignOut={handleSignOutFromMfa}
              onNeedVerify={(factorId) => setPhase({ kind: "mfa-verify", factorId })}
            />
          ) : phase.kind === "mfa-verify" ? (
            <MfaVerifyStep
              factorId={phase.factorId}
              onComplete={() => void completeMfaAndRoute()}
              onSignOut={handleSignOutFromMfa}
            />
          ) : phase.kind === "post-auth" ? (
            <PostAuthPanel
              roleResult={phase.roleResult}
              provisioning={provisioning}
              error={error}
              onContinue={() => handleContinueAfterAuth(phase.roleResult)}
              onProvision={() => void handleRetryOwnerProvision()}
              onDismissError={() => setError("")}
              onSetupMfa={() => void beginOptionalMfaSetup()}
            />
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center p-6">
      <PortalEntryHeader />

      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {credentialView === "form" ? (
          <>
            <div className="mb-6 flex rounded-lg border border-slate-200 p-1" role="tablist">
              <ModeButton
                active={mode === "sign-in"}
                label="Sign in"
                onClick={() => {
                  setMode("sign-in");
                  setError("");
                }}
              />
              <ModeButton
                active={mode === "sign-up"}
                label="Create account"
                onClick={() => {
                  setMode("sign-up");
                  setError("");
                }}
              />
            </div>

            <h2 className="mb-1 text-lg font-semibold text-slate-900">
              {mode === "sign-in" ? "Sign in" : "Create your account"}
            </h2>
            <p className="mb-4 text-sm text-slate-600">
              {mode === "sign-in"
                ? "Sign in for venue operators or internal operators."
                : "Register as a venue operator. Access may require approval after your account is created."}
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="block text-sm">
                Email
                <input
                  type="email"
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete={mode === "sign-in" ? "username" : "email"}
                  disabled={loading}
                />
              </label>
              <label className="block text-sm">
                Password
                <input
                  type="password"
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  autoComplete={mode === "sign-in" ? "current-password" : "new-password"}
                  disabled={loading}
                />
              </label>

              {mode === "sign-in" ? (
                <p className="text-right text-sm">
                  <button
                    type="button"
                    className="font-medium text-slate-900 underline"
                    onClick={() => {
                      setResetEmail(email);
                      setCredentialView("forgot-password");
                      setError("");
                    }}
                  >
                    Forgot password?
                  </button>
                </p>
              ) : null}

              <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />

              <button
                type="submit"
                aria-label={mode === "sign-in" ? "Submit sign in" : "Submit create account"}
                className="w-full rounded bg-slate-900 py-2 text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loading}
              >
                {loading
                  ? mode === "sign-in"
                    ? "Signing in…"
                    : "Creating account…"
                  : mode === "sign-in"
                    ? "Sign in"
                    : "Create account"}
              </button>
            </form>
          </>
        ) : credentialView === "forgot-password" ? (
          <>
            <h2 className="mb-1 text-lg font-semibold text-slate-900">Reset your password</h2>
            <p className="mb-4 text-sm text-slate-600">
              Enter the email for your account and we&apos;ll send reset instructions if it exists.
            </p>
            <form onSubmit={handleForgotPasswordSubmit} className="space-y-4">
              <label className="block text-sm">
                Email
                <input
                  type="email"
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  required
                  autoComplete="email"
                  disabled={loading}
                />
              </label>
              <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
              <button
                type="submit"
                className="w-full rounded bg-slate-900 py-2 text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loading}
              >
                {loading ? "Sending…" : "Send reset email"}
              </button>
            </form>
            <button
              type="button"
              className="mt-4 text-sm text-slate-600 underline"
              onClick={() => {
                setCredentialView("form");
                setError("");
              }}
            >
              Back to sign in
            </button>
          </>
        ) : credentialView === "reset-password" ? (
          <>
            <h2 className="mb-1 text-lg font-semibold text-slate-900">Set a new password</h2>
            <p className="mb-4 text-sm text-slate-600">
              Choose a new password for your portal account. You will sign in again after updating.
            </p>
            <form onSubmit={handleResetPasswordSubmit} className="space-y-4">
              <label className="block text-sm">
                New password
                <input
                  type="password"
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={6}
                  autoComplete="new-password"
                  disabled={loading}
                />
              </label>
              <label className="block text-sm">
                Confirm password
                <input
                  type="password"
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={6}
                  autoComplete="new-password"
                  disabled={loading}
                />
              </label>
              <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
              <button
                type="submit"
                className="w-full rounded bg-slate-900 py-2 text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={loading}
              >
                {loading ? "Updating…" : "Update password"}
              </button>
            </form>
            <button
              type="button"
              className="mt-4 text-sm text-slate-600 underline"
              onClick={() => {
                setCredentialView("form");
                setError("");
                navigate("/access", { replace: true });
              }}
            >
              Back to sign in
            </button>
          </>
        ) : credentialView === "reset-password-success" ? (
          <>
            <h2 className="mb-1 text-lg font-semibold text-slate-900">Password updated</h2>
            <p className="text-sm text-slate-600">
              Your password has been updated. You can now continue signing in to the portal.
            </p>
            <button
              type="button"
              className="mt-4 w-full rounded bg-slate-900 py-2 text-sm text-white hover:bg-slate-800"
              onClick={() => goToSignInAfterReset()}
            >
              Continue to sign in
            </button>
          </>
        ) : (
          <>
            <h2 className="mb-1 text-lg font-semibold text-slate-900">Check your email</h2>
            <p className="text-sm text-slate-600">
              If an account exists for this email, we&apos;ll send password reset instructions.
            </p>
            <button
              type="button"
              className="mt-4 text-sm font-medium text-slate-900 underline"
              onClick={() => {
                setCredentialView("form");
                setMode("sign-in");
                setError("");
              }}
            >
              Back to sign in
            </button>
          </>
        )}
      </div>

      {supportUrl ? (
        <p className="mt-6 text-center text-sm text-slate-600">
          Need help?{" "}
          <a
            href={supportUrl}
            className="font-medium text-slate-900 underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            Contact support
          </a>
        </p>
      ) : null}
    </div>
  );
}

function PostAuthPanel({
  roleResult,
  provisioning,
  error,
  onContinue,
  onProvision,
  onDismissError,
  onSetupMfa,
}: {
  roleResult: ResolvePortalRoleResult;
  provisioning: boolean;
  error: string;
  onContinue: () => void;
  onProvision: () => void;
  onDismissError: () => void;
  onSetupMfa: () => void;
}) {
  if (roleResult.role === "admin") {
    return (
      <>
        <h2 className="text-lg font-semibold text-slate-900">Signed in</h2>
        <p className="mt-2 text-sm text-slate-600">
          Two-step verification is complete. You can continue to the internal operator workspace.
        </p>
        <button
          type="button"
          className="mt-4 w-full rounded bg-slate-900 py-2 text-sm text-white hover:bg-slate-800"
          onClick={onContinue}
        >
          Continue to operator workspace
        </button>
      </>
    );
  }

  if (roleResult.role === "owner") {
    return (
      <>
        <h2 className="text-lg font-semibold text-slate-900">Signed in</h2>
        <p className="mt-2 text-sm text-slate-600">
          Your owner account is recognized. You can open the owner portal area; some features may
          still be pending depending on business or venue access.
        </p>
        <button
          type="button"
          className="mt-4 w-full rounded bg-slate-900 py-2 text-sm text-white hover:bg-slate-800"
          onClick={onContinue}
        >
          Continue to owner portal
        </button>
        <button
          type="button"
          className="mt-3 w-full text-sm font-medium text-slate-700 underline"
          onClick={onSetupMfa}
        >
          Set up two-step verification
        </button>
      </>
    );
  }

  if (roleResult.role === "none" && roleResult.reason === "owner_not_provisioned") {
    return (
      <>
        <h2 className="text-lg font-semibold text-slate-900">Complete owner setup</h2>
        <p className="mt-2 text-sm text-slate-600">
          Your sign-in is valid, but your owner account still needs to be provisioned before you can
          use the venue portal.
        </p>
        <ErrorBanner message={error} onDismiss={error ? onDismissError : undefined} />
        <button
          type="button"
          className="mt-4 w-full rounded bg-slate-900 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-60"
          onClick={onProvision}
          disabled={provisioning}
        >
          {provisioning ? "Provisioning…" : "Complete owner setup"}
        </button>
      </>
    );
  }

  if (roleResult.role === "error" && roleResult.code === "dual_access") {
    return (
      <>
        <h2 className="text-lg font-semibold text-slate-900">Access conflict</h2>
        <p className="mt-2 text-sm text-slate-600">{roleResult.message}</p>
        <Link to="/access/denied" className="mt-4 inline-block text-sm font-medium underline">
          View access details
        </Link>
      </>
    );
  }

  if (roleResult.role === "expired") {
    return (
      <>
        <h2 className="text-lg font-semibold text-slate-900">Session expired</h2>
        <p className="mt-2 text-sm text-slate-600">Please sign in again.</p>
        <button type="button" className="mt-4 text-sm underline" onClick={onDismissError}>
          Back to sign in
        </button>
      </>
    );
  }

  return (
    <>
      <h2 className="text-lg font-semibold text-slate-900">Access not available</h2>
      <p className="mt-2 text-sm text-slate-600">
        You are signed in, but neither operator nor owner portal access is available for this
        account yet.
      </p>
      <button
        type="button"
        className="mt-4 text-sm font-medium text-slate-900 underline"
        onClick={onContinue}
      >
        Continue
      </button>
    </>
  );
}

function PortalEntryHeader() {
  return (
    <header className="mb-8 text-center">
      <img
        src={portalBrand.logoSrc}
        alt={portalBrand.logoAlt}
        className="mx-auto h-12 w-12"
        width={48}
        height={48}
      />
      <h1 className="mt-4 text-2xl font-bold text-slate-900">{portalBrand.productName}</h1>
      {portalBrand.tagline ? (
        <p className="mt-1 text-sm text-slate-600">{portalBrand.tagline}</p>
      ) : null}
    </header>
  );
}

function ModeButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
        active ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"
      }`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
