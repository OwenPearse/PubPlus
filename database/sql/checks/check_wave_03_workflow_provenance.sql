-- PubPlus — Verification: Wave 3 (intake, proposals, review, publish, evidence, audit)
-- Run after migrations 0007–0009.
-- Reinforces: raw intake + proposals + reviews + lineage + evidence + audit are distinct; submissions are not published truth.

select
  'venue_change_proposal exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_change_proposal'
union all
select
  'proposal_review exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'proposal_review'
union all
select
  'venue_publish_event exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_publish_event'
union all
select
  'evidence_item exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'evidence_item'
union all
select
  'audit_event exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'audit_event';

-- Staging tables must not be named like published truth
select
  'staging_profile_is_distinct_from_published' as check_name,
  not exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name = 'venue_published_staging_profile'
  ) as ok;

-- Proposal anchors to venue
select
  'fk_proposal_to_venue' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
where
  tc.table_schema = 'public'
  and tc.table_name = 'venue_change_proposal'
  and tc.constraint_type = 'FOREIGN KEY';

-- Raw intake + provenance catalog (source registry)
select
  'raw_venue_intake_record_exists' as check_name,
  exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name = 'raw_venue_intake_record'
  ) as ok
union all
select
  'external_data_source_exists',
  exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name = 'external_data_source'
  ) as ok;

-- Staging payloads are explicit (not published-truth tables)
select
  'staging_tables_exist_for_proposal_packages' as check_name,
  (
    select
      count(*)
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name in (
        'venue_proposal_staging_profile',
        'venue_proposal_staging_location',
        'venue_proposal_staging_attribute',
        'venue_proposal_staging_hours'
      )
  ) = 4 as ok;

-- Publish lineage / history is separate from current-state published tables
select
  'venue_published_row_history_exists' as check_name,
  exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name = 'venue_published_row_history'
  ) as ok;
