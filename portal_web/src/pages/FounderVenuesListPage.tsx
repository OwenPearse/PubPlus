import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { ActiveFilterSummary } from "@/components/ActiveFilterSummary";
import { ContactIndicators } from "@/components/ContactIndicators";
import { ContactLegend } from "@/components/ContactLegend";
import { DashboardCards } from "@/components/DashboardCards";
import { ErrorBanner } from "@/components/ErrorBanner";
import { OutreachStatusCounts } from "@/components/OutreachStatusCounts";
import { StatusBadge } from "@/components/StatusBadge";
import { EnrichmentPanel } from "@/components/EnrichmentPanel";
import { ExternalLink } from "@/components/ExternalLink";
import { OutreachActionButtons } from "@/components/OutreachActionButtons";
import {
  enrichFounderVenueLead,
  formatApiError,
  getFounderVenueWorkspaceSummary,
  listFounderVenueLeads,
  markFounderVenueCalled,
  markFounderVenueDoNotContact,
  markFounderVenueEmailed,
  markFounderVenueQueued,
  markFounderVenueRejected,
  markFounderVenueReplied,
  markFounderVenueSignedUp,
} from "@/lib/api";
import {
  applyQuickFilter,
  buildExportConfirmMessage,
  downloadExportCsv,
  type QuickFilterPreset,
} from "@/lib/filters";
import {
  filtersFromSearchParams,
  filtersToSearchParams,
  listSearchString,
} from "@/lib/filterUrl";
import { getApiBaseUrl } from "@/lib/env";
import {
  findNextBestLeadId,
  mergeLeadFromDetail,
} from "@/lib/outreach";
import { getAccessToken } from "@/lib/supabase";
import type {
  EnrichmentResult,
  FounderVenueLeadListItem,
  FounderVenueWorkspaceSummary,
  ListFilters,
} from "@/lib/types";
import { DEFAULT_LIST_FILTERS } from "@/lib/types";

type ListRow = FounderVenueLeadListItem;

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function socialHref(lead: FounderVenueLeadListItem): string | null {
  return lead.instagram_url?.trim() || lead.facebook_url?.trim() || null;
}

const BATCH_ALLOWED = ["queued", "called", "emailed", "rejected"] as const;

export function FounderVenuesListPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<ListFilters>(() =>
    filtersFromSearchParams(searchParams),
  );
  const [items, setItems] = useState<ListRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [callSheetMode, setCallSheetMode] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [enrichLeadId, setEnrichLeadId] = useState<string | null>(null);
  const [enrichResult, setEnrichResult] = useState<EnrichmentResult | null>(null);
  const [enrichLoading, setEnrichLoading] = useState(false);
  const [summary, setSummary] = useState<FounderVenueWorkspaceSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [busyLeadId, setBusyLeadId] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const data = await getFounderVenueWorkspaceSummary();
      setSummary(data);
    } catch {
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  useEffect(() => {
    setSearchParams(filtersToSearchParams(filters), { replace: true });
  }, [filters, setSearchParams]);

  const listQuery = useMemo(() => listSearchString(filters), [filters]);

  const loadLeads = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listFounderVenueLeads(filters);
      setItems(data.items);
      setTotal(data.pagination.total);
      setSelected(new Set());
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

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  function updateFilter<K extends keyof ListFilters>(key: K, value: ListFilters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value, offset: 0 }));
  }

  function applyPreset(preset: QuickFilterPreset) {
    setFilters((prev) => applyQuickFilter(preset, prev));
  }

  function openDetail(leadId: string) {
    navigate(`/internal/founder-venues/${leadId}${listQuery}`, {
      state: { leadIds: items.map((i) => i.id) },
    });
  }

  async function handleExport() {
    setError("");
    setSuccess("");
    const confirmed = window.confirm(buildExportConfirmMessage(filters, total));
    if (!confirmed) return;
    try {
      const token = await getAccessToken();
      if (!token) throw new Error("Sign in required.");
      await downloadExportCsv(getApiBaseUrl(), filters, token);
      setSuccess("Export downloaded for the current filters.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    }
  }

  async function applyOutreachToLead(
    lead: ListRow,
    action: () => ReturnType<typeof markFounderVenueCalled>,
    successLabel: string,
  ) {
    setError("");
    setBusyLeadId(lead.id);
    try {
      const response = await action();
      setItems((prev) =>
        prev.map((row) => (row.id === lead.id ? mergeLeadFromDetail(row, response) : row)),
      );
      setSuccess(`${lead.name}: ${successLabel}`);
      void loadSummary();
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setBusyLeadId(null);
    }
  }

  async function handleMarkDnc(lead: ListRow) {
    const reason = window.prompt(
      `Mark "${lead.name}" as do-not-contact?\n\nOptional reason:`,
      "",
    );
    if (reason === null) return;
    if (!window.confirm(`Confirm do-not-contact for "${lead.name}".`)) return;
    setError("");
    try {
      const response = await markFounderVenueDoNotContact(lead.id, reason.trim() || undefined);
      setItems((prev) =>
        prev.map((row) => (row.id === lead.id ? mergeLeadFromDetail(row, response) : row)),
      );
      setSuccess(`Marked ${lead.name} as do-not-contact.`);
    } catch (err) {
      setError(formatApiError(err));
    }
  }

  function outreachActions(lead: ListRow) {
    const rowBusy = busyLeadId === lead.id;
    return [
      { id: "detail", label: "Open detail", disabled: rowBusy, onClick: () => openDetail(lead.id) },
      {
        id: "called",
        label: rowBusy ? "Saving…" : "Mark called",
        disabled: rowBusy,
        onClick: () =>
          void applyOutreachToLead(lead, () => markFounderVenueCalled(lead.id), "marked called."),
      },
      {
        id: "emailed",
        label: rowBusy ? "Saving…" : "Mark emailed",
        disabled: rowBusy,
        onClick: () =>
          void applyOutreachToLead(lead, () => markFounderVenueEmailed(lead.id), "marked emailed."),
      },
      {
        id: "replied",
        label: "Mark replied",
        disabled: rowBusy,
        onClick: () =>
          void applyOutreachToLead(lead, () => markFounderVenueReplied(lead.id), "marked replied."),
      },
      {
        id: "rejected",
        label: "Mark rejected",
        disabled: rowBusy,
        onClick: () =>
          void applyOutreachToLead(
            lead,
            () => markFounderVenueRejected(lead.id),
            "marked rejected.",
          ),
      },
      {
        id: "signed_up",
        label: "Mark signed up",
        disabled: rowBusy,
        onClick: () =>
          void applyOutreachToLead(
            lead,
            () => markFounderVenueSignedUp(lead.id),
            "marked signed up.",
          ),
      },
      {
        id: "dnc",
        label: "Mark DNC",
        className: "text-red-800",
        disabled: rowBusy,
        onClick: () => void handleMarkDnc(lead),
      },
    ];
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

  function openNextBestLead() {
    const id = findNextBestLeadId(items);
    if (!id) {
      setError("No not_contacted or queued leads in the current list.");
      return;
    }
    openDetail(id);
  }

  function toggleSelected(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function batchUpdate(status: (typeof BATCH_ALLOWED)[number]) {
    if (selected.size === 0) return;
    const label = status.replace("_", " ");
    if (!window.confirm(`Mark ${selected.size} lead(s) as ${label}?`)) return;
    setError("");
    let ok = 0;
    for (const id of selected) {
      try {
        if (status === "queued") await markFounderVenueQueued(id);
        else if (status === "called") await markFounderVenueCalled(id);
        else if (status === "emailed") await markFounderVenueEmailed(id);
        else if (status === "rejected") await markFounderVenueRejected(id);
        ok += 1;
      } catch {
        /* continue */
      }
    }
    setSuccess(`Batch update: ${ok} of ${selected.size} marked ${label}.`);
    await loadLeads();
  }

  const quickFilters: { preset: QuickFilterPreset; label: string }[] = [
    { preset: "follow_up", label: "Follow up" },
    { preset: "called_no_reply", label: "Called, no reply" },
    { preset: "emailed_no_reply", label: "Emailed, no reply" },
    { preset: "high_score_not_contacted", label: "High score, not contacted" },
    { preset: "missing_email", label: "Missing email" },
    { preset: "vic_80_not_contacted", label: "VIC 80+ not contacted" },
    { preset: "vic_60_missing_email", label: "VIC 60+ missing email" },
    { preset: "vic_phone_first", label: "VIC phone-first" },
    { preset: "vic_needs_review", label: "VIC needs review" },
    { preset: "already_called", label: "Already called" },
    { preset: "replied", label: "Replied" },
    { preset: "signed_up", label: "Signed up" },
    { preset: "rejected", label: "Rejected" },
    { preset: "dnc", label: "DNC" },
    { preset: "vic_80_plus", label: "VIC 80+" },
    { preset: "no_contact_channels", label: "No phone/email/website" },
  ];

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
            className={`rounded border px-3 py-1.5 text-sm ${
              callSheetMode
                ? "border-blue-600 bg-blue-600 text-white"
                : "border-slate-300 bg-white"
            }`}
            onClick={() => setCallSheetMode((v) => !v)}
          >
            Call sheet mode
          </button>
          <button
            type="button"
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm"
            onClick={() => openNextBestLead()}
          >
            Open next best lead
          </button>
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

      <DashboardCards summary={summary} loading={summaryLoading} />

      <div className="mb-3 space-y-2">
        <ContactLegend />
        <ActiveFilterSummary filters={filters} />
        <OutreachStatusCounts summary={summary} />
      </div>

      <p className="mb-4 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
        Export excludes do-not-contact and unsafe emails by default. The portal does not send
        email or SMS.
      </p>

      <ErrorBanner message={error} onDismiss={() => setError("")} />
      {success ? (
        <p className="mb-4 rounded border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
          {success}
        </p>
      ) : null}

      <div className="mb-4 flex flex-wrap gap-2">
        {quickFilters.map(({ preset, label }) => (
          <QuickButton key={preset} label={label} onClick={() => applyPreset(preset)} />
        ))}
        <QuickButton
          label="Reset filters"
          onClick={() => setFilters({ ...DEFAULT_LIST_FILTERS })}
        />
      </div>

      {callSheetMode && selected.size > 0 ? (
        <div className="mb-4 flex flex-wrap gap-2 rounded border border-slate-200 bg-white p-3">
          <span className="text-sm text-slate-600">{selected.size} selected</span>
          <button
            type="button"
            className="rounded border px-2 py-1 text-xs"
            onClick={() => void batchUpdate("queued")}
          >
            Batch: mark queued
          </button>
          <button
            type="button"
            className="rounded border px-2 py-1 text-xs"
            onClick={() => void batchUpdate("called")}
          >
            Batch: mark called
          </button>
          <button
            type="button"
            className="rounded border px-2 py-1 text-xs"
            onClick={() => void batchUpdate("emailed")}
          >
            Batch: mark emailed
          </button>
          <button
            type="button"
            className="rounded border px-2 py-1 text-xs"
            onClick={() => void batchUpdate("rejected")}
          >
            Batch: mark rejected
          </button>
        </div>
      ) : null}

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

      <div className="max-h-[70vh] overflow-auto rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="sticky top-0 z-10 border-b bg-slate-50 text-xs uppercase text-slate-500 shadow-sm">
            <tr>
              {callSheetMode ? <th className="px-2 py-2">Sel</th> : null}
              <th className="px-3 py-2">Venue</th>
              {callSheetMode ? (
                <>
                  <th className="px-3 py-2">Suburb</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Phone</th>
                  <th className="px-3 py-2">Email</th>
                  <th className="px-3 py-2">Web</th>
                  <th className="px-3 py-2">Social</th>
                  <th className="px-3 py-2">Outreach</th>
                  <th className="px-3 py-2">Last contact</th>
                  <th className="px-3 py-2">Actions</th>
                </>
              ) : (
                <>
                  <th className="px-3 py-2">Location</th>
                  <th className="px-3 py-2">Category</th>
                  <th className="px-3 py-2">Fit</th>
                  <th className="px-3 py-2">Conf</th>
                  <th className="px-3 py-2">Contact</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Updated</th>
                  <th className="px-3 py-2">Actions</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && !loading ? (
              <tr>
                <td
                  colSpan={callSheetMode ? 11 : 9}
                  className="px-3 py-8 text-center text-slate-500"
                >
                  No leads found for these filters.
                </td>
              </tr>
            ) : null}
            {items.map((lead) => (
              <tr
                key={lead.id}
                className={`border-b border-slate-100 hover:bg-slate-50 ${
                  lead.outreach_status === "do_not_contact" ? "bg-red-50/40" : ""
                }`}
              >
                {callSheetMode ? (
                  <td className="px-2 py-2">
                    <input
                      type="checkbox"
                      checked={selected.has(lead.id)}
                      onChange={() => toggleSelected(lead.id)}
                      aria-label={`Select ${lead.name}`}
                    />
                  </td>
                ) : null}
                <td className="px-3 py-2 font-medium">
                  <button
                    type="button"
                    className="text-left text-blue-700 underline"
                    onClick={() => openDetail(lead.id)}
                  >
                    {lead.name}
                  </button>
                  {lead.outreach_status === "do_not_contact" ? (
                    <span className="ml-1 rounded bg-red-100 px-1 text-xs text-red-900">DNC</span>
                  ) : null}
                </td>
                {callSheetMode ? (
                  <>
                    <td className="px-3 py-2">{lead.suburb ?? "—"}</td>
                    <td className="px-3 py-2 font-semibold">{lead.founder_fit_score}</td>
                    <td className="max-w-[8rem] truncate px-3 py-1.5 text-xs">
                      {lead.phone?.trim() ? (
                        <a className="text-blue-700 underline" href={`tel:${lead.phone}`}>
                          {lead.phone}
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-3 py-1.5 text-xs">{lead.email?.trim() ? "Yes" : "—"}</td>
                    <td className="px-3 py-1.5">
                      {lead.website?.trim() ? (
                        <ExternalLink href={lead.website} className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-xs no-underline">
                          Web
                        </ExternalLink>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-3 py-1.5">
                      {socialHref(lead) ? (
                        <ExternalLink href={socialHref(lead)!} className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-xs no-underline">
                          Social
                        </ExternalLink>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-3 py-1.5">
                      <StatusBadge status={lead.outreach_status} />
                    </td>
                    <td className="px-3 py-1.5 text-xs text-slate-600">
                      {formatDate(lead.last_contacted_at)}
                    </td>
                    <td className="px-3 py-1.5">
                      <OutreachActionButtons
                        layout="row"
                        variant="button"
                        actions={outreachActions(lead)}
                      />
                    </td>
                  </>
                ) : (
                  <>
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
                      <OutreachActionButtons
                        actions={[
                          ...outreachActions(lead),
                          {
                            id: "enrich",
                            label: "Enrich dry-run",
                            onClick: () => {
                              setEnrichResult(null);
                              setEnrichLeadId(lead.id);
                              void runEnrich(lead.id, true);
                            },
                          },
                        ]}
                      />
                    </td>
                  </>
                )}
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
