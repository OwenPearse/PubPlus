-- PubPlus — Wave 6 / Migration 0018
-- RLS: consumer-private tables and consumer-scoped workflow inputs.
-- Helpers are SECURITY INVOKER (not definer); safe for use in policies.

-- ---------------------------------------------------------------------------
-- Account resolution (caller identity)
-- ---------------------------------------------------------------------------
create or replace function public.current_consumer_account_id () returns uuid
language sql
stable
security invoker
set search_path = public
as $$
  select
    c.id
  from
    public.consumer_account c
  where
    c.auth_user_id = auth.uid ();
$$;

comment on function public.current_consumer_account_id () is
'RLS helper: resolves consumer_account.id for auth.uid(); null if not a consumer session.';

grant execute on function public.current_consumer_account_id () to anon,
authenticated;

-- ---------------------------------------------------------------------------
-- Consumer account anchor (self-read only; provisioning via service/triggers)
-- ---------------------------------------------------------------------------
alter table public.consumer_account enable row level security;

create policy consumer_account_select_self on public.consumer_account for
select
  to authenticated using (auth_user_id = auth.uid ());

-- ---------------------------------------------------------------------------
-- Consumer profile + preferences (self-scoped)
-- ---------------------------------------------------------------------------
alter table public.consumer_profile enable row level security;

create policy consumer_profile_rw_self on public.consumer_profile for all to authenticated using (
  consumer_account_id = public.current_consumer_account_id ()
)
with
  check (consumer_account_id = public.current_consumer_account_id ());

alter table public.consumer_default_location_preference enable row level security;

create policy consumer_default_location_rw_self on public.consumer_default_location_preference for all to authenticated using (
  consumer_account_id = public.current_consumer_account_id ()
)
with
  check (consumer_account_id = public.current_consumer_account_id ());

alter table public.consumer_notification_settings enable row level security;

create policy consumer_notification_settings_rw_self on public.consumer_notification_settings for all to authenticated using (
  consumer_account_id = public.current_consumer_account_id ()
)
with
  check (consumer_account_id = public.current_consumer_account_id ());

-- ---------------------------------------------------------------------------
-- Saved lists + membership (list-native; no cross-user access)
-- ---------------------------------------------------------------------------
alter table public.saved_list enable row level security;

create policy saved_list_rw_self on public.saved_list for all to authenticated using (
  consumer_account_id = public.current_consumer_account_id ()
)
with
  check (consumer_account_id = public.current_consumer_account_id ());

alter table public.saved_list_membership enable row level security;

create policy saved_list_membership_rw_via_own_list on public.saved_list_membership for all to authenticated using (
  exists (
    select
      1
    from
      public.saved_list sl
    where
      sl.id = saved_list_membership.saved_list_id
      and sl.consumer_account_id = public.current_consumer_account_id ()
  )
)
with
  check (
    exists (
      select
        1
      from
        public.saved_list sl
      where
        sl.id = saved_list_membership.saved_list_id
        and sl.consumer_account_id = public.current_consumer_account_id ()
    )
  );

-- ---------------------------------------------------------------------------
-- Consumer submission metadata + non-proposal intake (self-scoped)
-- ---------------------------------------------------------------------------
alter table public.consumer_submission_extension enable row level security;

create policy consumer_submission_extension_rw_self on public.consumer_submission_extension for all to authenticated using (
  consumer_account_id = public.current_consumer_account_id ()
)
with
  check (consumer_account_id = public.current_consumer_account_id ());

alter table public.consumer_workflow_submission enable row level security;

create policy consumer_workflow_submission_rw_self on public.consumer_workflow_submission for all to authenticated using (
  consumer_account_id = public.current_consumer_account_id ()
)
with
  check (consumer_account_id = public.current_consumer_account_id ());

-- ---------------------------------------------------------------------------
-- Consumer-originated proposals + staging (workflow; not published truth)
-- ---------------------------------------------------------------------------
alter table public.venue_change_proposal enable row level security;

create policy venue_change_proposal_select_consumer_actor on public.venue_change_proposal for
select
  to authenticated using (
    actor_consumer_account_id = public.current_consumer_account_id ()
  );

create policy venue_change_proposal_insert_consumer_actor on public.venue_change_proposal for
insert
  to authenticated
with
  check (
    actor_type = 'consumer'
    and actor_consumer_account_id = public.current_consumer_account_id ()
    and actor_owner_account_id is null
    and actor_admin_account_id is null
  );

create policy venue_change_proposal_update_consumer_actor on public.venue_change_proposal for
update
  to authenticated using (
    actor_consumer_account_id = public.current_consumer_account_id ()
  )
with
  check (
    actor_type = 'consumer'
    and actor_consumer_account_id = public.current_consumer_account_id ()
    and actor_owner_account_id is null
    and actor_admin_account_id is null
  );

create policy venue_change_proposal_delete_consumer_actor on public.venue_change_proposal for delete to authenticated using (
  actor_consumer_account_id = public.current_consumer_account_id ()
  and lifecycle_status in ('staged', 'withdrawn')
);

alter table public.venue_proposal_target enable row level security;

create policy venue_proposal_target_rw_consumer_proposal on public.venue_proposal_target for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_target.venue_change_proposal_id
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
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
        and p.actor_consumer_account_id = public.current_consumer_account_id ()
    )
  );

alter table public.venue_proposal_staging_profile enable row level security;

create policy venue_proposal_staging_profile_rw_consumer_proposal on public.venue_proposal_staging_profile for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_staging_profile.venue_change_proposal_id
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
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
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
  )
);

alter table public.venue_proposal_staging_location enable row level security;

create policy venue_proposal_staging_location_rw_consumer_proposal on public.venue_proposal_staging_location for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_staging_location.venue_change_proposal_id
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
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
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
  )
);

alter table public.venue_proposal_staging_attribute enable row level security;

create policy venue_proposal_staging_attribute_rw_consumer_proposal on public.venue_proposal_staging_attribute for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_staging_attribute.venue_change_proposal_id
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
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
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
  )
);

alter table public.venue_proposal_staging_hours enable row level security;

create policy venue_proposal_staging_hours_rw_consumer_proposal on public.venue_proposal_staging_hours for all to authenticated using (
  exists (
    select
      1
    from
      public.venue_change_proposal p
    where
      p.id = venue_proposal_staging_hours.venue_change_proposal_id
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
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
      and p.actor_consumer_account_id = public.current_consumer_account_id ()
  )
);
