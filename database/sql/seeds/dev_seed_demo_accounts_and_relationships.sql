-- PubPlus — demo accounts, businesses, authority chain, and light consumer private state
-- Depends on: dev_seed_reference_minimum.sql + dev_seed_demo_venues.sql
--
-- Auth rows: requires Supabase-style auth schema (auth.users + auth.identities) and pgcrypto
-- for password hashing. If you are not on Supabase Postgres, skip this file or adapt auth inserts.
--
-- Domain separation: distinct consumer vs owner vs admin auth subjects; separate consumer_account /
-- owner_account / admin_account rows. This seed is for local/dev — it does not describe production
-- signup or trust bypass; published venue rows are still seeded directly for convenience only.

begin;

create extension if not exists pgcrypto with schema extensions;

-- ---------------------------------------------------------------------------
-- Auth users + email identities (fixed UUIDs for repeatable local testing)
-- ---------------------------------------------------------------------------
insert into auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at
)
select
  coalesce(
    (
      select
        id
      from
        auth.instances
      limit
        1
    ),
    '00000000-0000-0000-0000-000000000000'::uuid
  ),
  x.id,
  'authenticated',
  'authenticated',
  x.email,
  extensions.crypt('demo-password-123', extensions.gen_salt('bf')),
  now(),
  jsonb_build_object('provider', 'email', 'providers', jsonb_build_array('email')),
  '{}'::jsonb,
  now(),
  now ()
from
  (
    values
      ('c1000001-0001-4001-8001-000000000001'::uuid, 'consumer1@demo.pubplus.local'),
      ('c1000002-0002-4002-8002-000000000002'::uuid, 'consumer2@demo.pubplus.local'),
      ('e2000001-0001-4001-8001-000000000001'::uuid, 'owner1@demo.pubplus.local'),
      ('e2000002-0002-4002-8002-000000000002'::uuid, 'owner2@demo.pubplus.local'),
      ('a3000001-0001-4001-8001-000000000001'::uuid, 'admin1@demo.pubplus.local')
  ) as x (id, email)
where
  not exists (
    select
      1
    from
      auth.users u
    where
      u.id = x.id
  );

insert into auth.identities (
  id,
  user_id,
  identity_data,
  provider,
  provider_id,
  last_sign_in_at,
  created_at,
  updated_at
)
select
  gen_random_uuid (),
  x.user_id,
  jsonb_build_object(
    'sub',
    x.user_id::text,
    'email',
    x.email
  ),
  'email',
  x.user_id::text,
  now(),
  now(),
  now ()
from
  (
    values
      ('c1000001-0001-4001-8001-000000000001'::uuid, 'consumer1@demo.pubplus.local'),
      ('c1000002-0002-4002-8002-000000000002'::uuid, 'consumer2@demo.pubplus.local'),
      ('e2000001-0001-4001-8001-000000000001'::uuid, 'owner1@demo.pubplus.local'),
      ('e2000002-0002-4002-8002-000000000002'::uuid, 'owner2@demo.pubplus.local'),
      ('a3000001-0001-4001-8001-000000000001'::uuid, 'admin1@demo.pubplus.local')
  ) as x (user_id, email)
where
  not exists (
    select
      1
    from
      auth.identities i
    where
      i.user_id = x.user_id
      and i.provider = 'email'
  );

-- ---------------------------------------------------------------------------
-- Logical account anchors (public domain tables)
-- ---------------------------------------------------------------------------
insert into public.consumer_account (id, auth_user_id)
values
  ('cc000001-0001-4001-8001-000000000001', 'c1000001-0001-4001-8001-000000000001'),
  ('cc000002-0002-4002-8002-000000000002', 'c1000002-0002-4002-8002-000000000002')
on conflict (id) do nothing;

insert into public.owner_account (id, auth_user_id)
values
  ('ee000001-0001-4001-8001-000000000001', 'e2000001-0001-4001-8001-000000000001'),
  ('ee000002-0002-4002-8002-000000000002', 'e2000002-0002-4002-8002-000000000002')
on conflict (id) do nothing;

insert into public.admin_account (id, auth_user_id)
values
  ('aa000001-0001-4001-8001-000000000001', 'a3000001-0001-4001-8001-000000000001')
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- Businesses + owner membership + managed venues + authority satellites
-- ---------------------------------------------------------------------------
insert into public.business (id, display_name)
values
  ('bb000001-0001-4001-8001-000000000001', 'Demo Harbour Pub Group'),
  ('bb000002-0002-4002-8002-000000000002', 'Demo Yeast & Barrel Pty Ltd')
on conflict (id) do nothing;

insert into public.owner_business_membership (
  id,
  owner_account_id,
  business_id,
  membership_status,
  membership_role,
  invited_at,
  activated_at
)
values
  (
    'dd000001-0001-4001-8001-000000000001',
    'ee000001-0001-4001-8001-000000000001',
    'bb000001-0001-4001-8001-000000000001',
    'active',
    'org_owner',
    now (),
    now ()
  ),
  (
    'dd000002-0002-4002-8002-000000000002',
    'ee000001-0001-4001-8001-000000000001',
    'bb000002-0002-4002-8002-000000000002',
    'active',
    'manager',
    now (),
    now ()
  ),
  (
    'dd000003-0003-4003-8003-000000000003',
    'ee000002-0002-4002-8002-000000000002',
    'bb000002-0002-4002-8002-000000000002',
    'active',
    'staff',
    now (),
    now ()
  )
on conflict (id) do nothing;

insert into public.business_venue_management_relationship (
  id,
  business_id,
  venue_id,
  relationship_lifecycle
)
values
  (
    'rm000001-0001-4001-8001-000000000011',
    'bb000001-0001-4001-8001-000000000001',
    'f1111111-1111-4111-8111-111111111101',
    'approved'
  ),
  (
    'rm000002-0002-4002-8002-000000000022',
    'bb000002-0002-4002-8002-000000000002',
    'f1111111-1111-4111-8111-111111111102',
    'approved'
  )
on conflict (id) do nothing;

insert into public.venue_verification_state (
  business_venue_management_relationship_id,
  verification_status,
  last_evaluated_at
)
values
  (
    'rm000001-0001-4001-8001-000000000011',
    'verified',
    now ()
  ),
  (
    'rm000002-0002-4002-8002-000000000022',
    'in_review',
    now ()
  )
on conflict (business_venue_management_relationship_id) do update set
  verification_status = excluded.verification_status,
  last_evaluated_at = excluded.last_evaluated_at,
  updated_at = now ();

insert into public.venue_management_rights (
  business_venue_management_relationship_id,
  rights_status,
  effective_from
)
values
  (
    'rm000001-0001-4001-8001-000000000011',
    'active',
    now ()
  ),
  (
    'rm000002-0002-4002-8002-000000000022',
    'active',
    now ()
  )
on conflict (business_venue_management_relationship_id) do update set
  rights_status = excluded.rights_status,
  effective_from = excluded.effective_from,
  updated_at = now ();

insert into public.venue_capability_grant (
  id,
  business_venue_management_relationship_id,
  owner_account_id,
  capability_code,
  grant_status
)
values
  (
    'gg000001-0001-4001-8001-000000000001',
    'rm000001-0001-4001-8001-000000000011',
    'ee000001-0001-4001-8001-000000000001',
    'manage_published_venue_operations',
    'active'
  ),
  (
    'gg000002-0002-4002-8002-000000000002',
    'rm000002-0002-4002-8002-000000000022',
    'ee000002-0002-4002-8002-000000000002',
    'submit_restricted_changes_for_review',
    'active'
  )
on conflict (id) do nothing;

insert into public.venue_claim_request (
  id,
  venue_id,
  business_id,
  initiated_by_owner_account_id,
  claim_lifecycle_status,
  summary
)
values
  (
    'bb000099-0009-4009-8009-000000000099',
    'f1111111-1111-4111-8111-111111111102',
    'bb000002-0002-4002-8002-000000000002',
    'ee000002-0002-4002-8002-000000000002',
    'draft',
    'Demo draft claim — not a live permission grant'
  )
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- Consumer private state (lightweight)
-- ---------------------------------------------------------------------------
insert into public.consumer_profile (
  consumer_account_id,
  display_name
)
values
  ('cc000001-0001-4001-8001-000000000001', 'Demo Consumer One')
on conflict (consumer_account_id) do update set
  display_name = excluded.display_name,
  updated_at = now ();

insert into public.consumer_default_location_preference (
  consumer_account_id,
  default_locality_id
)
values
  ('cc000001-0001-4001-8001-000000000001', '22222222-2222-4222-8222-222222222201')
on conflict (consumer_account_id) do update set
  default_locality_id = excluded.default_locality_id,
  updated_at = now ();

insert into public.consumer_notification_settings (consumer_account_id)
values
  ('cc000001-0001-4001-8001-000000000001')
on conflict (consumer_account_id) do nothing;

insert into public.saved_list (
  id,
  consumer_account_id,
  name,
  sort_order
)
values
  (
    'ss000001-0001-4001-8001-000000000001',
    'cc000001-0001-4001-8001-000000000001',
    'Weekend crawl',
    0
  )
on conflict (id) do nothing;

insert into public.saved_list_membership (
  saved_list_id,
  venue_id
)
values
  (
    'ss000001-0001-4001-8001-000000000001',
    'f1111111-1111-4111-8111-111111111101'
  )
on conflict (saved_list_id, venue_id) do nothing;

insert into public.consumer_workflow_submission (
  id,
  consumer_account_id,
  venue_id,
  submission_kind,
  summary
)
values
  (
    'ww000001-0001-4001-8001-000000000001',
    'cc000001-0001-4001-8001-000000000001',
    'f1111111-1111-4111-8111-111111111102',
    'venue_issue',
    'Demo: reporting an issue — not published truth'
  )
on conflict (id) do nothing;

commit;
