-- PubPlus — MVP Search feature filter efficacy (published boolean attributes on demo venues)
-- Safe to re-run: fixed IDs + ON CONFLICT DO UPDATE.
-- Depends on: dev_seed_mvp_filter_taxonomy.sql, dev_seed_demo_venues.sql,
--             dev_seed_melbourne_inner_venues.sql (venue rows must exist).
--
-- Assigns Stage 1 stable_key values so GET /api/v1/search/venues?venue_features=<key>
-- returns meaningful results in local/dev QA.

begin;

-- Attribute definition IDs (dev_seed_mvp_filter_taxonomy.sql)
-- beer_garden     33333333-3333-4333-8333-333333333401
-- rooftop         33333333-3333-4333-8333-333333333402
-- live_music      33333333-3333-4333-8333-333333333403
-- dog_friendly    33333333-3333-4333-8333-333333333404
-- sports_screens  33333333-3333-4333-8333-333333333405
-- pool_table      33333333-3333-4333-8333-333333333406
-- late_night      33333333-3333-4333-8333-333333333407
-- vegan_options   33333333-3333-4333-8333-333333333408

insert into public.venue_published_attribute_value (
  id,
  venue_id,
  attribute_definition_id,
  allowed_value_id,
  value_boolean,
  value_numeric
)
values
  -- beer_garden (2+ Melbourne + 1 Sydney)
  (
    '66666666-6666-4666-8666-000000070101',
    'f1111111-1111-4111-8111-000000000001',
    '33333333-3333-4333-8333-333333333401',
    null,
    true,
    null
  ),
  (
    '66666666-6666-4666-8666-000000070102',
    'f1111111-1111-4111-8111-000000000002',
    '33333333-3333-4333-8333-333333333401',
    null,
    true,
    null
  ),
  (
    '66666666-6666-4666-8666-000000070103',
    'f1111111-1111-4111-8111-111111111101',
    '33333333-3333-4333-8333-333333333401',
    null,
    true,
    null
  ),
  -- sports_screens (2+)
  (
    '66666666-6666-4666-8666-000000070201',
    'f1111111-1111-4111-8111-000000000001',
    '33333333-3333-4333-8333-333333333405',
    null,
    true,
    null
  ),
  (
    '66666666-6666-4666-8666-000000070202',
    'f1111111-1111-4111-8111-000000000016',
    '33333333-3333-4333-8333-333333333405',
    null,
    true,
    null
  ),
  (
    '66666666-6666-4666-8666-000000070203',
    'f1111111-1111-4111-8111-111111111102',
    '33333333-3333-4333-8333-333333333405',
    null,
    true,
    null
  ),
  -- pool_table (1)
  (
    '66666666-6666-4666-8666-000000070301',
    'f1111111-1111-4111-8111-000000000003',
    '33333333-3333-4333-8333-333333333406',
    null,
    true,
    null
  ),
  -- live_music (1)
  (
    '66666666-6666-4666-8666-000000070401',
    'f1111111-1111-4111-8111-000000000004',
    '33333333-3333-4333-8333-333333333403',
    null,
    true,
    null
  ),
  -- dog_friendly (1)
  (
    '66666666-6666-4666-8666-000000070501',
    'f1111111-1111-4111-8111-000000000005',
    '33333333-3333-4333-8333-333333333404',
    null,
    true,
    null
  ),
  -- rooftop (1)
  (
    '66666666-6666-4666-8666-000000070601',
    'f1111111-1111-4111-8111-000000000006',
    '33333333-3333-4333-8333-333333333402',
    null,
    true,
    null
  ),
  -- late_night (1)
  (
    '66666666-6666-4666-8666-000000070701',
    'f1111111-1111-4111-8111-000000000007',
    '33333333-3333-4333-8333-333333333407',
    null,
    true,
    null
  ),
  -- vegan_options (1)
  (
    '66666666-6666-4666-8666-000000070801',
    'f1111111-1111-4111-8111-000000000008',
    '33333333-3333-4333-8333-333333333408',
    null,
    true,
    null
  )
on conflict (id) do update set
  venue_id = excluded.venue_id,
  attribute_definition_id = excluded.attribute_definition_id,
  allowed_value_id = excluded.allowed_value_id,
  value_boolean = excluded.value_boolean,
  value_numeric = excluded.value_numeric,
  updated_at = now ();

commit;
