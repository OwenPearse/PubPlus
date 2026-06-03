-- PubPlus — Verification: Wave 8 (structured specials / promotions backbone)
-- Run after migrations 0021–0023.
-- Reinforces: structured truth vs marketing copy; recurring vs one-off; venue anchor;
-- validity/eligibility layers; no commercial columns in this truth model; RLS SELECT on published rows.

-- Core tables exist
select
  'venue_published_structured_special exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_structured_special'
union all
select
  'marketing_copy table exists (separate from structured parent)' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_structured_special_marketing_copy'
union all
select
  'recurring pattern table exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_special_recurring_pattern'
union all
select
  'one_off table exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_special_one_off'
union all
select
  'validity table exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_structured_special_validity'
union all
select
  'discovery_eligibility table exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_structured_special_discovery_eligibility';

-- Structured parent anchors canonical venue
select
  'fk_structured_special_to_venue' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
  join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
    and tc.table_schema = kcu.table_schema
where
  tc.table_schema = 'public'
  and tc.table_name = 'venue_published_structured_special'
  and tc.constraint_type = 'FOREIGN KEY'
  and kcu.column_name = 'venue_id';

-- Marketing copy is 1:1 child, not the discovery driver
select
  'fk_marketing_copy_to_structured_special' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
where
  tc.table_schema = 'public'
  and tc.table_name = 'venue_published_structured_special_marketing_copy'
  and tc.constraint_type = 'FOREIGN KEY';

-- Subtype tables attach to structured parent only
select
  'fk_recurring_to_structured_special' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
where
  tc.table_schema = 'public'
  and tc.table_name = 'venue_published_special_recurring_pattern'
  and tc.constraint_type = 'FOREIGN KEY'
union all
select
  'fk_one_off_to_structured_special' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
where
  tc.table_schema = 'public'
  and tc.table_name = 'venue_published_special_one_off'
  and tc.constraint_type = 'FOREIGN KEY';

-- Eligibility: four independent tier columns (not a single omni-boolean)
select
  'discovery_eligibility_has_four_tier_columns' as check_name,
  count(*) = 4 as ok
from
  information_schema.columns
where
  table_schema = 'public'
  and table_name = 'venue_published_structured_special_discovery_eligibility'
  and column_name in (
    'safe_for_detail_display',
    'safe_for_card_badge',
    'safe_for_filter_search',
    'safe_for_active_now_ranking'
  );

-- Validity layer separate from eligibility (distinct tables)
select
  'validity_and_eligibility_are_separate_tables' as check_name,
  (
    select
      count(*)
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name in (
        'venue_published_structured_special_validity',
        'venue_published_structured_special_discovery_eligibility'
      )
  ) = 2 as ok;

-- Parent distinguishes recurring vs one-off
select
  'parent_has_schedule_class' as check_name,
  exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'venue_published_structured_special'
      and column_name = 'schedule_class'
  ) as ok;

-- Weak timing suppression signal exists (conservative path)
select
  'validity_has_suppress_weak_timing' as check_name,
  exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'venue_published_structured_special_validity'
      and column_name = 'suppress_due_to_weak_or_stale_timing'
  ) as ok;

-- No obvious commercial overlay columns on published structured-special tables (spot check)
select
  'no_sponsored_column_on_structured_special_parent' as check_name,
  not exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'venue_published_structured_special'
      and column_name in ('sponsored', 'boost_rank', 'campaign_id', 'subscription_tier')
  ) as ok;

-- RLS enabled on published special tables (sample)
select
  'rls_enabled_structured_special' as check_name,
  coalesce(
    (
      select
        c.relrowsecurity
      from
        pg_catalog.pg_class c
        join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where
        n.nspname = 'public'
        and c.relname = 'venue_published_structured_special'
    ),
    false
  ) as ok
union all
select
  'rls_enabled_discovery_eligibility' as check_name,
  coalesce(
    (
      select
        c.relrowsecurity
      from
        pg_catalog.pg_class c
        join pg_catalog.pg_namespace n on n.oid = c.relnamespace
      where
        n.nspname = 'public'
        and c.relname = 'venue_published_structured_special_discovery_eligibility'
    ),
    false
  ) as ok;

-- Published catalog status is distinct from active-now tier column (both exist)
select
  'catalog_status_and_active_now_tier_both_exist' as check_name,
  exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'venue_published_structured_special'
      and column_name = 'catalog_record_status'
  )
  and exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'venue_published_structured_special_discovery_eligibility'
      and column_name = 'safe_for_active_now_ranking'
  ) as ok;
