-- PubPlus — Wave 6 / Migration 0020
-- RLS: workflow, publish lineage, evidence, audit, and raw intake default deny for anon/authenticated
-- except scoped admin-account reads. Mutations remain service_role / backend orchestration unless a later tranche adds explicit admin write policies.

-- ---------------------------------------------------------------------------
-- Admin account resolution
-- ---------------------------------------------------------------------------
create or replace function public.current_admin_account_id () returns uuid
language sql
stable
security invoker
set search_path = public
as $$
  select
    a.id
  from
    public.admin_account a
  where
    a.auth_user_id = auth.uid ();
$$;

comment on function public.current_admin_account_id () is
'RLS helper: resolves admin_account.id for auth.uid(); null if not an admin session.';

grant execute on function public.current_admin_account_id () to anon,
authenticated;

create or replace function public.is_admin_session () returns boolean
language sql
stable
security invoker
set search_path = public
as $$
  select
    public.current_admin_account_id () is not null;
$$;

comment on function public.is_admin_session () is
'RLS helper: true when the session maps to admin_account.';

grant execute on function public.is_admin_session () to anon,
authenticated;

-- ---------------------------------------------------------------------------
-- Admin anchor (self-read)
-- ---------------------------------------------------------------------------
alter table public.admin_account enable row level security;

create policy admin_account_select_self on public.admin_account for
select
  to authenticated using (auth_user_id = auth.uid ());

-- ---------------------------------------------------------------------------
-- Raw intake (trusted ingestion / imports only at the DB API boundary)
-- ---------------------------------------------------------------------------
alter table public.raw_venue_intake_record enable row level security;

create policy raw_venue_intake_record_select_admin on public.raw_venue_intake_record for
select
  to authenticated using (public.is_admin_session ());

-- ---------------------------------------------------------------------------
-- Stage-2 moderation + publish lineage + snapshots (history is not live authority)
-- ---------------------------------------------------------------------------
alter table public.proposal_review enable row level security;

create policy proposal_review_select_admin on public.proposal_review for
select
  to authenticated using (public.is_admin_session ());

alter table public.venue_publish_event enable row level security;

create policy venue_publish_event_select_admin on public.venue_publish_event for
select
  to authenticated using (public.is_admin_session ());

alter table public.venue_published_row_history enable row level security;

create policy venue_published_row_history_select_admin on public.venue_published_row_history for
select
  to authenticated using (public.is_admin_session ());

-- ---------------------------------------------------------------------------
-- Evidence + audit (append-only expectations; client writes via service_role)
-- ---------------------------------------------------------------------------
alter table public.evidence_item enable row level security;

create policy evidence_item_select_admin on public.evidence_item for
select
  to authenticated using (public.is_admin_session ());

alter table public.evidence_attachment enable row level security;

create policy evidence_attachment_select_admin on public.evidence_attachment for
select
  to authenticated using (public.is_admin_session ());

alter table public.audit_event enable row level security;

create policy audit_event_select_admin on public.audit_event for
select
  to authenticated using (public.is_admin_session ());

-- ---------------------------------------------------------------------------
-- Admin visibility across proposals + staging (orthogonal to consumer/owner scoped policies)
-- ---------------------------------------------------------------------------
create policy venue_change_proposal_select_admin on public.venue_change_proposal for
select
  to authenticated using (public.is_admin_session ());

create policy venue_proposal_target_select_admin on public.venue_proposal_target for
select
  to authenticated using (public.is_admin_session ());

create policy venue_proposal_staging_profile_select_admin on public.venue_proposal_staging_profile for
select
  to authenticated using (public.is_admin_session ());

create policy venue_proposal_staging_location_select_admin on public.venue_proposal_staging_location for
select
  to authenticated using (public.is_admin_session ());

create policy venue_proposal_staging_attribute_select_admin on public.venue_proposal_staging_attribute for
select
  to authenticated using (public.is_admin_session ());

create policy venue_proposal_staging_hours_select_admin on public.venue_proposal_staging_hours for
select
  to authenticated using (public.is_admin_session ());

-- ---------------------------------------------------------------------------
-- Authority decisions (admin tooling; separate from Stage-2 proposal_review)
-- ---------------------------------------------------------------------------
create policy venue_authority_decision_select_admin on public.venue_authority_decision for
select
  to authenticated using (public.is_admin_session ());

create policy venue_authority_event_select_admin on public.venue_authority_event for
select
  to authenticated using (public.is_admin_session ());

-- ---------------------------------------------------------------------------
-- Owner/business authority tables: admin read-all for review tooling (no client writes here)
-- ---------------------------------------------------------------------------
create policy business_select_admin on public.business for
select
  to authenticated using (public.is_admin_session ());

create policy owner_business_membership_select_admin on public.owner_business_membership for
select
  to authenticated using (public.is_admin_session ());

create policy business_venue_management_relationship_select_admin on public.business_venue_management_relationship for
select
  to authenticated using (public.is_admin_session ());

create policy venue_claim_request_select_admin on public.venue_claim_request for
select
  to authenticated using (public.is_admin_session ());

create policy venue_verification_state_select_admin on public.venue_verification_state for
select
  to authenticated using (public.is_admin_session ());

create policy venue_management_rights_select_admin on public.venue_management_rights for
select
  to authenticated using (public.is_admin_session ());

create policy venue_capability_grant_select_admin on public.venue_capability_grant for
select
  to authenticated using (public.is_admin_session ());

-- ---------------------------------------------------------------------------
-- Owner account: admin read for cross-domain support (does not grant consumer/owner role collapse)
-- ---------------------------------------------------------------------------
create policy owner_account_select_admin on public.owner_account for
select
  to authenticated using (public.is_admin_session ());

-- ---------------------------------------------------------------------------
-- Specials / tap lists: not present in schema v1 — no policies here (see WAVE_06 doc).
-- ---------------------------------------------------------------------------
