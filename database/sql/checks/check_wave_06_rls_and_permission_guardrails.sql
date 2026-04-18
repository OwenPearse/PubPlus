-- PubPlus — Verification: Wave 6 (RLS and permission guardrails)
-- Run after migrations 0017–0020.

-- RLS enabled on published-truth anchor tables
select
  'rls_enabled_venue' as check_name,
  c.relrowsecurity as ok
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'venue'
union all
select
  'rls_enabled_venue_published_profile',
  c.relrowsecurity
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'venue_published_profile'
union all
select
  'rls_enabled_consumer_profile',
  c.relrowsecurity
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'consumer_profile'
union all
select
  'rls_enabled_venue_change_proposal',
  c.relrowsecurity
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'venue_change_proposal'
union all
select
  'rls_enabled_audit_event',
  c.relrowsecurity
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'audit_event';

-- Published truth: no INSERT/UPDATE/DELETE/ALL policies (only SELECT is allowed for client roles)
select
  'published_truth_no_write_policies_venue_published_profile' as check_name,
  not exists (
    select
      1
    from
      pg_policies p
    where
      p.schemaname = 'public'
      and p.tablename = 'venue_published_profile'
      and p.cmd = any (array['INSERT', 'UPDATE', 'DELETE', 'ALL'])
  ) as ok
union all
select
  'published_truth_no_write_policies_venue_published_attribute_value',
  not exists (
    select
      1
    from
      pg_policies p
    where
      p.schemaname = 'public'
      and p.tablename = 'venue_published_attribute_value'
      and p.cmd = any (array['INSERT', 'UPDATE', 'DELETE', 'ALL'])
  ) as ok;

-- Helper functions exist (SECURITY INVOKER — prosecdef = false)
select
  'helper_current_consumer_account_id_exists' as check_name,
  exists (
    select
      1
    from
      pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
    where
      n.nspname = 'public'
      and p.proname = 'current_consumer_account_id'
      and not p.prosecdef
  ) as ok
union all
select
  'helper_current_owner_account_id_exists',
  exists (
    select
      1
    from
      pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
    where
      n.nspname = 'public'
      and p.proname = 'current_owner_account_id'
      and not p.prosecdef
  ) as ok
union all
select
  'helper_current_admin_account_id_exists',
  exists (
    select
      1
    from
      pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
    where
      n.nspname = 'public'
      and p.proname = 'current_admin_account_id'
      and not p.prosecdef
  ) as ok;

-- Consumer private: at least one policy on self-scoped table
select
  'consumer_profile_has_policies' as check_name,
  (
    select
      count(*) >= 1
    from
      pg_policies p
    where
      p.schemaname = 'public'
      and p.tablename = 'consumer_profile'
  ) as ok;

-- Admin workflow read: audit_event has an admin-oriented policy name pattern (coarse signal)
select
  'audit_event_has_select_policy' as check_name,
  exists (
    select
      1
    from
      pg_policies p
    where
      p.schemaname = 'public'
      and p.tablename = 'audit_event'
      and p.cmd = 'SELECT'
  ) as ok;

-- Owner chain tables have RLS on (sample)
select
  'rls_enabled_business_venue_management_relationship' as check_name,
  c.relrowsecurity as ok
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'business_venue_management_relationship';

-- Consumer private policies target authenticated sessions (coarse signal)
select
  'consumer_profile_policies_include_authenticated' as check_name,
  exists (
    select
      1
    from
      pg_policies p
    where
      p.schemaname = 'public'
      and p.tablename = 'consumer_profile'
      and (
        p.roles is null
        or 'authenticated' = any (p.roles)
      )
  ) as ok;
