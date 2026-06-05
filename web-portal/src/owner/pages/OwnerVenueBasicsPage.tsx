import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  buildHoursPatch,
  buildOperationalProfilePatch,
  buildRestrictedChangePayload,
  createDefaultWeeklyHours,
  hasRestrictedPendingReview,
  hydrateBasicsFormFromDetail,
  operationalFormChanged,
  publishedBaselinesFromDetail,
  type BasicsFormValues,
  type DayHoursState,
  type PublishedBaselines,
} from "@/owner/lib/ownerVenueBasicsForm";
import {
  mapServerValidationToFormErrors,
  validateOperationalForm,
  validateRestrictedForm,
  type BasicsFieldErrors,
} from "@/owner/lib/ownerVenueValidation";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerPatchHours,
  ownerPatchOperationalProfile,
  ownerRestrictedChangeRequest,
  ownerVenueDetail,
  parseApiValidationDetails,
  referenceLocalities,
  type OwnerVenueDetail,
  type ReferenceLocality,
} from "@/shared/lib/api";

const OPERATIONAL_SUCCESS_MESSAGE =
  "Saved. These updates are now reflected on your listing.";
const RESTRICTED_SUCCESS_MESSAGE =
  "Change request submitted. We'll review it before updating your listing.";
const RESTRICTED_ALREADY_PENDING =
  "Your change request is already waiting for review.";
const MISSING_DIRECT_CAPABILITY_MESSAGE =
  "Your account is not set up to edit this listing yet.";
const MISSING_RESTRICTED_CAPABILITY_MESSAGE =
  "Your account is not set up to request listing changes yet.";

function fieldClass(hasError: boolean, disabled?: boolean) {
  return `mt-1 w-full rounded border px-3 py-2 text-sm ${
    disabled ? "bg-slate-100 text-slate-500" : hasError ? "border-red-400 bg-red-50" : "border-slate-300"
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

function ownerCapabilityMessage(err: unknown, kind: "direct" | "restricted"): string | null {
  if (!isApiRequestError(err) || err.code !== "forbidden") return null;
  const msg = err.message.toLowerCase();
  if (kind === "direct" && msg.includes("direct listing edits")) {
    return MISSING_DIRECT_CAPABILITY_MESSAGE;
  }
  if (kind === "restricted" && msg.includes("change requests")) {
    return MISSING_RESTRICTED_CAPABILITY_MESSAGE;
  }
  return null;
}

export function OwnerVenueBasicsPage() {
  const { venueId } = useParams<{ venueId: string }>();
  const [detail, setDetail] = useState<OwnerVenueDetail | null>(null);
  const [baseline, setBaseline] = useState<PublishedBaselines | null>(null);
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
  }));
  const [fieldErrors, setFieldErrors] = useState<BasicsFieldErrors>({});
  const [loading, setLoading] = useState(true);
  const [localitiesLoading, setLocalitiesLoading] = useState(true);
  const [savingOperational, setSavingOperational] = useState(false);
  const [savingRestricted, setSavingRestricted] = useState(false);
  const [error, setError] = useState("");
  const [accessError, setAccessError] = useState<"forbidden" | "not_found" | null>(null);
  const [localitiesError, setLocalitiesError] = useState("");
  const [operationalSuccess, setOperationalSuccess] = useState("");
  const [restrictedSuccess, setRestrictedSuccess] = useState("");

  const loadPage = useCallback(async () => {
    if (!venueId) return;
    setLoading(true);
    setError("");
    setAccessError(null);
    try {
      const { data } = await ownerVenueDetail(venueId);
      setDetail(data);
      setBaseline(publishedBaselinesFromDetail(data));
      setValues(hydrateBasicsFormFromDetail(data));
    } catch (err) {
      setDetail(null);
      setBaseline(null);
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

  function clearFieldError(key: string) {
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }

  function updateField<K extends keyof BasicsFormValues>(key: K, value: BasicsFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
    clearFieldError(key as string);
    setOperationalSuccess("");
    setRestrictedSuccess("");
  }

  function updateDayHours(dayOfWeek: number, patch: Partial<DayHoursState>) {
    setValues((prev) => ({
      ...prev,
      weeklyHours: prev.weeklyHours.map((day) =>
        day.dayOfWeek === dayOfWeek ? { ...day, ...patch } : day,
      ),
    }));
    clearFieldError(`hours.${dayOfWeek}.opensAt`);
    clearFieldError(`hours.${dayOfWeek}.closesAt`);
    clearFieldError("openingHours");
    setOperationalSuccess("");
  }

  async function handleSaveOperational() {
    if (!venueId || !baseline) return;
    setError("");
    setOperationalSuccess("");
    setRestrictedSuccess("");

    const validationErrors = validateOperationalForm(values);
    if (Object.keys(validationErrors).length > 0) {
      setFieldErrors(validationErrors);
      setError("Please check the highlighted fields.");
      return;
    }

    if (!operationalFormChanged(values, baseline)) {
      setError("No listing detail changes to save.");
      return;
    }

    setFieldErrors({});
    setSavingOperational(true);
    try {
      const profilePatch = buildOperationalProfilePatch(values, baseline);
      const hoursPatch = buildHoursPatch(values, baseline);

      if (profilePatch) {
        await ownerPatchOperationalProfile(venueId, profilePatch);
      }
      if (hoursPatch) {
        await ownerPatchHours(venueId, hoursPatch);
      }

      setOperationalSuccess(OPERATIONAL_SUCCESS_MESSAGE);
      await loadPage();
    } catch (err) {
      const capMsg = ownerCapabilityMessage(err, "direct");
      if (capMsg) {
        setError(capMsg);
        return;
      }
      if (isApiRequestError(err) && err.code === "validation_error") {
        const mapped = mapServerValidationToFormErrors(parseApiValidationDetails(err));
        setFieldErrors(mapped);
        setError(err.message || "Please check the highlighted fields.");
        return;
      }
      setError(formatApiError(err));
    } finally {
      setSavingOperational(false);
    }
  }

  async function handleRequestRestrictedChange() {
    if (!venueId || !baseline) return;
    setError("");
    setOperationalSuccess("");
    setRestrictedSuccess("");

    const validationErrors = validateRestrictedForm(values);
    if (Object.keys(validationErrors).length > 0) {
      setFieldErrors(validationErrors);
      setError("Please check the highlighted fields.");
      return;
    }

    const payload = buildRestrictedChangePayload(values, baseline);
    if (!payload) {
      setError("Change at least one name or address field before requesting approval.");
      return;
    }

    setFieldErrors({});
    setSavingRestricted(true);
    try {
      const { data } = await ownerRestrictedChangeRequest(venueId, {
        section: "identity_location",
        payload,
      });
      const message =
        data.message.toLowerCase().includes("already waiting") ||
        data.message.toLowerCase().includes("already submitted")
          ? RESTRICTED_ALREADY_PENDING
          : RESTRICTED_SUCCESS_MESSAGE;
      setRestrictedSuccess(message);
      await loadPage();
    } catch (err) {
      const capMsg = ownerCapabilityMessage(err, "restricted");
      if (capMsg) {
        setError(capMsg);
        return;
      }
      if (isApiRequestError(err) && err.code === "validation_error") {
        const mapped = mapServerValidationToFormErrors(parseApiValidationDetails(err));
        setFieldErrors(mapped);
        setError(err.message || "Please check the highlighted fields.");
        return;
      }
      setError(formatApiError(err));
    } finally {
      setSavingRestricted(false);
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
        <Link to="/owner" className="inline-block text-sm font-medium text-slate-900 underline">
          Back to owner home
        </Link>
      </div>
    );
  }

  if (!detail || !baseline) {
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

  const restrictedPending = hasRestrictedPendingReview(detail);
  const restrictedDisabled = restrictedPending;

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
          Step 1 — Pub details
        </p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Pub details</h1>
        <p className="mt-2 text-sm text-slate-600">
          Update descriptions and hours instantly. Name and address changes need our review first.
        </p>
      </div>

      {restrictedPending ? (
        <StatusBanner>Name/address change pending review.</StatusBanner>
      ) : null}
      {operationalSuccess ? <SuccessBanner>{operationalSuccess}</SuccessBanner> : null}
      {restrictedSuccess ? <SuccessBanner>{restrictedSuccess}</SuccessBanner> : null}

      <ErrorBanner message={error} onDismiss={error ? () => setError("") : undefined} />
      {localitiesError ? (
        <ErrorBanner
          message={`Could not load locality options: ${localitiesError}`}
          onDismiss={() => setLocalitiesError("")}
        />
      ) : null}

      <section className="space-y-6 rounded-lg border border-slate-200 p-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">
            Listing details you can update now
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Descriptions and opening hours save directly to your public listing.
          </p>
        </div>

        <fieldset className="space-y-4">
          <legend className="px-1 text-sm font-semibold text-slate-900">Description</legend>
          <FieldError message={fieldErrors.operational} />
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

        <fieldset className="space-y-4">
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
              className={fieldClass(Boolean(fieldErrors.hoursNotes))}
              value={values.hoursNotes}
              onChange={(e) => updateField("hoursNotes", e.target.value)}
              placeholder="e.g. Kitchen closes at 9pm; hours may vary on public holidays."
            />
            <FieldError message={fieldErrors.hoursNotes} />
          </div>
        </fieldset>

        <button
          type="button"
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          disabled={savingOperational}
          onClick={() => void handleSaveOperational()}
        >
          {savingOperational ? "Saving…" : "Save changes"}
        </button>
      </section>

      <section className="space-y-6 rounded-lg border border-amber-200 bg-amber-50/40 p-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Details that require approval</h2>
          <p className="mt-1 text-sm text-slate-600">
            Your venue name and address identify the listing, so we review these changes before
            updating them.
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Some details, like your venue name and address, need approval before changing.
          </p>
        </div>

        <fieldset className="space-y-4" disabled={restrictedDisabled}>
          <legend className="px-1 text-sm font-semibold text-slate-900">Venue name</legend>
          <FieldError message={fieldErrors.restricted} />
          <div>
            <label htmlFor="displayName" className="text-sm font-medium text-slate-800">
              Display name
            </label>
            <input
              id="displayName"
              type="text"
              className={fieldClass(Boolean(fieldErrors.displayName), restrictedDisabled)}
              value={values.displayName}
              onChange={(e) => updateField("displayName", e.target.value)}
              autoComplete="organization"
            />
            <FieldError message={fieldErrors.displayName} />
          </div>
        </fieldset>

        <fieldset className="space-y-4" disabled={restrictedDisabled}>
          <legend className="px-1 text-sm font-semibold text-slate-900">Address</legend>
          <div>
            <label htmlFor="addressLine1" className="text-sm font-medium text-slate-800">
              Address line 1
            </label>
            <input
              id="addressLine1"
              type="text"
              className={fieldClass(Boolean(fieldErrors.addressLine1), restrictedDisabled)}
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
              className={fieldClass(Boolean(fieldErrors.addressLine2), restrictedDisabled)}
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
              className={fieldClass(Boolean(fieldErrors.postalCode), restrictedDisabled)}
              value={values.postalCode}
              onChange={(e) => updateField("postalCode", e.target.value)}
              autoComplete="postal-code"
            />
            <FieldError message={fieldErrors.postalCode} />
          </div>
        </fieldset>

        <fieldset className="space-y-4" disabled={restrictedDisabled}>
          <legend className="px-1 text-sm font-semibold text-slate-900">Locality</legend>
          <div>
            <label htmlFor="localityId" className="text-sm font-medium text-slate-800">
              Suburb / locality
            </label>
            <select
              id="localityId"
              className={fieldClass(Boolean(fieldErrors.localityId), restrictedDisabled)}
              value={values.localityId}
              onChange={(e) => updateField("localityId", e.target.value)}
              disabled={localitiesLoading || restrictedDisabled}
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

        <button
          type="button"
          className="rounded border border-slate-800 bg-white px-4 py-2 text-sm font-medium text-slate-900 hover:bg-slate-50 disabled:opacity-60"
          disabled={savingRestricted || restrictedDisabled}
          onClick={() => void handleRequestRestrictedChange()}
        >
          {savingRestricted ? "Submitting…" : "Request change"}
        </button>
      </section>
    </div>
  );
}
