-- PubPlus — Tranche 1 / Migration 0005
-- Discovery attribute definitions + optional allowed values + published assignments.
-- Values are normalized rows (not opaque JSON blobs for discovery-driving claims).

-- ---------------------------------------------------------------------------
-- Attribute definitions (controlled keys / families)
-- ---------------------------------------------------------------------------
create table public.venue_attribute_definition (
  id uuid primary key default gen_random_uuid (),
  stable_key text not null unique,
  display_label text not null,
  value_shape text not null check (
    value_shape in (
      'boolean',
      'single_select',
      'multi_select',
      'numeric',
      'text_non_discovery'
    )
  ),
  cardinality text not null default 'single' check (cardinality in ('single', 'multi')),
  is_discovery_driving boolean not null default true,
  publishability_risk_hint text check (
    publishability_risk_hint in ('low', 'medium', 'high')
  ),
  created_at timestamptz not null default now ()
);

comment on table public.venue_attribute_definition is
'Structured discovery schema: stable keys and shapes; drives filters/badges when is_discovery_driving.';

create index idx_venue_attribute_definition_stable_key on public.venue_attribute_definition (stable_key);

-- ---------------------------------------------------------------------------
-- Optional normalized allowed values for discrete attributes (evolving vocabularies)
-- ---------------------------------------------------------------------------
create table public.venue_attribute_allowed_value (
  id uuid primary key default gen_random_uuid (),
  attribute_definition_id uuid not null references public.venue_attribute_definition (id) on delete cascade,
  code text not null,
  display_label text not null,
  sort_order int not null default 0,
  created_at timestamptz not null default now (),
  unique (attribute_definition_id, code)
);

comment on table public.venue_attribute_allowed_value is
'Discrete value rows for select/multi-select; prefer FK here over ad hoc enums for MVP filters.';

create index idx_venue_attribute_allowed_value_def on public.venue_attribute_allowed_value (attribute_definition_id);

-- ---------------------------------------------------------------------------
-- Published structured assignments (current-state truth)
-- ---------------------------------------------------------------------------
create table public.venue_published_attribute_value (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  attribute_definition_id uuid not null references public.venue_attribute_definition (id) on delete restrict,
  allowed_value_id uuid references public.venue_attribute_allowed_value (id) on delete restrict,
  value_boolean boolean,
  value_numeric double precision,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  check (
    (
      allowed_value_id is not null
    )
    or (value_boolean is not null)
    or (value_numeric is not null)
  )
);

comment on table public.venue_published_attribute_value is
'Published structured discovery values; staging lives in venue_proposal_staging_attribute.';

create index idx_venue_published_attribute_value_venue on public.venue_published_attribute_value (venue_id);
create index idx_venue_published_attribute_value_def on public.venue_published_attribute_value (attribute_definition_id);

-- One row per (venue, definition, discrete value) to support multi-select without duplicate tuples.
create unique index uq_venue_published_attribute_value_discrete_tuple on public.venue_published_attribute_value (
  venue_id,
  attribute_definition_id,
  allowed_value_id
)
where
  allowed_value_id is not null;

-- Single-cardinality and boolean/numeric uniqueness are enforced in the publish workflow (no subquery in index predicates).
