-- PubPlus — Wave 5 / Migration 0014
-- Business ↔ canonical venue management junction: core authority anchor (DL-020).
-- Non-exclusive: many businesses may relate to one venue via separate rows.
-- v1: one row per (business_id, venue_id) + lifecycle column; a future migration may split or
-- version rows for heavier history without changing the conceptual junction requirement.
-- No shortcut authority columns on public.business or public.venue.
-- Optional link to initiating claim is added in migration 0015 after venue_claim_request exists.
-- RLS: deferred.

-- ---------------------------------------------------------------------------
-- Managed-venue relationship (explicit; lifecycle-controlled)
-- ---------------------------------------------------------------------------
create table public.business_venue_management_relationship (
  id uuid primary key default gen_random_uuid (),
  business_id uuid not null references public.business (id) on delete cascade,
  venue_id uuid not null references public.venue (id) on delete cascade,
  relationship_lifecycle text not null default 'requested' check (
    relationship_lifecycle in (
      'requested',
      'pending_review',
      'approved',
      'inactive',
      'revoked',
      'denied'
    )
  ),
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint bvm_rel_business_venue_unique unique (business_id, venue_id)
);

comment on table public.business_venue_management_relationship is
'Explicit business-to-venue management link; venue-scoped permissions and grants attach here, not on owner↔venue edges (relationship_authority_blueprint: owner/business/venue authority chain).';

create index idx_bvm_relationship_business on public.business_venue_management_relationship (business_id);

create index idx_bvm_relationship_venue on public.business_venue_management_relationship (venue_id);
