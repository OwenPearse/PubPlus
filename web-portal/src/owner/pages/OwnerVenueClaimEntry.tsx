import { useEffect, useState } from "react";

import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerVenueClaimCandidates,
  ownerVenueClaimRequest,
  parseApiValidationDetails,
  referenceLocalities,
  type ReferenceLocality,
  type VenueClaimCandidate,
} from "@/shared/lib/api";

type SearchPhase = "form" | "results" | "submitted";

function formatCandidateLocation(candidate: VenueClaimCandidate): string {
  const parts = [candidate.locality_name, candidate.state_code].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : "Location unknown";
}

export function OwnerVenueClaimEntry() {
  const [venueName, setVenueName] = useState("");
  const [localityId, setLocalityId] = useState("");
  const [addressLine1, setAddressLine1] = useState("");
  const [claimantNote, setClaimantNote] = useState("");
  const [localities, setLocalities] = useState<ReferenceLocality[]>([]);
  const [localitiesLoading, setLocalitiesLoading] = useState(true);
  const [localitiesError, setLocalitiesError] = useState("");
  const [phase, setPhase] = useState<SearchPhase>("form");
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [candidates, setCandidates] = useState<VenueClaimCandidate[]>([]);
  const [bestMatch, setBestMatch] = useState<VenueClaimCandidate | null>(null);
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

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    const trimmedName = venueName.trim();
    if (!trimmedName) {
      setFieldErrors({ venueName: "Venue name is required." });
      return;
    }
    setFieldErrors({});
    setError("");
    setSearching(true);
    try {
      const { data } = await ownerVenueClaimCandidates({
        name: trimmedName,
        locality_id: localityId || undefined,
        address_line_1: addressLine1.trim() || undefined,
      });
      setCandidates(data.candidates);
      setBestMatch(data.best_match);
      setPhase("results");
    } catch (err) {
      if (isApiRequestError(err)) {
        const details = parseApiValidationDetails(err);
        if (details.name?.[0]) {
          setFieldErrors({ venueName: details.name[0] });
        } else if (details.locality_id?.[0]) {
          setFieldErrors({ localityId: details.locality_id[0] });
        } else {
          setError(formatApiError(err));
        }
      } else {
        setError(formatApiError(err));
      }
    } finally {
      setSearching(false);
    }
  }

  async function submitClaimExisting(candidate: VenueClaimCandidate) {
    setSubmitting(true);
    setError("");
    try {
      const { data } = await ownerVenueClaimRequest({
        mode: "claim_existing",
        venue_id: candidate.venue_id,
        claimant_note: claimantNote.trim() || undefined,
      });
      setSuccessMessage(data.message);
      setPhase("submitted");
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function submitNewVenue() {
    setSubmitting(true);
    setError("");
    setFieldErrors({});
    try {
      const { data } = await ownerVenueClaimRequest({
        mode: "submit_new",
        venue_name: venueName.trim(),
        address_line_1: addressLine1.trim() || undefined,
        locality_id: localityId || undefined,
        claimant_note: claimantNote.trim() || undefined,
      });
      setSuccessMessage(data.message);
      setPhase("submitted");
    } catch (err) {
      if (isApiRequestError(err)) {
        const details = parseApiValidationDetails(err);
        const next: Record<string, string> = {};
        if (details.venue_name?.[0]) next.venueName = details.venue_name[0];
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
        <h3 className="text-lg font-semibold text-slate-900">Claim request submitted</h3>
        <p className="mt-2 text-sm text-slate-700">{successMessage}</p>
      </div>
    );
  }

  if (phase === "results") {
    return (
      <div className="space-y-4">
        <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
        {bestMatch ? (
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-5">
            <h3 className="text-base font-semibold text-slate-900">This looks like your venue</h3>
            <p className="mt-2 text-sm font-medium text-slate-900">{bestMatch.display_name}</p>
            <p className="text-sm text-slate-700">{formatCandidateLocation(bestMatch)}</p>
            {bestMatch.address_line_1 ? (
              <p className="text-sm text-slate-600">{bestMatch.address_line_1}</p>
            ) : null}
            <p className="mt-2 text-xs text-slate-600">{bestMatch.match_reason}</p>
            <button
              type="button"
              className="mt-4 rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-60"
              onClick={() => void submitClaimExisting(bestMatch)}
              disabled={submitting}
            >
              {submitting ? "Submitting…" : "Request to claim this listing"}
            </button>
          </div>
        ) : (
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <h3 className="text-base font-semibold text-slate-900">
              We couldn&apos;t find a matching listing
            </h3>
            <p className="mt-2 text-sm text-slate-700">
              Submit your venue details for review and we&apos;ll add it after confirming you manage
              it.
            </p>
            <button
              type="button"
              className="mt-4 rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-60"
              onClick={() => void submitNewVenue()}
              disabled={submitting}
            >
              {submitting ? "Submitting…" : "Submit as a new venue for review"}
            </button>
          </div>
        )}
        {candidates.length > 1 ? (
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <h4 className="text-sm font-semibold text-slate-900">Other possible matches</h4>
            <ul className="mt-3 space-y-3">
              {candidates
                .filter((candidate) => candidate.venue_id !== bestMatch?.venue_id)
                .map((candidate) => (
                  <li
                    key={candidate.venue_id}
                    className="flex flex-col gap-2 border-b border-slate-100 pb-3 last:border-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-900">{candidate.display_name}</p>
                      <p className="text-xs text-slate-600">
                        {formatCandidateLocation(candidate)}
                        {candidate.address_line_1 ? ` · ${candidate.address_line_1}` : ""}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="rounded border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
                      onClick={() => void submitClaimExisting(candidate)}
                      disabled={submitting}
                    >
                      Request to claim
                    </button>
                  </li>
                ))}
            </ul>
          </div>
        ) : null}
        <button
          type="button"
          className="text-sm font-medium text-slate-900 underline"
          onClick={() => {
            setPhase("form");
            setCandidates([]);
            setBestMatch(null);
            setError("");
          }}
        >
          Edit venue details
        </button>
      </div>
    );
  }

  return (
    <form className="space-y-4" onSubmit={(event) => void handleSearch(event)}>
      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
      {localitiesError ? (
        <ErrorBanner
          message={`Could not load locality options: ${localitiesError}`}
          onDismiss={() => setLocalitiesError("")}
        />
      ) : null}
      <div>
        <label htmlFor="claimVenueName" className="text-sm font-medium text-slate-800">
          Venue name
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
            {localitiesLoading ? "Loading localities…" : "Select a locality (optional)"}
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
        <label htmlFor="claimAddressLine1" className="text-sm font-medium text-slate-800">
          Address (optional)
        </label>
        <input
          id="claimAddressLine1"
          type="text"
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={addressLine1}
          onChange={(event) => setAddressLine1(event.target.value)}
          placeholder="Street address"
        />
      </div>
      <div>
        <label htmlFor="claimantNote" className="text-sm font-medium text-slate-800">
          Note proving you manage the venue
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
        disabled={searching}
      >
        {searching ? "Searching…" : "Add or claim a venue"}
      </button>
    </form>
  );
}
