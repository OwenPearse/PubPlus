-- PubPlus — Wave 6 / Migration 0019
-- RLS: owner/business/authority chain is relationship-scoped (membership → business → managed venue → grants).
-- No portal-login shortcut: visibility requires owner_account rows + business membership; grants attach via business_venue_management_relationship only.

-- ---------------------------------------------------------------------------
-- Owner account resolution (caller identity)
-- ---------------------------------------------------------------------------
create or replace function public.current_owner_account_id () returns uuid
language sql
stable
security invoker
set search_path = public
as $$
  select
    o.id
  from
    public.owner_account o
  where
    o.auth_user_id = auth.uid ();
$$;

comment on function public.current_owner_account_id () is
'RLS helper: resolves owner_account.id for auth.uid(); null if not an owner session.';

grant execute on function public.current_owner_account_id () to anon,
authenticated;

-- ---------------------------------------------------------------------------
-- Predicate: businesses this owner may see via non-removed membership (coarse v1)
-- ---------------------------------------------------------------------------
create or replace function public.owner_is_member_of_business (p_business_id uuid) returns boolean
language sql
stable
security invoker
set search_path = public
as $$
  select
    exists (
      select
        1
      from
        public.owner_business_membership obm
      where
        obm.business_id = p_business_id
        and obm.owner_account_id = public.current_owner_account_id ()
        and obm.membership_status <> 'removed'
    );
$$;

comment on function public.owner_is_member_of_business (uuid) is
'RLS helper: true when current owner has a non-removed membership row for the business.';

grant execute on function public.owner_is_member_of_business (uuid) to anon,
authenticated;

-- ---------------------------------------------------------------------------
-- Owner account anchor (self-read)
-- ---------------------------------------------------------------------------
alter table public.owner_account enable row level security;

create policy owner_account_select_self on public.owner_account for
select
  to authenticated using (auth_user_id = auth.uid ());

-- ---------------------------------------------------------------------------
-- Owner ↔ business membership (read + limited self-update; no casual inserts)
-- ---------------------------------------------------------------------------
alter table public.owner_business_membership enable row level security;

create policy owner_business_membership_select_self on public.owner_business_membership for
select
  to authenticated using (owner_account_id = public.current_owner_account_id ());

create policy owner_business_membership_update_self on public.owner_business_membership for
update
  to authenticated using (owner_account_id = public.current_owner_account_id ())
with
  check (owner_account_id = public.current_owner_account_id ());

-- ---------------------------------------------------------------------------
-- Business entity (only businesses the owner belongs to)
-- ---------------------------------------------------------------------------
alter table public.business enable row level security;

create policy business_select_member on public.business for
select
  to authenticated using (
    public.owner_is_member_of_business (business.id)
  );

-- ---------------------------------------------------------------------------
-- Managed venue relationship + authority satellites (scoped by business membership)
-- ---------------------------------------------------------------------------
alter table public.business_venue_management_relationship enable row level security;

create policy bvm_relationship_select_member on public.business_venue_management_relationship for
select
  to authenticated using (
    public.owner_is_member_of_business (business_venue_management_relationship.business_id)
  );

alter table public.venue_claim_request enable row level security;

create policy venue_claim_request_select_member on public.venue_claim_request for
select
  to authenticated using (
    initiated_by_owner_account_id = public.current_owner_account_id ()
    or public.owner_is_member_of_business (venue_claim_request.business_id)
  );

create policy venue_claim_request_insert_initiator on public.venue_claim_request for
insert
  to authenticated
with
  check (
    initiated_by_owner_account_id = public.current_owner_account_id ()
    and public.owner_is_member_of_business (business_id)
  );

create policy venue_claim_request_update_initiator on public.venue_claim_request for
update
  to authenticated using (
    initiated_by_owner_account_id = public.current_owner_account_id ()
  )
with
  check (
    initiated_by_owner_account_id = public.current_owner_account_id ()
    and public.owner_is_member_of_business (business_id)
  );

alter table public.venue_verification_state enable row level security;

create policy venue_verification_state_select_via_relationship on public.venue_verification_state for
select
  to authenticated using (
    exists (
      select
        1
      from
        public.business_venue_management_relationship bvm
      where
        bvm.id = venue_verification_state.business_venue_management_relationship_id
        and public.owner_is_member_of_business (bvm.business_id)
    )
  );

alter table public.venue_management_rights enable row level security;

create policy venue_management_rights_select_via_relationship on public.venue_management_rights for
select
  to authenticated using (
    exists (
      select
        1
      from
        public.business_venue_management_relationship bvm
      where
        bvm.id = venue_management_rights.business_venue_management_relationship_id
        and public.owner_is_member_of_business (bvm.business_id)
    )
  );

alter table public.venue_capability_grant enable row level security;

create policy venue_capability_grant_select_grantee_via_relationship on public.venue_capability_grant for
select
  to authenticated using (
    owner_account_id = public.current_owner_account_id ()
    and exists (
      select
        1
      from
        public.business_venue_management_relationship bvm
      where
        bvm.id = venue_capability_grant.business_venue_management_relationship_id
        and public.owner_is_member_of_business (bvm.business_id)
    )
  );

alter table public.venue_authority_decision enable row level security;

create policy venue_authority_decision_select_scoped on public.venue_authority_decision for
select
  to authenticated using (
    (
      venue_claim_request_id is not null
      and exists (
        select
          1
        from
          public.venue_claim_request vcr
        where
          vcr.id = venue_authority_decision.venue_claim_request_id
          and (
            vcr.initiated_by_owner_account_id = public.current_owner_account_id ()
            or public.owner_is_member_of_business (vcr.business_id)
          )
      )
    )
    or (
      business_venue_management_relationship_id is not null
      and exists (
        select
          1
        from
          public.business_venue_management_relationship bvm
        where
          bvm.id = venue_authority_decision.business_venue_management_relationship_id
          and public.owner_is_member_of_business (bvm.business_id)
      )
    )
  );

alter table public.venue_authority_event enable row level security;

create policy venue_authority_event_select_scoped on public.venue_authority_event for
select
  to authenticated using (
    owner_account_id = public.current_owner_account_id ()
    or (
      business_id is not null
      and public.owner_is_member_of_business (venue_authority_event.business_id)
    )
    or exists (
      select
        1
      from
        public.business_venue_management_relationship bvm
      where
        bvm.venue_id = venue_authority_event.venue_id
        and public.owner_is_member_of_business (bvm.business_id)
    )
  );

-- ---------------------------------------------------------------------------
-- Owner-originated proposals + staging (workflow; does not write published truth)
-- ---------------------------------------------------------------------------
create policy venue_change_proposal_select_owner_actor on public.venue_change_proposal for
select
  to authenticated using (
    actor_owner_account_id = public.current_owner_account_id ()
  );

create policy venue_change_proposal_insert_owner_actor on public.venue_change_proposal for
insert
  to authenticated
with
  check (
    actor_type = 'owner'
    and actor_owner_account_id = public.current_owner_account_id ()
    and actor_consumer_account_id is null
    and actor_admin_account_id is null
  );

create policy venue_change_proposal_update_owner_actor on public.venue_change_proposal for
update
  to authenticated using (
    actor_owner_account_id = public.current_owner_account_id ()
  )
with
  check (
    actor_type = 'owner'
    and actor_owner_account_id = public.current_owner_account_id ()
    and actor_consumer_account_id is null
    and actor_admin_account_id is null
  );

create policy venue_change_proposal_delete_owner_actor on public.venue_change_proposal for delete to authenticated using (
  actor_owner_account_id = public.current_owner_account_id ()
  and lifecycle_status in ('staged', 'withdrawn')
);

create policy venue_proposal_target_rw_owner_proposal on public.venue_proposal_target for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_target.venue_change_proposal_id
      and p.actor_owner_account_id = public.current_owner_account_id ()
  )
)
with
  check (
    exists (
      select
        1
      from
        public.venue_change_proposal p
      where
        p.id = venue_proposal_target.venue_change_proposal_id
        and p.actor_owner_account_id = public.current_owner_account_id ()
    )
  );

create policy venue_proposal_staging_profile_rw_owner_proposal on public.venue_proposal_staging_profile for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_staging_profile.venue_change_proposal_id
      and p.actor_owner_account_id = public.current_owner_account_id ()
  )
)
with
  check (
    exists (
      select
        1
      from
        public.venue_change_proposal p
      where
        p.id = venue_proposal_staging_profile.venue_change_proposal_id
        and p.actor_owner_account_id = public.current_owner_account_id ()
    )
  );

create policy venue_proposal_staging_location_rw_owner_proposal on public.venue_proposal_staging_location for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_staging_location.venue_change_proposal_id
      and p.actor_owner_account_id = public.current_owner_account_id ()
  )
)
with
  check (
    exists (
      select
        1
      from
        public.venue_change_proposal p
      where
        p.id = venue_proposal_staging_location.venue_change_proposal_id
        and p.actor_owner_account_id = public.current_owner_account_id ()
    )
  );

create policy venue_proposal_staging_attribute_rw_owner_proposal on public.venue_proposal_staging_attribute for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_staging_attribute.venue_change_proposal_id
      and p.actor_owner_account_id = public.current_owner_account_id ()
  )
)
with
  check (
    exists (
      select
        1
      from
        public.venue_change_proposal p
      where
        p.id = venue_proposal_staging_attribute.venue_change_proposal_id
        and p.actor_owner_account_id = public.current_owner_account_id ()
    )
  );

create policy venue_proposal_staging_hours_rw_owner_proposal on public.venue_proposal_staging_hours for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_staging_hours.venue_change_proposal_id
      and p.actor_owner_account_id = public.current_owner_account_id ()
  )
)
with
  check (
    exists (
      select
        1
      from
        public.venue_change_proposal p
      where
        p.id = venue_proposal_staging_hours.venue_change_proposal_id
        and p.actor_owner_account_id = public.current_owner_account_id ()
    )
  );
