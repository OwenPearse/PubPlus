import { useState } from "react";

import { OwnerVenueClaimEntry } from "@/owner/pages/OwnerVenueClaimEntry";

type Props = {
  variant: "membership" | "venue";
  businessCount?: number;
  venueCount?: number;
};

export function NoVenueAccessState({ variant, businessCount = 0, venueCount = 0 }: Props) {
  const [showClaimForm, setShowClaimForm] = useState(false);

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
        <h2 className="text-lg font-semibold text-slate-900">Add or claim your venue</h2>
        <p className="mt-2 text-sm text-slate-700">
          Tell us which pub you manage. If we already have a matching listing, you can request to
          claim it. If not, you can submit it as a new venue for review.
        </p>
        <p className="mt-2 text-sm text-slate-600">
          An admin will review that you are authorised to manage the venue.
        </p>
        {variant === "venue" ? (
          <p className="mt-3 text-xs text-slate-600">
            Businesses: {businessCount} · Approved venues: {venueCount}
          </p>
        ) : businessCount === 0 ? (
          <p className="mt-3 text-xs text-slate-600">Active businesses: 0</p>
        ) : null}
        {!showClaimForm ? (
          <button
            type="button"
            className="mt-4 rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800"
            onClick={() => setShowClaimForm(true)}
          >
            Add or claim a venue
          </button>
        ) : null}
      </div>
      {showClaimForm ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <OwnerVenueClaimEntry />
        </div>
      ) : null}
    </div>
  );
}
