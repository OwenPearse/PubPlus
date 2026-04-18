-- PubPlus — Tranche 1 / Migration 0006
-- Regular hours, date-bounded exceptions, explicit uncertainty, derived operational claims.
-- Unknown ≠ closed; weak/stale ≠ open-now (enforce in app + derived claim strength).

-- ---------------------------------------------------------------------------
-- Baseline weekly hours (multiple rows per day allowed for split shifts)
-- ---------------------------------------------------------------------------
create table public.venue_hours_regular (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  day_of_week smallint not null check (
    day_of_week >= 0
    and day_of_week <= 6
  ),
  -- 0 = Sunday … 6 = Saturday (document in app; adjust if ISO Monday-first is preferred)
  opens_at time not null,
  closes_at time not null,
  crosses_midnight boolean not null default false,
  sort_order smallint not null default 0,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_hours_regular is
'Baseline weekly pattern; exceptions in venue_hours_exception supersede for affected periods.';

create index idx_venue_hours_regular_venue on public.venue_hours_regular (venue_id);
create index idx_venue_hours_regular_venue_dow on public.venue_hours_regular (venue_id, day_of_week);

-- ---------------------------------------------------------------------------
-- Exceptions (date-bounded overrides)
-- ---------------------------------------------------------------------------
create table public.venue_hours_exception (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  start_date date not null,
  end_date date not null,
  exception_kind text not null check (
    exception_kind in (
      'closed_all_day',
      'modified_hours',
      'open_by_appointment_or_special'
    )
  ),
  opens_at time,
  closes_at time,
  crosses_midnight boolean not null default false,
  note text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  check (end_date >= start_date),
  check (
    exception_kind <> 'modified_hours'
    or (
      opens_at is not null
      and closes_at is not null
    )
  ),
  check (
    exception_kind <> 'closed_all_day'
    or (
      opens_at is null
      and closes_at is null
    )
  )
);

comment on table public.venue_hours_exception is
'Overrides baseline for [start_date, end_date]; must not be the only place uncertainty is stored.';

create index idx_venue_hours_exception_venue on public.venue_hours_exception (venue_id);
create index idx_venue_hours_exception_range on public.venue_hours_exception (venue_id, start_date, end_date);

-- ---------------------------------------------------------------------------
-- Explicit uncertainty / strength (separate from derived open-now)
-- ---------------------------------------------------------------------------
create table public.venue_hours_uncertainty (
  venue_id uuid primary key references public.venue (id) on delete cascade,
  uncertainty_level text not null default 'unknown' check (
    uncertainty_level in (
      'unknown',
      'partial',
      'weak_stale',
      'disputed',
      'resolved_confident'
    )
  ),
  as_of timestamptz,
  notes text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_hours_uncertainty is
'Explicit strength: unknown is not closed; weak/stale must not drive open-now alone.';

-- ---------------------------------------------------------------------------
-- Derived present-tense operational claims (materialized; recompute in app/cron)
-- ---------------------------------------------------------------------------
create table public.venue_derived_operational_claim (
  venue_id uuid primary key references public.venue (id) on delete cascade,
  open_now_eligible boolean not null default false,
  claim_strength text not null default 'none' check (
    claim_strength in (
      'none',
      'low',
      'medium',
      'high'
    )
  ),
  computed_at timestamptz not null default now (),
  valid_until timestamptz
);

comment on table public.venue_derived_operational_claim is
'Derived claims (e.g. open-now eligibility); separate from baseline/exception/uncertainty tables.';
