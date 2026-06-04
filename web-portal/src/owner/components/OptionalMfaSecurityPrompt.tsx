import { Link } from "react-router-dom";

type Props = {
  onDismiss: () => void;
};

export function OptionalMfaSecurityPrompt({ onDismiss }: Props) {
  return (
    <div
      className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-slate-800"
      role="region"
      aria-label="Optional two-step verification"
    >
      <p className="font-medium text-slate-900">Protect your account with two-step verification.</p>
      <p className="mt-1 text-slate-600">
        Two-step verification is optional but recommended for venue operator accounts.
      </p>
      <div className="mt-3 flex flex-wrap gap-3">
        <Link
          to="/access"
          state={{ setupMfa: true }}
          className="rounded bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
        >
          Set up 2FA
        </Link>
        <button
          type="button"
          className="text-sm font-medium text-slate-700 underline"
          onClick={onDismiss}
        >
          Maybe later
        </button>
      </div>
    </div>
  );
}
