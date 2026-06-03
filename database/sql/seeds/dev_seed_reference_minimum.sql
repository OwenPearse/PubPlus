-- PubPlus — minimal reference seed (local / dev / demo)
-- Safe to re-run: uses fixed IDs and ON CONFLICT where possible.
-- Depends on: migrations through 0005 (attribute tables) and 0007 (external_data_source).
-- Does not touch auth.users.

begin;

-- ---------------------------------------------------------------------------
-- Geography (AU → NSW → Sydney) — stable IDs shared with venue + consumer seeds
-- ---------------------------------------------------------------------------
insert into public.geographic_region (
  id,
  parent_region_id,
  name,
  region_code,
  region_level
)
values
  (
    '11111111-1111-4111-8111-111111111101',
    null,
    'Australia',
    'AU',
    'country'
  ),
  (
    '11111111-1111-4111-8111-111111111102',
    '11111111-1111-4111-8111-111111111101',
    'New South Wales',
    'NSW',
    'state'
  )
on conflict (id) do nothing;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values
  (
    '22222222-2222-4222-8222-222222222201',
    '11111111-1111-4111-8111-111111111102',
    'Sydney',
    'sydney'
  )
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- Discovery attribute definitions + allowed values (MVP-style)
-- ---------------------------------------------------------------------------
insert into public.venue_attribute_definition (
  id,
  stable_key,
  display_label,
  value_shape,
  cardinality,
  is_discovery_driving,
  publishability_risk_hint
)
values
  (
    '33333333-3333-4333-8333-333333333301',
    'serves_food',
    'Serves food',
    'boolean',
    'single',
    true,
    'low'
  ),
  (
    '33333333-3333-4333-8333-333333333302',
    'venue_style',
    'Venue style',
    'single_select',
    'single',
    true,
    'medium'
  )
on conflict (id) do nothing;

insert into public.venue_attribute_allowed_value (
  id,
  attribute_definition_id,
  code,
  display_label,
  sort_order
)
values
  (
    '44444444-4444-4444-8444-444444444401',
    '33333333-3333-4333-8333-333333333302',
    'pub',
    'Pub',
    10
  ),
  (
    '44444444-4444-4444-8444-444444444402',
    '33333333-3333-4333-8333-333333333302',
    'brewery',
    'Brewery / taproom',
    20
  )
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- External source registry (for intake / provenance demos)
-- ---------------------------------------------------------------------------
insert into public.external_data_source (
  id,
  code,
  display_name,
  kind,
  is_active
)
values
  (
    '55555555-5555-4555-8555-555555555501',
    'demo_admin_tool',
    'Demo admin tool',
    'admin_tool',
    true
  )
on conflict (id) do nothing;

commit;
