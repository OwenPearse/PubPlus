export type FounderVenueLeadListItem = {
  id: string;
  name: string;
  suburb: string | null;
  state: string | null;
  category: string | null;
  phone: string | null;
  website: string | null;
  email: string | null;
  instagram_url: string | null;
  facebook_url: string | null;
  confidence_score: number;
  founder_fit_score: number;
  enrichment_status: string;
  outreach_status: string;
  contact_permission_status: string;
  created_at: string | null;
  updated_at: string | null;
};

export type ListLeadsResponse = {
  items: FounderVenueLeadListItem[];
  pagination: {
    limit: number;
    offset: number;
    count: number;
    total: number;
    has_more: boolean;
  };
};

export type FounderFitBreakdown = {
  score?: number;
  components?: Record<string, number>;
  positive_signals?: string[];
  negative_signals?: string[];
  warnings?: string[];
};

export type FounderVenueLeadDetail = FounderVenueLeadListItem & {
  venue_id: string | null;
  normalized_name: string | null;
  address_line: string | null;
  postcode: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  contact_name: string | null;
  contact_role: string | null;
  source_summary: string | null;
  notes: string | null;
  founder_fit_breakdown: FounderFitBreakdown;
  last_contacted_at: string | null;
  last_contact_channel: string | null;
  unsubscribe_at: string | null;
  unsubscribe_source: string | null;
  suppressed_at: string | null;
  suppression_reason: string | null;
};

export type LeadSource = {
  id: string;
  source_type: string;
  source_url: string | null;
  source_name: string | null;
  fetched_at: string | null;
  confidence: number | null;
  created_at: string | null;
};

export type FieldAttribution = {
  id: string;
  field_name: string;
  source_type: string;
  source_url: string | null;
  confidence: number | null;
  raw_value: string | null;
  normalized_value: string | null;
  contact_safety_class: string | null;
  fetched_at: string | null;
  created_at: string | null;
};

export type LeadEvent = {
  id: string;
  event_type: string;
  metadata: Record<string, unknown>;
  created_by: string | null;
  created_at: string | null;
};

export type LeadDetailResponse = {
  lead: FounderVenueLeadDetail;
  sources: LeadSource[];
  field_attributions: FieldAttribution[];
  events: LeadEvent[];
};

export type EnrichmentResult = {
  lead_id: string;
  fetched_urls: string[];
  candidates: Array<{
    field_name: string;
    raw_value: string;
    normalized_value: string | null;
    source_url: string;
    confidence: number;
    contact_safety_class: string | null;
  }>;
  product_signals: string[];
  warnings: string[];
  errors: string[];
  fields_promoted: string[];
  enrichment_status: string | null;
  dry_run: boolean;
};

export type ListFilters = {
  state: string;
  suburb: string;
  search: string;
  enrichment_status: string;
  outreach_status: string;
  contact_permission_status: string;
  score_min: string;
  missing_email: boolean;
  missing_website: boolean;
  missing_phone: boolean;
  needs_review: boolean;
  include_do_not_contact: boolean;
  sort: string;
  limit: number;
  offset: number;
};

export const DEFAULT_LIST_FILTERS: ListFilters = {
  state: "VIC",
  suburb: "",
  search: "",
  enrichment_status: "",
  outreach_status: "",
  contact_permission_status: "",
  score_min: "",
  missing_email: false,
  missing_website: false,
  missing_phone: false,
  needs_review: false,
  include_do_not_contact: false,
  sort: "founder_fit_score_desc",
  limit: 50,
  offset: 0,
};

export const PATCHABLE_LEAD_FIELDS = [
  "name",
  "category",
  "address_line",
  "suburb",
  "state",
  "postcode",
  "phone",
  "website",
  "email",
  "instagram_url",
  "facebook_url",
  "contact_name",
  "contact_role",
  "notes",
  "enrichment_status",
  "outreach_status",
  "contact_permission_status",
  "last_contacted_at",
  "last_contact_channel",
] as const;

export type PatchableLeadField = (typeof PATCHABLE_LEAD_FIELDS)[number];
