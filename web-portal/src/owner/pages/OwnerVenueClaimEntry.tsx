import { useEffect, useState } from "react";

import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerVenueClaimRequest,
  parseApiValidationDetails,
  referenceLocalities,
  type ReferenceLocality,
} from "@/shared/lib/api";

type FormPhase = "form" | "submitted";

export function OwnerVenueClaimEntry() {
  const [venueName, setVenueName] = useState("");
  const [localityId, setLocalityId] = useState("");
  const [addressLine1, setAddressLine1] = useState("");
  const [claimantNote, setClaimantNote] = useState("");
  const [localities, setLocalities] = useState<ReferenceLocality[]>([]);
  const [localitiesLoading, setLocalitiesLoading] = useState(true);
  const [localitiesError, setLocalitiesError] = useState("");
  const [phase, setPhase] = useState<FormPhase>("form");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    let active = true;
    setLocalitiesLoading(true);
    setLocalitiesError("");
    void referenceLocalities()
      .then(({ data }) => {
        if (!active) return;
        setLocalities(data.localities);
      })
      .catch((err) => {
        if (!active) return;
        setLocalities([]);
        setLocalitiesError(formatApiError(err));
      })
      .finally(() => {
        if (active) setLocalitiesLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmedName = venueName.trim();
    const trimmedAddress = addressLine1.trim();
    const nextErrors: Record<string, string> = {};
    if (!trimmedName) nextErrors.venueName = "Pub name is required.";
    if (!trimmedAddress) nextErrors.addressLine1 = "Address is required.";
    if (!localityId) nextErrors.localityId = "Suburb / locality is required.";
    if (Object.keys(nextErrors).length > 0) {
      setFieldErrors(nextErrors);
      return;
    }

    setFieldErrors({});
    setError("");
    setSubmitting(true);
    try {
      const { data } = await ownerVenueClaimRequest({
        mode: "submit_new_or_claim",
        venue_name: trimmedName,
        address_line_1: trimmedAddress,
        locality_id: localityId,
        claimant_note: claimantNote.trim() || undefined,
      });
      setSuccessMessage(data.message);
      setPhase("submitted");
    } catch (err) {
      if (isApiRequestError(err)) {
        const details = parseApiValidationDetails(err);
        const next: Record<string, string> = {};
        if (details.venue_name?.[0]) next.venueName = details.venue_name[0];
        if (details.address_line_1?.[0]) next.addressLine1 = details.address_line_1[0];
        if (details.locality_id?.[0]) next.localityId = details.locality_id[0];
        if (Object.keys(next).length > 0) {
          setFieldErrors(next);
        } else {
          setError(formatApiError(err));
        }
      } else {
        setError(formatApiError(err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (phase === "submitted") {
    return (
      <div className="rounded-lg border border-green-200 bg-green-50 p-6">
        <h3 className="text-lg font-semibold text-slate-900">Submitted for review</h3>
        <p className="mt-2 text-sm text-slate-700">{successMessage}</p>
      </div>
    );
  }

  return (
    <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
      {localitiesError ? (
        <ErrorBanner
          message={`Could not load locality options: ${localitiesError}`}
          onDismiss={() => setLocalitiesError("")}
        />
      ) : null}
      <div>
        <label htmlFor="claimVenueName" className="text-sm font-medium text-slate-800">
          Pub name
        </label>
        <input
          id="claimVenueName"
          type="text"
          className={`mt-1 w-full rounded border px-3 py-2 text-sm ${
            fieldErrors.venueName ? "border-red-400 bg-red-50" : "border-slate-300"
          }`}
          value={venueName}
          onChange={(event) => setVenueName(event.target.value)}
          placeholder="e.g. The Royal Hotel"
        />
        {fieldErrors.venueName ? (
          <p className="mt-1 text-xs text-red-700">{fieldErrors.venueName}</p>
        ) : null}
      </div>
      <div>
        <label htmlFor="claimAddressLine1" className="text-sm font-medium text-slate-800">
          Address
        </label>
        <input
          id="claimAddressLine1"
          type="text"
          className={`mt-1 w-full rounded border px-3 py-2 text-sm ${
            fieldErrors.addressLine1 ? "border-red-400 bg-red-50" : "border-slate-300"
          }`}
          value={addressLine1}
          onChange={(event) => setAddressLine1(event.target.value)}
          placeholder="Street address"
        />
        {fieldErrors.addressLine1 ? (
          <p className="mt-1 text-xs text-red-700">{fieldErrors.addressLine1}</p>
        ) : null}
      </div>
      <div>
        <label htmlFor="claimLocalityId" className="text-sm font-medium text-slate-800">
          Suburb / locality
        </label>
        <select
          id="claimLocalityId"
          className={`mt-1 w-full rounded border px-3 py-2 text-sm ${
            fieldErrors.localityId ? "border-red-400 bg-red-50" : "border-slate-300"
          }`}
          value={localityId}
          onChange={(event) => setLocalityId(event.target.value)}
          disabled={localitiesLoading}
        >
          <option value="">
            {localitiesLoading ? "Loading localities…" : "Select a suburb / locality"}
          </option>
          {localities.map((locality) => (
            <option key={locality.id} value={locality.id}>
              {locality.name}
              {locality.state ? `, ${locality.state}` : ""}
            </option>
          ))}
        </select>
        {fieldErrors.localityId ? (
          <p className="mt-1 text-xs text-red-700">{fieldErrors.localityId}</p>
        ) : null}
      </div>
      <div>
        <label htmlFor="claimantNote" className="text-sm font-medium text-slate-800">
          Tell us your role or how you&apos;re connected to this venue (optional)
        </label>
        <textarea
          id="claimantNote"
          rows={3}
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={claimantNote}
          onChange={(event) => setClaimantNote(event.target.value)}
          placeholder="e.g. I am the licensee and can verify with our ABN."
        />
      </div>
      <button
        type="submit"
        className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-60"
        disabled={submitting}
      >
        {submitting ? "Submitting…" : "Submit for review"}
      </button>
    </form>
  );
}
