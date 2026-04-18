-- PubPlus — Wave 11 / Migration 0031
-- Business-first entitlements and venue-scoped commercial overlays (DL-024).
-- Entitlements express commercial capability/limit state, not owner permissions (DL-021).
-- Venue overlays attach through the managed-venue relationship spine, not public truth tables.
-- RLS: deferred to migration 0032.

-- ---------------------------------------------------------------------------
-- Explicit entitlements / limits keyed per business (extend via entitlement_code + payload)
-- ---------------------------------------------------------------------------
create table public.business_entitlement (
  id uuid primary key default gen_random_uuid (),
  business_id uuid not null references public.business (id) on delete cascade,
  entitlement_code text not null,
  entitlement_payload jsonb not null default '{}'::jsonb,
  effective_from timestamptz,
  effective_to timestamptz,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint business_entitlement_business_code_unique unique (business_id, entitlement_code),
  constraint business_entitlement_code_format check (
    entitlement_code ~ '^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$'
  ),
  constraint business_entitlement_effective_window check (
    effective_from is null
    or effective_to is null
    or effective_from <= effective_to
  )
);

comment on table public.business_entitlement is
'Commercial/limit flags and numeric caps for a business; not venue_capability_grant and not a substitute for authority decisions (see domain_boundary_map public vs commercial; relationship_authority_blueprint business-to-commercial section).';

comment on column public.business_entitlement.entitlement_payload is
'Structured limits or feature toggles (e.g. max venues); application interprets keys — still not public discovery truth.';

create index idx_business_entitlement_business on public.business_entitlement (business_id);

-- ---------------------------------------------------------------------------
-- Per managed-venue commercial overlay bundle (secondary to business-level rows)
-- ---------------------------------------------------------------------------
create table public.business_venue_commercial_overlay (
  id uuid primary key default gen_random_uuid (),
  business_venue_management_relationship_id uuid not null references public.business_venue_management_relationship (id) on delete cascade,
  overlay_scope text not null default 'default' check (overlay_scope in ('default', 'listing', 'promoted_surface')),
  overlay_payload jsonb not null default '{}'::jsonb,
  overlay_status text not null default 'inactive' check (
    overlay_status in ('inactive', 'active')
  ),
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint business_venue_commercial_overlay_scope_unique unique (
    business_venue_management_relationship_id,
    overlay_scope
  )
);

comment on table public.business_venue_commercial_overlay is
'Venue-scoped commercial overlay state keyed through the business↔venue management junction; does not mutate published venue truth or discovery eligibility tiers (DL-030).';

comment on column public.business_venue_commercial_overlay.overlay_payload is
'Opaque commercial flags for portal/serving layers — must not be read as moderation approval or confidence.';

create index idx_business_venue_commercial_overlay_bvm on public.business_venue_commercial_overlay (
  business_venue_management_relationship_id
);
