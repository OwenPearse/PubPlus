import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  DAY_LABELS,
  formatDaysAvailable,
  formatTimeWindow,
  MEAL_SPECIALS_ADD_LABEL,
  MEAL_SPECIALS_MISSING_CAPABILITY_MESSAGE,
  MEAL_SPECIALS_PAGE_HELPER,
  MEAL_SPECIALS_PAGE_TITLE,
  MEAL_SPECIALS_SAVE_LABEL,
  MEAL_SPECIALS_SUCCESS_MESSAGE,
} from "@/owner/lib/ownerVenueMealSpecialsUi";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerCreateMealSpecial,
  ownerDeactivateMealSpecial,
  ownerPatchMealSpecial,
  ownerVenueMealSpecials,
  type OwnerMealSpecial,
  type OwnerMealSpecialInput,
} from "@/shared/lib/api";

function SuccessBanner({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-900">
      {children}
    </div>
  );
}

type FormState = {
  title: string;
  description: string;
  days_available: number[];
  start_time: string;
  end_time: string;
  price_text: string;
  conditions: string;
  active: boolean;
};

const EMPTY_FORM: FormState = {
  title: "",
  description: "",
  days_available: [],
  start_time: "",
  end_time: "",
  price_text: "",
  conditions: "",
  active: true,
};

function specialToForm(special: OwnerMealSpecial): FormState {
  return {
    title: special.title,
    description: special.description ?? "",
    days_available: [...special.days_available],
    start_time: special.start_time ?? "",
    end_time: special.end_time ?? "",
    price_text: special.price_text ?? "",
    conditions: special.conditions ?? "",
    active: special.active,
  };
}

function formToPayload(form: FormState): OwnerMealSpecialInput {
  const hasStart = form.start_time.trim().length > 0;
  const hasEnd = form.end_time.trim().length > 0;
  return {
    title: form.title.trim(),
    description: form.description.trim() || null,
    days_available: form.days_available.length > 0 ? form.days_available : [],
    start_time: hasStart ? form.start_time.trim() : null,
    end_time: hasEnd ? form.end_time.trim() : null,
    price_text: form.price_text.trim() || null,
    conditions: form.conditions.trim() || null,
    active: form.active,
  };
}

function validateForm(form: FormState): string | null {
  const title = form.title.trim();
  if (title.length < 2) return "Special name must be at least 2 characters.";
  if (title.length > 120) return "Special name must be at most 120 characters.";
  const hasStart = form.start_time.trim().length > 0;
  const hasEnd = form.end_time.trim().length > 0;
  if (hasStart !== hasEnd) {
    return "Start and end time must both be set, or both left empty.";
  }
  const timePattern = /^([01]\d|2[0-3]):[0-5]\d$/;
  if (hasStart && !timePattern.test(form.start_time.trim())) {
    return "Start time must use HH:MM format.";
  }
  if (hasEnd && !timePattern.test(form.end_time.trim())) {
    return "End time must use HH:MM format.";
  }
  return null;
}

function ownerMealSpecialsCapabilityMessage(err: unknown): string | null {
  if (!isApiRequestError(err) || err.code !== "forbidden") return null;
  const msg = err.message.toLowerCase();
  if (msg.includes("direct listing edits")) {
    return MEAL_SPECIALS_MISSING_CAPABILITY_MESSAGE;
  }
  return null;
}

function MealSpecialForm({
  form,
  setForm,
  onSubmit,
  onCancel,
  saving,
  submitLabel,
}: {
  form: FormState;
  setForm: React.Dispatch<React.SetStateAction<FormState>>;
  onSubmit: () => void;
  onCancel: () => void;
  saving: boolean;
  submitLabel: string;
}) {
  const toggleDay = (day: number) => {
    setForm((current) => {
      const days = current.days_available.includes(day)
        ? current.days_available.filter((d) => d !== day)
        : [...current.days_available, day].sort((a, b) => a - b);
      return { ...current, days_available: days };
    });
  };

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div>
        <label htmlFor="meal-special-title" className="block text-sm font-medium text-slate-900">
          Special name
        </label>
        <input
          id="meal-special-title"
          type="text"
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.title}
          onChange={(e) => setForm((c) => ({ ...c, title: e.target.value }))}
        />
      </div>
      <div>
        <label htmlFor="meal-special-description" className="block text-sm font-medium text-slate-900">
          Description
        </label>
        <textarea
          id="meal-special-description"
          rows={3}
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.description}
          onChange={(e) => setForm((c) => ({ ...c, description: e.target.value }))}
        />
      </div>
      <fieldset>
        <legend className="text-sm font-medium text-slate-900">Days available</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {DAY_LABELS.map((label, day) => (
            <label key={label} className="flex items-center gap-1.5 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={form.days_available.includes(day)}
                onChange={() => toggleDay(day)}
              />
              {label.slice(0, 3)}
            </label>
          ))}
        </div>
        <p className="mt-1 text-xs text-slate-500">Leave all unchecked for every day.</p>
      </fieldset>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="meal-special-start" className="block text-sm font-medium text-slate-900">
            Start time
          </label>
          <input
            id="meal-special-start"
            type="time"
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={form.start_time}
            onChange={(e) => setForm((c) => ({ ...c, start_time: e.target.value }))}
          />
        </div>
        <div>
          <label htmlFor="meal-special-end" className="block text-sm font-medium text-slate-900">
            End time
          </label>
          <input
            id="meal-special-end"
            type="time"
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={form.end_time}
            onChange={(e) => setForm((c) => ({ ...c, end_time: e.target.value }))}
          />
        </div>
      </div>
      <div>
        <label htmlFor="meal-special-price" className="block text-sm font-medium text-slate-900">
          Price
        </label>
        <input
          id="meal-special-price"
          type="text"
          placeholder="$20"
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.price_text}
          onChange={(e) => setForm((c) => ({ ...c, price_text: e.target.value }))}
        />
      </div>
      <div>
        <label htmlFor="meal-special-conditions" className="block text-sm font-medium text-slate-900">
          Conditions
        </label>
        <input
          id="meal-special-conditions"
          type="text"
          placeholder="Dine-in only"
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.conditions}
          onChange={(e) => setForm((c) => ({ ...c, conditions: e.target.value }))}
        />
      </div>
      <label className="flex items-center gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.active}
          onChange={(e) => setForm((c) => ({ ...c, active: e.target.checked }))}
        />
        Active on listing
      </label>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={saving}
          onClick={onSubmit}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {submitLabel}
        </button>
        <button
          type="button"
          disabled={saving}
          onClick={onCancel}
          className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-white"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export function OwnerVenueMealSpecialsPage() {
  const { venueId } = useParams<{ venueId: string }>();
  const [specials, setSpecials] = useState<OwnerMealSpecial[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [accessError, setAccessError] = useState<"forbidden" | "not_found" | null>(null);
  const [formMode, setFormMode] = useState<"hidden" | "create" | "edit">("hidden");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);

  const loadSpecials = useCallback(async () => {
    if (!venueId) return;
    setLoading(true);
    setError("");
    setAccessError(null);
    try {
      const { data } = await ownerVenueMealSpecials(venueId);
      setSpecials(data.meal_specials);
    } catch (err) {
      setSpecials([]);
      const capabilityMsg = ownerMealSpecialsCapabilityMessage(err);
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
    void loadSpecials();
  }, [loadSpecials]);

  const openCreate = () => {
    setSuccess("");
    setError("");
    setForm(EMPTY_FORM);
    setEditingId(null);
    setFormMode("create");
  };

  const openEdit = (special: OwnerMealSpecial) => {
    setSuccess("");
    setError("");
    setForm(specialToForm(special));
    setEditingId(special.id);
    setFormMode("edit");
  };

  const closeForm = () => {
    setFormMode("hidden");
    setEditingId(null);
    setForm(EMPTY_FORM);
  };

  const handleSave = async () => {
    if (!venueId) return;
    const validationError = validateForm(form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      if (formMode === "create") {
        const { data } = await ownerCreateMealSpecial(venueId, formToPayload(form));
        setSpecials((current) => [...current, data.meal_special]);
        setSuccess(data.message ?? MEAL_SPECIALS_SUCCESS_MESSAGE);
      } else if (formMode === "edit" && editingId) {
        const { data } = await ownerPatchMealSpecial(
          venueId,
          editingId,
          formToPayload(form),
        );
        setSpecials((current) =>
          current.map((s) => (s.id === editingId ? data.meal_special : s)),
        );
        setSuccess(data.message ?? MEAL_SPECIALS_SUCCESS_MESSAGE);
      }
      closeForm();
    } catch (err) {
      const capabilityMsg = ownerMealSpecialsCapabilityMessage(err);
      setError(capabilityMsg ?? formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (specialId: string) => {
    if (!venueId) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const { data } = await ownerDeactivateMealSpecial(venueId, specialId);
      setSpecials((current) =>
        current.map((s) => (s.id === specialId ? data.meal_special : s)),
      );
      setSuccess(data.message ?? MEAL_SPECIALS_SUCCESS_MESSAGE);
      if (editingId === specialId) closeForm();
    } catch (err) {
      setError(formatApiError(err));
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
    return <p className="text-sm text-slate-600">Loading meal specials…</p>;
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

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <Link
          to={`/owner/venues/${venueId}`}
          className="text-sm font-medium text-slate-600 underline"
        >
          Back to checklist
        </Link>
        <h1 className="mt-2 text-xl font-bold text-slate-900">{MEAL_SPECIALS_PAGE_TITLE}</h1>
        <p className="mt-1 text-sm text-slate-600">{MEAL_SPECIALS_PAGE_HELPER}</p>
      </div>

      {error ? <ErrorBanner message={error} /> : null}
      {success ? <SuccessBanner>{success}</SuccessBanner> : null}

      {formMode !== "hidden" ? (
        <MealSpecialForm
          form={form}
          setForm={setForm}
          onSubmit={() => void handleSave()}
          onCancel={closeForm}
          saving={saving}
          submitLabel={MEAL_SPECIALS_SAVE_LABEL}
        />
      ) : (
        <button
          type="button"
          onClick={openCreate}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          {MEAL_SPECIALS_ADD_LABEL}
        </button>
      )}

      {specials.length === 0 && formMode === "hidden" ? (
        <p className="text-sm text-slate-600">
          No meal specials yet. Add your first parma night, steak night or Sunday roast.
        </p>
      ) : (
        <ul className="space-y-3">
          {specials.map((special) => (
            <li
              key={special.id}
              className={`rounded-lg border p-4 ${
                special.active ? "border-slate-200 bg-white" : "border-slate-100 bg-slate-50 opacity-75"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-medium text-slate-900">{special.title}</h2>
                  {!special.active ? (
                    <span className="mt-1 inline-block text-xs text-slate-500">Inactive</span>
                  ) : null}
                  {special.description ? (
                    <p className="mt-1 text-sm text-slate-600">{special.description}</p>
                  ) : null}
                  <p className="mt-2 text-xs text-slate-500">
                    {formatDaysAvailable(special.days_available)} ·{" "}
                    {formatTimeWindow(special.start_time, special.end_time)}
                    {special.price_text ? ` · ${special.price_text}` : ""}
                  </p>
                  {special.conditions ? (
                    <p className="mt-1 text-xs text-slate-500">{special.conditions}</p>
                  ) : null}
                </div>
                <div className="flex shrink-0 flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => openEdit(special)}
                    className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
                  >
                    Edit
                  </button>
                  {special.active ? (
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void handleDeactivate(special.id)}
                      className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      Deactivate
                    </button>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
