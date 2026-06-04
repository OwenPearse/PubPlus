import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { NoVenueAccessState } from "@/owner/components/NoVenueAccessState";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  ownerAuthProbe,
  ownerProvision,
  type OwnerAuthProbeBody,
} from "@/shared/lib/api";
import { portalBrand } from "@/shared/lib/portalBrand";

export function OwnerHomePlaceholder() {
  const [probe, setProbe] = useState<OwnerAuthProbeBody | null>(null);
  const [loading, setLoading] = useState(true);
  const [provisioning, setProvisioning] = useState(false);
  const [error, setError] = useState("");

  async function loadProbe() {
    setLoading(true);
    setError("");
    try {
      const result = await ownerAuthProbe();
      setProbe(result.body);
    } catch (err) {
      setError(formatApiError(err));
      setProbe(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProbe();
  }, []);

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

  if (probe.next_step === "enroll_mfa") {
    return (
      <div className="max-w-lg space-y-4">
        <h1 className="text-2xl font-bold text-slate-900">Two-step verification required</h1>
        <p className="text-sm text-slate-600">
          Finish setting up your authenticator before using the owner portal.
        </p>
        <Link to="/access" className="text-sm font-medium text-slate-900 underline">
          Continue at sign-in
        </Link>
      </div>
    );
  }

  if (probe.next_step === "owner_waiting_for_membership") {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold text-slate-900">Owner portal</h1>
        <NoVenueAccessState variant="membership" businessCount={probe.business_count} />
      </div>
    );
  }

  if (probe.next_step === "owner_waiting_for_venue_access") {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold text-slate-900">Owner portal</h1>
        <NoVenueAccessState
          variant="venue"
          businessCount={probe.business_count}
          venueCount={probe.venue_count}
        />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold text-slate-900">Owner portal</h1>
      <p className="text-sm text-slate-600">
        Welcome to {portalBrand.productName}. Your account is ready; venue management features will
        appear here in a future release.
      </p>
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <p>Businesses: {probe.business_count}</p>
        <p className="mt-1">Approved venues: {probe.venue_count}</p>
      </div>
    </div>
  );
}
