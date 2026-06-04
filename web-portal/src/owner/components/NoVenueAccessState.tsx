type Props = {
  variant: "membership" | "venue";
  businessCount?: number;
  venueCount?: number;
};

export function NoVenueAccessState({ variant, businessCount = 0, venueCount = 0 }: Props) {
  if (variant === "membership") {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
        <h2 className="text-lg font-semibold text-slate-900">Awaiting business access</h2>
        <p className="mt-2 text-sm text-slate-700">
          Your owner account is active, but you are not linked to a business yet. An administrator
          must add you to a business before you can manage venues.
        </p>
        {businessCount === 0 ? (
          <p className="mt-3 text-xs text-slate-600">Active businesses: 0</p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
      <h2 className="text-lg font-semibold text-slate-900">Awaiting venue access</h2>
      <p className="mt-2 text-sm text-slate-700">
        Your business membership is active, but no approved venue management relationships were
        found. Venue access requires an approved link between your business and a venue.
      </p>
      <p className="mt-3 text-xs text-slate-600">
        Businesses: {businessCount} · Approved venues: {venueCount}
      </p>
    </div>
  );
}
