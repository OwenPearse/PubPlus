import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  FEATURES_MISSING_CAPABILITY_MESSAGE,
  FEATURES_PAGE_HELPER,
  FEATURES_PAGE_TITLE,
  FEATURES_SAVE_LABEL,
  FEATURES_SUCCESS_MESSAGE,
  groupOwnerVenueFeatures,
} from "@/owner/lib/ownerVenueFeaturesUi";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerPatchVenueFeatures,
  ownerVenueFeatures,
  type OwnerVenueFeatureItem,
} from "@/shared/lib/api";

function SuccessBanner({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-900">
      {children}
    </div>
  );
}

function ownerFeaturesCapabilityMessage(err: unknown): string | null {
  if (!isApiRequestError(err) || err.code !== "forbidden") return null;
  const msg = err.message.toLowerCase();
  if (msg.includes("direct listing edits")) {
    return FEATURES_MISSING_CAPABILITY_MESSAGE;
  }
  return null;
}

export function OwnerVenueFeaturesPage() {
  const { venueId } = useParams<{ venueId: string }>();
  const [features, setFeatures] = useState<OwnerVenueFeatureItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [accessError, setAccessError] = useState<"forbidden" | "not_found" | null>(
    null,
  );

  const loadFeatures = useCallback(async () => {
    if (!venueId) return;
    setLoading(true);
    setError("");
    setAccessError(null);
    try {
      const { data } = await ownerVenueFeatures(venueId);
      setFeatures(data.features);
    } catch (err) {
      setFeatures([]);
      const capabilityMsg = ownerFeaturesCapabilityMessage(err);
      if (capabilityMsg) {
        setAccessError("forbidden");
        setError(capabilityMsg);
        return;
      }
      if (isApiRequestError(err)) {
        if (err.code === "forbidden") {
          setAccessError("forbidden");
          return;
        }
        if (err.code === "not_found") {
          setAccessError("not_found");
          return;
        }
      }
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [venueId]);

  useEffect(() => {
    void loadFeatures();
  }, [loadFeatures]);

  const toggleFeature = (attributeDefinitionId: string, checked: boolean) => {
    setSuccess("");
    setFeatures((current) =>
      current.map((feature) =>
        feature.attribute_definition_id === attributeDefinitionId
          ? { ...feature, value: checked }
          : feature,
      ),
    );
  };

  const handleSave = async () => {
    if (!venueId) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const { data } = await ownerPatchVenueFeatures(venueId, {
        features: features.map((feature) => ({
          attribute_definition_id: feature.attribute_definition_id,
          value_boolean: feature.value,
        })),
      });
      setFeatures(data.features);
      setSuccess(data.message ?? FEATURES_SUCCESS_MESSAGE);
    } catch (err) {
      const capabilityMsg = ownerFeaturesCapabilityMessage(err);
      if (capabilityMsg) {
        setError(capabilityMsg);
      } else {
        setError(formatApiError(err));
      }
    } finally {
      setSaving(false);
    }
  };

  if (!venueId) {
    return (
      <div className="max-w-lg">
        <ErrorBanner message="Venue ID is missing." />
        <Link to="/owner" className="mt-4 inline-block text-sm font-medium text-slate-900 underline">
          Back to owner home
        </Link>
      </div>
    );
  }

  if (loading) {
    return <p className="text-sm text-slate-600">Loading features…</p>;
  }

  if (accessError === "not_found") {
    return (
      <div className="max-w-lg space-y-4">
        <h1 className="text-xl font-bold text-slate-900">Venue not found</h1>
        <p className="text-sm text-slate-600">
          This venue does not exist or is no longer available to your account.
        </p>
        <Link to="/owner" className="text-sm font-medium text-slate-900 underline">
          Back to owner home
        </Link>
      </div>
    );
  }

  if (accessError === "forbidden" && !features.length) {
    return (
      <div className="max-w-lg space-y-4">
        <h1 className="text-xl font-bold text-slate-900">{FEATURES_PAGE_TITLE}</h1>
        <p className="text-sm text-slate-600">
          {error || "You do not have permission to manage this venue."}
        </p>
        <Link
          to={`/owner/venues/${venueId}`}
          className="text-sm font-medium text-slate-900 underline"
        >
          Back to venue hub
        </Link>
      </div>
    );
  }

  const grouped = groupOwnerVenueFeatures(features);

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <Link
          to={`/owner/venues/${venueId}`}
          className="text-sm text-slate-600 underline"
        >
          ← Venue hub
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">{FEATURES_PAGE_TITLE}</h1>
        <p className="mt-2 text-sm text-slate-600">{FEATURES_PAGE_HELPER}</p>
      </div>

      {success ? <SuccessBanner>{success}</SuccessBanner> : null}
      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />

      <div className="space-y-6">
        {grouped.map((group) => (
          <section key={group.key} className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-semibold text-slate-900">{group.label}</h2>
            <ul className="mt-3 space-y-3">
              {group.items.map((feature) => (
                <li key={feature.attribute_definition_id}>
                  <label className="flex cursor-pointer items-center gap-3 text-sm text-slate-800">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-slate-300"
                      checked={feature.value}
                      onChange={(event) =>
                        toggleFeature(
                          feature.attribute_definition_id,
                          event.target.checked,
                        )
                      }
                    />
                    <span>{feature.label}</span>
                  </label>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          disabled={saving || features.length === 0}
          onClick={() => void handleSave()}
        >
          {saving ? "Saving…" : FEATURES_SAVE_LABEL}
        </button>
        <Link
          to={`/owner/venues/${venueId}`}
          className="text-sm font-medium text-slate-700 underline"
        >
          Back to venue hub
        </Link>
      </div>
    </div>
  );
}
