import { useState, type FormEvent } from "react";

import { ErrorBanner } from "@/shared/components/ErrorBanner";
import { challengeMfaFactor, verifyMfaChallenge } from "@/shared/lib/supabase";

type Props = {
  factorId: string;
  onComplete: () => void;
  onSignOut: () => void | Promise<void>;
};

export function MfaVerifyStep({ factorId, onComplete, onSignOut }: Props) {
  const [code, setCode] = useState("");
  const [challengeLoading, setChallengeLoading] = useState(false);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [error, setError] = useState("");
  const [signingOut, setSigningOut] = useState(false);

  const busy = challengeLoading || verifyLoading || signingOut;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setChallengeLoading(true);
    try {
      const challengeId = await challengeMfaFactor(factorId);
      setChallengeLoading(false);
      setVerifyLoading(true);
      await verifyMfaChallenge({ factorId, challengeId, code });
      onComplete();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "That code did not work. Check your authenticator app and try again.",
      );
    } finally {
      setChallengeLoading(false);
      setVerifyLoading(false);
    }
  }

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await onSignOut();
    } finally {
      setSigningOut(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Two-step verification</h2>
        <p className="mt-2 text-sm text-slate-600">
          Two-step verification helps protect your venue portal account. Enter the 6-digit code
          from your authenticator app. After verification, we&apos;ll check whether your owner
          access has been provisioned.
        </p>
      </div>

      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block text-sm">
          Authenticator code
          <input
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{6}"
            maxLength={6}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 tracking-widest"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            required
            disabled={busy}
            aria-label="Authenticator code"
          />
        </label>
        <button
          type="submit"
          className="w-full rounded bg-slate-900 py-2 text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={busy || code.length !== 6}
        >
          {challengeLoading || verifyLoading ? "Verifying…" : "Verify and continue"}
        </button>
      </form>

      <div className="flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
        {error ? (
          <button
            type="button"
            className="rounded border border-slate-300 px-3 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
            onClick={() => {
              setCode("");
              setError("");
            }}
            disabled={busy}
          >
            Try again
          </button>
        ) : (
          <span className="hidden sm:block" aria-hidden />
        )}
        <button
          type="button"
          className="text-sm text-slate-600 underline disabled:opacity-60 sm:ml-auto"
          onClick={() => void handleSignOut()}
          disabled={busy}
        >
          {signingOut ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </div>
  );
}
