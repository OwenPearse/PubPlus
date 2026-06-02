import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { ContactIndicators } from "@/components/ContactIndicators";
import { ContactLegend } from "@/components/ContactLegend";
import { ContactShortcuts } from "@/components/ContactShortcuts";
import { EnrichmentPanel } from "@/components/EnrichmentPanel";
import { ErrorBanner } from "@/components/ErrorBanner";
import { OutreachPanel } from "@/components/OutreachPanel";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import {
  enrichFounderVenueLead,
  formatApiError,
  getFounderVenueLead,
  patchFounderVenueLead,
} from "@/lib/api";
import { findNextLeadIdInList } from "@/lib/outreach";
import type {
  EnrichmentResult,
  FounderVenueLeadDetail,
  LeadDetailResponse,
  LeadEvent,
  PatchableLeadField,
} from "@/lib/types";
import { PATCHABLE_LEAD_FIELDS } from "@/lib/types";

const VENUE_EDIT_FIELDS = PATCHABLE_LEAD_FIELDS.filter(
  (f) =>
    f !== "notes" &&
    f !== "outreach_status" &&
    f !== "contact_permission_status" &&
    f !== "last_contacted_at" &&
    f !== "last_contact_channel",
);

function eventSummary(metadata: Record<string, unknown>): string {
  const keys = Object.keys(metadata);
  if (keys.length === 0) return "—";
  const preview = keys.slice(0, 4).map((k) => `${k}: ${String(metadata[k])}`);
  return preview.join(" · ");
}

export function FounderVenueDetailPage() {
  const { leadId } = useParams<{ leadId: string }>();
  const location = useLocation();
  const listBackHref = `/internal/founder-venues${location.search}`;
  const leadIds = useMemo(() => {
    const state = location.state as { leadIds?: string[] } | null;
    return state?.leadIds ?? [];
  }, [location.state]);
  const nextLeadId = leadId ? findNextLeadIdInList(leadIds, leadId) : null;
  const [detail, setDetail] = useState<LeadDetailResponse | null>(null);
  const [form, setForm] = useState<Partial<Record<PatchableLeadField, string>>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [enrichResult, setEnrichResult] = useState<EnrichmentResult | null>(null);
  const [enrichLoading, setEnrichLoading] = useState(false);

  const loadDetail = useCallback(async () => {
    if (!leadId) return;
    setLoading(true);
    setError("");
    try {
      const data = await getFounderVenueLead(leadId);
      setDetail(data);
      setForm(leadToForm(data.lead));
    } catch (err) {
      setError(formatApiError(err));
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  function updateField(field: PatchableLeadField, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    if (!leadId || !detail) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const body: Partial<Record<PatchableLeadField, string | null>> = {};
      for (const field of VENUE_EDIT_FIELDS) {
        const next = form[field] ?? "";
        const prev = stringifyField(detail.lead, field);
        if (next !== prev) {
          body[field] = next.trim() === "" ? null : next;
        }
      }
      const updated = await patchFounderVenueLead(leadId, body);
      setDetail(updated);
      setForm(leadToForm(updated.lead));
      setSuccess("Lead saved. Scores were recomputed on the server.");
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setSaving(false);
    }
  }

  async function runEnrich(dryRun: boolean) {
    if (!leadId) return;
    setEnrichLoading(true);
    setError("");
    try {
      const result = await enrichFounderVenueLead(leadId, dryRun);
      setEnrichResult(result);
      if (!dryRun) {
        setSuccess("Enrichment applied.");
        await loadDetail();
      }
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setEnrichLoading(false);
    }
  }

  if (!leadId) {
    return <p className="text-red-700">Missing lead id.</p>;
  }

  if (loading) {
    return <p className="text-slate-600">Loading lead…</p>;
  }

  if (!detail) {
    return (
      <div>
        <ErrorBanner message={error || "Lead not found."} />
        <Link to={listBackHref} className="text-blue-700 underline">
          Back to list
        </Link>
      </div>
    );
  }

  const { lead, sources, field_attributions, events } = detail;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <Link to={listBackHref} className="text-sm text-blue-700 underline">
            ← Back to list
          </Link>
          <h1 className="mt-1 text-2xl font-bold">{lead.name}</h1>
          <p className="text-sm text-slate-600">
            {[lead.suburb, lead.state, lead.postcode].filter(Boolean).join(", ")}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {nextLeadId ? (
            <Link
              to={`/internal/founder-venues/${nextLeadId}${location.search}`}
              state={{ leadIds }}
              className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm text-blue-800 underline"
            >
              Next lead →
            </Link>
          ) : null}
        </div>
      </div>

      <div className="mb-3">
        <ContactLegend />
      </div>

      <ErrorBanner message={error} onDismiss={() => setError("")} />
      {success ? (
        <p className="mb-4 rounded border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
          {success}
        </p>
      ) : null}

      <section className="mb-6 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="mb-3 text-lg font-semibold">Summary</h2>
        <dl className="grid gap-2 text-sm sm:grid-cols-2">
          <SummaryItem label="Category" value={lead.category} />
          <SummaryItem label="Founder fit" value={String(lead.founder_fit_score)} />
          <SummaryItem label="Confidence" value={String(lead.confidence_score)} />
          <SummaryItem label="Enrichment" value={lead.enrichment_status} />
          <SummaryItem label="Outreach" value={lead.outreach_status} />
          <SummaryItem label="Permission" value={lead.contact_permission_status} />
        </dl>
        <div className="mt-3">
          <ContactIndicators {...lead} />
        </div>
      </section>

      <OutreachPanel
        lead={lead}
        notes={form.notes ?? ""}
        onNotesChange={(value) => updateField("notes", value)}
        onUpdated={(response) => {
          setDetail(response);
          setForm(leadToForm(response.lead));
        }}
        onError={setError}
        onSuccess={setSuccess}
      />

      <ContactShortcuts lead={lead} onCopied={setSuccess} />

      <ScoreBreakdown
        breakdown={lead.founder_fit_breakdown}
        founderFitScore={lead.founder_fit_score}
        confidenceScore={lead.confidence_score}
      />

      <div className="my-6">
        <EnrichmentPanel
          result={enrichResult}
          loading={enrichLoading}
          onDryRun={() => void runEnrich(true)}
          onRealEnrich={() => void runEnrich(false)}
        />
      </div>

      <form
        onSubmit={(e) => void handleSave(e)}
        className="mb-6 space-y-4 rounded-lg border border-slate-200 bg-white p-4"
      >
        <h2 className="text-lg font-semibold">Edit lead</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {VENUE_EDIT_FIELDS.map((field) => (
            <EditField
              key={field}
              field={field}
              value={form[field] ?? ""}
              onChange={(v) => updateField(field, v)}
            />
          ))}
        </div>
        <button
          type="submit"
          disabled={saving}
          className="rounded bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
      </form>

      <DataTable
        title="Sources"
        empty="No sources recorded."
        headers={["Type", "Name", "URL", "Fetched", "Confidence"]}
        rows={sources.map((s) => [
          s.source_type,
          s.source_name ?? "—",
          s.source_url ?? "—",
          s.fetched_at ?? "—",
          s.confidence != null ? String(s.confidence) : "—",
        ])}
      />

      <DataTable
        title="Field attributions"
        empty="No attributions."
        headers={["Field", "Normalized", "Source", "Safety", "Confidence"]}
        rows={field_attributions.map((a) => [
          a.field_name,
          a.normalized_value ?? "—",
          a.source_type,
          a.contact_safety_class ?? "—",
          a.confidence != null ? String(a.confidence) : "—",
        ])}
      />

      <EventsTable events={events} />
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium">{value ?? "—"}</dd>
    </div>
  );
}

function EditField({
  field,
  value,
  onChange,
}: {
  field: PatchableLeadField;
  value: string;
  onChange: (value: string) => void;
}) {
  const label = field.replace(/_/g, " ");
  const isLong = field === "notes";

  if (field === "enrichment_status") {
    return (
      <label className="text-sm">
        {label}
        <select
          className="mt-1 w-full rounded border px-2 py-1.5"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {["imported", "pending_enrichment", "enriched", "needs_review", "rejected"].map(
            (v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ),
          )}
        </select>
      </label>
    );
  }

  if (field === "outreach_status") {
    return (
      <label className="text-sm">
        {label}
        <select
          className="mt-1 w-full rounded border px-2 py-1.5"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {[
            "not_contacted",
            "queued",
            "called",
            "emailed",
            "replied",
            "signed_up",
            "rejected",
            "do_not_contact",
          ].map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field === "contact_permission_status") {
    return (
      <label className="text-sm">
        {label}
        <select
          className="mt-1 w-full rounded border px-2 py-1.5"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {[
            "unknown",
            "public_business_contact",
            "requested_info_by_phone",
            "requested_info_by_dm",
            "opted_in",
            "opted_out",
            "do_not_contact",
          ].map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field === "last_contact_channel") {
    return (
      <label className="text-sm">
        {label}
        <select
          className="mt-1 w-full rounded border px-2 py-1.5"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          <option value="">—</option>
          {["phone", "email", "instagram", "facebook", "website_form", "in_person", "other"].map(
            (v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ),
          )}
        </select>
      </label>
    );
  }

  return (
    <label className={`text-sm ${isLong ? "sm:col-span-2" : ""}`}>
      {label}
      {isLong ? (
        <textarea
          className="mt-1 w-full rounded border px-2 py-1.5"
          rows={4}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          className="mt-1 w-full rounded border px-2 py-1.5"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </label>
  );
}

function DataTable({
  title,
  headers,
  rows,
  empty,
}: {
  title: string;
  headers: string[];
  rows: string[][];
  empty: string;
}) {
  return (
    <section className="mb-6 overflow-x-auto rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="mb-3 text-lg font-semibold">{title}</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-slate-500">{empty}</p>
      ) : (
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b text-xs uppercase text-slate-500">
              {headers.map((h) => (
                <th key={h} className="px-2 py-1">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b border-slate-100">
                {row.map((cell, j) => (
                  <td key={j} className="max-w-xs truncate px-2 py-1">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function EventsTable({ events }: { events: LeadEvent[] }) {
  return (
    <section className="mb-6 overflow-x-auto rounded-lg border border-slate-200 bg-white p-4">
      <h2 className="mb-3 text-lg font-semibold">Events</h2>
      {events.length === 0 ? (
        <p className="text-sm text-slate-500">No events.</p>
      ) : (
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b text-xs uppercase text-slate-500">
              <th className="px-2 py-1">Type</th>
              <th className="px-2 py-1">When</th>
              <th className="px-2 py-1">Summary</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id} className="border-b border-slate-100">
                <td className="px-2 py-1">{e.event_type}</td>
                <td className="px-2 py-1 text-xs text-slate-600">{e.created_at ?? "—"}</td>
                <td className="px-2 py-1 text-xs">{eventSummary(e.metadata)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

function leadToForm(lead: FounderVenueLeadDetail): Partial<Record<PatchableLeadField, string>> {
  const form: Partial<Record<PatchableLeadField, string>> = {};
  for (const field of PATCHABLE_LEAD_FIELDS) {
    form[field] = stringifyField(lead, field);
  }
  return form;
}

function stringifyField(lead: FounderVenueLeadDetail, field: PatchableLeadField): string {
  const value = lead[field as keyof FounderVenueLeadDetail];
  if (value == null) return "";
  return String(value);
}
