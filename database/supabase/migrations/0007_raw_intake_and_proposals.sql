-- PubPlus — Tranche 1 / Migration 0007
-- Raw/source intake, proposal header, staging payloads (non-published), proposal targets.
-- Published truth is not written here; formal publish + lineage tables apply later.

-- ---------------------------------------------------------------------------
-- Source registry
-- ---------------------------------------------------------------------------
create table public.external_data_source (
  id uuid primary key default gen_random_uuid (),
  code text not null unique,
  display_name text not null,
  kind text not null check (
    kind in (
      'import_batch',
      'api_partner',
      'admin_tool',
      'scrape',
      'other'
    )
  ),
  is_active boolean not null default true,
  created_at timestamptz not null default now ()
);

comment on table public.external_data_source is
'Registered provenance sources; source IDs do not define venue identity (DL-002).';

-- ---------------------------------------------------------------------------
-- Raw intake capture (workflow; not published truth)
-- ---------------------------------------------------------------------------
create table public.raw_venue_intake_record (
  id uuid primary key default gen_random_uuid (),
  external_data_source_id uuid not null references public.external_data_source (id) on delete restrict,
  venue_id uuid references public.venue (id) on delete set null,
  source_record_key text,
  captured_at timestamptz not null default now (),
  payload_jsonb jsonb not null,
  content_fingerprint text
);

comment on table public.raw_venue_intake_record is
'Raw/semi-structured payload + metadata; feeds proposals only through moderation/publish.';

create index idx_raw_venue_intake_source on public.raw_venue_intake_record (external_data_source_id);
create index idx_raw_venue_intake_venue on public.raw_venue_intake_record (venue_id);

-- ---------------------------------------------------------------------------
-- Proposal header (submission + lifecycle; not truth)
-- ---------------------------------------------------------------------------
create table public.venue_change_proposal (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  actor_type text not null check (
    actor_type in (
      'consumer',
      'owner',
      'admin',
      'system',
      'source'
    )
  ),
  actor_consumer_account_id uuid references public.consumer_account (id) on delete set null,
  actor_owner_account_id uuid references public.owner_account (id) on delete set null,
  actor_admin_account_id uuid references public.admin_account (id) on delete set null,
  actor_external_data_source_id uuid references public.external_data_source (id) on delete set null,
  raw_venue_intake_record_id uuid references public.raw_venue_intake_record (id) on delete set null,
  channel text not null check (
    channel in (
      'app_consumer',
      'app_owner',
      'owner_portal',
      'import_batch',
      'admin_tool',
      'system_job',
      'other'
    )
  ),
  proposal_kind text not null check (
    proposal_kind in (
      'whole_record',
      'field_family'
    )
  ),
  lifecycle_status text not null default 'staged' check (
    lifecycle_status in (
      'staged',
      'in_review',
      'approved',
      'rejected',
      'withdrawn',
      'superseded'
    )
  ),
  created_at timestamptz not null default now (),
  submitted_at timestamptz,
  closed_at timestamptz,
  superseded_by_proposal_id uuid references public.venue_change_proposal (id) on delete set null,
  constraint venue_change_proposal_actor_source_consistency check (
    (
      actor_type <> 'source'
    )
    or (actor_external_data_source_id is not null)
  )
);

comment on table public.venue_change_proposal is
'Workflow submission header; actor resolution + minimum evidence metadata enforced at application layer.';

create index idx_venue_change_proposal_venue on public.venue_change_proposal (venue_id);
create index idx_venue_change_proposal_lifecycle on public.venue_change_proposal (lifecycle_status);

-- ---------------------------------------------------------------------------
-- Target families (hybrid proposals)
-- ---------------------------------------------------------------------------
create table public.venue_proposal_target (
  venue_change_proposal_id uuid not null references public.venue_change_proposal (id) on delete cascade,
  target_family text not null check (
    target_family in (
      'profile',
      'geo',
      'attributes',
      'hours',
      'descriptive_copy',
      'whole_venue'
    )
  ),
  primary key (venue_change_proposal_id, target_family)
);

comment on table public.venue_proposal_target is
'Which published-truth families this proposal touches; payloads live in staging tables.';

-- ---------------------------------------------------------------------------
-- Staging: profile
-- ---------------------------------------------------------------------------
create table public.venue_proposal_staging_profile (
  id uuid primary key default gen_random_uuid (),
  venue_change_proposal_id uuid not null unique references public.venue_change_proposal (id) on delete cascade,
  venue_id uuid not null references public.venue (id) on delete cascade,
  proposed_display_name text,
  proposed_slug text,
  proposed_discovery_eligibility_status text,
  proposed_operational_status text,
  proposed_short_description text,
  proposed_long_description text
);

comment on table public.venue_proposal_staging_profile is
'Non-published profile + descriptive copy candidates; promotion only via Stage-2 review + publish.';

create index idx_venue_proposal_staging_profile_venue on public.venue_proposal_staging_profile (venue_id);

-- ---------------------------------------------------------------------------
-- Staging: geo / map candidates
-- ---------------------------------------------------------------------------
create table public.venue_proposal_staging_location (
  id uuid primary key default gen_random_uuid (),
  venue_change_proposal_id uuid not null unique references public.venue_change_proposal (id) on delete cascade,
  venue_id uuid not null references public.venue (id) on delete cascade,
  proposed_locality_id uuid references public.locality (id) on delete restrict,
  proposed_address_line_1 text,
  proposed_address_line_2 text,
  proposed_postal_code text,
  proposed_country_code char(2),
  proposed_latitude double precision,
  proposed_longitude double precision
);

comment on table public.venue_proposal_staging_location is
'Staged geo; weak/disputed values stay here until approved into published tables.';

create index idx_venue_proposal_staging_location_venue on public.venue_proposal_staging_location (venue_id);

-- ---------------------------------------------------------------------------
-- Staging: attributes
-- ---------------------------------------------------------------------------
create table public.venue_proposal_staging_attribute (
  id uuid primary key default gen_random_uuid (),
  venue_change_proposal_id uuid not null references public.venue_change_proposal (id) on delete cascade,
  venue_id uuid not null references public.venue (id) on delete cascade,
  attribute_definition_id uuid not null references public.venue_attribute_definition (id) on delete restrict,
  allowed_value_id uuid references public.venue_attribute_allowed_value (id) on delete restrict,
  value_boolean boolean,
  value_numeric double precision,
  check (
    (
      allowed_value_id is not null
    )
    or (value_boolean is not null)
    or (value_numeric is not null)
  )
);

comment on table public.venue_proposal_staging_attribute is
'Staged attribute assignments mirroring published value columns.';

create index idx_venue_proposal_staging_attribute_proposal on public.venue_proposal_staging_attribute (venue_change_proposal_id);
create index idx_venue_proposal_staging_attribute_venue on public.venue_proposal_staging_attribute (venue_id);

-- ---------------------------------------------------------------------------
-- Staging: hours packages (JSON for baseline/exception complexity; uncertainty explicit)
-- ---------------------------------------------------------------------------
create table public.venue_proposal_staging_hours (
  id uuid primary key default gen_random_uuid (),
  venue_change_proposal_id uuid not null unique references public.venue_change_proposal (id) on delete cascade,
  venue_id uuid not null references public.venue (id) on delete cascade,
  proposed_uncertainty_level text check (
    proposed_uncertainty_level in (
      'unknown',
      'partial',
      'weak_stale',
      'disputed',
      'resolved_confident'
    )
  ),
  regular_hours_json jsonb not null default '[]'::jsonb,
  exceptions_json jsonb not null default '[]'::jsonb,
  notes text
);

comment on table public.venue_proposal_staging_hours is
'Staged hours packages; publish workflow materializes into normalized published hours tables.';

create index idx_venue_proposal_staging_hours_venue on public.venue_proposal_staging_hours (venue_id);
