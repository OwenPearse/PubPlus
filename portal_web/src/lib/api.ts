import { getAccessToken } from "@/lib/supabase";
import { getApiBaseUrl } from "@/lib/env";
import type {
  EnrichmentResult,
  LeadDetailResponse,
  ListFilters,
  ListLeadsResponse,
  PatchableLeadField,
} from "@/lib/types";
import { buildListQueryParams } from "@/lib/filters";

export type ApiErrorCode =
  | "network_error"
  | "validation_error"
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "server_error"
  | "unknown_error";

export type ApiRequestError = {
  code: ApiErrorCode;
  message: string;
  status: number | null;
  details?: unknown;
};

const DEFAULT_HEADERS: HeadersInit = {
  Accept: "application/json, application/problem+json",
};

function toApiPath(path: string): string {
  const base = getApiBaseUrl();
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalized}`;
}

function applyQuery(path: string, query?: Record<string, string>): string {
  if (!query || Object.keys(query).length === 0) return path;
  const qs = new URLSearchParams(query).toString();
  return qs ? `${path}?${qs}` : path;
}

function toApiError(error: unknown): ApiRequestError {
  if (error && typeof error === "object" && "status" in error) {
    const status = Number((error as { status?: number }).status);
    const details = (error as { data?: unknown }).data;
    let message = `Request failed (${status})`;
    if (details && typeof details === "object" && "message" in details) {
      message = String((details as { message: string }).message);
    }
    if (status === 401) return { code: "unauthorized", message, status, details };
    if (status === 403) return { code: "forbidden", message, status, details };
    if (status === 404) return { code: "not_found", message, status, details };
    if (status === 400 || status === 422) {
      return { code: "validation_error", message, status, details };
    }
    if (status >= 500) return { code: "server_error", message, status, details };
    return { code: "unknown_error", message, status, details };
  }
  if (error instanceof TypeError) {
    return { code: "network_error", message: error.message, status: null };
  }
  return {
    code: "unknown_error",
    message: error instanceof Error ? error.message : "Unknown error",
    status: null,
  };
}

async function apiRequest<T>(
  path: string,
  options: RequestInit & { query?: Record<string, string> } = {},
): Promise<T> {
  const { query, ...rest } = options;
  const url = applyQuery(toApiPath(path), query);
  const headers = new Headers(DEFAULT_HEADERS);
  if (options.headers) {
    new Headers(options.headers).forEach((v, k) => headers.set(k, v));
  }
  const token = await getAccessToken();
  if (!token) {
    throw toApiError({ status: 401, data: { message: "Sign in required." } });
  }
  headers.set("authorization", `Bearer ${token}`);
  if (rest.body && !headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }

  try {
    const response = await fetch(url, { ...rest, headers });
    if (!response.ok) {
      let data: unknown = null;
      const text = await response.text();
      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          data = text;
        }
      }
      throw { status: response.status, data };
    }
    if (response.status === 204) return null as T;
    const ct = response.headers.get("content-type") ?? "";
    if (ct.includes("application/json")) return (await response.json()) as T;
    return (await response.text()) as T;
  } catch (error) {
    throw toApiError(error);
  }
}

export function listFounderVenueLeads(filters: ListFilters) {
  return apiRequest<ListLeadsResponse>("/api/v1/internal/founder-venues/leads", {
    query: buildListQueryParams(filters),
  });
}

export function getFounderVenueLead(leadId: string) {
  return apiRequest<LeadDetailResponse>(
    `/api/v1/internal/founder-venues/leads/${leadId}`,
  );
}

export function patchFounderVenueLead(
  leadId: string,
  body: Partial<Record<PatchableLeadField, string | null>>,
) {
  return apiRequest<LeadDetailResponse>(
    `/api/v1/internal/founder-venues/leads/${leadId}`,
    { method: "PATCH", body: JSON.stringify(body) },
  );
}

export function markLeadDoNotContact(leadId: string, reason?: string) {
  return apiRequest<LeadDetailResponse>(
    `/api/v1/internal/founder-venues/leads/${leadId}/mark-do-not-contact`,
    { method: "POST", body: JSON.stringify(reason ? { reason } : {}) },
  );
}

export function enrichFounderVenueLead(leadId: string, dryRun: boolean) {
  return apiRequest<EnrichmentResult>(
    `/api/v1/internal/founder-venues/leads/${leadId}/enrich`,
    { method: "POST", body: JSON.stringify({ dry_run: dryRun }) },
  );
}

export function internalAuthProbe() {
  return apiRequest<{ status: string; subject: string }>(
    "/api/v1/internal/auth-probe",
  );
}

export function formatApiError(error: unknown): string {
  if (error && typeof error === "object" && "code" in error) {
    const e = error as ApiRequestError;
    if (e.code === "forbidden") {
      return "Access denied. Your account needs internal admin permission.";
    }
    if (e.code === "unauthorized") {
      return "Please sign in with an internal admin account.";
    }
    return e.message;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}
