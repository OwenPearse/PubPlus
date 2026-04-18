-- PubPlus — Tranche 1 / Migration 0009
-- Evidence pointers + attachments + minimal append-only audit log.
-- Full object storage / URLs are out of band; DB holds pointers and linkage only.

-- ---------------------------------------------------------------------------
-- Evidence items (durable pointers)
-- ---------------------------------------------------------------------------
create table public.evidence_item (
  id uuid primary key default gen_random_uuid (),
  kind text not null check (
    kind in (
      'document',
      'url',
      'source_record_ref',
      'note',
      'other'
    )
  ),
  title text,
  external_ref text,
  storage_url text,
  created_at timestamptz not null default now ()
);

comment on table public.evidence_item is
'Evidence pointer (not blob store); binary content lives in object storage.';

-- ---------------------------------------------------------------------------
-- Attach evidence to proposals and/or Stage-2 reviews
-- ---------------------------------------------------------------------------
create table public.evidence_attachment (
  id uuid primary key default gen_random_uuid (),
  evidence_item_id uuid not null references public.evidence_item (id) on delete cascade,
  venue_change_proposal_id uuid references public.venue_change_proposal (id) on delete cascade,
  proposal_review_id uuid references public.proposal_review (id) on delete cascade,
  attached_at timestamptz not null default now (),
  check (
    (
      venue_change_proposal_id is not null
    )
    or (proposal_review_id is not null)
  )
);

comment on table public.evidence_attachment is
'Bridge: evidence links to workflow objects; authority-side decisions deferred to later tranche.';

create index idx_evidence_attachment_evidence on public.evidence_attachment (evidence_item_id);
create index idx_evidence_attachment_proposal on public.evidence_attachment (venue_change_proposal_id);
create index idx_evidence_attachment_review on public.evidence_attachment (proposal_review_id);

-- ---------------------------------------------------------------------------
-- Minimal audit append-only log (optional; explicit decision rows remain primary)
-- ---------------------------------------------------------------------------
create table public.audit_event (
  id uuid primary key default gen_random_uuid (),
  occurred_at timestamptz not null default now (),
  actor_type text not null check (
    actor_type in (
      'consumer',
      'owner',
      'admin',
      'system',
      'source'
    )
  ),
  actor_consumer_account_id uuid references public.consumer_account (id) on delete set null,
  actor_owner_account_id uuid references public.owner_account (id) on delete set null,
  actor_admin_account_id uuid references public.admin_account (id) on delete set null,
  entity_table text not null,
  entity_id uuid not null,
  action text not null,
  detail jsonb
);

comment on table public.audit_event is
'Cross-cutting minimal audit trail; domain-specific decision tables remain authoritative.';

create index idx_audit_event_entity on public.audit_event (entity_table, entity_id);
create index idx_audit_event_occurred on public.audit_event (occurred_at desc);

-- ---------------------------------------------------------------------------
-- RLS / security (posture)
-- ---------------------------------------------------------------------------
-- RLS policies are intentionally deferred. Future migrations should:
-- - deny direct UPDATE/DELETE on published-truth tables for non-service roles
-- - route mutations through service role / edge functions that record venue_publish_event
-- - scope audit_event inserts to trusted roles
