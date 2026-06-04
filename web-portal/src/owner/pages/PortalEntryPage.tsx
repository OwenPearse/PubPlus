import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ErrorBanner } from "@/shared/components/ErrorBanner";
import { getPortalSupportUrl, hasSupabaseAuthConfig } from "@/shared/lib/env";
import { portalBrand } from "@/shared/lib/portalBrand";
import { signInWithPassword, signUpWithPassword } from "@/shared/lib/supabase";

type EntryMode = "sign-in" | "sign-up";

type SuccessKind = "signed-in" | "sign-up-confirm" | "sign-up-pending";

export function PortalEntryPage() {
  const [mode, setMode] = useState<EntryMode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState<SuccessKind | null>(null);

  const supportUrl = getPortalSupportUrl();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess(null);
    setLoading(true);
    try {
      if (mode === "sign-in") {
        await signInWithPassword(email.trim(), password);
        setSuccess("signed-in");
      } else {
        const data = await signUpWithPassword(email.trim(), password);
        if (data.session) {
          setSuccess("sign-up-pending");
        } else {
          setSuccess("sign-up-confirm");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
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

  if (success) {
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center p-6">
        <PortalEntryHeader />
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          {success === "sign-up-confirm" ? (
            <>
              <h2 className="text-lg font-semibold text-slate-900">Check your email</h2>
              <p className="mt-2 text-sm text-slate-600">
                We sent a confirmation link to <strong>{email}</strong>. After you confirm, sign in
                here. Venue portal access may require account approval before you can manage a venue.
              </p>
            </>
          ) : success === "sign-up-pending" ? (
            <>
              <h2 className="text-lg font-semibold text-slate-900">Account created</h2>
              <p className="mt-2 text-sm text-slate-600">
                Your sign-in details were accepted. Venue portal access may require approval or
                provisioning before you can enter the owner area. Sign in again once access has been
                granted.
              </p>
            </>
          ) : (
            <>
              <h2 className="text-lg font-semibold text-slate-900">Signed in</h2>
              <p className="mt-2 text-sm text-slate-600">
                You are signed in. Role-based routing and two-factor verification will be enabled in
                a later release. If you have internal operator access, you can open the admin
                workspace below.
              </p>
              <p className="mt-3 text-sm text-slate-600">
                Venue owners: your account may still need approval before the owner portal is
                available.
              </p>
            </>
          )}
          <button
            type="button"
            className="mt-4 text-sm text-slate-600 underline"
            onClick={() => {
              setSuccess(null);
              setPassword("");
            }}
          >
            Back to sign in
          </button>
          {success === "signed-in" ? (
            <p className="mt-4">
              <Link
                to="/internal/founder-venues"
                className="text-sm font-medium text-slate-900 underline"
              >
                Continue to operator workspace
              </Link>
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center p-6">
      <PortalEntryHeader />

      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
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
