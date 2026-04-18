-- PubPlus — demo tap list rows (local / dev / demo)
-- Minimal exercise of 0024–0026: one brewery, one style, one product, two tap lines on a demo venue.
-- Depends on: dev_seed_demo_venues.sql (canonical venue IDs).
-- Do not treat seed inserts as proof of production publish hygiene — RLS blocks normal client writes.

begin;

-- ---------------------------------------------------------------------------
-- Reference layer
-- ---------------------------------------------------------------------------
insert into public.beverage_brewery (id, display_name)
values
  ('b3333333-3333-4333-8333-333333333301', 'Yeast & Barrel Brewing')
on conflict (id) do nothing;

insert into public.beverage_style (id, display_name)
values
  ('b3333333-3333-4333-8333-333333333302', 'Australian pale ale')
on conflict (id) do nothing;

insert into public.beverage_product (
  id,
  display_name,
  brewery_id,
  style_id
)
values
  (
    'b3333333-3333-4333-8333-333333333303',
    'Harbour Haze APA',
    'b3333333-3333-4333-8333-333333333301',
    'b3333333-3333-4333-8333-333333333302'
  )
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- Venue tap offerings (same demo brewery venue as product — illustrative only)
-- ---------------------------------------------------------------------------
insert into public.venue_published_tap_offering (
  id,
  venue_id,
  beverage_product_id,
  catalog_record_status,
  is_rotating,
  is_guest_tap,
  is_limited_run,
  unstructured_line_label,
  sort_order
)
values
  (
    'b3333333-3333-4333-8333-333333333311',
    'f1111111-1111-4111-8111-111111111102',
    'b3333333-3333-4333-8333-333333333303',
    'active',
    false,
    true,
    false,
    null,
    1
  ),
  (
    'b3333333-3333-4333-8333-333333333312',
    'f1111111-1111-4111-8111-111111111102',
    null,
    'active',
    true,
    false,
    false,
    'Ask bartender — rotating craft guest',
    2
  )
on conflict (id) do nothing;

-- Line 1: structured product + conservative strong-current tier (demo)
insert into public.venue_published_tap_offering_validity (
  tap_offering_id,
  last_pour_asserted_at,
  freshness_signal_strength,
  availability_truth_state,
  suppress_strong_current_tap_claim
)
values
  (
    'b3333333-3333-4333-8333-333333333311',
    now () - interval '2 hours',
    'strong',
    'current_valid',
    false
  )
on conflict (tap_offering_id) do update set
  last_pour_asserted_at = excluded.last_pour_asserted_at,
  freshness_signal_strength = excluded.freshness_signal_strength,
  availability_truth_state = excluded.availability_truth_state,
  suppress_strong_current_tap_claim = excluded.suppress_strong_current_tap_claim,
  updated_at = now ();

insert into public.venue_published_tap_offering_discovery_eligibility (
  tap_offering_id,
  safe_for_detail_display,
  safe_for_card_or_list_row,
  safe_for_filter_search,
  safe_for_strong_current_tap_claim,
  tier_notes
)
values
  (
    'b3333333-3333-4333-8333-333333333311',
    true,
    true,
    true,
    true,
    'Demo: strong freshness + structured product — eligible for strong current-tap copy.'
  )
on conflict (tap_offering_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_or_list_row = excluded.safe_for_card_or_list_row,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_strong_current_tap_claim = excluded.safe_for_strong_current_tap_claim,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- Line 2: rotating + unstructured label — detail-safe only; withhold strong current-tap claim
insert into public.venue_published_tap_offering_validity (
  tap_offering_id,
  last_pour_asserted_at,
  freshness_signal_strength,
  availability_truth_state,
  suppress_strong_current_tap_claim
)
values
  (
    'b3333333-3333-4333-8333-333333333312',
    null,
    'weak',
    'uncertain',
    true
  )
on conflict (tap_offering_id) do update set
  last_pour_asserted_at = excluded.last_pour_asserted_at,
  freshness_signal_strength = excluded.freshness_signal_strength,
  availability_truth_state = excluded.availability_truth_state,
  suppress_strong_current_tap_claim = excluded.suppress_strong_current_tap_claim,
  updated_at = now ();

insert into public.venue_published_tap_offering_discovery_eligibility (
  tap_offering_id,
  safe_for_detail_display,
  safe_for_card_or_list_row,
  safe_for_filter_search,
  safe_for_strong_current_tap_claim,
  tier_notes
)
values
  (
    'b3333333-3333-4333-8333-333333333312',
    true,
    true,
    false,
    false,
    'Demo: unstructured rotating line — OK for detail context, not for strong “now pouring” discovery.'
  )
on conflict (tap_offering_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_or_list_row = excluded.safe_for_card_or_list_row,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_strong_current_tap_claim = excluded.safe_for_strong_current_tap_claim,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

commit;
