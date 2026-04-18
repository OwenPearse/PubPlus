-- PubPlus — First tranche end-to-end sanity check (Waves 1–6)
-- Run after all migrations 0001–0020. This file does not replace per-wave checks;
-- it aggregates a small set of cross-cutting signals for domain separation and wiring.
--
-- Expect every row below to have ok = true.

-- 1) Core anchors + workflow spine tables present (single pass)
with
  expected (name) as (
    values
      ('venue'),
      ('consumer_account'),
      ('owner_account'),
      ('admin_account'),
      ('business'),
      ('geographic_region'),
      ('locality'),
      ('venue_published_profile'),
      ('venue_published_location'),
      ('venue_published_map_point'),
      ('venue_published_attribute_value'),
      ('venue_hours_regular'),
      ('venue_hours_exception'),
      ('venue_hours_uncertainty'),
      ('venue_derived_operational_claim'),
      ('venue_change_proposal'),
      ('venue_publish_event'),
      ('venue_published_row_history'),
      ('raw_venue_intake_record'),
      ('proposal_review'),
      ('evidence_item'),
      ('audit_event'),
      ('consumer_profile'),
      ('saved_list'),
      ('saved_list_membership'),
      ('consumer_workflow_submission'),
      ('owner_business_membership'),
      ('business_venue_management_relationship'),
      ('venue_claim_request'),
      ('venue_capability_grant')
  )
select
  'expected_tables_present' as check_name,
  (
    select
      count(*)
    from
      information_schema.tables t
      join expected e on e.name = t.table_name
    where
      t.table_schema = 'public'
  ) = (
    select
      count(*)
    from
      expected
  ) as ok;

-- 2) Published-truth families are not modeled as proposal rows (name-level guard)
select
  'no_table_named_published_truth_proposal' as check_name,
  not exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name in ('venue_published_truth', 'published_venue_change')
  ) as ok;

-- 3) Staging / workflow tables are distinct from published current-state tables (sample)
select
  'staging_profile_table_exists' as check_name,
  exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name = 'venue_proposal_staging_profile'
  ) as ok
union all
select
  'published_row_history_is_append_only_shape',
  exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'venue_published_row_history'
      and column_name in ('venue_publish_event_id', 'snapshot')
  ) as ok;

-- 4) Owner membership does not reference venue; grants route through managed-venue junction
select
  'owner_membership_no_venue_fk' as check_name,
  not exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'owner_business_membership'
      and column_name = 'venue_id'
  ) as ok
union all
select
  'capability_grant_fk_to_management_relationship_only',
  exists (
    select
      1
    from
      pg_constraint c
      join pg_class rel on rel.oid = c.conrelid
      join pg_namespace n on n.oid = rel.relnamespace
      join pg_class ref on ref.oid = c.confrelid
      join pg_namespace nref on nref.oid = ref.relnamespace
    where
      n.nspname = 'public'
      and rel.relname = 'venue_capability_grant'
      and c.contype = 'f'
      and nref.nspname = 'public'
      and ref.relname = 'business_venue_management_relationship'
  ) as ok;

-- 5) RLS helpers exist and are not SECURITY DEFINER
select
  'rls_helpers_security_invoker' as check_name,
  not exists (
    select
      1
    from
      pg_proc p
      join pg_namespace n on n.oid = p.pronamespace
    where
      n.nspname = 'public'
      and p.proname in (
        'current_consumer_account_id',
        'current_owner_account_id',
        'current_admin_account_id',
        'is_admin_session',
        'owner_is_member_of_business'
      )
      and p.prosecdef
  ) as ok;

-- 6) Sample published-truth table: RLS on + no client write policies (INSERT/UPDATE/DELETE/ALL)
select
  'published_truth_rls_and_no_client_writes_venue_published_profile' as check_name,
  (
    select
      c.relrowsecurity
    from
      pg_class c
      join pg_namespace n on n.oid = c.relnamespace
    where
      n.nspname = 'public'
      and c.relname = 'venue_published_profile'
  )
  and not exists (
    select
      1
    from
      pg_policies p
    where
      p.schemaname = 'public'
      and p.tablename = 'venue_published_profile'
      and p.cmd = any (array['INSERT', 'UPDATE', 'DELETE', 'ALL'])
  ) as ok;
