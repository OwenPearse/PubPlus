-- PubPlus — MVP Search filter taxonomy (boolean venue features + drink products)
-- Safe to re-run: ON CONFLICT on stable_key / id.
-- Depends on: migrations 0005 (attributes), 0024 (beverage_product).

begin;

-- ---------------------------------------------------------------------------
-- Boolean discovery-driving venue features (stable_key = search filter value)
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
    '33333333-3333-4333-8333-333333333401',
    'beer_garden',
    'Beer garden',
    'boolean',
    'single',
    true,
    'low'
  ),
  (
    '33333333-3333-4333-8333-333333333402',
    'rooftop',
    'Rooftop',
    'boolean',
    'single',
    true,
    'low'
  ),
  (
    '33333333-3333-4333-8333-333333333403',
    'live_music',
    'Live music',
    'boolean',
    'single',
    true,
    'low'
  ),
  (
    '33333333-3333-4333-8333-333333333404',
    'dog_friendly',
    'Dog friendly',
    'boolean',
    'single',
    true,
    'low'
  ),
  (
    '33333333-3333-4333-8333-333333333405',
    'sports_screens',
    'Sports screens',
    'boolean',
    'single',
    true,
    'low'
  ),
  (
    '33333333-3333-4333-8333-333333333406',
    'pool_table',
    'Pool table',
    'boolean',
    'single',
    true,
    'low'
  ),
  (
    '33333333-3333-4333-8333-333333333407',
    'late_night',
    'Late night',
    'boolean',
    'single',
    true,
    'low'
  ),
  (
    '33333333-3333-4333-8333-333333333408',
    'vegan_options',
    'Vegan options',
    'boolean',
    'single',
    true,
    'low'
  )
on conflict (stable_key) do nothing;

-- ---------------------------------------------------------------------------
-- Beverage products for drink_types search filter (product id = filter value)
-- ---------------------------------------------------------------------------
insert into public.beverage_product (id, display_name)
values
  ('b3333333-3333-4333-8333-333333333401', 'Craft beer'),
  ('b3333333-3333-4333-8333-333333333402', 'Lager'),
  ('b3333333-3333-4333-8333-333333333403', 'IPA'),
  ('b3333333-3333-4333-8333-333333333404', 'Pale ale'),
  ('b3333333-3333-4333-8333-333333333405', 'Cocktails'),
  ('b3333333-3333-4333-8333-333333333406', 'Wine'),
  ('b3333333-3333-4333-8333-333333333407', 'Cider')
on conflict (id) do nothing;

commit;
