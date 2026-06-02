import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ContactIndicators } from "@/components/ContactIndicators";
import { ErrorBanner } from "@/components/ErrorBanner";
import { EnrichmentPanel } from "@/components/EnrichmentPanel";
import {
  enrichFounderVenueLead,
  formatApiError,
  listFounderVenueLeads,
  markLeadDoNotContact,
} from "@/lib/api";
import { applyQuickFilter, downloadExportCsv, type QuickFilterPreset } from "@/lib/filters";
import { getApiBaseUrl } from "@/lib/env";
import { getAccessToken } from "@/lib/supabase";
import type { EnrichmentResult, FounderVenueLeadListItem, ListFilters } from "@/lib/types";
import { DEFAULT_LIST_FILTERS } from "@/lib/types";

function formatDate(value: string | null) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export function FounderVenuesListPage() {
  const [filters, setFilters] = useState<ListFilters>({ ...DEFAULT_LIST_FILTERS });
  const [items, setItems] = useState<FounderVenueLeadListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [enrichLeadId, setEnrichLeadId] = useState<string | null>(null);
  const [enrichResult, setEnrichResult] = useState<EnrichmentResult | null>(null);
  const [enrichLoading, setEnrichLoading] = useState(false);

  const loadLeads = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listFounderVenueLeads(filters);
      setItems(data.items);
      setTotal(data.pagination.total);
    } catch (err) {
      setError(formatApiError(err));
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadLeads();
  }, [loadLeads]);

  function updateFilter<K extends keyof ListFilters>(key: K, value: ListFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value, offset: 0 }));
  }

  function applyPreset(preset: QuickFilterPreset) {
    setFilters((prev) => applyQuickFilter(preset, prev));
  }

  async function handleExport() {
    setError("");
    setSuccess("");
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Sign in required.");
      await downloadExportCsv(getApiBaseUrl(), filters, token);
      setSuccess("Export downloaded.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    }
  }

  async function runEnrich(leadId: string, dryRun: boolean) {
    setEnrichLeadId(leadId);
    setEnrichLoading(true);
    setError("");
    try {
      const result = await enrichFounderVenueLead(leadId, dryRun);
      setEnrichResult(result);
      if (!dryRun) {
        setSuccess("Enrichment applied.");
        await loadLeads();
      }
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setEnrichLoading(false);
    }
  }

  async function handleMarkDnc(lead: FounderVenueLeadListItem) {
    if (
      !window.confirm(
        `Mark "${lead.name}" as do-not-contact? This updates outreach and permission status.`,
      )
    ) {
      return;
    }
    setError("");
    try {
      await markLeadDoNotContact(lead.id);
      setSuccess(`Marked ${lead.name} as do-not-contact.`);
      await loadLeads();
    } catch (err) {
      setError(formatApiError(err));
    }
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Founder venue leads</h1>
          <p className="text-sm text-slate-600">
            {loading ? "Loading…" : `${total} leads match filters`}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm"
            onClick={() => void loadLeads()}
          >
            Refresh
          </button>
          <button
            type="button"
            className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white"
            onClick={() => void handleExport()}
          >
            Export CSV
          </button>
        </div>
      </div>

      <p className="mb-4 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
        Export excludes do-not-contact and unsafe emails by default.
      </p>

      <ErrorBanner message={error} onDismiss={() => setError("")} />
      {success ? (
        <p className="mb-4 rounded border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
          {success}
        </p>
      ) : null}

      <div className="mb-4 flex flex-wrap gap-2">
        <QuickButton label="VIC 80+" onClick={() => applyPreset("vic_80_plus")} />
        <QuickButton
          label="VIC 60+ missing email"
          onClick={() => applyPreset("vic_60_missing_email")}
        />
        <QuickButton label="VIC needs review" onClick={() => applyPreset("vic_needs_review")} />
        <QuickButton
          label="No phone/email/website"
          onClick={() => applyPreset("no_contact_channels")}
        />
        <QuickButton
          label="Reset filters"
          onClick={() => setFilters({ ...DEFAULT_LIST_FILTERS })}
        />
      </div>

      <FiltersPanel filters={filters} onChange={updateFilter} />

      {enrichLeadId ? (
        <div className="mb-6">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-sm font-medium">Enrichment for lead {enrichLeadId}</p>
            <button
              type="button"
              className="text-sm underline"
              onClick={() => {
                setEnrichLeadId(null);
                setEnrichResult(null);
              }}
            >
              Close
            </button>
          </div>
          <EnrichmentPanel
            result={enrichResult}
            loading={enrichLoading}
            onDryRun={() => void runEnrich(enrichLeadId, true)}
            onRealEnrich={() => void runEnrich(enrichLeadId, false)}
          />
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Venue</th>
              <th className="px-3 py-2">Location</th>
              <th className="px-3 py-2">Category</th>
              <th className="px-3 py-2">Fit</th>
              <th className="px-3 py-2">Conf</th>
              <th className="px-3 py-2">Contact</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Updated</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && !loading ? (
              <tr>
                <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
                  No leads found for these filters.
                </td>
              </tr>
            ) : null}
            {items.map((lead) => (
              <tr key={lead.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2 font-medium">
                  <Link
                    to={`/internal/founder-venues/${lead.id}`}
                    className="text-blue-700 hover:underline"
                  >
                    {lead.name}
                  </Link>
                </td>
                <td className="px-3 py-2">
                  {[lead.suburb, lead.state].filter(Boolean).join(", ") || "—"}
                </td>
                <td className="px-3 py-2">{lead.category ?? "—"}</td>
                <td className="px-3 py-2 font-semibold">{lead.founder_fit_score}</td>
                <td className="px-3 py-2">{lead.confidence_score}</td>
                <td className="px-3 py-2">
                  <ContactIndicators {...lead} />
                </td>
                <td className="px-3 py-2 text-xs">
                  <div>{lead.enrichment_status}</div>
                  <div className="text-slate-500">{lead.outreach_status}</div>
                </td>
                <td className="px-3 py-2 text-xs text-slate-600">
                  {formatDate(lead.updated_at)}
                </td>
                <td className="px-3 py-2">
                  <div className="flex flex-col gap-1 text-xs">
                    <Link
                      to={`/internal/founder-venues/${lead.id}`}
                      className="text-blue-700 underline"
                    >
                      Detail
                    </Link>
                    <button
                      type="button"
                      className="text-left text-slate-700 underline"
                      onClick={() => {
                        setEnrichResult(null);
                        setEnrichLeadId(lead.id);
                        void runEnrich(lead.id, true);
                      }}
                    >
                      Enrich dry-run
                    </button>
                    <button
                      type="button"
                      className="text-left text-red-700 underline"
                      onClick={() => void handleMarkDnc(lead)}
                    >
                      Mark DNC
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination
        offset={filters.offset}
        limit={filters.limit}
        total={total}
        count={items.length}
        onPageChange={(offset) => updateFilter("offset", offset)}
      />
    </div>
  );
}

function QuickButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs hover:bg-slate-50"
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function FiltersPanel({
  filters,
  onChange,
}: {
  filters: ListFilters;
  onChange: <K extends keyof ListFilters>(key: K, value: ListFilters[K]) => void;
}) {
  return (
    <form
      className="mb-6 grid gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-4"
      onSubmit={(e) => e.preventDefault()}
    >
      <FilterInput label="State" value={filters.state} onChange={(v) => onChange("state", v)} />
      <FilterInput label="Suburb" value={filters.suburb} onChange={(v) => onChange("suburb", v)} />
      <FilterInput label="Search" value={filters.search} onChange={(v) => onChange("search", v)} />
      <FilterInput
        label="Score min"
        value={filters.score_min}
        onChange={(v) => onChange("score_min", v)}
      />
      <label className="text-sm">
        Enrichment status
        <select
          className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
          value={filters.enrichment_status}
          onChange={(e) => onChange("enrichment_status", e.target.value)}
        >
          <option value="">Any</option>
          <option value="imported">imported</option>
          <option value="pending_enrichment">pending_enrichment</option>
          <option value="enriched">enriched</option>
          <option value="needs_review">needs_review</option>
          <option value="rejected">rejected</option>
        </select>
      </label>
      <label className="text-sm">
        Outreach status
        <select
          className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
          value={filters.outreach_status}
          onChange={(e) => onChange("outreach_status", e.target.value)}
        >
          <option value="">Any</option>
          <option value="not_contacted">not_contacted</option>
          <option value="queued">queued</option>
          <option value="called">called</option>
          <option value="emailed">emailed</option>
          <option value="replied">replied</option>
          <option value="signed_up">signed_up</option>
          <option value="rejected">rejected</option>
          <option value="do_not_contact">do_not_contact</option>
        </select>
      </label>
      <label className="text-sm">
        Contact permission
        <select
          className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
          value={filters.contact_permission_status}
          onChange={(e) => onChange("contact_permission_status", e.target.value)}
        >
          <option value="">Any</option>
          <option value="unknown">unknown</option>
          <option value="public_business_contact">public_business_contact</option>
          <option value="requested_info_by_phone">requested_info_by_phone</option>
          <option value="requested_info_by_dm">requested_info_by_dm</option>
          <option value="opted_in">opted_in</option>
          <option value="opted_out">opted_out</option>
          <option value="do_not_contact">do_not_contact</option>
        </select>
      </label>
      <label className="text-sm">
        Sort
        <select
          className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
          value={filters.sort}
          onChange={(e) => onChange("sort", e.target.value)}
        >
          <option value="founder_fit_score_desc">Founder fit (high first)</option>
          <option value="confidence_score_desc">Confidence (high first)</option>
          <option value="updated_at_desc">Recently updated</option>
          <option value="created_at_desc">Recently created</option>
          <option value="name_asc">Name A–Z</option>
        </select>
      </label>
      <div className="flex flex-col gap-2 text-sm sm:col-span-2">
        <Checkbox
          label="Missing email"
          checked={filters.missing_email}
          onChange={(v) => onChange("missing_email", v)}
        />
        <Checkbox
          label="Missing website"
          checked={filters.missing_website}
          onChange={(v) => onChange("missing_website", v)}
        />
        <Checkbox
          label="Needs review"
          checked={filters.needs_review}
          onChange={(v) => onChange("needs_review", v)}
        />
        <Checkbox
          label="Include do-not-contact"
          checked={filters.include_do_not_contact}
          onChange={(v) => onChange("include_do_not_contact", v)}
        />
      </div>
    </form>
  );
}

function FilterInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-sm">
      {label}
      <input
        className="mt-1 w-full rounded border border-slate-300 px-2 py-1.5"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

function Checkbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center gap-2">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  );
}

function Pagination({
  offset,
  limit,
  total,
  count,
  onPageChange,
}: {
  offset: number;
  limit: number;
  total: number;
  count: number;
  onPageChange: (offset: number) => void;
}) {
  const prev = Math.max(0, offset - limit);
  const next = offset + count < total ? offset + limit : null;
  return (
    <div className="mt-4 flex items-center justify-between text-sm">
      <span>
        Showing {total === 0 ? 0 : offset + 1}–{offset + count} of {total}
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded border px-3 py-1 disabled:opacity-40"
          disabled={offset === 0}
          onClick={() => onPageChange(prev)}
        >
          Previous
        </button>
        <button
          type="button"
          className="rounded border px-3 py-1 disabled:opacity-40"
          disabled={next === null}
          onClick={() => next !== null && onPageChange(next)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
