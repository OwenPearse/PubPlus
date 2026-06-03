-- PubPlus — Wave 5 / Migration 0015
-- Claim initiation, verification state, management-rights state, and authority-side decisions/events.
-- Distinct concepts: claim ≠ verification ≠ management rights ≠ capability grants (0016) (DL-009, Worker B).
-- Live grants remain on venue_capability_grant; history here is not the permission read model (DL-022).
-- RLS: deferred.

-- ---------------------------------------------------------------------------
-- Claim initiation (workflow; not permission grants)
-- ---------------------------------------------------------------------------
create table public.venue_claim_request (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  business_id uuid not null references public.business (id) on delete cascade,
  initiated_by_owner_account_id uuid not null references public.owner_account (id) on delete restrict,
  claim_lifecycle_status text not null default 'draft' check (
    claim_lifecycle_status in (
      'draft',
      'submitted',
      'under_review',
      'withdrawn',
      'denied',
      'closed'
    )
  ),
  resulting_business_venue_management_relationship_id uuid unique references public.business_venue_management_relationship (id) on delete set null,
  summary text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue_claim_request is
'Claim initiation only: intent to manage under a business/venue context; does not encode live permissions (Worker B).';

create index idx_venue_claim_request_venue on public.venue_claim_request (venue_id);

create index idx_venue_claim_request_business on public.venue_claim_request (business_id);

create index idx_venue_claim_request_initiator on public.venue_claim_request (initiated_by_owner_account_id);

-- Optional provenance from relationship row → initiating claim (added after claim table exists)
alter table public.business_venue_management_relationship
add column source_venue_claim_request_id uuid references public.venue_claim_request (id) on delete set null;

comment on column public.business_venue_management_relationship.source_venue_claim_request_id is
'Optional link to the claim request that started this management relationship; authority still flows through this row.';

create index idx_bvm_relationship_source_claim on public.business_venue_management_relationship (source_venue_claim_request_id)
where
  source_venue_claim_request_id is not null;

-- ---------------------------------------------------------------------------
-- Verification state (current snapshot; distinct from Stage-2 proposal_review)
-- ---------------------------------------------------------------------------
create table public.venue_verification_state (
  business_venue_management_relationship_id uuid primary key references public.business_venue_management_relationship (id) on delete cascade,
  context_venue_claim_request_id uuid references public.venue_claim_request (id) on delete set null,
  verification_status text not null default 'pending' check (
    verification_status in (
      'pending',
      'in_review',
      'verified',
      'failed',
      'expired',
      'waived'
    )
  ),
  last_evaluated_at timestamptz,
  updated_at timestamptz not null default now ()
);

comment on table public.venue_verification_state is
'Current verification posture for the management relationship; not venue-scoped capability grants (Worker B).';

-- ---------------------------------------------------------------------------
-- Management-rights state (current snapshot; companion to relationship lifecycle)
-- ---------------------------------------------------------------------------
create table public.venue_management_rights (
  business_venue_management_relationship_id uuid primary key references public.business_venue_management_relationship (id) on delete cascade,
  rights_status text not null default 'none' check (
    rights_status in (
      'none',
      'active',
      'suspended',
      'revoked'
    )
  ),
  effective_from timestamptz,
  updated_at timestamptz not null default now ()
);

comment on table public.venue_management_rights is
'Current management-rights posture on the business↔venue link; distinct from claim narrative and verification rows.';

-- ---------------------------------------------------------------------------
-- Authority decisions (admin/reviewer; parallel to Stage-2 publish reviews)
-- ---------------------------------------------------------------------------
create table public.venue_authority_decision (
  id uuid primary key default gen_random_uuid (),
  decided_by_admin_account_id uuid not null references public.admin_account (id) on delete restrict,
  decision_kind text not null check (
    decision_kind in (
      'claim_decision',
      'verification_decision',
      'relationship_lifecycle_decision',
      'management_rights_decision'
    )
  ),
  venue_claim_request_id uuid references public.venue_claim_request (id) on delete set null,
  business_venue_management_relationship_id uuid references public.business_venue_management_relationship (id) on delete set null,
  decision_outcome text not null,
  rationale text,
  evidence_basis_ref text,
  decided_at timestamptz not null default now (),
  constraint venue_authority_decision_target_ck check (
    venue_claim_request_id is not null
    or business_venue_management_relationship_id is not null
  )
);

comment on table public.venue_authority_decision is
'Human decisions on authority workflows; not Stage-2 field-family publish outcomes (Worker B / Worker D).';

create index idx_venue_authority_decision_admin on public.venue_authority_decision (decided_by_admin_account_id);

create index idx_venue_authority_decision_claim on public.venue_authority_decision (venue_claim_request_id)
where
  venue_claim_request_id is not null;

create index idx_venue_authority_decision_bvm_rel on public.venue_authority_decision (business_venue_management_relationship_id)
where
  business_venue_management_relationship_id is not null;

-- ---------------------------------------------------------------------------
-- Authority events (append-only lineage; not live permission source of truth)
-- ---------------------------------------------------------------------------
create table public.venue_authority_event (
  id uuid primary key default gen_random_uuid (),
  event_kind text not null,
  venue_id uuid not null references public.venue (id) on delete cascade,
  business_id uuid references public.business (id) on delete set null,
  owner_account_id uuid references public.owner_account (id) on delete set null,
  venue_claim_request_id uuid references public.venue_claim_request (id) on delete set null,
  business_venue_management_relationship_id uuid references public.business_venue_management_relationship (id) on delete set null,
  payload_note text,
  created_at timestamptz not null default now ()
);

comment on table public.venue_authority_event is
'Append-only authority-side transitions; operational permission reads use venue_capability_grant + rights/verification snapshots (DL-022).';

create index idx_venue_authority_event_venue on public.venue_authority_event (venue_id);

create index idx_venue_authority_event_created on public.venue_authority_event (created_at);
