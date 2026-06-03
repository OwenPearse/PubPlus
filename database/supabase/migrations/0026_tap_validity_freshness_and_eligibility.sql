-- PubPlus — Wave 9 / Migration 0026
-- Freshness / assertion strength vs discovery tiers — intentionally not one boolean (DL-019, DL-028 analog for taps).
-- Row existence and catalog_record_status do not imply strong current pour claims — tiers are explicit.
-- RLS: published tap + beverage reference reads match migration 0023 posture (SELECT for anon + authenticated).

-- ---------------------------------------------------------------------------
-- Validity / freshness: conservative signals for “asserted current” vs weak/stale withholding
-- ---------------------------------------------------------------------------
create table public.venue_published_tap_offering_validity (
  tap_offering_id uuid primary key references public.venue_published_tap_offering (id) on delete cascade,
  -- Optional timestamp when an owner/system last asserted the line reflects what is pouring.
  last_pour_asserted_at timestamptz,
  -- Strength of the inputs backing freshness (weak/unknown must not silently power strong current-tap claims).
  freshness_signal_strength text not null default 'unknown' check (
    freshness_signal_strength in ('strong', 'weak', 'unknown')
  ),
  -- Coarse interpretation boundary for stale / uncertain / suppressed handling.
  availability_truth_state text not null default 'unknown' check (
    availability_truth_state in (
      'current_valid',
      'uncertain',
      'stale_suspected',
      'suppressed'
    )
  ),
  -- When true, surfaces must withhold strong present-tense pour claims even if a parent row exists.
  suppress_strong_current_tap_claim boolean not null default false,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_tap_offering_validity is
'Freshness and assertion strength for tap lines: distinct from catalog presence and from per-tier discovery eligibility.';

comment on column public.venue_published_tap_offering_validity.freshness_signal_strength is
'How trustworthy the freshness inputs are; weak/unknown cannot silently drive “on tap now” surfaces.';

comment on column public.venue_published_tap_offering_validity.availability_truth_state is
'Conservative bucket for current vs uncertain vs stale vs suppressed — not a single active bit.';

comment on column public.venue_published_tap_offering_validity.suppress_strong_current_tap_claim is
'Explicit guardrail: prefer withholding strong current-tap language over guessing (DL-028 analog).';

-- ---------------------------------------------------------------------------
-- Discovery eligibility tiers: detail vs list vs search vs strong current-tap claim
-- ---------------------------------------------------------------------------
create table public.venue_published_tap_offering_discovery_eligibility (
  tap_offering_id uuid primary key references public.venue_published_tap_offering (id) on delete cascade,
  safe_for_detail_display boolean not null default false,
  safe_for_card_or_list_row boolean not null default false,
  safe_for_filter_search boolean not null default false,
  safe_for_strong_current_tap_claim boolean not null default false,
  tier_notes text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_tap_offering_discovery_eligibility is
'Independent discovery tiers; catalog presence does not imply any tier — especially strong current-tap claims.';

comment on column public.venue_published_tap_offering_discovery_eligibility.safe_for_strong_current_tap_claim is
'Strongest tier for present-tense “now pouring” / ranking surfaces; separable from filter/search and from mere publication.';

-- No CHECK forcing implications between tiers — conservative derivation stays in application logic.

-- ---------------------------------------------------------------------------
-- RLS: SELECT-only for anon + authenticated (published discovery reads)
-- ---------------------------------------------------------------------------
alter table public.beverage_brewery enable row level security;

create policy beverage_brewery_select_public on public.beverage_brewery for
select
  to anon,
  authenticated using (true);

alter table public.beverage_style enable row level security;

create policy beverage_style_select_public on public.beverage_style for
select
  to anon,
  authenticated using (true);

alter table public.beverage_product enable row level security;

create policy beverage_product_select_public on public.beverage_product for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_tap_offering enable row level security;

create policy venue_published_tap_offering_select_public on public.venue_published_tap_offering for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_tap_offering_validity enable row level security;

create policy venue_published_tap_offering_validity_select_public on public.venue_published_tap_offering_validity for
select
  to anon,
  authenticated using (true);

alter table public.venue_published_tap_offering_discovery_eligibility enable row level security;

create policy venue_published_tap_offering_discovery_eligibility_select_public on public.venue_published_tap_offering_discovery_eligibility for
select
  to anon,
  authenticated using (true);
