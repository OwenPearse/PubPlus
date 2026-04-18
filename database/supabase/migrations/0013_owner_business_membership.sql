-- PubPlus — Wave 5 / Migration 0013
-- Owner-to-business membership: bridge only; not venue authority (DL-021).
-- RLS: deferred.

-- ---------------------------------------------------------------------------
-- Owner ↔ business membership (lifecycle; coarse role only)
-- ---------------------------------------------------------------------------
create table public.owner_business_membership (
  id uuid primary key default gen_random_uuid (),
  owner_account_id uuid not null references public.owner_account (id) on delete cascade,
  business_id uuid not null references public.business (id) on delete cascade,
  membership_status text not null default 'invited' check (
    membership_status in (
      'invited',
      'active',
      'suspended',
      'removed'
    )
  ),
  membership_role text not null default 'staff' check (
    membership_role in (
      'org_owner',
      'manager',
      'staff'
    )
  ),
  invited_at timestamptz,
  activated_at timestamptz,
  removed_at timestamptz,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint owner_business_membership_owner_business_unique unique (owner_account_id, business_id)
);

comment on table public.owner_business_membership is
'Which owner portal users belong to which business; does not grant venue-scoped authority without managed-venue chain (Worker B).';

create index idx_owner_business_membership_business on public.owner_business_membership (business_id);

create index idx_owner_business_membership_owner on public.owner_business_membership (owner_account_id);
