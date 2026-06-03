-- PubPlus — Wave 8 / Migration 0023
-- Validity / timing strength vs discovery eligibility tiers — intentionally not one boolean (DL-019).
-- Published catalog presence lives on the parent; valid-current and active-now-safe are expressed here.
-- Weak/vague timing can be suppressed without inventing optimistic windows.
-- RLS: published specials are discovery-readable like other public truth (parity with 0017).

-- ---------------------------------------------------------------------------
-- Validity / timing: conservative signals for “valid now” vs weak/stale suppression
-- ---------------------------------------------------------------------------
create table public.venue_published_structured_special_validity (
  structured_special_id uuid primary key references public.venue_published_structured_special (id) on delete cascade,
  -- Optional absolute bounds for “this offer is meant to be active between…” (may be unknown).
  offer_valid_from timestamptz,
  offer_valid_to timestamptz,
  validity_bounds_kind text not null default 'unknown' check (
    validity_bounds_kind in (
      'fully_bounded',
      'open_started',
      'open_ended',
      'unknown'
    )
  ),
  -- Strength of the timing inputs backing this row — weak/unknown must not silently power active-now.
  timing_signal_strength text not null default 'unknown' check (
    timing_signal_strength in ('strong', 'weak', 'unknown')
  ),
  -- When true, discovery surfaces should withhold strong timing-dependent claims (DL-019 guardrail).
  suppress_due_to_weak_or_stale_timing boolean not null default false,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint validity_offer_bounds_order check (
    offer_valid_from is null
    or offer_valid_to is null
    or offer_valid_to >= offer_valid_from
  )
);

comment on table public.venue_published_structured_special_validity is
'Validity/timing layer for structured specials: distinct from catalog presence and from per-tier discovery eligibility.';

comment on column public.venue_published_structured_special_validity.suppress_due_to_weak_or_stale_timing is
'Explicit suppression for weak/vague/stale timing — prefer withholding over guessing (DL-019).';

-- ---------------------------------------------------------------------------
-- Discovery eligibility tiers: detail vs card/badge vs filter/search vs active-now/ranking
-- ---------------------------------------------------------------------------
create table public.venue_published_structured_special_discovery_eligibility (
  structured_special_id uuid primary key references public.venue_published_structured_special (id) on delete cascade,
  safe_for_detail_display boolean not null default false,
  safe_for_card_badge boolean not null default false,
  safe_for_filter_search boolean not null default false,
  safe_for_active_now_ranking boolean not null default false,
  tier_notes text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_structured_special_discovery_eligibility is
'Independent discovery tiers; published/catalog presence does not imply any tier — especially active-now/ranking (DL-019).';

comment on column public.venue_published_structured_special_discovery_eligibility.safe_for_active_now_ranking is
'Strongest tier for present-tense/ranking surfaces; must remain separable from filter/search and from mere publication.';

-- No CHECK forcing implications between tiers — conservative derivation stays in application logic.

-- ---------------------------------------------------------------------------
-- RLS: SELECT-only for anon + authenticated (published discovery reads)
-- ---------------------------------------------------------------------------
alter table public.venue_published_structured_special enable row level security;

create policy venue_published_structured_special_select_public on public.venue_published_structured_special for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_structured_special_marketing_copy enable row level security;

create policy venue_published_structured_special_marketing_copy_select_public on public.venue_published_structured_special_marketing_copy for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_special_recurring_pattern enable row level security;

create policy venue_published_special_recurring_pattern_select_public on public.venue_published_special_recurring_pattern for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_special_one_off enable row level security;

create policy venue_published_special_one_off_select_public on public.venue_published_special_one_off for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_structured_special_validity enable row level security;

create policy venue_published_structured_special_validity_select_public on public.venue_published_structured_special_validity for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_structured_special_discovery_eligibility enable row level security;

create policy venue_published_structured_special_discovery_eligibility_select_public on public.venue_published_structured_special_discovery_eligibility for
select
  to anon,
  authenticated using (true);
