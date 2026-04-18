-- PubPlus — Verification: Wave 10 (post-wave cleanup and hardening)
-- Run after migrations 0027–0029 (depends on 0026 and earlier).
-- Confirms: purposeful indexes exist; optional CHECK constraints applied; no domain-collapse signals.

-- Representative new indexes from 0027
select
  'index_exists_idx_venue_published_attribute_value_allowed_value_id' as check_name,
  exists (
    select
      1
    from
      pg_catalog.pg_indexes
    where
      schemaname = 'public'
      and indexname = 'idx_venue_published_attribute_value_allowed_value_id'
  ) as ok
union all
select
  'index_exists_idx_venue_proposal_staging_attribute_definition_id',
  exists (
    select
      1
    from
      pg_catalog.pg_indexes
    where
      schemaname = 'public'
      and indexname = 'idx_venue_proposal_staging_attribute_definition_id'
  ) as ok
union all
select
  'index_exists_idx_venue_change_proposal_superseded_by',
  exists (
    select
      1
    from
      pg_catalog.pg_indexes
    where
      schemaname = 'public'
      and indexname = 'idx_venue_change_proposal_superseded_by'
  ) as ok
union all
select
  'index_exists_idx_venue_publish_event_venue_change_proposal',
  exists (
    select
      1
    from
      pg_catalog.pg_indexes
    where
      schemaname = 'public'
      and indexname = 'idx_venue_publish_event_venue_change_proposal'
  ) as ok
union all
select
  'index_exists_idx_venue_verification_state_context_claim',
  exists (
    select
      1
    from
      pg_catalog.pg_indexes
    where
      schemaname = 'public'
      and indexname = 'idx_venue_verification_state_context_claim'
  ) as ok
union all
select
  'index_exists_idx_venue_published_structured_special_venue_active_catalog',
  exists (
    select
      1
    from
      pg_catalog.pg_indexes
    where
      schemaname = 'public'
      and indexname = 'idx_venue_published_structured_special_venue_active_catalog'
  ) as ok
union all
select
  'index_exists_idx_venue_published_tap_offering_venue_active_catalog',
  exists (
    select
      1
    from
      pg_catalog.pg_indexes
    where
      schemaname = 'public'
      and indexname = 'idx_venue_published_tap_offering_venue_active_catalog'
  ) as ok;

-- Optional CHECK constraints from 0028
select
  'check_recurring_pattern_dow_values_in_week' as check_name,
  exists (
    select
      1
    from
      pg_catalog.pg_constraint c
      join pg_catalog.pg_class rel on rel.oid = c.conrelid
      join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
    where
      n.nspname = 'public'
      and rel.relname = 'venue_published_special_recurring_pattern'
      and c.conname = 'recurring_pattern_dow_values_in_week'
  ) as ok
union all
select
  'check_validity_fully_bounded_requires_bounds',
  exists (
    select
      1
    from
      pg_catalog.pg_constraint c
      join pg_catalog.pg_class rel on rel.oid = c.conrelid
      join pg_catalog.pg_namespace n on n.oid = rel.relnamespace
    where
      n.nspname = 'public'
      and rel.relname = 'venue_published_structured_special_validity'
      and c.conname = 'venue_published_structured_special_validity_fully_bounded_requires_bounds'
  ) as ok;

-- Domain separation spot checks (beverage product still has no venue_id)
select
  'beverage_product_still_has_no_venue_id' as check_name,
  not exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'beverage_product'
      and column_name = 'venue_id'
  ) as ok;
