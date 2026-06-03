-- PubPlus — Wave 9 / Migration 0024
-- Lightweight beverage product reference layer (DL-029): product identity separate from venue offering state.
-- Optional brewery + style anchors for later filter/search enrichment without a heavy master catalog.
-- No inventory, pricing, supplier, or commercial columns.

-- ---------------------------------------------------------------------------
-- Brewery / producer reference (optional anchor on beverage_product)
-- ---------------------------------------------------------------------------
create table public.beverage_brewery (
  id uuid primary key default gen_random_uuid (),
  display_name text not null,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.beverage_brewery is
'Lightweight producer/brewery reference; not venue-specific tap state.';

create index idx_beverage_brewery_display_name on public.beverage_brewery (display_name);

-- ---------------------------------------------------------------------------
-- Style / category reference (optional anchor on beverage_product)
-- ---------------------------------------------------------------------------
create table public.beverage_style (
  id uuid primary key default gen_random_uuid (),
  display_name text not null,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.beverage_style is
'Lightweight style/category label (e.g. IPA, lager family); extend with hierarchy later if needed.';

create index idx_beverage_style_display_name on public.beverage_style (display_name);

-- ---------------------------------------------------------------------------
-- Beverage product identity (global reference, not per-venue availability)
-- ---------------------------------------------------------------------------
create table public.beverage_product (
  id uuid primary key default gen_random_uuid (),
  display_name text not null,
  brewery_id uuid references public.beverage_brewery (id) on delete set null,
  style_id uuid references public.beverage_style (id) on delete set null,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.beverage_product is
'Product identity in the reference layer; does not encode whether any venue currently pours it (DL-029).';

comment on column public.beverage_product.brewery_id is
'Optional brewery anchor; null when unknown or not modeled.';

comment on column public.beverage_product.style_id is
'Optional style anchor; null when unknown or not modeled.';

create index idx_beverage_product_brewery_id on public.beverage_product (brewery_id);

create index idx_beverage_product_style_id on public.beverage_product (style_id);

create index idx_beverage_product_display_name on public.beverage_product (display_name);
