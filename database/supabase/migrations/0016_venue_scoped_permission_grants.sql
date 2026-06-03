-- PubPlus — Wave 5 / Migration 0016
-- Coarse venue-scoped capability grants through the managed-venue relationship only (DL-020, DL-021).
-- Does not bypass claim, verification, or management-rights semantics elsewhere (Worker B).
-- RLS: deferred.

-- ---------------------------------------------------------------------------
-- Venue-scoped capability grants (coarse v1 set)
-- ---------------------------------------------------------------------------
create table public.venue_capability_grant (
  id uuid primary key default gen_random_uuid (),
  business_venue_management_relationship_id uuid not null references public.business_venue_management_relationship (id) on delete cascade,
  owner_account_id uuid not null references public.owner_account (id) on delete cascade,
  capability_code text not null check (
    capability_code in (
      'manage_published_venue_operations',
      'submit_restricted_changes_for_review',
      'manage_owner_private_venue_operations',
      'manage_business_team_settings'
    )
  ),
  grant_status text not null default 'active' check (
    grant_status in (
      'active',
      'revoked'
    )
  ),
  granted_at timestamptz not null default now (),
  revoked_at timestamptz,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint venue_capability_grant_rel_owner_cap_unique unique (
    business_venue_management_relationship_id,
    owner_account_id,
    capability_code
  )
);

comment on table public.venue_capability_grant is
'Coarse capabilities for an owner user scoped through business↔venue management relationship; not a fine-grained ACL matrix (Worker B).';

create index idx_venue_capability_grant_owner on public.venue_capability_grant (owner_account_id);

create index idx_venue_capability_grant_relationship on public.venue_capability_grant (business_venue_management_relationship_id);
