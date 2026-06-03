-- PubPlus — Wave 9 / Migration 0025
-- Venue-scoped published tap offering rows: canonical venue anchor, separate from beverage product identity (DL-029).
-- Offering traits (guest / rotating / limited) live here — they are not product identity (non_negotiable rules 20–21).
-- unstructured_line_label is display-only; it must not substitute for structured discovery drivers (DL-005, DL-029).
-- Existence of a row + catalog_record_status do not assert strong “currently on tap” truth — see 0026.

-- ---------------------------------------------------------------------------
-- One row per tap offering line / slot at a venue (published catalog object)
-- ---------------------------------------------------------------------------
create table public.venue_published_tap_offering (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  -- Structured product link when known; nullable when the line is intentionally unstructured or TBD.
  beverage_product_id uuid references public.beverage_product (id) on delete set null,
  -- Catalog presence for this published row (does not encode validity, freshness, or discovery tiers — 0026).
  catalog_record_status text not null default 'active' check (
    catalog_record_status in ('active', 'retired')
  ),
  -- Offering traits: venue-scoped semantics, not proof of a specific pour batch (rules 20–21).
  is_rotating boolean not null default false,
  is_guest_tap boolean not null default false,
  is_limited_run boolean not null default false,
  -- Owner chalkboard / POS line text — detail context only; not structured product identity.
  unstructured_line_label text,
  sort_order int,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_tap_offering is
'Venue-specific tap offering state; distinct from beverage_product reference rows (DL-029).';

comment on column public.venue_published_tap_offering.beverage_product_id is
'Optional link to structured product identity; absence does not mean “no beer” — pairing is explicit.';

comment on column public.venue_published_tap_offering.catalog_record_status is
'Whether this tap line remains in the owner/catalog set; does not imply current pour, freshness, or discovery eligibility.';

comment on column public.venue_published_tap_offering.is_rotating is
'Trait: line is treated as rotating; does not assert which SKU is on tap now.';

comment on column public.venue_published_tap_offering.is_guest_tap is
'Trait: guest/visiting line — not brewery identity.';

comment on column public.venue_published_tap_offering.is_limited_run is
'Trait: limited/small-run positioning — not inventory proof.';

comment on column public.venue_published_tap_offering.unstructured_line_label is
'Raw display text; must not be promoted to strong discovery truth without structured backing (DL-005).';

create index idx_venue_published_tap_offering_venue_id on public.venue_published_tap_offering (venue_id);

create index idx_venue_published_tap_offering_product_id on public.venue_published_tap_offering (beverage_product_id);
