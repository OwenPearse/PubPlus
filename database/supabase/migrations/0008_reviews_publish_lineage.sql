-- PubPlus — Tranche 1 / Migration 0008
-- Stage-2 public-truth review decisions + publish lineage (history; not live truth by itself).
-- RLS must eventually restrict who can insert/update these rows (DL-008).

-- ---------------------------------------------------------------------------
-- Stage-2 moderation decision on a proposal (distinct from authority verification)
-- ---------------------------------------------------------------------------
create table public.proposal_review (
  id uuid primary key default gen_random_uuid (),
  venue_change_proposal_id uuid not null references public.venue_change_proposal (id) on delete cascade,
  reviewer_admin_account_id uuid not null references public.admin_account (id) on delete restrict,
  review_sequence int not null default 1 check (review_sequence >= 1),
  review_outcome text not null check (
    review_outcome in (
      'approved',
      'rejected',
      'changes_requested',
      'withheld'
    )
  ),
  reason_code text,
  decision_reason_text text,
  evidence_basis_ref text,
  reviewed_at timestamptz not null default now (),
  unique (venue_change_proposal_id, review_sequence)
);

comment on table public.proposal_review is
'Stage-2 decision on public-truth package; not authority/verification outcomes (Worker B).';

create index idx_proposal_review_proposal on public.proposal_review (venue_change_proposal_id);
create index idx_proposal_review_reviewer on public.proposal_review (reviewer_admin_account_id);

-- ---------------------------------------------------------------------------
-- Publish lineage (append-only narrative; pairs with published current-state tables)
-- ---------------------------------------------------------------------------
create table public.venue_publish_event (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  publish_event_kind text not null check (
    publish_event_kind in (
      'published_success',
      'withheld',
      'rollback',
      'restored',
      'superseded_lineage_note',
      'other'
    )
  ),
  venue_change_proposal_id uuid references public.venue_change_proposal (id) on delete set null,
  proposal_review_id uuid references public.proposal_review (id) on delete set null,
  supersedes_publish_event_id uuid references public.venue_publish_event (id) on delete set null,
  occurred_at timestamptz not null default now (),
  narrative text,
  actor_admin_account_id uuid references public.admin_account (id) on delete set null
);

comment on table public.venue_publish_event is
'Formal publish/withhold/rollback lineage; do not read as sole source of current published fields.';

create index idx_venue_publish_event_venue on public.venue_publish_event (venue_id);
create index idx_venue_publish_event_occurred on public.venue_publish_event (venue_id, occurred_at desc);

-- ---------------------------------------------------------------------------
-- Optional lineage snapshots (rollback-safe; not workflow staging)
-- ---------------------------------------------------------------------------
create table public.venue_published_row_history (
  id uuid primary key default gen_random_uuid (),
  venue_id uuid not null references public.venue (id) on delete cascade,
  venue_publish_event_id uuid not null references public.venue_publish_event (id) on delete cascade,
  truth_family text not null check (
    truth_family in (
      'profile',
      'geo',
      'attributes',
      'hours',
      'descriptive_copy',
      'whole_venue'
    )
  ),
  snapshot jsonb not null,
  created_at timestamptz not null default now ()
);

comment on table public.venue_published_row_history is
'Append-only prior snapshots per publish event; optional pattern for rollback narratives.';

create index idx_venue_published_row_history_venue on public.venue_published_row_history (venue_id);
create index idx_venue_published_row_history_event on public.venue_published_row_history (venue_publish_event_id);
