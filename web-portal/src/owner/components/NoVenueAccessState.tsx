import { OwnerVenueClaimEntry } from "@/owner/pages/OwnerVenueClaimEntry";

export function NoVenueAccessState() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Tell us about your pub</h1>
        <p className="mt-2 text-sm text-slate-600">
          Add the basic details for the pub you manage. We&apos;ll check whether it already exists
          and review that you&apos;re authorised to manage it.
        </p>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <OwnerVenueClaimEntry />
      </div>
    </div>
  );
}
