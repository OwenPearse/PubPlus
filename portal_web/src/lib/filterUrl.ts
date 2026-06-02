import type { ListFilters } from "@/lib/types";
import { DEFAULT_LIST_FILTERS } from "@/lib/types";

function setIfNonDefault(
  params: URLSearchParams,
  key: string,
  value: string | number | boolean,
  defaultValue: string | number | boolean,
) {
  if (value === defaultValue) return;
  params.set(key, String(value));
}

export function filtersToSearchParams(filters: ListFilters): URLSearchParams {
  const params = new URLSearchParams();
  const d = DEFAULT_LIST_FILTERS;

  setIfNonDefault(params, "state", filters.state, d.state);
  setIfNonDefault(params, "suburb", filters.suburb, d.suburb);
  setIfNonDefault(params, "search", filters.search, d.search);
  setIfNonDefault(params, "enrichment_status", filters.enrichment_status, d.enrichment_status);
  setIfNonDefault(params, "outreach_status", filters.outreach_status, d.outreach_status);
  setIfNonDefault(
    params,
    "contact_permission_status",
    filters.contact_permission_status,
    d.contact_permission_status,
  );
  setIfNonDefault(params, "score_min", filters.score_min, d.score_min);
  if (filters.missing_email) params.set("missing_email", "true");
  if (filters.missing_website) params.set("missing_website", "true");
  if (filters.missing_phone) params.set("missing_phone", "true");
  if (filters.needs_review) params.set("needs_review", "true");
  if (filters.include_do_not_contact) params.set("include_do_not_contact", "true");
  setIfNonDefault(params, "sort", filters.sort, d.sort);
  setIfNonDefault(params, "limit", filters.limit, d.limit);
  setIfNonDefault(params, "offset", filters.offset, d.offset);

  return params;
}

export function filtersFromSearchParams(search: URLSearchParams): ListFilters {
  const d = DEFAULT_LIST_FILTERS;
  const bool = (key: string) => search.get(key) === "true";
  const str = (key: string, fallback: string) => search.get(key) ?? fallback;
  const num = (key: string, fallback: number) => {
    const raw = search.get(key);
    if (!raw) return fallback;
    const n = Number(raw);
    return Number.isFinite(n) ? n : fallback;
  };

  return {
    state: str("state", d.state),
    suburb: str("suburb", d.suburb),
    search: str("search", d.search),
    enrichment_status: str("enrichment_status", d.enrichment_status),
    outreach_status: str("outreach_status", d.outreach_status),
    contact_permission_status: str("contact_permission_status", d.contact_permission_status),
    score_min: str("score_min", d.score_min),
    missing_email: bool("missing_email"),
    missing_website: bool("missing_website"),
    missing_phone: bool("missing_phone"),
    needs_review: bool("needs_review"),
    include_do_not_contact: bool("include_do_not_contact"),
    sort: str("sort", d.sort),
    limit: num("limit", d.limit),
    offset: num("offset", d.offset),
  };
}

export function listSearchString(filters: ListFilters): string {
  const qs = filtersToSearchParams(filters).toString();
  return qs ? `?${qs}` : "";
}
