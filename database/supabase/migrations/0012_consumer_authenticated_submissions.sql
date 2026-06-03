-- PubPlus — Wave 4 / Migration 0012
-- Consumer-authenticated workflow inputs: thin proposal extension + optional non-proposal submissions.
-- Truth-impacting field packages remain on venue_change_proposal + staging (Wave 3); no parallel truth store.
-- Application must align consumer_submission_extension rows with actor_consumer_account_id on the proposal.
-- RLS: deferred.

-- ---------------------------------------------------------------------------
-- Optional 1:1 extension for consumer-originated proposals (non-truth metadata only)
-- ---------------------------------------------------------------------------
create table public.consumer_submission_extension (
  venue_change_proposal_id uuid primary key references public.venue_change_proposal (id) on delete cascade,
  consumer_account_id uuid not null references public.consumer_account (id) on delete cascade,
  app_surface text,
  client_correlation_id text,
  created_at timestamptz not null default now ()
);

comment on table public.consumer_submission_extension is
'Thin consumer-only metadata for a proposal row; staged/public payloads stay on staging tables (Worker B).';

create index idx_consumer_submission_extension_consumer on public.consumer_submission_extension (consumer_account_id);

-- ---------------------------------------------------------------------------
-- Standalone authenticated submissions (no venue_change_proposal row yet / never)
-- ---------------------------------------------------------------------------
create table public.consumer_workflow_submission (
  id uuid primary key default gen_random_uuid (),
  consumer_account_id uuid not null references public.consumer_account (id) on delete cascade,
  venue_id uuid references public.venue (id) on delete set null,
  submission_kind text not null check (
    submission_kind in (
      'venue_issue',
      'app_feedback',
      'other'
    )
  ),
  lifecycle_status text not null default 'submitted' check (
    lifecycle_status in (
      'submitted',
      'triaged',
      'closed'
    )
  ),
  summary text not null,
  detail text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.consumer_workflow_submission is
'Consumer workflow intake not modeled as published truth; moderation routing and linkage to proposals are product/Stage-2 concerns.';

create index idx_consumer_workflow_submission_consumer on public.consumer_workflow_submission (consumer_account_id);

create index idx_consumer_workflow_submission_venue on public.consumer_workflow_submission (venue_id)
where
  venue_id is not null;
