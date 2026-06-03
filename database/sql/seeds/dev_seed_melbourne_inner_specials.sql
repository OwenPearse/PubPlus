-- Melbourne structured specials (idempotent; Stage 3 filters).
-- Pairs with dev_seed_melbourne_inner_venues.sql (same venue_id block).

begin;

-- special 'Parma and pot night' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-0000000a0001',
  'f1111111-1111-4111-8111-00000000000a',
  'meal_special',
  'recurring',
  'Parma and pot night',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-0000000a0001',
  'Recurring: Wednesday pub classic',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-0000000a0001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[3]::smallint[],
  time '18:00',
  time '21:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-0000000a0001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-0000000a0001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- special 'Parma and pot night' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-0000000b0001',
  'f1111111-1111-4111-8111-00000000000b',
  'meal_special',
  'recurring',
  'Parma and pot night',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-0000000b0001',
  'Recurring: Wednesday pub classic',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-0000000b0001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[3]::smallint[],
  time '18:00',
  time '21:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-0000000b0001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-0000000b0001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- special 'Parma and pot night' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-0000000c0001',
  'f1111111-1111-4111-8111-00000000000c',
  'meal_special',
  'recurring',
  'Parma and pot night',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-0000000c0001',
  'Recurring: Wednesday pub classic',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-0000000c0001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[3]::smallint[],
  time '18:00',
  time '21:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-0000000c0001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-0000000c0001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- special 'Happy hour: house pour' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-0000000d0001',
  'f1111111-1111-4111-8111-00000000000d',
  'happy_hour',
  'recurring',
  'Happy hour: house pour',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-0000000d0001',
  'Thu–Sun happy hour',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-0000000d0001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[4, 5, 6, 0]::smallint[],
  time '17:00',
  time '19:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-0000000d0001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-0000000d0001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- special 'Happy hour: house pour' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-0000000e0001',
  'f1111111-1111-4111-8111-00000000000e',
  'happy_hour',
  'recurring',
  'Happy hour: house pour',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-0000000e0001',
  'Thu–Sun happy hour',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-0000000e0001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[4, 5, 6, 0]::smallint[],
  time '17:00',
  time '19:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-0000000e0001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-0000000e0001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- special 'Happy hour: house pour' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-0000000f0001',
  'f1111111-1111-4111-8111-00000000000f',
  'happy_hour',
  'recurring',
  'Happy hour: house pour',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-0000000f0001',
  'Thu–Sun happy hour',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-0000000f0001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[4, 5, 6, 0]::smallint[],
  time '17:00',
  time '19:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-0000000f0001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-0000000f0001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- special 'Tap jugs and pints' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-000000100001',
  'f1111111-1111-4111-8111-000000000010',
  'drink_special',
  'recurring',
  'Tap jugs and pints',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-000000100001',
  'Weekend jugs and selected pints',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-000000100001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[5, 6, 0]::smallint[],
  time '16:00',
  time '20:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-000000100001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-000000100001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- special 'Tap jugs and pints' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-000000110001',
  'f1111111-1111-4111-8111-000000000011',
  'drink_special',
  'recurring',
  'Tap jugs and pints',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-000000110001',
  'Weekend jugs and selected pints',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-000000110001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[5, 6, 0]::smallint[],
  time '16:00',
  time '20:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-000000110001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-000000110001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- special 'Tap jugs and pints' @ venue f1111111…
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
) values (
  'a3111111-1111-4111-8111-000000120001',
  'f1111111-1111-4111-8111-000000000012',
  'drink_special',
  'recurring',
  'Tap jugs and pints',
  'active'
)
on conflict (id) do update set
  venue_id = excluded.venue_id,
  structured_kind = excluded.structured_kind,
  schedule_class = excluded.schedule_class,
  short_label = excluded.short_label,
  catalog_record_status = excluded.catalog_record_status,
  updated_at = now ();

insert into public.venue_published_structured_special_marketing_copy (
  structured_special_id,
  headline,
  body
)
values (
  'a3111111-1111-4111-8111-000000120001',
  'Weekend jugs and selected pints',
  'Seeded recurring offer for filter + detail validation.'
)
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_recurring_pattern (
  structured_special_id,
  recurrence_kind,
  anchor_timezone,
  recurring_days_of_week,
  window_start_time_local,
  window_end_time_local,
  crosses_local_midnight
)
values (
  'a3111111-1111-4111-8111-000000120001',
  'weekly_local_time_window',
  'Australia/Sydney',
  array[5, 6, 0]::smallint[],
  time '16:00',
  time '20:00',
  false
)
on conflict (structured_special_id) do update set
  recurrence_kind = excluded.recurrence_kind,
  anchor_timezone = excluded.anchor_timezone,
  recurring_days_of_week = excluded.recurring_days_of_week,
  window_start_time_local = excluded.window_start_time_local,
  window_end_time_local = excluded.window_end_time_local,
  crosses_local_midnight = excluded.crosses_local_midnight,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values (
  'a3111111-1111-4111-8111-000000120001',
  null,
  null,
  'unknown',
  'strong',
  false
)
on conflict (structured_special_id) do update set
  offer_valid_from = excluded.offer_valid_from,
  offer_valid_to = excluded.offer_valid_to,
  validity_bounds_kind = excluded.validity_bounds_kind,
  timing_signal_strength = excluded.timing_signal_strength,
  suppress_due_to_weak_or_stale_timing = excluded.suppress_due_to_weak_or_stale_timing,
  updated_at = now ();

insert into public.venue_published_structured_special_discovery_eligibility (
  structured_special_id,
  safe_for_detail_display,
  safe_for_card_badge,
  safe_for_filter_search,
  safe_for_active_now_ranking,
  tier_notes
)
values (
  'a3111111-1111-4111-8111-000000120001',
  true,
  true,
  true,
  true,
  'Seeded: all tiers for Stage 3 Melbourne set.'
)
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

commit;

