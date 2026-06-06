import { useEffect, useState } from "react";

import { OwnerClaimStatusState } from "@/owner/pages/OwnerClaimStatusState";
import { OwnerVenueClaimEntry } from "@/owner/pages/OwnerVenueClaimEntry";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  ownerCurrentVenueClaim,
  type OwnerClaimStatus,
} from "@/shared/lib/api";

function shouldShowClaimStatus(claim: OwnerClaimStatus): boolean {
  const status = claim.claim_lifecycle_status;
  return (
    status === "draft" ||
    status === "submitted" ||
    status === "under_review" ||
    status === "needs_more_info" ||
    status === "denied"
  );
}

export function NoVenueAccessState() {
  const [claim, setClaim] = useState<OwnerClaimStatus | null | undefined>(undefined);
  const [error, setError] = useState("");
  const [showNewRequestForm, setShowNewRequestForm] = useState(false);

  useEffect(() => {
    let active = true;
    setError("");
    void ownerCurrentVenueClaim()
      .then(({ data }) => {
        if (!active) return;
        setClaim(data);
      })
      .catch((err) => {
        if (!active) return;
        setClaim(null);
        setError(formatApiError(err));
      });
    return () => {
      active = false;
    };
  }, []);

  if (claim === undefined) {
    return <p className="text-sm text-slate-600">Loading your venue request…</p>;
  }

  if (claim && shouldShowClaimStatus(claim) && !showNewRequestForm) {
    return (
      <div className="space-y-4">
        <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
        <OwnerClaimStatusState
          claim={claim}
          onSubmitNew={
            claim.claim_lifecycle_status === "denied"
              ? () => setShowNewRequestForm(true)
              : undefined
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Tell us about your pub</h1>
        <p className="mt-2 text-sm text-slate-600">
          Add the basic details for the pub you manage. We&apos;ll check whether it already exists
          and review that you&apos;re authorised to manage it.
        </p>
      </div>
      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <OwnerVenueClaimEntry />
      </div>
    </div>
  );
}
