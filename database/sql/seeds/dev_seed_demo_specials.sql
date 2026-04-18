-- PubPlus — demo structured specials (local / dev / demo)
-- Depends on: dev_seed_demo_venues.sql (canonical venue IDs + published profile rows).
-- Inserts published-truth specials directly for local/dev only — production writes go through publish orchestration.
-- Included from database/supabase/seed.sql after venues (requires migrations through 0023). See WAVE_12_FINAL_READINESS_REVIEW.md for full seed order.

begin;

-- ---------------------------------------------------------------------------
-- 1) Recurring happy hour (venue 101)
-- ---------------------------------------------------------------------------
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
)
values
  (
    'a2111111-1111-4111-8111-111111111101',
    'f1111111-1111-4111-8111-111111111101',
    'happy_hour',
    'recurring',
    'Weeknight Happy Hour',
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
values
  (
    'a2111111-1111-4111-8111-111111111101',
    'Happy hour on selected nights',
    'Demo marketing copy — structured recurrence + eligibility tables carry discovery-safe timing.'
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
values
  (
    'a2111111-1111-4111-8111-111111111101',
    'weekly_local_time_window',
    'Australia/Sydney',
    array [3, 4, 5]::smallint[],
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
values
  (
    'a2111111-1111-4111-8111-111111111101',
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
values
  (
    'a2111111-1111-4111-8111-111111111101',
    true,
    true,
    true,
    true,
    'Demo: all tiers enabled for the recurring special.'
  )
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- ---------------------------------------------------------------------------
-- 2) One-off lunch promotion (venue 102)
-- ---------------------------------------------------------------------------
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
)
values
  (
    'a2111111-1111-4111-8111-111111111102',
    'f1111111-1111-4111-8111-111111111102',
    'meal_special',
    'one_off',
    'Long Lunch Tuesday',
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
values
  (
    'a2111111-1111-4111-8111-111111111102',
    'Chef set menu — one day only',
    'Demo descriptive copy for a date-bounded promotion.'
  )
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_one_off (
  structured_special_id,
  one_off_start_at,
  one_off_end_at
)
values
  (
    'a2111111-1111-4111-8111-111111111102',
    timestamptz '2026-04-21 11:30:00+10',
    timestamptz '2026-04-21 15:30:00+10'
  )
on conflict (structured_special_id) do update set
  one_off_start_at = excluded.one_off_start_at,
  one_off_end_at = excluded.one_off_end_at,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values
  (
    'a2111111-1111-4111-8111-111111111102',
    timestamptz '2026-04-21 11:30:00+10',
    timestamptz '2026-04-21 15:30:00+10',
    'fully_bounded',
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
values
  (
    'a2111111-1111-4111-8111-111111111102',
    true,
    true,
    true,
    true,
    'Demo: bounded one-off with strong timing — tiers all on while valid.'
  )
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

-- ---------------------------------------------------------------------------
-- 3) Detail/search safe but not active-now/ranking safe (venue 101)
-- ---------------------------------------------------------------------------
insert into public.venue_published_structured_special (
  id,
  venue_id,
  structured_kind,
  schedule_class,
  short_label,
  catalog_record_status
)
values
  (
    'a2111111-1111-4111-8111-111111111103',
    'f1111111-1111-4111-8111-111111111101',
    'venue_offer',
    'one_off',
    'Anniversary Dinner Package',
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
values
  (
    'a2111111-1111-4111-8111-111111111103',
    'Celebrate on-site',
    'Demo: structured dates are strong, but product policy keeps this off ranking/active-now surfaces.'
  )
on conflict (structured_special_id) do update set
  headline = excluded.headline,
  body = excluded.body,
  updated_at = now ();

insert into public.venue_published_special_one_off (
  structured_special_id,
  one_off_start_at,
  one_off_end_at
)
values
  (
    'a2111111-1111-4111-8111-111111111103',
    timestamptz '2026-05-01 17:00:00+10',
    timestamptz '2026-05-01 23:00:00+10'
  )
on conflict (structured_special_id) do update set
  one_off_start_at = excluded.one_off_start_at,
  one_off_end_at = excluded.one_off_end_at,
  updated_at = now ();

insert into public.venue_published_structured_special_validity (
  structured_special_id,
  offer_valid_from,
  offer_valid_to,
  validity_bounds_kind,
  timing_signal_strength,
  suppress_due_to_weak_or_stale_timing
)
values
  (
    'a2111111-1111-4111-8111-111111111103',
    timestamptz '2026-05-01 17:00:00+10',
    timestamptz '2026-05-01 23:00:00+10',
    'fully_bounded',
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
values
  (
    'a2111111-1111-4111-8111-111111111103',
    true,
    true,
    true,
    false,
    'Demo: valid structured window but active-now/ranking tier withheld intentionally.'
  )
on conflict (structured_special_id) do update set
  safe_for_detail_display = excluded.safe_for_detail_display,
  safe_for_card_badge = excluded.safe_for_card_badge,
  safe_for_filter_search = excluded.safe_for_filter_search,
  safe_for_active_now_ranking = excluded.safe_for_active_now_ranking,
  tier_notes = excluded.tier_notes,
  updated_at = now ();

commit;
