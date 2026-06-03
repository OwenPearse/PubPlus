-- PubPlus — Wave 6 / Migration 0017
-- RLS: published public-truth tables are discovery-readable; normal client roles must not write published truth.
-- Supabase service_role bypasses RLS (backend publish orchestration, migrations).

-- ---------------------------------------------------------------------------
-- Published public truth + geography reference (SELECT for anon + authenticated only)
-- ---------------------------------------------------------------------------
alter table public.venue enable row level security;

create policy venue_select_public on public.venue for
select
  to anon,
  authenticated using (true);

alter table public.geographic_region enable row level security;

create policy geographic_region_select_public on public.geographic_region for
select
  to anon,
  authenticated using (true);

alter table public.locality enable row level security;

create policy locality_select_public on public.locality for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_location enable row level security;

create policy venue_published_location_select_public on public.venue_published_location for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_map_point enable row level security;

create policy venue_published_map_point_select_public on public.venue_published_map_point for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_profile enable row level security;

create policy venue_published_profile_select_public on public.venue_published_profile for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_descriptive_copy enable row level security;

create policy venue_published_descriptive_copy_select_public on public.venue_published_descriptive_copy for
select
  to anon,
  authenticated using (true);

alter table public.venue_attribute_definition enable row level security;

create policy venue_attribute_definition_select_public on public.venue_attribute_definition for
select
  to anon,
  authenticated using (true);

alter table public.venue_attribute_allowed_value enable row level security;

create policy venue_attribute_allowed_value_select_public on public.venue_attribute_allowed_value for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_attribute_value enable row level security;

create policy venue_published_attribute_value_select_public on public.venue_published_attribute_value for
select
  to anon,
  authenticated using (true);

alter table public.venue_hours_regular enable row level security;

create policy venue_hours_regular_select_public on public.venue_hours_regular for
select
  to anon,
  authenticated using (true);

alter table public.venue_hours_exception enable row level security;

create policy venue_hours_exception_select_public on public.venue_hours_exception for
select
  to anon,
  authenticated using (true);

alter table public.venue_hours_uncertainty enable row level security;

create policy venue_hours_uncertainty_select_public on public.venue_hours_uncertainty for
select
  to anon,
  authenticated using (true);

alter table public.venue_derived_operational_claim enable row level security;

create policy venue_derived_operational_claim_select_public on public.venue_derived_operational_claim for
select
  to anon,
  authenticated using (true);

-- ---------------------------------------------------------------------------
-- Provenance source catalog (read-only reference; not workflow payloads)
-- ---------------------------------------------------------------------------
alter table public.external_data_source enable row level security;

create policy external_data_source_select_public on public.external_data_source for
select
  to anon,
  authenticated using (true);
