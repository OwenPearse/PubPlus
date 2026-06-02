import { describeActiveFilters } from "@/lib/filterSummary";
import type { ListFilters } from "@/lib/types";

export function buildListQueryParams(filters: ListFilters): Record<string, string> {
  const params: Record<string, string> = {
    sort: filters.sort,
    limit: String(filters.limit),
    offset: String(filters.offset),
  };

  if (filters.state.trim()) params.state = filters.state.trim().toUpperCase();
  if (filters.suburb.trim()) params.suburb = filters.suburb.trim();
  if (filters.search.trim()) params.search = filters.search.trim();
  if (filters.enrichment_status) params.enrichment_status = filters.enrichment_status;
  if (filters.outreach_status) params.outreach_status = filters.outreach_status;
  if (filters.outreach_status_in.trim()) {
    params.outreach_status_in = filters.outreach_status_in.trim();
  }
  if (filters.last_contact_channel.trim()) {
    params.last_contact_channel = filters.last_contact_channel.trim();
  }
  if (filters.contacted_before.trim()) {
    params.contacted_before = filters.contacted_before.trim();
  }
  if (filters.contacted_after.trim()) {
    params.contacted_after = filters.contacted_after.trim();
  }
  if (filters.contact_permission_status) {
    params.contact_permission_status = filters.contact_permission_status;
  }
  if (filters.score_min.trim()) params.score_min = filters.score_min.trim();
  if (filters.missing_email) params.missing_email = "true";
  if (filters.missing_website) params.missing_website = "true";
  if (filters.missing_phone) params.missing_phone = "true";
  if (filters.needs_review) params.needs_review = "true";
  if (filters.include_do_not_contact) params.include_do_not_contact = "true";

  return params;
}

export function buildExportUrl(
  apiBaseUrl: string,
  filters: ListFilters,
  accessToken: string,
): string {
  const params = new URLSearchParams(buildListQueryParams(filters));
  params.set("limit", String(Math.min(filters.limit, 5000)));
  const url = `${apiBaseUrl}/api/v1/internal/founder-venues/export.csv?${params.toString()}`;
  return url;
}

export async function downloadExportCsv(
  apiBaseUrl: string,
  filters: ListFilters,
  accessToken: string,
): Promise<void> {
  const params = new URLSearchParams(buildListQueryParams(filters));
  params.set("limit", "5000");
  const response = await fetch(
    `${apiBaseUrl}/api/v1/internal/founder-venues/export.csv?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "text/csv",
      },
    },
  );
  if (!response.ok) {
    const text = await response.text();
    let message = `Export failed (${response.status})`;
    try {
      const json = JSON.parse(text) as { message?: string };
      if (json.message) message = json.message;
    } catch {
      if (text) message = text.slice(0, 200);
    }
    throw new Error(message);
  }
  const blob = await response.blob();
  const disposition = response.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match?.[1] ?? "pubplus_founder_venues.csv";
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}

export function sevenDaysAgoIso(): string {
  const d = new Date();
  d.setDate(d.getDate() - 7);
  return d.toISOString();
}

export function buildExportConfirmMessage(filters: ListFilters, total: number): string {
  return [
    "Export CSV with current filters?",
    "",
    describeActiveFilters(filters),
    "",
    `About ${total} lead(s) match these filters.`,
    "",
    "Safe defaults:",
    "• Do-not-contact leads excluded (unless filter includes DNC)",
    "• Unsafe personal emails redacted",
    "• Full raw notes not included",
  ].join("\n");
}

export type QuickFilterPreset =
  | "vic_80_plus"
  | "vic_60_missing_email"
  | "vic_needs_review"
  | "no_contact_channels"
  | "vic_80_not_contacted"
  | "vic_phone_first"
  | "follow_up"
  | "called_no_reply"
  | "emailed_no_reply"
  | "high_score_not_contacted"
  | "missing_email"
  | "already_called"
  | "replied"
  | "signed_up"
  | "rejected"
  | "dnc";

function resetQueueFilters(current: ListFilters): ListFilters {
  return {
    ...current,
    state: "VIC",
    offset: 0,
    missing_email: false,
    missing_website: false,
    missing_phone: false,
    needs_review: false,
    score_min: "",
    outreach_status: "",
    outreach_status_in: "",
    last_contact_channel: "",
    contacted_before: "",
    contacted_after: "",
    enrichment_status: "",
    contact_permission_status: "",
    include_do_not_contact: false,
    sort: "founder_fit_score_desc",
  };
}

export function applyQuickFilter(
  preset: QuickFilterPreset,
  current: ListFilters,
): ListFilters {
  const base = resetQueueFilters(current);

  switch (preset) {
    case "vic_80_plus":
      return { ...base, score_min: "80" };
    case "vic_60_missing_email":
      return { ...base, score_min: "60", missing_email: true };
    case "vic_needs_review":
      return { ...base, needs_review: true };
    case "no_contact_channels":
      return {
        ...base,
        missing_email: true,
        missing_website: true,
        missing_phone: true,
      };
    case "vic_80_not_contacted":
      return { ...base, score_min: "80", outreach_status: "not_contacted" };
    case "vic_phone_first":
      return { ...base, score_min: "60", outreach_status: "not_contacted" };
    case "follow_up":
      return {
        ...base,
        outreach_status_in: "called,emailed",
        contacted_before: sevenDaysAgoIso(),
      };
    case "called_no_reply":
      return { ...base, outreach_status: "called" };
    case "emailed_no_reply":
      return { ...base, outreach_status: "emailed" };
    case "high_score_not_contacted":
      return { ...base, score_min: "80", outreach_status: "not_contacted" };
    case "missing_email":
      return { ...base, missing_email: true };
    case "already_called":
      return { ...base, outreach_status: "called" };
    case "replied":
      return { ...base, outreach_status: "replied" };
    case "signed_up":
      return { ...base, outreach_status: "signed_up" };
    case "rejected":
      return { ...base, outreach_status: "rejected" };
    case "dnc":
      return {
        ...base,
        outreach_status: "do_not_contact",
        include_do_not_contact: true,
      };
    default:
      return base;
  }
}
