import { useEffect, useRef, useState, type FormEvent } from "react";

import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  challengeMfaFactor,
  formatMfaError,
  isDuplicateMfaFactorError,
  restartUnverifiedTotpEnrollment,
  startOrRecoverTotpEnrollment,
  type MfaTotpEnrollment,
  type TotpEnrollmentStart,
  verifyMfaChallenge,
} from "@/shared/lib/supabase";

type Props = {
  onComplete: () => void;
  onSignOut: () => void | Promise<void>;
  onNeedVerify: (factorId: string) => void;
};

type EnrollMode = "loading" | "new" | "resume-unverified";

export function MfaEnrollStep({ onComplete, onSignOut, onNeedVerify }: Props) {
  const [mode, setMode] = useState<EnrollMode>("loading");
  const [enrollment, setEnrollment] = useState<MfaTotpEnrollment | null>(null);
  const [resumeFactorId, setResumeFactorId] = useState<string | null>(null);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [restartLoading, setRestartLoading] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [signingOut, setSigningOut] = useState(false);
  const onNeedVerifyRef = useRef(onNeedVerify);
  onNeedVerifyRef.current = onNeedVerify;

  function applyEnrollmentStart(result: TotpEnrollmentStart) {
    if (result.kind === "existing-verified") {
      onNeedVerifyRef.current(result.factorId);
      return;
    }
    if (result.kind === "resume-unverified") {
      setResumeFactorId(result.factorId);
      setEnrollment(null);
      setError("");
      setMode("resume-unverified");
      return;
    }
    setEnrollment(result.enrollment);
    setResumeFactorId(null);
    setError("");
    setMode("new");
  }

  useEffect(() => {
    let cancelled = false;

    async function initEnrollment() {
      setMode("loading");
      setError("");
      setEnrollment(null);
      setResumeFactorId(null);
      try {
        const result = await startOrRecoverTotpEnrollment();
        if (cancelled) return;
        applyEnrollmentStart(result);
      } catch (err) {
        if (!cancelled) {
          setError(
            formatMfaError(
              err,
              "Could not start two-step verification setup. Please try again.",
            ),
          );
          setMode("new");
        }
      }
    }

    void initEnrollment();
    return () => {
      cancelled = true;
    };
  }, []);

  async function verifyFactor(factorId: string) {
    const challengeId = await challengeMfaFactor(factorId);
    await verifyMfaChallenge({
      factorId,
      challengeId,
      code,
    });
    onComplete();
  }

  async function handleVerify(event: FormEvent) {
    event.preventDefault();
    const factorId = enrollment?.factorId ?? resumeFactorId;
    if (!factorId) return;
    setError("");
    setVerifyLoading(true);
    try {
      await verifyFactor(factorId);
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

  async function handleRestartSetup() {
    setCode("");
    setError("");
    setRestartLoading(true);
    setEnrollment(null);
    setResumeFactorId(null);
    setMode("loading");
    try {
      const data = await restartUnverifiedTotpEnrollment();
      setEnrollment(data);
      setMode("new");
    } catch (err) {
      setError(
        formatMfaError(err, "Could not restart authenticator setup. Please try again."),
      );
      setMode("resume-unverified");
    } finally {
      setRestartLoading(false);
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

  const busy = mode === "loading" || verifyLoading || restartLoading || signingOut;
  const activeFactorId = enrollment?.factorId ?? resumeFactorId;
  const showCodeForm = Boolean(activeFactorId) && mode !== "loading";

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Set up two-step verification</h2>
        <p className="mt-2 text-sm text-slate-600">
          Two-step verification helps protect your venue portal account. After verification,
          we&apos;ll check whether your owner access has been provisioned.
        </p>
      </div>

      {mode === "loading" ? (
        <p className="text-sm text-slate-600" role="status">
          Preparing your authenticator setup…
        </p>
      ) : null}

      {mode === "resume-unverified" ? (
        <p className="text-sm text-slate-600">
          An authenticator setup already exists for this account. Enter the 6-digit code from your
          authenticator app to finish setup, or restart setup if you no longer have access to that
          app.
        </p>
      ) : null}

      {enrollment?.qrCode ? (
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

      {enrollment?.secret ? (
        <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
          <p className="font-medium text-slate-700">Manual setup code</p>
          <p className="mt-1 break-all font-mono text-slate-900">{enrollment.secret}</p>
        </div>
      ) : null}

      {enrollment && mode === "new" ? (
        <p className="text-sm text-slate-600">
          Scan the QR code or enter the manual code in your authenticator app, then enter the
          6-digit code below.
        </p>
      ) : null}

      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />

      {showCodeForm ? (
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

      {!showCodeForm && mode !== "loading" && error ? (
        <button
          type="button"
          className="rounded border border-slate-300 px-3 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
          onClick={() => {
            if (isDuplicateMfaFactorError(error)) {
              void handleRestartSetup();
              return;
            }
            setError("");
            setMode("loading");
            void startOrRecoverTotpEnrollment()
              .then(applyEnrollmentStart)
              .catch((err) => {
                setError(
                  formatMfaError(
                    err,
                    "Could not start two-step verification setup. Please try again.",
                  ),
                );
                setMode("new");
              });
          }}
          disabled={busy}
        >
          {isDuplicateMfaFactorError(error) ? "Restart setup" : "Retry setup"}
        </button>
      ) : null}

      {mode === "resume-unverified" ? (
        <button
          type="button"
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
          onClick={() => void handleRestartSetup()}
          disabled={busy}
        >
          {restartLoading ? "Restarting setup…" : "Restart setup"}
        </button>
      ) : null}

      <div className="flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
        {showCodeForm && mode === "new" && !error ? (
          <button
            type="button"
            className="rounded border border-slate-300 px-3 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
            onClick={() => void handleRestartSetup()}
            disabled={busy}
          >
            {restartLoading ? "Restarting…" : "Restart setup"}
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
