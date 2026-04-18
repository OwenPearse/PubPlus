-- PubPlus — Full drafted-schema readiness check (migrations 0001–0032, Waves 1–11)
-- Run after all migrations in database/supabase/migrations/ are applied on a fresh database.
-- Purpose: one pass over anchor tables, coarse domain separation, and RLS posture — not a substitute
-- for per-wave checks (those stay the first line of defense for a touched domain).
--
-- Expect every row below to have ok = true.

-- ---------------------------------------------------------------------------
-- 1) All public tables from drafted migrations present (single cardinality match)
-- ---------------------------------------------------------------------------
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
      ('venue_published_descriptive_copy'),
      ('venue_published_location'),
      ('venue_published_map_point'),
      ('venue_attribute_definition'),
      ('venue_attribute_allowed_value'),
      ('venue_published_attribute_value'),
      ('venue_hours_regular'),
      ('venue_hours_exception'),
      ('venue_hours_uncertainty'),
      ('venue_derived_operational_claim'),
      ('external_data_source'),
      ('raw_venue_intake_record'),
      ('venue_change_proposal'),
      ('venue_proposal_target'),
      ('venue_proposal_staging_profile'),
      ('venue_proposal_staging_location'),
      ('venue_proposal_staging_attribute'),
      ('venue_proposal_staging_hours'),
      ('proposal_review'),
      ('venue_publish_event'),
      ('venue_published_row_history'),
      ('evidence_item'),
      ('evidence_attachment'),
      ('audit_event'),
      ('consumer_profile'),
      ('consumer_default_location_preference'),
      ('consumer_notification_settings'),
      ('saved_list'),
      ('saved_list_membership'),
      ('consumer_submission_extension'),
      ('consumer_workflow_submission'),
      ('owner_business_membership'),
      ('business_venue_management_relationship'),
      ('venue_claim_request'),
      ('venue_verification_state'),
      ('venue_management_rights'),
      ('venue_authority_decision'),
      ('venue_authority_event'),
      ('venue_capability_grant'),
      ('venue_published_structured_special'),
      ('venue_published_structured_special_marketing_copy'),
      ('venue_published_special_recurring_pattern'),
      ('venue_published_special_one_off'),
      ('venue_published_structured_special_validity'),
      ('venue_published_structured_special_discovery_eligibility'),
      ('beverage_brewery'),
      ('beverage_style'),
      ('beverage_product'),
      ('venue_published_tap_offering'),
      ('venue_published_tap_offering_validity'),
      ('venue_published_tap_offering_discovery_eligibility'),
      ('subscription_plan_reference'),
      ('business_subscription'),
      ('business_entitlement'),
      ('business_venue_commercial_overlay'),
      ('commercial_overlay_reference'),
      ('business_commercial_overlay_attachment')
  )
select
  'expected_all_drafted_tables_present' as check_name,
  (
    select
      count(*)
    from
      information_schema.tables t
      join expected e on e.name = t.table_name
    where
      t.table_schema = 'public'
      and t.table_type = 'BASE TABLE'
  ) = (
    select
      count(*)
    from
      expected
  ) as ok;

-- ---------------------------------------------------------------------------
-- 2) Domain separation (sample — complements wave-specific checks)
-- ---------------------------------------------------------------------------
select
  'beverage_product_has_no_venue_id' as check_name,
  not exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'beverage_product'
      and column_name = 'venue_id'
  ) as ok
union all
select
  'business_subscription_has_no_owner_account_id',
  not exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'business_subscription'
      and column_name = 'owner_account_id'
  ) as ok
union all
select
  'no_table_named_published_truth_proposal',
  not exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name in ('venue_published_truth', 'published_venue_change')
  ) as ok
union all
select
  'specials_and_tap_roots_not_collapsed',
  not exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name in ('venue_published_special_tap', 'venue_published_tap_special')
  ) as ok;

-- ---------------------------------------------------------------------------
-- 3) Authority wiring: owner membership does not reference venue; grants attach to BVM only
-- ---------------------------------------------------------------------------
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
  'venue_capability_grant_fk_to_bvm_only',
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

-- ---------------------------------------------------------------------------
-- 4) RLS helpers: SECURITY INVOKER (not DEFINER)
-- ---------------------------------------------------------------------------
select
  'rls_helpers_not_security_definer' as check_name,
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

-- ---------------------------------------------------------------------------
-- 5) Published-truth sample: RLS on, no client write policies on profile
-- ---------------------------------------------------------------------------
select
  'venue_published_profile_rls_no_client_writes' as check_name,
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

-- ---------------------------------------------------------------------------
-- 6) Commercial domain: RLS enabled on business-private tables (Wave 11)
-- ---------------------------------------------------------------------------
select
  'rls_enabled_business_subscription' as check_name,
  (
    select
      c.relrowsecurity
    from
      pg_class c
      join pg_namespace n on n.oid = c.relnamespace
    where
      n.nspname = 'public'
      and c.relname = 'business_subscription'
  ) as ok
union all
select
  'rls_enabled_business_entitlement',
  (
    select
      c.relrowsecurity
    from
      pg_class c
      join pg_namespace n on n.oid = c.relnamespace
    where
      n.nspname = 'public'
      and c.relname = 'business_entitlement'
  ) as ok
union all
select
  'rls_enabled_business_commercial_overlay_attachment',
  (
    select
      c.relrowsecurity
    from
      pg_class c
      join pg_namespace n on n.oid = c.relnamespace
    where
      n.nspname = 'public'
      and c.relname = 'business_commercial_overlay_attachment'
  ) as ok;

-- ---------------------------------------------------------------------------
-- 7) Posture: public published-truth reads include anon; commercial plans are not anon-wide
--     (subscription_plan_reference is authenticated-only per 0032 — differs from 0017 public truth)
-- ---------------------------------------------------------------------------
select
  'subscription_plan_reference_no_anon_select_policy' as check_name,
  not exists (
    select
      1
    from
      pg_policies p
    where
      p.schemaname = 'public'
      and p.tablename = 'subscription_plan_reference'
      and p.cmd = 'SELECT'
      and 'anon'::name = any (p.roles)
  ) as ok;
