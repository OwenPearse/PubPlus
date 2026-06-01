-- PubPlus — Migration 0033
-- Founder venue lead research domain: pre-launch outreach CRM separate from published truth.
--
-- RLS assumptions (matches 0020 workflow/intake pattern):
--   - authenticated admin sessions (admin_account + auth.uid()) may SELECT
--   - INSERT/UPDATE/DELETE are not granted to anon/authenticated API roles
--   - Django backend uses service_role / direct DB credentials for writes
-- updated_at: no DB trigger (project convention — timestamps maintained in application layer)

-- ---------------------------------------------------------------------------
-- Leads (operational research; not venue_published_* truth)
-- ---------------------------------------------------------------------------
create table public.founder_venue_leads (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid references public.venue (id) on delete set null,
  name text not null,
  normalized_name text,
  category text,
  address_line text,
  suburb text,
  state text,
  postcode text,
  country text not null default 'AU',
  latitude numeric check (
    latitude is null
    or (
      latitude >= -90
      and latitude <= 90
    )
  ),
  longitude numeric check (
    longitude is null
    or (
      longitude >= -180
      and longitude <= 180
    )
  ),
  phone text,
  website text,
  email text,
  instagram_url text,
  facebook_url text,
  contact_name text,
  contact_role text,
  source_summary text,
  confidence_score integer not null default 0 check (
    confidence_score >= 0
    and confidence_score <= 100
  ),
  founder_fit_score integer not null default 0 check (
    founder_fit_score >= 0
    and founder_fit_score <= 100
  ),
  founder_fit_breakdown jsonb not null default '{}'::jsonb,
  enrichment_status text not null default 'imported' check (
    enrichment_status in (
      'imported',
      'pending_enrichment',
      'enriched',
      'needs_review',
      'rejected'
    )
  ),
  outreach_status text not null default 'not_contacted' check (
    outreach_status in (
      'not_contacted',
      'queued',
      'called',
      'emailed',
      'replied',
      'signed_up',
      'rejected',
      'do_not_contact'
    )
  ),
  contact_permission_status text not null default 'unknown' check (
    contact_permission_status in (
      'unknown',
      'public_business_contact',
      'requested_info_by_phone',
      'requested_info_by_dm',
      'opted_in',
      'opted_out',
      'do_not_contact'
    )
  ),
  last_contacted_at timestamptz,
  last_contact_channel text check (
    last_contact_channel is null
    or last_contact_channel in (
      'phone',
      'email',
      'instagram',
      'facebook',
      'website_form',
      'in_person',
      'other'
    )
  ),
  unsubscribe_at timestamptz,
  unsubscribe_source text,
  notes text,
  dedupe_key text,
  suppressed_at timestamptz,
  suppression_reason text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.founder_venue_leads is
'Pre-launch founder venue research leads; separate from published venue truth until a future convert/moderation path.';

create index idx_founder_venue_leads_venue_id on public.founder_venue_leads (venue_id);

create index idx_founder_venue_leads_state on public.founder_venue_leads (state);

create index idx_founder_venue_leads_suburb on public.founder_venue_leads (suburb);

create index idx_founder_venue_leads_postcode on public.founder_venue_leads (postcode);

create index idx_founder_venue_leads_normalized_name on public.founder_venue_leads (normalized_name);

create index idx_founder_venue_leads_website on public.founder_venue_leads (website);

create index idx_founder_venue_leads_phone on public.founder_venue_leads (phone);

create index idx_founder_venue_leads_email on public.founder_venue_leads (email);

create index idx_founder_venue_leads_outreach_status on public.founder_venue_leads (outreach_status);

create index idx_founder_venue_leads_enrichment_status on public.founder_venue_leads (enrichment_status);

create index idx_founder_venue_leads_contact_permission_status on public.founder_venue_leads (contact_permission_status);

create index idx_founder_venue_leads_founder_fit_score on public.founder_venue_leads (founder_fit_score desc);

create index idx_founder_venue_leads_confidence_score on public.founder_venue_leads (confidence_score desc);

create index idx_founder_venue_leads_dedupe_key on public.founder_venue_leads (dedupe_key)
where
  dedupe_key is not null;

create index idx_founder_venue_leads_suppressed_at on public.founder_venue_leads (suppressed_at);

-- ---------------------------------------------------------------------------
-- Source records (batch or fetch provenance)
-- ---------------------------------------------------------------------------
create table public.founder_venue_lead_sources (
  id uuid primary key default gen_random_uuid (),
  lead_id uuid not null references public.founder_venue_leads (id) on delete cascade,
  source_type text not null check (
    source_type in (
      'csv_import',
      'purchased_dataset',
      'venue_website',
      'business_directory',
      'open_data',
      'google_places',
      'osm',
      'manual',
      'other'
    )
  ),
  source_url text,
  source_name text,
  raw_payload jsonb,
  fetched_at timestamptz not null default now (),
  confidence integer not null default 0 check (
    confidence >= 0
    and confidence <= 100
  ),
  created_at timestamptz not null default now ()
);

comment on table public.founder_venue_lead_sources is
'Provenance for lead data imports and enrichment fetches; not published truth.';

create index idx_founder_venue_lead_sources_lead_id on public.founder_venue_lead_sources (lead_id);

create index idx_founder_venue_lead_sources_source_type on public.founder_venue_lead_sources (source_type);

create index idx_founder_venue_lead_sources_created_at on public.founder_venue_lead_sources (created_at desc);

-- ---------------------------------------------------------------------------
-- Per-field attributions (raw/normalized values + contact safety)
-- ---------------------------------------------------------------------------
create table public.founder_venue_lead_field_attributions (
  id uuid primary key default gen_random_uuid (),
  lead_id uuid not null references public.founder_venue_leads (id) on delete cascade,
  source_id uuid references public.founder_venue_lead_sources (id) on delete set null,
  field_name text not null,
  source_type text check (
    source_type is null
    or source_type in (
      'csv_import',
      'purchased_dataset',
      'venue_website',
      'business_directory',
      'open_data',
      'google_places',
      'osm',
      'manual',
      'other'
    )
  ),
  source_url text,
  fetched_at timestamptz not null default now (),
  confidence integer not null default 0 check (
    confidence >= 0
    and confidence <= 100
  ),
  raw_value text,
  normalized_value text,
  contact_safety_class text check (
    contact_safety_class is null
    or contact_safety_class in (
      'generic_business_contact',
      'role_based_contact',
      'personal_business_contact',
      'likely_personal_or_unsafe'
    )
  ),
  created_at timestamptz not null default now ()
);

comment on table public.founder_venue_lead_field_attributions is
'Field-level provenance and contact-safety classification for founder leads.';

create index idx_founder_venue_lead_field_attributions_lead_id on public.founder_venue_lead_field_attributions (lead_id);

create index idx_founder_venue_lead_field_attributions_field_name on public.founder_venue_lead_field_attributions (field_name);

create index idx_founder_venue_lead_field_attributions_lead_field on public.founder_venue_lead_field_attributions (lead_id, field_name);

-- ---------------------------------------------------------------------------
-- Audit events (outreach, enrichment, import, suppression)
-- ---------------------------------------------------------------------------
create table public.founder_venue_lead_events (
  id uuid primary key default gen_random_uuid (),
  lead_id uuid not null references public.founder_venue_leads (id) on delete cascade,
  event_type text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid references public.admin_account (id) on delete set null,
  created_at timestamptz not null default now ()
);

comment on table public.founder_venue_lead_events is
'Append-only operational audit trail for founder lead workflow.';

create index idx_founder_venue_lead_events_lead_id on public.founder_venue_lead_events (lead_id);

create index idx_founder_venue_lead_events_event_type on public.founder_venue_lead_events (event_type);

create index idx_founder_venue_lead_events_created_at on public.founder_venue_lead_events (created_at desc);

create index idx_founder_venue_lead_events_lead_created_at on public.founder_venue_lead_events (lead_id, created_at desc);

-- ---------------------------------------------------------------------------
-- RLS: admin read visibility; writes via service_role / Django backend
-- ---------------------------------------------------------------------------
alter table public.founder_venue_leads enable row level security;

create policy founder_venue_leads_select_admin on public.founder_venue_leads for
select
  to authenticated using (public.is_admin_session ());

alter table public.founder_venue_lead_sources enable row level security;

create policy founder_venue_lead_sources_select_admin on public.founder_venue_lead_sources for
select
  to authenticated using (public.is_admin_session ());

alter table public.founder_venue_lead_field_attributions enable row level security;

create policy founder_venue_lead_field_attributions_select_admin on public.founder_venue_lead_field_attributions for
select
  to authenticated using (public.is_admin_session ());

alter table public.founder_venue_lead_events enable row level security;

create policy founder_venue_lead_events_select_admin on public.founder_venue_lead_events for
select
  to authenticated using (public.is_admin_session ());
