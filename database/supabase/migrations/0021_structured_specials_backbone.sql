-- PubPlus — Wave 8 / Migration 0021
-- Structured specials / promotions backbone (published truth layer only).
-- Separates structured offer identity + kind from descriptive marketing copy (DL-017).
-- Recurring vs one-off schedule classes are distinguished on the parent; subtype tables follow in 0022.
-- No workflow/staging objects here; no commercial/sponsored overlays.

-- ---------------------------------------------------------------------------
-- Parent: one row per structured special/promotion anchored to canonical venue
-- ---------------------------------------------------------------------------
create table public.venue_published_structured_special (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  structured_kind text not null check (
    structured_kind in (
      'meal_special',
      'drink_special',
      'happy_hour',
      'venue_offer'
    )
  ),
  schedule_class text not null check (schedule_class in ('recurring', 'one_off')),
  -- Short, structured label for cards/slugs/UI keys — not a substitute for timing/offer truth.
  short_label text not null,
  -- Catalog visibility for this published row (does not encode validity or discovery tiers).
  catalog_record_status text not null default 'active' check (
    catalog_record_status in ('active', 'retired')
  ),
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_structured_special is
'Published structured special/offer anchor per canonical venue; distinct from workflow proposals and from marketing copy.';

comment on column public.venue_published_structured_special.structured_kind is
'Structured offer category for discovery logic — not free-text-driven.';

comment on column public.venue_published_structured_special.schedule_class is
'Recurring vs one-off: subtype rows must exist in the matching table from migration 0022.';

comment on column public.venue_published_structured_special.catalog_record_status is
'Whether this published row is still intended for the live catalog; does not imply valid-current or active-now (see 0023).';

create index idx_venue_published_structured_special_venue_id on public.venue_published_structured_special (venue_id);

create index idx_venue_published_structured_special_kind on public.venue_published_structured_special (structured_kind);

-- ---------------------------------------------------------------------------
-- Descriptive marketing copy (display-only; not a discovery driver)
-- ---------------------------------------------------------------------------
create table public.venue_published_structured_special_marketing_copy (
  structured_special_id uuid primary key references public.venue_published_structured_special (id) on delete cascade,
  headline text,
  body text,
  terms_and_conditions text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_published_structured_special_marketing_copy is
'Marketing/descriptive copy adjacent to structured specials; must not replace structured timing/offer truth (DL-017).';
