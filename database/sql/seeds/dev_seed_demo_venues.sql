-- PubPlus — demo published venues (local / dev / demo)
-- Inserts canonical venues + published profile/location/map + attributes + hours families.
-- Depends on: dev_seed_reference_minimum.sql (geography + attribute defs + external source IDs).
-- Note: direct inserts into published-truth tables are for local/dev convenience only; production
-- mutations are expected via service_role / publish orchestration (RLS blocks normal clients).

begin;

-- ---------------------------------------------------------------------------
-- Venues
-- ---------------------------------------------------------------------------
insert into public.venue (id)
values
  ('f1111111-1111-4111-8111-111111111101'),
  ('f1111111-1111-4111-8111-111111111102')
on conflict (id) do nothing;

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values
  (
    'f1111111-1111-4111-8111-111111111101',
    'Harbour View Hotel',
    'harbour-view-hotel-sydney',
    'eligible',
    'open'
  ),
  (
    'f1111111-1111-4111-8111-111111111102',
    'Yeast & Barrel Brewing',
    'yeast-barrel-brewing-sydney',
    'eligible',
    'open'
  )
on conflict (venue_id) do update set
  display_name = excluded.display_name,
  slug = excluded.slug,
  discovery_eligibility_status = excluded.discovery_eligibility_status,
  operational_status = excluded.operational_status,
  updated_at = now ();

insert into public.venue_published_descriptive_copy (
  venue_id,
  short_description,
  long_description
)
values
  (
    'f1111111-1111-4111-8111-111111111101',
    'Heritage pub near the water.',
    'Demo narrative copy only — structured discovery filters use attribute + hours tables.'
  ),
  (
    'f1111111-1111-4111-8111-111111111102',
    'Small-batch brewery with tasting room.',
    'Demo narrative copy only — structured discovery filters use attribute + hours tables.'
  )
on conflict (venue_id) do update set
  short_description = excluded.short_description,
  long_description = excluded.long_description,
  updated_at = now ();

insert into public.venue_published_location (
  venue_id,
  locality_id,
  address_line_1,
  postal_code,
  country_code
)
values
  (
    'f1111111-1111-4111-8111-111111111101',
    '22222222-2222-4222-8222-222222222201',
    '1 Demo Wharf Rd',
    '2000',
    'AU'
  ),
  (
    'f1111111-1111-4111-8111-111111111102',
    '22222222-2222-4222-8222-222222222201',
    '88 Fermentation Ln',
    '2000',
    'AU'
  )
on conflict (venue_id) do update set
  locality_id = excluded.locality_id,
  address_line_1 = excluded.address_line_1,
  postal_code = excluded.postal_code,
  country_code = excluded.country_code,
  updated_at = now ();

insert into public.venue_published_map_point (
  venue_id,
  latitude,
  longitude,
  coordinate_system,
  precision_meters
)
values
  (
    'f1111111-1111-4111-8111-111111111101',
    -33.86,
    151.21,
    'WGS84',
    25
  ),
  (
    'f1111111-1111-4111-8111-111111111102',
    -33.89,
    151.2,
    'WGS84',
    35
  )
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

-- Structured attributes (boolean + single-select)
insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values
  (
    '66666666-6666-4666-8666-666666666601',
    'f1111111-1111-4111-8111-111111111101',
    '33333333-3333-4333-8333-333333333301',
    null,
    true,
    null
  ),
  (
    '66666666-6666-4666-8666-666666666602',
    'f1111111-1111-4111-8111-111111111101',
    '33333333-3333-4333-8333-333333333302',
    '44444444-4444-4444-8444-444444444401',
    null,
    null
  ),
  (
    '66666666-6666-4666-8666-666666666603',
    'f1111111-1111-4111-8111-111111111102',
    '33333333-3333-4333-8333-333333333301',
    null,
    false,
    null
  ),
  (
    '66666666-6666-4666-8666-666666666604',
    'f1111111-1111-4111-8111-111111111102',
    '33333333-3333-4333-8333-333333333302',
    '44444444-4444-4444-8444-444444444402',
    null,
    null
  )
on conflict (id) do nothing;

-- Hours: baseline + exception + uncertainty + derived claim (distinct families)
insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
)
values
  (
    '77777777-7777-4777-8777-777777777701',
    'f1111111-1111-4111-8111-111111111101',
    3,
    time '11:00',
    time '23:00',
    false,
    0
  ),
  (
    '77777777-7777-4777-8777-777777777702',
    'f1111111-1111-4111-8111-111111111102',
    5,
    time '12:00',
    time '22:00',
    false,
    0
  )
on conflict (id) do nothing;

insert into public.venue_hours_exception (
  id,
  venue_id,
  start_date,
  end_date,
  exception_kind,
  note
)
values
  (
    '88888888-8888-4888-8888-888888888801',
    'f1111111-1111-4111-8111-111111111101',
    date '2026-12-25',
    date '2026-12-25',
    'closed_all_day',
    'Demo public holiday closure'
  )
on conflict (id) do nothing;

insert into public.venue_hours_exception (
  id,
  venue_id,
  start_date,
  end_date,
  exception_kind,
  opens_at,
  closes_at,
  crosses_midnight,
  note
)
values
  (
    '88888888-8888-4888-8888-888888888802',
    'f1111111-1111-4111-8111-111111111102',
    date '2026-06-01',
    date '2026-06-02',
    'modified_hours',
    time '11:00',
    time '23:30',
    false,
    'Demo festival hours'
  )
on conflict (id) do update set
  venue_id = excluded.venue_id,
  start_date = excluded.start_date,
  end_date = excluded.end_date,
  exception_kind = excluded.exception_kind,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  note = excluded.note,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values
  (
    'f1111111-1111-4111-8111-111111111101',
    'resolved_confident',
    now (),
    'Demo: hours verified for seed run'
  ),
  (
    'f1111111-1111-4111-8111-111111111102',
    'partial',
    now (),
    'Demo: partial confidence — exercise uncertainty table'
  )
on conflict (venue_id) do update set
  uncertainty_level = excluded.uncertainty_level,
  as_of = excluded.as_of,
  notes = excluded.notes,
  updated_at = now ();

insert into public.venue_derived_operational_claim (
  venue_id,
  open_now_eligible,
  claim_strength,
  computed_at,
  valid_until
)
values
  (
    'f1111111-1111-4111-8111-111111111101',
    true,
    'medium',
    now (),
    null
  ),
  (
    'f1111111-1111-4111-8111-111111111102',
    false,
    'low',
    now (),
    null
  )
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

commit;
