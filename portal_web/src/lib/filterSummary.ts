import type { ListFilters } from "@/lib/types";
import { DEFAULT_LIST_FILTERS } from "@/lib/types";

const SORT_LABELS: Record<string, string> = {
  founder_fit_score_desc: "founder fit (high first)",
  confidence_score_desc: "confidence (high first)",
  updated_at_desc: "recently updated",
  created_at_desc: "recently created",
  name_asc: "name A–Z",
};

export function describeActiveFilters(filters: ListFilters): string {
  const parts: string[] = ["Showing"];

  if (filters.state.trim()) {
    parts.push(`${filters.state.trim().toUpperCase()} leads`);
  } else {
    parts.push("all states");
  }

  if (filters.suburb.trim()) parts.push(`suburb ${filters.suburb.trim()}`);
  if (filters.search.trim()) parts.push(`search “${filters.search.trim()}”`);
  if (filters.score_min.trim()) parts.push(`score ≥ ${filters.score_min.trim()}`);
  if (filters.enrichment_status) parts.push(`enrichment ${filters.enrichment_status}`);
  if (filters.outreach_status) parts.push(`outreach ${filters.outreach_status}`);
  if (filters.outreach_status_in.trim()) {
    parts.push(`outreach in (${filters.outreach_status_in.trim()})`);
  }
  if (filters.last_contact_channel.trim()) {
    parts.push(`last channel ${filters.last_contact_channel.trim()}`);
  }
  if (filters.contacted_before.trim()) {
    parts.push(`contacted before ${filters.contacted_before.trim()}`);
  }
  if (filters.contacted_after.trim()) {
    parts.push(`contacted after ${filters.contacted_after.trim()}`);
  }
  if (filters.contact_permission_status) {
    parts.push(`permission ${filters.contact_permission_status}`);
  }
  if (filters.missing_email) parts.push("missing email");
  if (filters.missing_website) parts.push("missing website");
  if (filters.missing_phone) parts.push("missing phone");
  if (filters.needs_review) parts.push("needs review");
  if (filters.include_do_not_contact) parts.push("including DNC");
  else parts.push("excluding DNC by default");

  parts.push(`sorted by ${SORT_LABELS[filters.sort] ?? filters.sort}`);

  return parts.join(", ");
}

export function isDefaultFilters(filters: ListFilters): boolean {
  return JSON.stringify(filters) === JSON.stringify(DEFAULT_LIST_FILTERS);
}
