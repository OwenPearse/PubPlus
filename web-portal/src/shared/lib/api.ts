import { waitForAccessToken } from "@/shared/lib/supabase";
import { getApiBaseUrl } from "@/shared/lib/env";
import type {
  EnrichmentResult,
  FounderVenueWorkspaceSummary,
  LeadDetailResponse,
  ListFilters,
  ListLeadsResponse,
  PatchableLeadField,
} from "@/shared/lib/types";
import { buildListQueryParams } from "@/shared/lib/filters";

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
    let code: ApiErrorCode = "unknown_error";

    if (details && typeof details === "object") {
      const body = details as {
        error?: { code?: string; message?: string };
        message?: string;
      };
      if (body.error?.message) {
        message = body.error.message;
      } else if ("message" in body) {
        message = String(body.message);
      }
      if (body.error?.code === "validation_error") code = "validation_error";
      else if (body.error?.code === "forbidden") code = "forbidden";
      else if (body.error?.code === "not_found") code = "not_found";
      else if (body.error?.code === "unauthorized") code = "unauthorized";
    }

    if (code === "unknown_error") {
      if (status === 401) code = "unauthorized";
      else if (status === 403) code = "forbidden";
      else if (status === 404) code = "not_found";
      else if (status === 400 || status === 422) code = "validation_error";
      else if (status >= 500) code = "server_error";
    }
    return { code, message, status, details };
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
  const token = await waitForAccessToken();
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

export function getFounderVenueWorkspaceSummary() {
  return apiRequest<FounderVenueWorkspaceSummary>(
    "/api/v1/internal/founder-venues/summary",
  );
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

export type OwnerNextStep =
  | "complete_owner_provisioning"
  | "enroll_mfa"
  | "owner_waiting_for_membership"
  | "owner_waiting_for_venue_access"
  | "portal_home";

export type OwnerProvisionResponse = {
  authenticated: boolean;
  owner_account_exists: boolean;
  owner_account_id: string;
  provisioned: boolean;
  created: boolean;
  next_step: OwnerNextStep;
};

export type OwnerAuthProbeBody = {
  authenticated: boolean;
  owner_account_exists: boolean;
  owner_account_active: boolean;
  mfa_required: boolean;
  mfa_enabled?: boolean;
  aal: string | null;
  has_active_business_membership: boolean;
  has_approved_managed_venue_relationship: boolean;
  business_count: number;
  venue_count: number;
  owner_account_id: string | null;
  next_step: OwnerNextStep;
  error?: { code: string; message: string };
};

export type OwnerAuthProbeResult =
  | { status: 200; body: OwnerAuthProbeBody }
  | { status: 403; body: OwnerAuthProbeBody };

export function ownerProvision() {
  return apiRequest<OwnerProvisionResponse>("/api/v1/owner/provision", {
    method: "POST",
  });
}

export async function ownerAuthProbe(): Promise<OwnerAuthProbeResult> {
  try {
    const body = await apiRequest<OwnerAuthProbeBody>("/api/v1/owner/auth-probe");
    return { status: 200, body };
  } catch (error) {
    if (isApiRequestError(error) && error.status === 403 && error.details) {
      return { status: 403, body: error.details as OwnerAuthProbeBody };
    }
    throw error;
  }
}

export type ApiResponse<T> = { data: T };

export type OwnerOnboardingStatus =
  | "not_started"
  | "in_progress"
  | "submitted"
  | "needs_changes"
  | "complete";

export type OwnerVenueListItem = {
  venue_id: string;
  display_name: string;
  locality_name: string | null;
  state_code: string | null;
  relationship_lifecycle: "approved";
  onboarding_status: OwnerOnboardingStatus;
  pending_proposal_count: number;
  completeness_percent: number;
  required_basics_complete: boolean;
};

export type OwnerVenueListResponse = {
  venues: OwnerVenueListItem[];
  meta: {
    total: number;
    default_venue_id: string | null;
  };
};

export type OwnerVenueHoursRegular = {
  day_of_week: number;
  opens_at: string;
  closes_at: string;
  crosses_midnight: boolean;
};

export type OwnerVenueContactBlock = {
  supported: false;
  phone: null;
  email: null;
  website: null;
};

export type OwnerVenueCompletenessSection = {
  key: string;
  label: string;
  status: string;
  required: boolean;
  available: boolean;
};

export type OwnerOpeningHoursPayload = {
  uncertainty_level?:
    | "unknown"
    | "partial"
    | "weak_stale"
    | "disputed"
    | "resolved_confident";
  regular_hours_json?: Array<{
    day_of_week: number;
    opens_at: string;
    closes_at: string;
    crosses_midnight?: boolean;
    sort_order?: number;
  }>;
  exceptions_json?: Array<Record<string, unknown>>;
  notes?: string | null;
};

export type OwnerCoreDetailsPayload = {
  display_name?: string;
  address_line_1?: string;
  address_line_2?: string | null;
  postal_code?: string;
  locality_id?: string;
  country_code?: string;
  latitude?: number | null;
  longitude?: number | null;
  short_description?: string;
  long_description?: string | null;
  opening_hours?: OwnerOpeningHoursPayload;
  owner_confirms_management?: boolean;
};

export type OwnerVenueDetail = {
  venue_id: string;
  display_name: string;
  listing: {
    discovery_eligibility_status: string;
    operational_status: string;
  };
  relationship: {
    lifecycle: "approved";
    business_id: string;
    capabilities: string[];
  };
  published: {
    profile: {
      display_name: string | null;
      slug: string | null;
      operational_status: string | null;
    };
    location: {
      locality_id: string | null;
      locality_name: string | null;
      state_code: string | null;
      address_line_1: string | null;
      address_line_2: string | null;
      postal_code: string | null;
      country_code: string | null;
      latitude: number | null;
      longitude: number | null;
    };
    descriptions: {
      short_description: string | null;
      long_description: string | null;
    };
    hours: {
      uncertainty_level: string;
      regular: OwnerVenueHoursRegular[];
      exceptions: unknown[];
    };
    contact: OwnerVenueContactBlock;
  };
  draft: {
    proposal_id: string | null;
    lifecycle_status: string | null;
    last_saved_at: string | null;
    payload_preview: {
      display_name: string | null;
      address_line_1: string | null;
      locality_id: string | null;
    };
    core_details_payload: OwnerCoreDetailsPayload | null;
  };
  pending_review: {
    proposal_id: string | null;
    lifecycle_status: string | null;
    submitted_at: string | null;
    reviewed_at: string | null;
    review_outcome: "approved" | "rejected" | "changes_requested" | null;
  };
  completeness: {
    percent: number;
    required_basics_complete: boolean;
    sections: OwnerVenueCompletenessSection[];
  };
  sections_available: {
    core_details: boolean;
    events: boolean;
    meal_specials: boolean;
    tap_list: boolean;
    features: boolean;
    photos: boolean;
  };
};

export type OwnerVenueDetailResponse = OwnerVenueDetail;

export function ownerVenueList() {
  return apiRequest<ApiResponse<OwnerVenueListResponse>>("/api/v1/owner/venues");
}

export function ownerVenueDetail(venueId: string) {
  return apiRequest<ApiResponse<OwnerVenueDetailResponse>>(
    `/api/v1/owner/venues/${encodeURIComponent(venueId)}`,
  );
}

export type OwnerVenueProposalRequest = {
  section: "core_details";
  intent: "draft" | "submit";
  payload: OwnerCoreDetailsPayload;
};

export type OwnerVenueProposalResponse = {
  proposal_id: string;
  venue_id: string;
  section: "core_details";
  intent: "draft" | "submit";
  lifecycle_status: "staged" | "in_review";
  submitted_at: string | null;
  message: string;
};

export function ownerVenueProposal(venueId: string, body: OwnerVenueProposalRequest) {
  return apiRequest<ApiResponse<OwnerVenueProposalResponse>>(
    `/api/v1/owner/venues/${encodeURIComponent(venueId)}/proposals`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

export type OwnerOperationalProfilePatchRequest = {
  short_description?: string | null;
  long_description?: string | null;
};

export type OwnerOperationalProfilePatchResponse = {
  venue_id: string;
  updated: {
    short_description: string | null;
    long_description: string | null;
  };
  message: string;
};

export function ownerPatchOperationalProfile(
  venueId: string,
  body: OwnerOperationalProfilePatchRequest,
) {
  return apiRequest<ApiResponse<OwnerOperationalProfilePatchResponse>>(
    `/api/v1/owner/venues/${encodeURIComponent(venueId)}/operational-profile`,
    { method: "PATCH", body: JSON.stringify(body) },
  );
}

export type OwnerHoursPatchRequest = OwnerOpeningHoursPayload;

export type OwnerHoursPatchResponse = {
  venue_id: string;
  hours: {
    uncertainty_level: string;
    regular: OwnerVenueHoursRegular[];
    exceptions: unknown[];
    notes: string | null;
  };
  message: string;
};

export function ownerPatchHours(venueId: string, body: OwnerHoursPatchRequest) {
  return apiRequest<ApiResponse<OwnerHoursPatchResponse>>(
    `/api/v1/owner/venues/${encodeURIComponent(venueId)}/hours`,
    { method: "PATCH", body: JSON.stringify(body) },
  );
}

export type OwnerRestrictedIdentityPayload = {
  display_name?: string;
  address_line_1?: string;
  address_line_2?: string | null;
  postal_code?: string;
  locality_id?: string;
  country_code?: string;
  latitude?: number | null;
  longitude?: number | null;
};

export type OwnerRestrictedChangeRequest = {
  section: "identity_location";
  payload: OwnerRestrictedIdentityPayload;
};

export type OwnerRestrictedChangeResponse = {
  proposal_id: string;
  venue_id: string;
  section: "identity_location";
  lifecycle_status: "in_review";
  submitted_at: string | null;
  message: string;
};

export function ownerRestrictedChangeRequest(
  venueId: string,
  body: OwnerRestrictedChangeRequest,
) {
  return apiRequest<ApiResponse<OwnerRestrictedChangeResponse>>(
    `/api/v1/owner/venues/${encodeURIComponent(venueId)}/restricted-change-requests`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

export type ReferenceLocality = {
  id: string;
  name: string;
  state?: string;
  country_code?: string;
  geographic_region_id: string;
  geographic_region_name: string;
  latitude?: number;
  longitude?: number;
};

export type ReferenceLocalitiesResponse = {
  localities: ReferenceLocality[];
};

export function referenceLocalities() {
  return apiRequest<ApiResponse<ReferenceLocalitiesResponse>>(
    "/api/v1/reference/localities",
  );
}

export type VenueClaimCandidate = {
  venue_id: string;
  display_name: string;
  locality_name: string | null;
  state_code: string | null;
  address_line_1: string | null;
  match_reason: string;
  match_score: number;
};

export type VenueClaimCandidatesResponse = {
  candidates: VenueClaimCandidate[];
  best_match: VenueClaimCandidate | null;
  has_good_match: boolean;
};

export type ExistingVenueClaimRequest = {
  mode: "claim_existing";
  venue_id: string;
  claimant_note?: string;
};

export type NewVenueClaimRequest = {
  mode: "submit_new";
  venue_name: string;
  address_line_1?: string;
  locality_id?: string;
  claimant_note?: string;
};

export type SubmitNewOrClaimRequest = {
  mode: "submit_new_or_claim";
  venue_name: string;
  address_line_1: string;
  locality_id: string;
  claimant_note?: string;
};

export type VenueClaimRequestResponse = {
  claim_request_id: string;
  status: "submitted" | "under_review";
  message: string;
};

export function ownerVenueClaimCandidates(query: {
  name?: string;
  locality_id?: string;
  q?: string;
  address_line_1?: string;
}) {
  const params: Record<string, string> = {};
  if (query.name) params.name = query.name;
  if (query.locality_id) params.locality_id = query.locality_id;
  if (query.q) params.q = query.q;
  if (query.address_line_1) params.address_line_1 = query.address_line_1;
  return apiRequest<ApiResponse<VenueClaimCandidatesResponse>>(
    "/api/v1/owner/venue-claim-candidates",
    { query: params },
  );
}

export function ownerVenueClaimRequest(
  body: ExistingVenueClaimRequest | NewVenueClaimRequest | SubmitNewOrClaimRequest,
) {
  return apiRequest<ApiResponse<VenueClaimRequestResponse>>(
    "/api/v1/owner/venue-claim-requests",
    { method: "POST", body: JSON.stringify(body) },
  );
}

export function parseApiValidationDetails(error: unknown): Record<string, string[]> {
  if (!isApiRequestError(error)) return {};
  const data = error.details;
  if (!data || typeof data !== "object") return {};
  const body = data as { error?: { details?: Record<string, string[]> } };
  if (body.error?.details && typeof body.error.details === "object") {
    return body.error.details;
  }
  return {};
}

export function isApiRequestError(error: unknown): error is ApiRequestError {
  return Boolean(error && typeof error === "object" && "code" in error && "status" in error);
}

export {
  markFounderVenueCalled,
  markFounderVenueDoNotContact,
  markFounderVenueEmailed,
  markFounderVenueQueued,
  markFounderVenueRejected,
  markFounderVenueReplied,
  markFounderVenueSignedUp,
  saveFounderVenueNotes,
} from "@/shared/lib/outreach";

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
