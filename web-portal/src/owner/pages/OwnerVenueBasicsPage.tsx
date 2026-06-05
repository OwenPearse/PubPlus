import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  buildCoreDetailsPayload,
  createDefaultWeeklyHours,
  hasPendingReview,
  hasSavedDraft,
  hydrateBasicsFormFromDetail,
  type BasicsFormValues,
  type DayHoursState,
} from "@/owner/lib/ownerVenueBasicsForm";
import {
  mapServerValidationToFormErrors,
  validateBasicsForm,
  type BasicsFieldErrors,
} from "@/owner/lib/ownerVenueValidation";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerVenueDetail,
  ownerVenueProposal,
  parseApiValidationDetails,
  referenceLocalities,
  type OwnerVenueDetail,
  type ReferenceLocality,
} from "@/shared/lib/api";

const SAVED_DRAFT_MESSAGE = "Saved. You can come back anytime to finish or submit.";
const SUBMITTED_MESSAGE =
  "Submitted for review. Your changes will be reviewed before they appear publicly.";

function fieldClass(hasError: boolean) {
  return `mt-1 w-full rounded border px-3 py-2 text-sm ${
    hasError ? "border-red-400 bg-red-50" : "border-slate-300"
  }`;
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="mt-1 text-xs text-red-700">{message}</p>;
}

function StatusBanner({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
      {children}
    </div>
  );
}

function SuccessBanner({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-900">
      {children}
    </div>
  );
}

export function OwnerVenueBasicsPage() {
  const { venueId } = useParams<{ venueId: string }>();
  const [detail, setDetail] = useState<OwnerVenueDetail | null>(null);
  const [localities, setLocalities] = useState<ReferenceLocality[]>([]);
  const [values, setValues] = useState<BasicsFormValues>(() => ({
    displayName: "",
    addressLine1: "",
    addressLine2: "",
    postalCode: "",
    localityId: "",
    countryCode: "AU",
    shortDescription: "",
    longDescription: "",
    hoursNotes: "",
    weeklyHours: createDefaultWeeklyHours(),
    ownerConfirmsManagement: false,
  }));
  const [fieldErrors, setFieldErrors] = useState<BasicsFieldErrors>({});
  const [loading, setLoading] = useState(true);
  const [localitiesLoading, setLocalitiesLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [accessError, setAccessError] = useState<"forbidden" | "not_found" | null>(null);
  const [localitiesError, setLocalitiesError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const loadPage = useCallback(async () => {
    if (!venueId) return;
    setLoading(true);
    setError("");
    setAccessError(null);
    try {
      const { data } = await ownerVenueDetail(venueId);
      setDetail(data);
      setValues(hydrateBasicsFormFromDetail(data));
    } catch (err) {
      setDetail(null);
      if (isApiRequestError(err)) {
        if (err.code === "forbidden" || err.code === "not_found") {
          setAccessError(err.code);
          return;
        }
      }
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [venueId]);

  const loadLocalities = useCallback(async () => {
    setLocalitiesLoading(true);
    setLocalitiesError("");
    try {
      const { data } = await referenceLocalities();
      setLocalities(data.localities);
    } catch (err) {
      setLocalities([]);
      setLocalitiesError(formatApiError(err));
    } finally {
      setLocalitiesLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPage();
    void loadLocalities();
  }, [loadPage, loadLocalities]);

  function updateField<K extends keyof BasicsFormValues>(key: K, value: BasicsFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[key as string];
      return next;
    });
    setSuccessMessage("");
  }

  function updateDayHours(dayOfWeek: number, patch: Partial<DayHoursState>) {
    setValues((prev) => ({
      ...prev,
      weeklyHours: prev.weeklyHours.map((day) =>
        day.dayOfWeek === dayOfWeek ? { ...day, ...patch } : day,
      ),
    }));
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[`hours.${dayOfWeek}.opensAt`];
      delete next[`hours.${dayOfWeek}.closesAt`];
      delete next.openingHours;
      return next;
    });
    setSuccessMessage("");
  }

  async function handleSave(intent: "draft" | "submit") {
    if (!venueId) return;
    setError("");
    setSuccessMessage("");
    setSubmitted(false);

    const validationErrors = validateBasicsForm(values, intent);
    if (Object.keys(validationErrors).length > 0) {
      setFieldErrors(validationErrors);
      setError("Please check the highlighted fields.");
      return;
    }

    setFieldErrors({});
    setSaving(true);
    try {
      const { data } = await ownerVenueProposal(venueId, {
        section: "core_details",
        intent,
        payload: buildCoreDetailsPayload(values),
      });
      if (intent === "draft") {
        setSuccessMessage(SAVED_DRAFT_MESSAGE);
      } else {
        setSuccessMessage(SUBMITTED_MESSAGE);
        setSubmitted(true);
      }
      await loadPage();
      if (data.message && intent === "submit") {
        setSuccessMessage(SUBMITTED_MESSAGE);
      }
    } catch (err) {
      if (isApiRequestError(err) && err.code === "validation_error") {
        const serverDetails = parseApiValidationDetails(err);
        const mapped = mapServerValidationToFormErrors(serverDetails);
        setFieldErrors(mapped);
        setError(err.message || "Please check the highlighted fields.");
        return;
      }
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  }

  if (!venueId) {
    return (
      <div className="max-w-lg">
        <ErrorBanner message="Venue ID is missing." />
      </div>
    );
  }

  if (loading) {
    return <p className="text-sm text-slate-600">Loading pub details…</p>;
  }

  if (accessError) {
    return (
      <div className="max-w-lg space-y-4">
        <h1 className="text-xl font-bold text-slate-900">Pub details</h1>
        <p className="text-sm text-slate-600">We could not open this venue for your account.</p>
        <Link
          to="/owner"
          className="inline-block text-sm font-medium text-slate-900 underline"
        >
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
          onClick={() => void loadPage()}
        >
          Retry
        </button>
        <Link
          to={`/owner/venues/${venueId}`}
          className="block text-sm text-slate-600 underline"
        >
          Back to checklist
        </Link>
      </div>
    );
  }

  const showPendingBanner = hasPendingReview(detail);
  const showDraftBanner = hasSavedDraft(detail);

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <Link
          to={`/owner/venues/${venueId}`}
          className="text-sm text-slate-600 underline"
        >
          ← Back to checklist
        </Link>
        <p className="mt-3 text-sm font-medium text-slate-700">
          Step 1 of 1 — Confirm your pub details
        </p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Pub details</h1>
        <p className="mt-2 text-sm text-slate-600">
          This helps customers find your venue and understand what to expect.
        </p>
        <p className="mt-1 text-sm text-slate-500">
          Your changes are reviewed before they appear publicly. You can save progress and come
          back anytime.
        </p>
      </div>

      {showPendingBanner ? (
        <StatusBanner>Your latest changes are waiting for review.</StatusBanner>
      ) : null}
      {showDraftBanner ? <StatusBanner>You have a saved draft.</StatusBanner> : null}
      {successMessage ? <SuccessBanner>{successMessage}</SuccessBanner> : null}

      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
      {localitiesError ? (
        <ErrorBanner
          message={`Could not load locality options: ${localitiesError}`}
          onDismiss={() => setLocalitiesError("")}
        />
      ) : null}

      <form
        className="space-y-8"
        onSubmit={(event) => {
          event.preventDefault();
          void handleSave("submit");
        }}
      >
        <fieldset className="space-y-4 rounded-lg border border-slate-200 p-4">
          <legend className="px-1 text-sm font-semibold text-slate-900">Venue name</legend>
          <div>
            <label htmlFor="displayName" className="text-sm font-medium text-slate-800">
              Display name
            </label>
            <input
              id="displayName"
              type="text"
              className={fieldClass(Boolean(fieldErrors.displayName))}
              value={values.displayName}
              onChange={(e) => updateField("displayName", e.target.value)}
              autoComplete="organization"
            />
            <FieldError message={fieldErrors.displayName} />
          </div>
        </fieldset>

        <fieldset className="space-y-4 rounded-lg border border-slate-200 p-4">
          <legend className="px-1 text-sm font-semibold text-slate-900">Address</legend>
          <div>
            <label htmlFor="addressLine1" className="text-sm font-medium text-slate-800">
              Address line 1
            </label>
            <input
              id="addressLine1"
              type="text"
              className={fieldClass(Boolean(fieldErrors.addressLine1))}
              value={values.addressLine1}
              onChange={(e) => updateField("addressLine1", e.target.value)}
              autoComplete="address-line1"
            />
            <FieldError message={fieldErrors.addressLine1} />
          </div>
          <div>
            <label htmlFor="addressLine2" className="text-sm font-medium text-slate-800">
              Address line 2 <span className="text-slate-500">(optional)</span>
            </label>
            <input
              id="addressLine2"
              type="text"
              className={fieldClass(Boolean(fieldErrors.addressLine2))}
              value={values.addressLine2}
              onChange={(e) => updateField("addressLine2", e.target.value)}
              autoComplete="address-line2"
            />
            <FieldError message={fieldErrors.addressLine2} />
          </div>
          <div>
            <label htmlFor="postalCode" className="text-sm font-medium text-slate-800">
              Postcode <span className="text-slate-500">(optional)</span>
            </label>
            <input
              id="postalCode"
              type="text"
              className={fieldClass(Boolean(fieldErrors.postalCode))}
              value={values.postalCode}
              onChange={(e) => updateField("postalCode", e.target.value)}
              autoComplete="postal-code"
            />
            <FieldError message={fieldErrors.postalCode} />
          </div>
        </fieldset>

        <fieldset className="space-y-4 rounded-lg border border-slate-200 p-4">
          <legend className="px-1 text-sm font-semibold text-slate-900">Locality</legend>
          <div>
            <label htmlFor="localityId" className="text-sm font-medium text-slate-800">
              Suburb / locality
            </label>
            <select
              id="localityId"
              className={fieldClass(Boolean(fieldErrors.localityId))}
              value={values.localityId}
              onChange={(e) => updateField("localityId", e.target.value)}
              disabled={localitiesLoading}
            >
              <option value="">
                {localitiesLoading ? "Loading localities…" : "Select a locality"}
              </option>
              {localities.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                  {loc.state ? `, ${loc.state}` : ""}
                </option>
              ))}
            </select>
            <FieldError message={fieldErrors.localityId} />
          </div>
        </fieldset>

        <fieldset className="space-y-4 rounded-lg border border-slate-200 p-4">
          <legend className="px-1 text-sm font-semibold text-slate-900">Description</legend>
          <div>
            <label htmlFor="shortDescription" className="text-sm font-medium text-slate-800">
              Short description
            </label>
            <textarea
              id="shortDescription"
              rows={3}
              className={fieldClass(Boolean(fieldErrors.shortDescription))}
              value={values.shortDescription}
              onChange={(e) => updateField("shortDescription", e.target.value)}
            />
            <FieldError message={fieldErrors.shortDescription} />
          </div>
          <div>
            <label htmlFor="longDescription" className="text-sm font-medium text-slate-800">
              Long description <span className="text-slate-500">(optional)</span>
            </label>
            <textarea
              id="longDescription"
              rows={5}
              className={fieldClass(Boolean(fieldErrors.longDescription))}
              value={values.longDescription}
              onChange={(e) => updateField("longDescription", e.target.value)}
            />
            <FieldError message={fieldErrors.longDescription} />
          </div>
        </fieldset>

        <fieldset className="space-y-4 rounded-lg border border-slate-200 p-4">
          <legend className="px-1 text-sm font-semibold text-slate-900">Opening hours</legend>
          <FieldError message={fieldErrors.openingHours} />
          <div className="space-y-3">
            {values.weeklyHours.map((day) => (
              <div
                key={day.dayOfWeek}
                className="rounded border border-slate-100 bg-slate-50 p-3"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <span className="w-24 text-sm font-medium text-slate-800">{day.label}</span>
                  <label className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={day.closed}
                      onChange={(e) => updateDayHours(day.dayOfWeek, { closed: e.target.checked })}
                    />
                    Closed
                  </label>
                  {!day.closed ? (
                    <>
                      <label className="flex flex-col text-xs text-slate-600">
                        Opens
                        <input
                          type="text"
                          inputMode="numeric"
                          placeholder="HH:MM"
                          className={fieldClass(
                            Boolean(fieldErrors[`hours.${day.dayOfWeek}.opensAt`]),
                          )}
                          value={day.opensAt}
                          onChange={(e) =>
                            updateDayHours(day.dayOfWeek, { opensAt: e.target.value })
                          }
                        />
                      </label>
                      <label className="flex flex-col text-xs text-slate-600">
                        Closes
                        <input
                          type="text"
                          inputMode="numeric"
                          placeholder="HH:MM"
                          className={fieldClass(
                            Boolean(fieldErrors[`hours.${day.dayOfWeek}.closesAt`]),
                          )}
                          value={day.closesAt}
                          onChange={(e) =>
                            updateDayHours(day.dayOfWeek, { closesAt: e.target.value })
                          }
                        />
                      </label>
                      <label className="flex items-center gap-2 text-sm text-slate-700">
                        <input
                          type="checkbox"
                          checked={day.crossesMidnight}
                          onChange={(e) =>
                            updateDayHours(day.dayOfWeek, { crossesMidnight: e.target.checked })
                          }
                        />
                        Crosses midnight
                      </label>
                    </>
                  ) : null}
                </div>
                <FieldError message={fieldErrors[`hours.${day.dayOfWeek}.opensAt`]} />
                <FieldError message={fieldErrors[`hours.${day.dayOfWeek}.closesAt`]} />
              </div>
            ))}
          </div>
          <div>
            <label htmlFor="hoursNotes" className="text-sm font-medium text-slate-800">
              Hours notes <span className="text-slate-500">(optional)</span>
            </label>
            <textarea
              id="hoursNotes"
              rows={2}
              className={fieldClass(false)}
              value={values.hoursNotes}
              onChange={(e) => updateField("hoursNotes", e.target.value)}
              placeholder="e.g. Kitchen closes at 9pm; hours may vary on public holidays."
            />
          </div>
        </fieldset>

        <fieldset className="space-y-3 rounded-lg border border-slate-200 p-4">
          <legend className="px-1 text-sm font-semibold text-slate-900">
            Confirm you manage this venue
          </legend>
          <label className="flex items-start gap-3 text-sm text-slate-700">
            <input
              type="checkbox"
              className="mt-0.5"
              checked={values.ownerConfirmsManagement}
              onChange={(e) => updateField("ownerConfirmsManagement", e.target.checked)}
            />
            <span>I confirm I manage this venue and the information I provide is accurate.</span>
          </label>
          <FieldError message={fieldErrors.ownerConfirmsManagement} />
        </fieldset>

        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <button
            type="button"
            className="rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
            disabled={saving}
            onClick={() => void handleSave("draft")}
          >
            {saving ? "Saving…" : "Save progress"}
          </button>
          <button
            type="submit"
            className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
            disabled={saving}
          >
            {saving ? "Submitting…" : "Submit for review"}
          </button>
        </div>

        {submitted ? (
          <p className="text-sm text-slate-600">
            <Link
              to={`/owner/venues/${venueId}`}
              className="font-medium text-slate-900 underline"
            >
              Return to checklist
            </Link>
          </p>
        ) : null}
      </form>
    </div>
  );
}
