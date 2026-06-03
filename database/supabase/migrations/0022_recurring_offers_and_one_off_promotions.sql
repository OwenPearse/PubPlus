-- PubPlus — Wave 8 / Migration 0022
-- Recurring offer patterns vs one-off promotions — separate subtype tables (DL-018).
-- Parents carry schedule_class; exactly one subtype row is expected per parent (enforced outside DDL v1).

-- ---------------------------------------------------------------------------
-- Recurring: pattern-based local-time window (v1 — weekly DOW + local window)
-- ---------------------------------------------------------------------------
create table public.venue_published_special_recurring_pattern (
  structured_special_id uuid primary key references public.venue_published_structured_special (id) on delete cascade,
  recurrence_kind text not null default 'weekly_local_time_window' check (
    recurrence_kind in ('weekly_local_time_window')
  ),
  -- IANA timezone name for interpreting local window fields (e.g. Australia/Sydney).
  anchor_timezone text not null,
  -- 0 = Sunday .. 6 = Saturday (documented; align app validation with this convention).
  recurring_days_of_week smallint[] not null,
  window_start_time_local time not null,
  window_end_time_local time not null,
  -- When true, window spans local midnight (e.g. 22:00–02:00).
  crosses_local_midnight boolean not null default false,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint recurring_pattern_window_order check (
    crosses_local_midnight
    or window_end_time_local > window_start_time_local
  ),
  constraint recurring_pattern_dow_non_empty check (
    coalesce(
      array_length(recurring_days_of_week, 1),
      0
    ) >= 1
  )
);

comment on table public.venue_published_special_recurring_pattern is
'Recurring/pattern specials: distinct lifecycle and validation from one-off promotions (DL-018).';

comment on column public.venue_published_special_recurring_pattern.recurring_days_of_week is
'Array of weekday integers 0–6 with 0=Sunday; validate membership in application or a later CHECK.';

-- ---------------------------------------------------------------------------
-- One-off: absolute time-bounded promotion window
-- ---------------------------------------------------------------------------
create table public.venue_published_special_one_off (
  structured_special_id uuid primary key references public.venue_published_structured_special (id) on delete cascade,
  one_off_start_at timestamptz not null,
  one_off_end_at timestamptz not null,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint one_off_end_after_start check (one_off_end_at > one_off_start_at)
);

comment on table public.venue_published_special_one_off is
'Date/time-bounded one-off promotions; not merged into recurring pattern rows (DL-018).';
