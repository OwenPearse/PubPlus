import type { OwnerClaimStatus } from "@/shared/lib/api";
import { getPortalSupportUrl } from "@/shared/lib/env";

type Props = {
  claim: OwnerClaimStatus;
  onSubmitNew?: () => void;
};

function formatVenueSummary(claim: OwnerClaimStatus): string {
  const name = claim.submitted_venue_name?.trim() || "your venue";
  const address = claim.submitted_address_line_1?.trim();
  const locality = claim.locality_name?.trim();
  if (address && locality) return `${name} (${address}, ${locality})`;
  if (address) return `${name} (${address})`;
  if (locality) return `${name} (${locality})`;
  return name;
}

function isPendingStatus(status: OwnerClaimStatus["claim_lifecycle_status"]) {
  return status === "draft" || status === "submitted" || status === "under_review";
}

export function OwnerClaimStatusState({ claim, onSubmitNew }: Props) {
  const supportUrl = getPortalSupportUrl();
  const venueSummary = formatVenueSummary(claim);

  if (claim.claim_lifecycle_status === "needs_more_info") {
    return (
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">We need a bit more information</h1>
          <p className="mt-2 text-sm text-slate-600">
            Please check the note below and update your request or contact support.
          </p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
          <p className="text-sm font-medium text-slate-900">{venueSummary}</p>
          {claim.admin_message ? (
            <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{claim.admin_message}</p>
          ) : null}
          {supportUrl ? (
            <p className="mt-4 text-sm">
              <a
                href={supportUrl}
                className="font-medium text-slate-900 underline"
                target="_blank"
                rel="noreferrer"
              >
                Contact support
              </a>
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  if (claim.claim_lifecycle_status === "denied") {
    return (
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Your venue request wasn&apos;t approved
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            If you think this is a mistake, contact support or submit a new request with more
            detail.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <p className="text-sm font-medium text-slate-900">{venueSummary}</p>
          {claim.admin_message ? (
            <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{claim.admin_message}</p>
          ) : null}
          <div className="mt-4 flex flex-wrap gap-3">
            {onSubmitNew ? (
              <button
                type="button"
                className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800"
                onClick={onSubmitNew}
              >
                Submit a new request
              </button>
            ) : null}
            {supportUrl ? (
              <a
                href={supportUrl}
                className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50"
                target="_blank"
                rel="noreferrer"
              >
                Contact support
              </a>
            ) : null}
          </div>
        </div>
      </div>
    );
  }

  if (isPendingStatus(claim.claim_lifecycle_status)) {
    return (
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Your venue request is under review</h1>
          <p className="mt-2 text-sm text-slate-600">
            Thanks — we&apos;ve received your request for {venueSummary}. We&apos;ll review that
            you&apos;re authorised to manage this venue. Once approved, you&apos;ll be able to
            update the listing.
          </p>
        </div>
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
          <p className="text-sm text-blue-900">
            Status:{" "}
            <span className="font-medium capitalize">
              {claim.claim_lifecycle_status.replace(/_/g, " ")}
            </span>
          </p>
          {claim.submitted_at ? (
            <p className="mt-2 text-xs text-blue-800">
              Submitted {new Date(claim.submitted_at).toLocaleString()}
            </p>
          ) : null}
        </div>
      </div>
    );
  }

  return null;
}
