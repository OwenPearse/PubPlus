import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  formatTapAvailability,
  TAP_AVAILABILITY_OPTIONS,
  TAP_LIST_ADD_LABEL,
  TAP_LIST_MISSING_CAPABILITY_MESSAGE,
  TAP_LIST_PAGE_HELPER,
  TAP_LIST_PAGE_TITLE,
  TAP_LIST_SAVE_LABEL,
  TAP_LIST_SUCCESS_MESSAGE,
} from "@/owner/lib/ownerVenueTapListUi";
import { ErrorBanner } from "@/shared/components/ErrorBanner";
import {
  formatApiError,
  isApiRequestError,
  ownerCreateTapListItem,
  ownerDeactivateTapListItem,
  ownerPatchTapListItem,
  ownerVenueTapList,
  type OwnerTapListItem,
  type OwnerTapListItemInput,
} from "@/shared/lib/api";

function SuccessBanner({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-900">
      {children}
    </div>
  );
}

type FormState = {
  drink_name: string;
  brewery_or_brand: string;
  drink_type: string;
  abv: string;
  price_text: string;
  availability: OwnerTapListItemInput["availability"];
  notes: string;
  active: boolean;
};

const EMPTY_FORM: FormState = {
  drink_name: "",
  brewery_or_brand: "",
  drink_type: "",
  abv: "",
  price_text: "",
  availability: "permanent",
  notes: "",
  active: true,
};

function itemToForm(item: OwnerTapListItem): FormState {
  return {
    drink_name: item.drink_name,
    brewery_or_brand: item.brewery_or_brand ?? "",
    drink_type: item.drink_type ?? "",
    abv: item.abv ?? "",
    price_text: item.price_text ?? "",
    availability: item.availability ?? "permanent",
    notes: item.notes ?? "",
    active: item.active,
  };
}

function formToPayload(form: FormState): OwnerTapListItemInput {
  return {
    drink_name: form.drink_name.trim(),
    brewery_or_brand: form.brewery_or_brand.trim() || null,
    drink_type: form.drink_type.trim() || null,
    abv: form.abv.trim() || null,
    price_text: form.price_text.trim() || null,
    availability: form.availability ?? "permanent",
    notes: form.notes.trim() || null,
    active: form.active,
  };
}

function validateForm(form: FormState): string | null {
  const drinkName = form.drink_name.trim();
  if (drinkName.length < 2) return "Drink name must be at least 2 characters.";
  if (drinkName.length > 120) return "Drink name must be at most 120 characters.";
  return null;
}

function ownerTapListCapabilityMessage(err: unknown): string | null {
  if (!isApiRequestError(err) || err.code !== "forbidden") return null;
  const msg = err.message.toLowerCase();
  if (msg.includes("direct listing edits")) {
    return TAP_LIST_MISSING_CAPABILITY_MESSAGE;
  }
  return null;
}

function TapListItemForm({
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
  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div>
        <label htmlFor="tap-drink-name" className="block text-sm font-medium text-slate-900">
          Drink name
        </label>
        <input
          id="tap-drink-name"
          type="text"
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.drink_name}
          onChange={(e) => setForm((c) => ({ ...c, drink_name: e.target.value }))}
        />
      </div>
      <div>
        <label htmlFor="tap-brewery" className="block text-sm font-medium text-slate-900">
          Brewery / brand
        </label>
        <input
          id="tap-brewery"
          type="text"
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.brewery_or_brand}
          onChange={(e) => setForm((c) => ({ ...c, brewery_or_brand: e.target.value }))}
        />
      </div>
      <div>
        <label htmlFor="tap-type" className="block text-sm font-medium text-slate-900">
          Type
        </label>
        <input
          id="tap-type"
          type="text"
          placeholder="Pale ale, red wine, cocktail…"
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.drink_type}
          onChange={(e) => setForm((c) => ({ ...c, drink_type: e.target.value }))}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="tap-abv" className="block text-sm font-medium text-slate-900">
            ABV
          </label>
          <input
            id="tap-abv"
            type="text"
            placeholder="4.4%"
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={form.abv}
            onChange={(e) => setForm((c) => ({ ...c, abv: e.target.value }))}
          />
        </div>
        <div>
          <label htmlFor="tap-price" className="block text-sm font-medium text-slate-900">
            Price
          </label>
          <input
            id="tap-price"
            type="text"
            placeholder="$12 schooner"
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={form.price_text}
            onChange={(e) => setForm((c) => ({ ...c, price_text: e.target.value }))}
          />
        </div>
      </div>
      <div>
        <label htmlFor="tap-availability" className="block text-sm font-medium text-slate-900">
          Permanent or rotating
        </label>
        <select
          id="tap-availability"
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.availability ?? "permanent"}
          onChange={(e) =>
            setForm((c) => ({
              ...c,
              availability: e.target.value as FormState["availability"],
            }))
          }
        >
          {TAP_AVAILABILITY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="tap-notes" className="block text-sm font-medium text-slate-900">
          Notes
        </label>
        <textarea
          id="tap-notes"
          rows={2}
          className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          value={form.notes}
          onChange={(e) => setForm((c) => ({ ...c, notes: e.target.value }))}
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

export function OwnerVenueTapListPage() {
  const { venueId } = useParams<{ venueId: string }>();
  const [items, setItems] = useState<OwnerTapListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [accessError, setAccessError] = useState<"forbidden" | "not_found" | null>(null);
  const [formMode, setFormMode] = useState<"hidden" | "create" | "edit">("hidden");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);

  const loadItems = useCallback(async () => {
    if (!venueId) return;
    setLoading(true);
    setError("");
    setAccessError(null);
    try {
      const { data } = await ownerVenueTapList(venueId);
      setItems(data.tap_list);
    } catch (err) {
      setItems([]);
      const capabilityMsg = ownerTapListCapabilityMessage(err);
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
    void loadItems();
  }, [loadItems]);

  const openCreate = () => {
    setSuccess("");
    setError("");
    setForm(EMPTY_FORM);
    setEditingId(null);
    setFormMode("create");
  };

  const openEdit = (item: OwnerTapListItem) => {
    setSuccess("");
    setError("");
    setForm(itemToForm(item));
    setEditingId(item.id);
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
        const { data } = await ownerCreateTapListItem(venueId, formToPayload(form));
        setItems((current) => [...current, data.tap_item]);
        setSuccess(data.message ?? TAP_LIST_SUCCESS_MESSAGE);
      } else if (formMode === "edit" && editingId) {
        const { data } = await ownerPatchTapListItem(
          venueId,
          editingId,
          formToPayload(form),
        );
        setItems((current) =>
          current.map((item) => (item.id === editingId ? data.tap_item : item)),
        );
        setSuccess(data.message ?? TAP_LIST_SUCCESS_MESSAGE);
      }
      closeForm();
    } catch (err) {
      setError(ownerTapListCapabilityMessage(err) ?? formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (itemId: string) => {
    if (!venueId) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const { data } = await ownerDeactivateTapListItem(venueId, itemId);
      setItems((current) =>
        current.map((item) => (item.id === itemId ? data.tap_item : item)),
      );
      setSuccess(data.message ?? TAP_LIST_SUCCESS_MESSAGE);
      if (editingId === itemId) closeForm();
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
    return <p className="text-sm text-slate-600">Loading tap list…</p>;
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
        <h1 className="mt-2 text-xl font-bold text-slate-900">{TAP_LIST_PAGE_TITLE}</h1>
        <p className="mt-1 text-sm text-slate-600">{TAP_LIST_PAGE_HELPER}</p>
      </div>

      {error ? <ErrorBanner message={error} /> : null}
      {success ? <SuccessBanner>{success}</SuccessBanner> : null}

      {formMode !== "hidden" ? (
        <TapListItemForm
          form={form}
          setForm={setForm}
          onSubmit={() => void handleSave()}
          onCancel={closeForm}
          saving={saving}
          submitLabel={TAP_LIST_SAVE_LABEL}
        />
      ) : (
        <button
          type="button"
          onClick={openCreate}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          {TAP_LIST_ADD_LABEL}
        </button>
      )}

      {items.length === 0 && formMode === "hidden" ? (
        <p className="text-sm text-slate-600">
          No drinks listed yet. Add the key beers, wines and cocktails customers can expect.
        </p>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li
              key={item.id}
              className={`rounded-lg border p-4 ${
                item.active ? "border-slate-200 bg-white" : "border-slate-100 bg-slate-50 opacity-75"
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-medium text-slate-900">{item.drink_name}</h2>
                  {!item.active ? (
                    <span className="mt-1 inline-block text-xs text-slate-500">Inactive</span>
                  ) : null}
                  {item.brewery_or_brand ? (
                    <p className="mt-1 text-sm text-slate-600">{item.brewery_or_brand}</p>
                  ) : null}
                  <p className="mt-2 text-xs text-slate-500">
                    {[item.drink_type, item.abv, formatTapAvailability(item.availability)]
                      .filter(Boolean)
                      .join(" · ")}
                    {item.price_text ? ` · ${item.price_text}` : ""}
                  </p>
                  {item.notes ? (
                    <p className="mt-1 text-xs text-slate-500">{item.notes}</p>
                  ) : null}
                </div>
                <div className="flex shrink-0 flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => openEdit(item)}
                    className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
                  >
                    Edit
                  </button>
                  {item.active ? (
                    <button
                      type="button"
                      disabled={saving}
                      onClick={() => void handleDeactivate(item.id)}
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
