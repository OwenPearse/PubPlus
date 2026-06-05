import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { NoVenueAccessState } from "@/owner/components/NoVenueAccessState";
import { OptionalMfaSecurityPrompt } from "@/owner/components/OptionalMfaSecurityPrompt";
import {
  formatVenueLocation,
  listItemStatusMessage,
  onboardingStatusLabel,
  OWNER_HUB_HEADLINE,
  OWNER_HUB_REVIEW_NOTE,
  OWNER_HUB_SUBHEAD,
} from "@/owner/lib/ownerVenueUi";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerAuthProbe,
  ownerProvision,
  ownerVenueList,
  type OwnerAuthProbeBody,
  type OwnerVenueListItem,
  type OwnerVenueListResponse,
} from "@/shared/lib/api";
import { getPortalSupportUrl } from "@/shared/lib/env";
import { portalBrand } from "@/shared/lib/portalBrand";

function VenuePickerCard({ venue }: { venue: OwnerVenueListItem }) {
  const location = formatVenueLocation(venue.locality_name, venue.state_code);
  const statusNote = listItemStatusMessage(venue);

  return (
    <Link
      to={`/owner/venues/${venue.venue_id}`}
      className="flex flex-col rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300 hover:shadow-md"
    >
      <h2 className="text-lg font-semibold text-slate-900">{venue.display_name}</h2>
      <p className="mt-1 text-sm text-slate-600">{location}</p>
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-600">
        <span className="rounded-full bg-slate-100 px-2 py-0.5">
          {venue.completeness_percent}% complete
        </span>
        <span className="rounded-full bg-slate-100 px-2 py-0.5">
          {onboardingStatusLabel(venue.onboarding_status)}
        </span>
        {venue.pending_proposal_count > 0 ? (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-900">
            {venue.pending_proposal_count} pending
          </span>
        ) : null}
      </div>
      {statusNote ? <p className="mt-3 text-sm text-slate-700">{statusNote}</p> : null}
      <span className="mt-4 text-sm font-medium text-slate-900">Continue listing →</span>
    </Link>
  );
}

function VenueListEmptyState() {
  const supportUrl = getPortalSupportUrl();
  return (
    <div className="max-w-lg rounded-lg border border-amber-200 bg-amber-50 p-6">
      <h2 className="text-lg font-semibold text-slate-900">No venues assigned yet</h2>
      <p className="mt-2 text-sm text-slate-700">
        Your owner account is ready, but we could not find any approved venues to manage. An
        administrator must link your business to a venue before you can complete your listing.
      </p>
      {supportUrl ? (
        <p className="mt-3 text-sm">
          <a href={supportUrl} className="font-medium text-slate-900 underline" target="_blank" rel="noreferrer">
            Contact support
          </a>
        </p>
      ) : null}
    </div>
  );
}

export function OwnerPortalEntry() {
  const navigate = useNavigate();
  const [probe, setProbe] = useState<OwnerAuthProbeBody | null>(null);
  const [venues, setVenues] = useState<OwnerVenueListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [venuesLoading, setVenuesLoading] = useState(false);
  const [provisioning, setProvisioning] = useState(false);
  const [error, setError] = useState("");
  const [mfaPromptDismissed, setMfaPromptDismissed] = useState(false);

  async function loadProbe() {
    setLoading(true);
    setError("");
    try {
      const result = await ownerAuthProbe();
      setProbe(result.body);
      return result.body;
    } catch (err) {
      setError(formatApiError(err));
      setProbe(null);
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function loadVenues() {
    setVenuesLoading(true);
    setError("");
    try {
      const { data } = await ownerVenueList();
      setVenues(data);
      return data;
    } catch (err) {
      setError(formatApiError(err));
      setVenues(null);
      return null;
    } finally {
      setVenuesLoading(false);
    }
  }

  useEffect(() => {
    void loadProbe();
  }, []);

  useEffect(() => {
    if (!probe || probe.next_step !== "portal_home") {
      setVenues(null);
      return;
    }
    void loadVenues();
  }, [probe?.next_step]);

  useEffect(() => {
    if (!venues) return;
    const defaultId = venues.meta.default_venue_id;
    if (venues.venues.length === 1 && defaultId) {
      navigate(`/owner/venues/${defaultId}`, { replace: true });
    }
  }, [venues, navigate]);

  async function handleProvision() {
    setProvisioning(true);
    setError("");
    try {
      await ownerProvision();
      await loadProbe();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setProvisioning(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-600">Loading owner portal…</p>;
  }

  if (!probe) {
    return (
      <div className="max-w-lg">
        <ErrorBanner message={error} />
        <button
          type="button"
          className="mt-4 text-sm font-medium text-slate-900 underline"
          onClick={() => void loadProbe()}
        >
          Retry
        </button>
      </div>
    );
  }

  if (probe.next_step === "complete_owner_provisioning") {
    return (
      <div className="max-w-lg space-y-4">
        <h1 className="text-2xl font-bold text-slate-900">{portalBrand.productName}</h1>
        <p className="text-sm text-slate-600">
          Your sign-in is valid, but your owner account still needs to be provisioned on our servers.
        </p>
        <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
        <button
          type="button"
          className="rounded bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-60"
          onClick={() => void handleProvision()}
          disabled={provisioning}
        >
          {provisioning ? "Provisioning…" : "Complete owner setup"}
        </button>
      </div>
    );
  }

  const showOptionalMfaPrompt =
    !mfaPromptDismissed && probe.aal === "aal1" && !probe.mfa_enabled;

  if (
    probe.next_step === "owner_waiting_for_membership" ||
    probe.next_step === "owner_waiting_for_venue_access"
  ) {
    return (
      <div className="max-w-2xl space-y-4">
        {showOptionalMfaPrompt ? (
          <OptionalMfaSecurityPrompt onDismiss={() => setMfaPromptDismissed(true)} />
        ) : null}
        <NoVenueAccessState />
      </div>
    );
  }

  if (venuesLoading || (venues?.venues.length === 1 && venues.meta.default_venue_id)) {
    return <p className="text-sm text-slate-600">Loading your venues…</p>;
  }

  if (!venues) {
    return (
      <div className="max-w-lg space-y-4">
        <ErrorBanner message={error} />
        <button
          type="button"
          className="mt-2 text-sm font-medium text-slate-900 underline"
          onClick={() => void loadVenues()}
        >
          Retry
        </button>
      </div>
    );
  }

  if (venues.venues.length === 0) {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold text-slate-900">{OWNER_HUB_HEADLINE}</h1>
        {showOptionalMfaPrompt ? (
          <OptionalMfaSecurityPrompt onDismiss={() => setMfaPromptDismissed(true)} />
        ) : null}
        <VenueListEmptyState />
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{OWNER_HUB_HEADLINE}</h1>
        <p className="mt-2 text-sm text-slate-600">{OWNER_HUB_SUBHEAD}</p>
        <p className="mt-1 text-sm text-slate-500">{OWNER_HUB_REVIEW_NOTE}</p>
      </div>
      {showOptionalMfaPrompt ? (
        <OptionalMfaSecurityPrompt onDismiss={() => setMfaPromptDismissed(true)} />
      ) : null}
      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
      <p className="text-sm text-slate-700">Choose a venue to continue your listing.</p>
      <div className="grid gap-4 sm:grid-cols-2">
        {venues.venues.map((venue) => (
          <VenuePickerCard key={venue.venue_id} venue={venue} />
        ))}
      </div>
    </div>
  );
}
