-- PubPlus — Tranche 1 / Migration 0003
-- Geography reference spine + published authoritative location + single map point per venue.
-- Weak/disputed/staging geo stays in workflow tables (later migration), not here.

-- ---------------------------------------------------------------------------
-- Geography reference (hierarchy + canonical locality)
-- ---------------------------------------------------------------------------
create table public.geographic_region (
  id uuid primary key default gen_random_uuid (),
  parent_region_id uuid references public.geographic_region (id) on delete restrict,
  name text not null,
  region_code text,
  region_level text not null check (
    region_level in (
      'country',
      'state',
      'region',
      'macro',
      'other'
    )
  ),
  created_at timestamptz not null default now ()
);

comment on table public.geographic_region is
'Geography hierarchy node (country/state/region/etc.); optional self-parent for trees.';

create index idx_geographic_region_parent on public.geographic_region (parent_region_id);

create table public.locality (
  id uuid primary key default gen_random_uuid (),
  geographic_region_id uuid not null references public.geographic_region (id) on delete restrict,
  name text not null,
  slug text,
  created_at timestamptz not null default now ()
);

comment on table public.locality is
'Canonical suburb/locality for structured search, grouping, and published venue addressing.';

create index idx_locality_region on public.locality (geographic_region_id);
create index idx_locality_slug on public.locality (slug) where slug is not null;

-- ---------------------------------------------------------------------------
-- Published structured address (one coherent family per venue)
-- ---------------------------------------------------------------------------
create table public.venue_published_location (
  venue_id uuid primary key references public.venue (id) on delete cascade,
  locality_id uuid not null references public.locality (id) on delete restrict,
  address_line_1 text,
  address_line_2 text,
  postal_code text,
  country_code char(2) not null default 'AU',
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_location is
'Published structured address; not raw import text. FK to locality for hierarchy joins.';

create index idx_venue_published_location_locality on public.venue_published_location (locality_id);

-- ---------------------------------------------------------------------------
-- Exactly one authoritative published map point per venue (1:1)
-- ---------------------------------------------------------------------------
create table public.venue_published_map_point (
  venue_id uuid primary key references public.venue (id) on delete cascade,
  latitude double precision not null check (
    latitude >= -90
    and latitude <= 90
  ),
  longitude double precision not null check (
    longitude >= -180
    and longitude <= 180
  ),
  coordinate_system text not null default 'WGS84' check (coordinate_system in ('WGS84')),
  precision_meters double precision check (precision_meters is null or precision_meters >= 0),
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_map_point is
'Single live map pin for discovery; not source scrape coordinates or staging candidates.';
