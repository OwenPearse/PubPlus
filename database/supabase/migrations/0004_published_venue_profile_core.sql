-- PubPlus — Tranche 1 / Migration 0004
-- Published venue profile + optional descriptive copy (non–discovery-driving narrative).

-- ---------------------------------------------------------------------------
-- Published public profile (discovery-facing; not workflow state)
-- ---------------------------------------------------------------------------
create table public.venue_published_profile (
  venue_id uuid primary key references public.venue (id) on delete cascade,
  display_name text not null,
  slug text,
  discovery_eligibility_status text not null default 'unknown' check (
    discovery_eligibility_status in (
      'unknown',
      'eligible',
      'limited',
      'hidden',
      'retired'
    )
  ),
  operational_status text not null default 'unknown' check (
    operational_status in (
      'unknown',
      'open',
      'closed',
      'temporarily_closed',
      'seasonal'
    )
  ),
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_profile is
'Live published profile for search/detail; distinct from proposal lifecycle and authority states.';

create unique index uq_venue_published_profile_slug on public.venue_published_profile (slug)
where
  slug is not null;

create index idx_venue_published_profile_display_name on public.venue_published_profile (display_name);

-- ---------------------------------------------------------------------------
-- Low-risk narrative / marketing copy (explicitly not structured discovery filters)
-- ---------------------------------------------------------------------------
create table public.venue_published_descriptive_copy (
  venue_id uuid primary key references public.venue (id) on delete cascade,
  short_description text,
  long_description text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_descriptive_copy is
'Public narrative copy; must not be the sole carrier of filter/badge/search-driving claims (DL-005).';
