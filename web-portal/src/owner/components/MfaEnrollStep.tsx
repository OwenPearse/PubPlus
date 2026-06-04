import { useEffect, useState, type FormEvent } from "react";

import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  challengeMfaFactor,
  enrollTotpFactor,
  type MfaTotpEnrollment,
  verifyMfaChallenge,
} from "@/shared/lib/supabase";

type Props = {
  onComplete: () => void;
  onSignOut: () => void | Promise<void>;
};

export function MfaEnrollStep({ onComplete, onSignOut }: Props) {
  const [enrollment, setEnrollment] = useState<MfaTotpEnrollment | null>(null);
  const [enrollLoading, setEnrollLoading] = useState(true);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function startEnrollment() {
      setEnrollLoading(true);
      setError("");
      try {
        const data = await enrollTotpFactor();
        if (!cancelled) setEnrollment(data);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not start two-step verification setup. Please try again.",
          );
        }
      } finally {
        if (!cancelled) setEnrollLoading(false);
      }
    }

    void startEnrollment();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleVerify(event: FormEvent) {
    event.preventDefault();
    if (!enrollment) return;
    setError("");
    setVerifyLoading(true);
    try {
      const challengeId = await challengeMfaFactor(enrollment.factorId);
      await verifyMfaChallenge({
        factorId: enrollment.factorId,
        challengeId,
        code,
      });
      onComplete();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "That code did not work. Check your authenticator app and try again.",
      );
    } finally {
      setVerifyLoading(false);
    }
  }

  async function handleRetryEnrollment() {
    setEnrollment(null);
    setCode("");
    setError("");
    setEnrollLoading(true);
    try {
      const data = await enrollTotpFactor();
      setEnrollment(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not restart enrollment. Please try again.",
      );
    } finally {
      setEnrollLoading(false);
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

  const busy = enrollLoading || verifyLoading || signingOut;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Set up two-step verification</h2>
        <p className="mt-2 text-sm text-slate-600">
          Two-step verification helps protect your venue portal account. After verification,
          we&apos;ll check whether your owner access has been provisioned.
        </p>
      </div>

      {enrollLoading ? (
        <p className="text-sm text-slate-600" role="status">
          Preparing your authenticator setup…
        </p>
      ) : null}

      {enrollment ? (
        <div className="space-y-4">
          {enrollment.qrCode ? (
            <div className="flex justify-center rounded-lg border border-slate-200 bg-white p-4">
              <img
                src={enrollment.qrCode}
                alt="QR code for authenticator app"
                className="h-40 w-40"
                width={160}
                height={160}
              />
            </div>
          ) : null}
          {enrollment.secret ? (
            <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
              <p className="font-medium text-slate-700">Manual setup code</p>
              <p className="mt-1 break-all font-mono text-slate-900">{enrollment.secret}</p>
            </div>
          ) : null}
          <p className="text-sm text-slate-600">
            Scan the QR code or enter the manual code in your authenticator app, then enter the
            6-digit code below.
          </p>
        </div>
      ) : null}

      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />

      {enrollment ? (
        <form onSubmit={handleVerify} className="space-y-4">
          <label className="block text-sm">
            Verification code
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
              aria-label="Authenticator verification code"
            />
          </label>
          <button
            type="submit"
            className="w-full rounded bg-slate-900 py-2 text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={busy || code.length !== 6}
          >
            {verifyLoading ? "Verifying…" : "Verify code"}
          </button>
        </form>
      ) : null}

      {!enrollLoading && !enrollment ? (
        <button
          type="button"
          className="text-sm font-medium text-slate-900 underline disabled:opacity-60"
          onClick={() => void handleRetryEnrollment()}
          disabled={busy}
        >
          Retry setup
        </button>
      ) : null}

      <button
        type="button"
        className="text-sm text-slate-600 underline disabled:opacity-60"
        onClick={() => void handleSignOut()}
        disabled={busy}
      >
        {signingOut ? "Signing out…" : "Sign out"}
      </button>
    </div>
  );
}
