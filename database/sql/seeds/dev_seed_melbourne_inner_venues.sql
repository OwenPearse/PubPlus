-- PubPlus — Melbourne inner-city test venues (Stage 3 discovery / open-now).
-- Idempotent. Source: dataCollection/melbourne_inner_seed_venues.json
--
-- Roles: idx 1-3 late_night, 4-6 exception, 7-9 sparse+partial, 10-12 meal, 13-15 happy, 16-18 drink, else standard.

begin;

insert into public.venue (id) values
  ('f1111111-1111-4111-8111-000000000001'),
  ('f1111111-1111-4111-8111-000000000002'),
  ('f1111111-1111-4111-8111-000000000003'),
  ('f1111111-1111-4111-8111-000000000004'),
  ('f1111111-1111-4111-8111-000000000005'),
  ('f1111111-1111-4111-8111-000000000006'),
  ('f1111111-1111-4111-8111-000000000007'),
  ('f1111111-1111-4111-8111-000000000008'),
  ('f1111111-1111-4111-8111-000000000009'),
  ('f1111111-1111-4111-8111-00000000000a'),
  ('f1111111-1111-4111-8111-00000000000b'),
  ('f1111111-1111-4111-8111-00000000000c'),
  ('f1111111-1111-4111-8111-00000000000d'),
  ('f1111111-1111-4111-8111-00000000000e'),
  ('f1111111-1111-4111-8111-00000000000f'),
  ('f1111111-1111-4111-8111-000000000010'),
  ('f1111111-1111-4111-8111-000000000011'),
  ('f1111111-1111-4111-8111-000000000012'),
  ('f1111111-1111-4111-8111-000000000013'),
  ('f1111111-1111-4111-8111-000000000014'),
  ('f1111111-1111-4111-8111-000000000015'),
  ('f1111111-1111-4111-8111-000000000016'),
  ('f1111111-1111-4111-8111-000000000017'),
  ('f1111111-1111-4111-8111-000000000018'),
  ('f1111111-1111-4111-8111-000000000019'),
  ('f1111111-1111-4111-8111-00000000001a'),
  ('f1111111-1111-4111-8111-00000000001b'),
  ('f1111111-1111-4111-8111-00000000001c')
on conflict (id) do nothing;

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000001',
  'The Penny Black',
  'the-penny-black-brunswick-001',
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
values (
  'f1111111-1111-4111-8111-000000000001',
  'Seeded inner-Melbourne dev venue.',
  'The Penny Black — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000001',
  '22222222-2222-4222-8222-000000000002',
  '420 Sydney Rd',
  '3056',
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
values (
  'f1111111-1111-4111-8111-000000000001',
  -37.768078,
  144.962174,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000010001', 'f1111111-1111-4111-8111-000000000001', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000010002', 'f1111111-1111-4111-8111-000000000001', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000002',
  'Grand View Hotel',
  'grand-view-hotel-brunswick-west-002',
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
values (
  'f1111111-1111-4111-8111-000000000002',
  'Seeded inner-Melbourne dev venue.',
  'Grand View Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000002',
  '22222222-2222-4222-8222-000000000003',
  '47 Pearson St',
  '3055',
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
values (
  'f1111111-1111-4111-8111-000000000002',
  -37.766339,
  144.948859,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000020001', 'f1111111-1111-4111-8111-000000000002', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000020002', 'f1111111-1111-4111-8111-000000000002', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000003',
  'Prince Alfred Rooftop & Bar',
  'prince-alfred-rooftop-bar-carlton-003',
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
values (
  'f1111111-1111-4111-8111-000000000003',
  'Seeded inner-Melbourne dev venue.',
  'Prince Alfred Rooftop & Bar — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000003',
  '22222222-2222-4222-8222-000000000004',
  '191 Grattan St',
  '3053',
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
values (
  'f1111111-1111-4111-8111-000000000003',
  -37.8004228,
  144.9622287,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000030001', 'f1111111-1111-4111-8111-000000000003', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000030002', 'f1111111-1111-4111-8111-000000000003', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000004',
  'Great Northern Hotel',
  'great-northern-hotel-carlton-north-004',
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
values (
  'f1111111-1111-4111-8111-000000000004',
  'Seeded inner-Melbourne dev venue.',
  'Great Northern Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000004',
  '22222222-2222-4222-8222-000000000005',
  '644 Rathdowne St',
  '3054',
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
values (
  'f1111111-1111-4111-8111-000000000004',
  -37.7819954,
  144.9734771,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000040001', 'f1111111-1111-4111-8111-000000000004', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000040002', 'f1111111-1111-4111-8111-000000000004', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000005',
  'The Gasometer Hotel',
  'the-gasometer-hotel-collingwood-005',
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
values (
  'f1111111-1111-4111-8111-000000000005',
  'Seeded inner-Melbourne dev venue.',
  'The Gasometer Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000005',
  '22222222-2222-4222-8222-000000000006',
  '484 Smith St',
  '3066',
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
values (
  'f1111111-1111-4111-8111-000000000005',
  -37.7942407,
  144.9853235,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000050001', 'f1111111-1111-4111-8111-000000000005', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000050002', 'f1111111-1111-4111-8111-000000000005', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000006',
  'The Workers Club',
  'the-workers-club-fitzroy-006',
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
values (
  'f1111111-1111-4111-8111-000000000006',
  'Seeded inner-Melbourne dev venue.',
  'The Workers Club — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000006',
  '22222222-2222-4222-8222-000000000009',
  '51 Brunswick St',
  '3065',
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
values (
  'f1111111-1111-4111-8111-000000000006',
  -37.8055556,
  144.9769444,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000060001', 'f1111111-1111-4111-8111-000000000006', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000060002', 'f1111111-1111-4111-8111-000000000006', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000007',
  'Royal Oak Hotel',
  'royal-oak-hotel-fitzroy-north-007',
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
values (
  'f1111111-1111-4111-8111-000000000007',
  'Seeded inner-Melbourne dev venue.',
  'Royal Oak Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000007',
  '22222222-2222-4222-8222-00000000000a',
  '442 Nicholson St',
  '3068',
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
values (
  'f1111111-1111-4111-8111-000000000007',
  -37.789462,
  144.9767245,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000070001', 'f1111111-1111-4111-8111-000000000007', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000070002', 'f1111111-1111-4111-8111-000000000007', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000008',
  'Retreat Hotel',
  'retreat-hotel-abbotsford-008',
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
values (
  'f1111111-1111-4111-8111-000000000008',
  'Seeded inner-Melbourne dev venue.',
  'Retreat Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000008',
  '22222222-2222-4222-8222-000000000001',
  '226 Nicholson St',
  '3067',
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
values (
  'f1111111-1111-4111-8111-000000000008',
  -37.8010712,
  144.997764,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000080001', 'f1111111-1111-4111-8111-000000000008', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000080002', 'f1111111-1111-4111-8111-000000000008', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000009',
  'The Grand Hotel Richmond',
  'the-grand-hotel-richmond-richmond-009',
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
values (
  'f1111111-1111-4111-8111-000000000009',
  'Seeded inner-Melbourne dev venue.',
  'The Grand Hotel Richmond — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000009',
  '22222222-2222-4222-8222-00000000000f',
  '333 Burnley St',
  '3121',
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
values (
  'f1111111-1111-4111-8111-000000000009',
  -37.8246628,
  145.0075649,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000090001', 'f1111111-1111-4111-8111-000000000009', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000090002', 'f1111111-1111-4111-8111-000000000009', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000000a',
  'Bridie O''Reilly’s',
  'bridie-o-reillys-south-yarra-010',
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
values (
  'f1111111-1111-4111-8111-00000000000a',
  'Seeded inner-Melbourne dev venue.',
  'Bridie O''Reilly’s — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000000a',
  '22222222-2222-4222-8222-000000000011',
  '462 Chapel St',
  '3141',
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
values (
  'f1111111-1111-4111-8111-00000000000a',
  -37.843584,
  144.995101,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000000a0001', 'f1111111-1111-4111-8111-00000000000a', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000000a0002', 'f1111111-1111-4111-8111-00000000000a', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000000b',
  'Glenferrie Hotel',
  'glenferrie-hotel-hawthorn-011',
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
values (
  'f1111111-1111-4111-8111-00000000000b',
  'Seeded inner-Melbourne dev venue.',
  'Glenferrie Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000000b',
  '22222222-2222-4222-8222-00000000000b',
  '324 Burwood Rd',
  '3122',
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
values (
  'f1111111-1111-4111-8111-00000000000b',
  -37.8227474,
  145.0345455,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000000b0001', 'f1111111-1111-4111-8111-00000000000b', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000000b0002', 'f1111111-1111-4111-8111-00000000000b', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000000c',
  'The Flying Duck Hotel',
  'the-flying-duck-hotel-prahran-012',
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
values (
  'f1111111-1111-4111-8111-00000000000c',
  'Seeded inner-Melbourne dev venue.',
  'The Flying Duck Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000000c',
  '22222222-2222-4222-8222-00000000000e',
  '67 Bendigo St',
  '3181',
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
values (
  'f1111111-1111-4111-8111-00000000000c',
  -37.8497643,
  144.9973785,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000000c0001', 'f1111111-1111-4111-8111-00000000000c', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000000c0002', 'f1111111-1111-4111-8111-00000000000c', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000000d',
  'The Wolf Windsor',
  'the-wolf-windsor-windsor-013',
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
values (
  'f1111111-1111-4111-8111-00000000000d',
  'Seeded inner-Melbourne dev venue.',
  'The Wolf Windsor — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000000d',
  '22222222-2222-4222-8222-000000000014',
  '152 Chapel St',
  '3181',
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
values (
  'f1111111-1111-4111-8111-00000000000d',
  -37.8528314,
  144.993357,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000000d0001', 'f1111111-1111-4111-8111-00000000000d', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000000d0002', 'f1111111-1111-4111-8111-00000000000d', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000000e',
  'The Lion & Wombat',
  'the-lion-wombat-st-kilda-014',
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
values (
  'f1111111-1111-4111-8111-00000000000e',
  'Seeded inner-Melbourne dev venue.',
  'The Lion & Wombat — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000000e',
  '22222222-2222-4222-8222-000000000012',
  '107 Grey St',
  '3182',
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
values (
  'f1111111-1111-4111-8111-00000000000e',
  -37.8638509,
  144.9810967,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000000e0001', 'f1111111-1111-4111-8111-00000000000e', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000000e0002', 'f1111111-1111-4111-8111-00000000000e', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000000f',
  'The Crafty Squire',
  'the-crafty-squire-melbourne-015',
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
values (
  'f1111111-1111-4111-8111-00000000000f',
  'Seeded inner-Melbourne dev venue.',
  'The Crafty Squire — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000000f',
  '22222222-2222-4222-8222-00000000000c',
  '127 Russell St',
  '3000',
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
values (
  'f1111111-1111-4111-8111-00000000000f',
  -37.8137597,
  144.9682772,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000000f0001', 'f1111111-1111-4111-8111-00000000000f', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000000f0002', 'f1111111-1111-4111-8111-00000000000f', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000010',
  'McMahon''s Hotel',
  'mcmahon-s-hotel-west-melbourne-016',
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
values (
  'f1111111-1111-4111-8111-000000000010',
  'Seeded inner-Melbourne dev venue.',
  'McMahon''s Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000010',
  '22222222-2222-4222-8222-000000000013',
  '575 Spencer St',
  '3003',
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
values (
  'f1111111-1111-4111-8111-000000000010',
  -37.8073681,
  144.9470219,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000100001', 'f1111111-1111-4111-8111-000000000010', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000100002', 'f1111111-1111-4111-8111-000000000010', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000011',
  'The Palace Hotel (South Melbourne)',
  'the-palace-hotel-south-melbourne-south-melbourne-017',
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
values (
  'f1111111-1111-4111-8111-000000000011',
  'Seeded inner-Melbourne dev venue.',
  'The Palace Hotel (South Melbourne) — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000011',
  '22222222-2222-4222-8222-000000000010',
  '505-507 City Rd',
  '3205',
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
values (
  'f1111111-1111-4111-8111-000000000011',
  -37.8339964,
  144.9500626,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000110001', 'f1111111-1111-4111-8111-000000000011', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000110002', 'f1111111-1111-4111-8111-000000000011', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000012',
  'Prince Alfred Hotel',
  'prince-alfred-hotel-port-melbourne-018',
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
values (
  'f1111111-1111-4111-8111-000000000012',
  'Seeded inner-Melbourne dev venue.',
  'Prince Alfred Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000012',
  '22222222-2222-4222-8222-00000000000d',
  '355 Bay St',
  '3207',
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
values (
  'f1111111-1111-4111-8111-000000000012',
  -37.8353503,
  144.9450198,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000120001', 'f1111111-1111-4111-8111-000000000012', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000120002', 'f1111111-1111-4111-8111-000000000012', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000013',
  'Urban Alley Brewery',
  'urban-alley-brewery-docklands-019',
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
values (
  'f1111111-1111-4111-8111-000000000013',
  'Seeded inner-Melbourne dev venue.',
  'Urban Alley Brewery — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000013',
  '22222222-2222-4222-8222-000000000008',
  '12 Star Circus',
  '3008',
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
values (
  'f1111111-1111-4111-8111-000000000013',
  -37.812277,
  144.936629,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000130001', 'f1111111-1111-4111-8111-000000000013', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000130002', 'f1111111-1111-4111-8111-000000000013', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000014',
  'The Cherry Tree Hotel',
  'the-cherry-tree-hotel-cremorne-020',
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
values (
  'f1111111-1111-4111-8111-000000000014',
  'Seeded inner-Melbourne dev venue.',
  'The Cherry Tree Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000014',
  '22222222-2222-4222-8222-000000000007',
  '53 Balmain St',
  '3121',
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
values (
  'f1111111-1111-4111-8111-000000000014',
  -37.829968,
  144.993249,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000140001', 'f1111111-1111-4111-8111-000000000014', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000140002', 'f1111111-1111-4111-8111-000000000014', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000015',
  'Edinburgh Castle Hotel',
  'edinburgh-castle-hotel-brunswick-021',
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
values (
  'f1111111-1111-4111-8111-000000000015',
  'Seeded inner-Melbourne dev venue.',
  'Edinburgh Castle Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000015',
  '22222222-2222-4222-8222-000000000002',
  '681 Sydney Rd',
  '3056',
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
values (
  'f1111111-1111-4111-8111-000000000015',
  -37.7609136,
  144.9630165,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000150001', 'f1111111-1111-4111-8111-000000000015', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000150002', 'f1111111-1111-4111-8111-000000000015', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000016',
  'Queensberry Hotel',
  'queensberry-hotel-carlton-022',
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
values (
  'f1111111-1111-4111-8111-000000000016',
  'Seeded inner-Melbourne dev venue.',
  'Queensberry Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000016',
  '22222222-2222-4222-8222-000000000004',
  '593 Swanston St',
  '3053',
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
values (
  'f1111111-1111-4111-8111-000000000016',
  -37.8047158,
  144.9630204,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000160001', 'f1111111-1111-4111-8111-000000000016', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000160002', 'f1111111-1111-4111-8111-000000000016', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000017',
  'The Fox Hotel',
  'the-fox-hotel-collingwood-023',
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
values (
  'f1111111-1111-4111-8111-000000000017',
  'Seeded inner-Melbourne dev venue.',
  'The Fox Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000017',
  '22222222-2222-4222-8222-000000000006',
  '351 Wellington St',
  '3066',
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
values (
  'f1111111-1111-4111-8111-000000000017',
  -37.7945098,
  144.9878839,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000170001', 'f1111111-1111-4111-8111-000000000017', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000170002', 'f1111111-1111-4111-8111-000000000017', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000018',
  'Rochester Hotel',
  'rochester-hotel-fitzroy-024',
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
values (
  'f1111111-1111-4111-8111-000000000018',
  'Seeded inner-Melbourne dev venue.',
  'Rochester Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000018',
  '22222222-2222-4222-8222-000000000009',
  '202 Johnston St',
  '3065',
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
values (
  'f1111111-1111-4111-8111-000000000018',
  -37.7988868,
  144.9816649,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000180001', 'f1111111-1111-4111-8111-000000000018', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000180002', 'f1111111-1111-4111-8111-000000000018', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-000000000019',
  'The Empress Hotel',
  'the-empress-hotel-fitzroy-north-025',
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
values (
  'f1111111-1111-4111-8111-000000000019',
  'Seeded inner-Melbourne dev venue.',
  'The Empress Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-000000000019',
  '22222222-2222-4222-8222-00000000000a',
  '714 Nicholson St',
  '3068',
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
values (
  'f1111111-1111-4111-8111-000000000019',
  -37.7828107,
  144.9779182,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-000000190001', 'f1111111-1111-4111-8111-000000000019', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-000000190002', 'f1111111-1111-4111-8111-000000000019', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000001a',
  'Terminus Hotel',
  'terminus-hotel-abbotsford-026',
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
values (
  'f1111111-1111-4111-8111-00000000001a',
  'Seeded inner-Melbourne dev venue.',
  'Terminus Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000001a',
  '22222222-2222-4222-8222-000000000001',
  '605 Victoria St',
  '3067',
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
values (
  'f1111111-1111-4111-8111-00000000001a',
  -37.8110948,
  145.0072168,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000001a0001', 'f1111111-1111-4111-8111-00000000001a', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000001a0002', 'f1111111-1111-4111-8111-00000000001a', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000001b',
  'All Nations Hotel',
  'all-nations-hotel-richmond-027',
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
values (
  'f1111111-1111-4111-8111-00000000001b',
  'Seeded inner-Melbourne dev venue.',
  'All Nations Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000001b',
  '22222222-2222-4222-8222-00000000000f',
  '64 Lennox St',
  '3121',
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
values (
  'f1111111-1111-4111-8111-00000000001b',
  -37.8132761,
  144.995271,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000001b0001', 'f1111111-1111-4111-8111-00000000001b', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000001b0002', 'f1111111-1111-4111-8111-00000000001b', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_published_profile (
  venue_id,
  display_name,
  slug,
  discovery_eligibility_status,
  operational_status
)
values (
  'f1111111-1111-4111-8111-00000000001c',
  'Temperance Hotel',
  'temperance-hotel-south-yarra-028',
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
values (
  'f1111111-1111-4111-8111-00000000001c',
  'Seeded inner-Melbourne dev venue.',
  'Temperance Hotel — frozen Pub_Australia selection; see melbourne_inner_seed_venues.json.'
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
values (
  'f1111111-1111-4111-8111-00000000001c',
  '22222222-2222-4222-8222-000000000011',
  '426 Chapel St',
  '3141',
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
values (
  'f1111111-1111-4111-8111-00000000001c',
  -37.8446159,
  144.9947399,
  'WGS84',
  40
)
on conflict (venue_id) do update set
  latitude = excluded.latitude,
  longitude = excluded.longitude,
  coordinate_system = excluded.coordinate_system,
  precision_meters = excluded.precision_meters,
  updated_at = now ();

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values (
  ('66666666-6666-4666-8666-0000001c0001', 'f1111111-1111-4111-8111-00000000001c', '33333333-3333-4333-8333-333333333301', null, true, null),
  ('66666666-6666-4666-8666-0000001c0002', 'f1111111-1111-4111-8111-00000000001c', '33333333-3333-4333-8333-333333333302', '44444444-4444-4444-8444-444444444401', null, null)
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000010000', 'f1111111-1111-4111-8111-000000000001', 5, time '17:00', time '02:00', true, 0::smallint),
  ('77777777-7777-4777-8777-000000010001', 'f1111111-1111-4111-8111-000000000001', 6, time '12:00', time '01:00', true, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000001',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000001',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000020000', 'f1111111-1111-4111-8111-000000000002', 5, time '17:00', time '02:00', true, 0::smallint),
  ('77777777-7777-4777-8777-000000020001', 'f1111111-1111-4111-8111-000000000002', 6, time '12:00', time '01:00', true, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000002',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000002',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000030000', 'f1111111-1111-4111-8111-000000000003', 5, time '17:00', time '02:00', true, 0::smallint),
  ('77777777-7777-4777-8777-000000030001', 'f1111111-1111-4111-8111-000000000003', 6, time '12:00', time '01:00', true, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000003',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000003',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000040000', 'f1111111-1111-4111-8111-000000000004', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000040001', 'f1111111-1111-4111-8111-000000000004', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000040002', 'f1111111-1111-4111-8111-000000000004', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

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
values (
  '88888888-8888-4888-8888-000000040000',
  'f1111111-1111-4111-8111-000000000004',
  date '2020-01-01',
  date '2030-12-31',
  'modified_hours',
  time '10:00',
  time '22:00',
  false,
  'Seeded: long-ranged modified hours (exception overrides regular).'
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
values (
  'f1111111-1111-4111-8111-000000000004',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000004',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000050000', 'f1111111-1111-4111-8111-000000000005', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000050001', 'f1111111-1111-4111-8111-000000000005', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000050002', 'f1111111-1111-4111-8111-000000000005', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

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
values (
  '88888888-8888-4888-8888-000000050000',
  'f1111111-1111-4111-8111-000000000005',
  date '2020-01-01',
  date '2030-12-31',
  'modified_hours',
  time '10:00',
  time '22:00',
  false,
  'Seeded: long-ranged modified hours (exception overrides regular).'
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
values (
  'f1111111-1111-4111-8111-000000000005',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000005',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000060000', 'f1111111-1111-4111-8111-000000000006', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000060001', 'f1111111-1111-4111-8111-000000000006', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000060002', 'f1111111-1111-4111-8111-000000000006', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

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
values (
  '88888888-8888-4888-8888-000000060000',
  'f1111111-1111-4111-8111-000000000006',
  date '2020-01-01',
  date '2030-12-31',
  'modified_hours',
  time '10:00',
  time '22:00',
  false,
  'Seeded: long-ranged modified hours (exception overrides regular).'
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
values (
  'f1111111-1111-4111-8111-000000000006',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000006',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000070000', 'f1111111-1111-4111-8111-000000000007', 3, time '12:00', time '20:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000007',
  'partial',
  now(),
  'Seeded partial hours knowledge (sparse regular rows)'
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
values (
  'f1111111-1111-4111-8111-000000000007',
  true,
  'low',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000080000', 'f1111111-1111-4111-8111-000000000008', 3, time '12:00', time '20:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000008',
  'partial',
  now(),
  'Seeded partial hours knowledge (sparse regular rows)'
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
values (
  'f1111111-1111-4111-8111-000000000008',
  true,
  'low',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000090000', 'f1111111-1111-4111-8111-000000000009', 3, time '12:00', time '20:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000009',
  'partial',
  now(),
  'Seeded partial hours knowledge (sparse regular rows)'
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
values (
  'f1111111-1111-4111-8111-000000000009',
  true,
  'low',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000000a0000', 'f1111111-1111-4111-8111-00000000000a', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000a0001', 'f1111111-1111-4111-8111-00000000000a', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000a0002', 'f1111111-1111-4111-8111-00000000000a', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000000a',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000000a',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000000b0000', 'f1111111-1111-4111-8111-00000000000b', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000b0001', 'f1111111-1111-4111-8111-00000000000b', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000b0002', 'f1111111-1111-4111-8111-00000000000b', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000000b',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000000b',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000000c0000', 'f1111111-1111-4111-8111-00000000000c', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000c0001', 'f1111111-1111-4111-8111-00000000000c', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000c0002', 'f1111111-1111-4111-8111-00000000000c', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000000c',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000000c',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000000d0000', 'f1111111-1111-4111-8111-00000000000d', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000d0001', 'f1111111-1111-4111-8111-00000000000d', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000d0002', 'f1111111-1111-4111-8111-00000000000d', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000000d',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000000d',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000000e0000', 'f1111111-1111-4111-8111-00000000000e', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000e0001', 'f1111111-1111-4111-8111-00000000000e', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000e0002', 'f1111111-1111-4111-8111-00000000000e', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000000e',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000000e',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000000f0000', 'f1111111-1111-4111-8111-00000000000f', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000f0001', 'f1111111-1111-4111-8111-00000000000f', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000000f0002', 'f1111111-1111-4111-8111-00000000000f', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000000f',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000000f',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000100000', 'f1111111-1111-4111-8111-000000000010', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000100001', 'f1111111-1111-4111-8111-000000000010', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000100002', 'f1111111-1111-4111-8111-000000000010', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000010',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000010',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000110000', 'f1111111-1111-4111-8111-000000000011', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000110001', 'f1111111-1111-4111-8111-000000000011', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000110002', 'f1111111-1111-4111-8111-000000000011', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000011',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000011',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000120000', 'f1111111-1111-4111-8111-000000000012', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000120001', 'f1111111-1111-4111-8111-000000000012', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000120002', 'f1111111-1111-4111-8111-000000000012', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000012',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000012',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000130000', 'f1111111-1111-4111-8111-000000000013', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000130001', 'f1111111-1111-4111-8111-000000000013', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000130002', 'f1111111-1111-4111-8111-000000000013', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000013',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000013',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000140000', 'f1111111-1111-4111-8111-000000000014', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000140001', 'f1111111-1111-4111-8111-000000000014', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000140002', 'f1111111-1111-4111-8111-000000000014', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000014',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000014',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000150000', 'f1111111-1111-4111-8111-000000000015', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000150001', 'f1111111-1111-4111-8111-000000000015', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000150002', 'f1111111-1111-4111-8111-000000000015', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000015',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000015',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000160000', 'f1111111-1111-4111-8111-000000000016', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000160001', 'f1111111-1111-4111-8111-000000000016', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000160002', 'f1111111-1111-4111-8111-000000000016', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000016',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000016',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000170000', 'f1111111-1111-4111-8111-000000000017', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000170001', 'f1111111-1111-4111-8111-000000000017', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000170002', 'f1111111-1111-4111-8111-000000000017', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000017',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000017',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000180000', 'f1111111-1111-4111-8111-000000000018', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000180001', 'f1111111-1111-4111-8111-000000000018', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000180002', 'f1111111-1111-4111-8111-000000000018', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000018',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000018',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-000000190000', 'f1111111-1111-4111-8111-000000000019', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000190001', 'f1111111-1111-4111-8111-000000000019', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-000000190002', 'f1111111-1111-4111-8111-000000000019', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-000000000019',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-000000000019',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000001a0000', 'f1111111-1111-4111-8111-00000000001a', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000001a0001', 'f1111111-1111-4111-8111-00000000001a', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000001a0002', 'f1111111-1111-4111-8111-00000000001a', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000001a',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000001a',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000001b0000', 'f1111111-1111-4111-8111-00000000001b', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000001b0001', 'f1111111-1111-4111-8111-00000000001b', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000001b0002', 'f1111111-1111-4111-8111-00000000001b', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000001b',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000001b',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

insert into public.venue_hours_regular (
  id,
  venue_id,
  day_of_week,
  opens_at,
  closes_at,
  crosses_midnight,
  sort_order
) values
  ('77777777-7777-4777-8777-0000001c0000', 'f1111111-1111-4111-8111-00000000001c', 1, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000001c0001', 'f1111111-1111-4111-8111-00000000001c', 3, time '11:00', time '23:00', false, 0::smallint),
  ('77777777-7777-4777-8777-0000001c0002', 'f1111111-1111-4111-8111-00000000001c', 5, time '11:00', time '23:00', false, 0::smallint)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  day_of_week = excluded.day_of_week,
  opens_at = excluded.opens_at,
  closes_at = excluded.closes_at,
  crosses_midnight = excluded.crosses_midnight,
  sort_order = excluded.sort_order,
  updated_at = now ();

insert into public.venue_hours_uncertainty (
  venue_id,
  uncertainty_level,
  as_of,
  notes
)
values (
  'f1111111-1111-4111-8111-00000000001c',
  'resolved_confident',
  now(),
  'Seeded confident hours snapshot'
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
values (
  'f1111111-1111-4111-8111-00000000001c',
  true,
  'medium',
  now(),
  null
)
on conflict (venue_id) do update set
  open_now_eligible = excluded.open_now_eligible,
  claim_strength = excluded.claim_strength,
  computed_at = excluded.computed_at,
  valid_until = excluded.valid_until;

commit;

