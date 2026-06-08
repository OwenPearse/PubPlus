import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PHOTOS_HUB_DESCRIPTION } from "@/owner/lib/ownerVenuePhotosUi";
import {
  FEATURES_HUB_DESCRIPTION,
} from "@/owner/lib/ownerVenueFeaturesUi";
import { MEAL_SPECIALS_HUB_DESCRIPTION } from "@/owner/lib/ownerVenueMealSpecialsUi";
import { TAP_LIST_HUB_DESCRIPTION } from "@/owner/lib/ownerVenueTapListUi";
import {
  formatVenueLocation,
  OWNER_HUB_HEADLINE,
  OWNER_HUB_REVIEW_NOTE,
  OWNER_HUB_SUBHEAD,
  sectionIsDeferred,
  venueHubStatusMessage,
} from "@/owner/lib/ownerVenueUi";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerVenueDetail,
  type OwnerVenueCompletenessSection,
  type OwnerVenueDetail,
} from "@/shared/lib/api";

function CompletenessBar({ percent }: { percent: number }) {
  const clamped = Math.min(100, Math.max(0, percent));
  return (
    <div className="mt-2">
      <div className="flex items-center justify-between text-sm text-slate-600">
        <span>Listing progress</span>
        <span>{clamped}%</span>
      </div>
      <div
        className="mt-1 h-2 overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full bg-slate-900 transition-all"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}

function ChecklistRow({
  venueId,
  section,
}: {
  venueId: string;
  section: OwnerVenueCompletenessSection;
}) {
  const deferred = sectionIsDeferred(section);
  const isCore = section.key === "core_details" && section.available;
  const isMealSpecials = section.key === "meal_specials" && section.available;
  const isTapList = section.key === "tap_list" && section.available;
  const isFeatures = section.key === "features" && section.available;
  const isPhotos = section.key === "photos" && section.available;

  return (
    <li
      className={`rounded-lg border p-4 ${
        deferred ? "border-slate-100 bg-slate-50" : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-medium text-slate-900">{section.label}</h3>
            {section.required ? (
              <span className="rounded bg-slate-900 px-1.5 py-0.5 text-xs text-white">
                Required
              </span>
            ) : (
              <span className="text-xs text-slate-500">Optional</span>
            )}
          </div>
          {deferred ? (
            <p className="mt-2 text-sm text-slate-600">
              Coming later — you can skip this for now.
            </p>
          ) : isMealSpecials ? (
            <p className="mt-2 text-sm text-slate-600">{MEAL_SPECIALS_HUB_DESCRIPTION}</p>
          ) : isTapList ? (
            <p className="mt-2 text-sm text-slate-600">{TAP_LIST_HUB_DESCRIPTION}</p>
          ) : isFeatures ? (
            <p className="mt-2 text-sm text-slate-600">{FEATURES_HUB_DESCRIPTION}</p>
          ) : isPhotos ? (
            <p className="mt-2 text-sm text-slate-600">{PHOTOS_HUB_DESCRIPTION}</p>
          ) : (
            <p className="mt-1 text-xs capitalize text-slate-500">{section.status}</p>
          )}
        </div>
        {isCore ? (
          <Link
            to={`/owner/venues/${venueId}/basics`}
            className="shrink-0 rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Edit pub details
          </Link>
        ) : isMealSpecials ? (
          <Link
            to={`/owner/venues/${venueId}/meal-specials`}
            className="shrink-0 rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Edit meal specials
          </Link>
        ) : isTapList ? (
          <Link
            to={`/owner/venues/${venueId}/tap-list`}
            className="shrink-0 rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Edit tap list
          </Link>
        ) : isFeatures ? (
          <Link
            to={`/owner/venues/${venueId}/features`}
            className="shrink-0 rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Edit features
          </Link>
        ) : isPhotos ? (
          <Link
            to={`/owner/venues/${venueId}/photos`}
            className="shrink-0 rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Edit photos
          </Link>
        ) : (
          <span
            className="shrink-0 rounded border border-slate-200 px-3 py-2 text-sm text-slate-400"
            aria-disabled="true"
          >
            Coming later
          </span>
        )}
      </div>
    </li>
  );
}

export function OwnerVenueHub() {
  const { venueId } = useParams<{ venueId: string }>();
  const [detail, setDetail] = useState<OwnerVenueDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [accessError, setAccessError] = useState<"forbidden" | "not_found" | null>(null);

  const loadDetail = useCallback(async () => {
    if (!venueId) return;
    setLoading(true);
    setError("");
    setAccessError(null);
    try {
      const { data } = await ownerVenueDetail(venueId);
      setDetail(data);
    } catch (err) {
      setDetail(null);
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
    void loadDetail();
  }, [loadDetail]);

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
    return <p className="text-sm text-slate-600">Loading venue…</p>;
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

  if (accessError === "forbidden") {
    return (
      <div className="max-w-lg space-y-4">
        <h1 className="text-xl font-bold text-slate-900">Access denied</h1>
        <p className="text-sm text-slate-600">
          You do not have permission to manage this venue.
        </p>
        <Link to="/owner" className="text-sm font-medium text-slate-900 underline">
          Back to owner home
        </Link>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="max-w-lg space-y-4">
        <ErrorBanner message={error || "Could not load this venue."} />
        <button
          type="button"
          className="text-sm font-medium text-slate-900 underline"
          onClick={() => void loadDetail()}
        >
          Retry
        </button>
        <Link to="/owner" className="block text-sm text-slate-600 underline">
          Back to owner home
        </Link>
      </div>
    );
  }

  const location = formatVenueLocation(
    detail.published.location.locality_name,
    detail.published.location.state_code,
  );
  const statusMessage = venueHubStatusMessage(detail);
  const addressLine = detail.published.location.address_line_1;

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <Link to="/owner" className="text-sm text-slate-600 underline">
          ← All venues
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">{detail.display_name}</h1>
        <p className="mt-1 text-sm text-slate-600">
          {addressLine ? `${addressLine} · ` : ""}
          {location}
        </p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm font-medium text-slate-900">{OWNER_HUB_HEADLINE}</p>
        <p className="mt-1 text-sm text-slate-600">{OWNER_HUB_SUBHEAD}</p>
        <p className="mt-1 text-xs text-slate-500">{OWNER_HUB_REVIEW_NOTE}</p>
        <CompletenessBar percent={detail.completeness.percent} />
        <p className="mt-3 text-sm text-slate-700">
          {detail.completeness.required_basics_complete
            ? "Required basics are complete."
            : "Required basics still need attention."}
        </p>
      </div>

      {statusMessage ? (
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
          {statusMessage}
        </div>
      ) : null}

      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />

      <section>
        <h2 className="text-lg font-semibold text-slate-900">Your checklist</h2>
        <ul className="mt-4 space-y-3">
          {detail.completeness.sections.map((section) => (
            <ChecklistRow key={section.key} venueId={venueId} section={section} />
          ))}
        </ul>
      </section>
    </div>
  );
}
