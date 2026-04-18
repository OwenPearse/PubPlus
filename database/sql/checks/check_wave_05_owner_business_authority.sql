-- PubPlus — Verification: Wave 5 (owner/business authority backbone)
-- Run after migrations 0013–0016.

-- Expected Wave 5 tables exist
select
  'owner_business_membership exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'owner_business_membership'
union all
select
  'business_venue_management_relationship exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'business_venue_management_relationship'
union all
select
  'venue_claim_request exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_claim_request'
union all
select
  'venue_verification_state exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_verification_state'
union all
select
  'venue_management_rights exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_management_rights'
union all
select
  'venue_authority_decision exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_authority_decision'
union all
select
  'venue_authority_event exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_authority_event'
union all
select
  'venue_capability_grant exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_capability_grant';

-- Membership bridge does not carry venue_id (no membership→venue shortcut)
select
  'owner_business_membership_has_no_venue_id' as check_name,
  not exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'owner_business_membership'
      and column_name = 'venue_id'
  ) as ok;

-- Capability grants attach through managed-venue relationship (Postgres catalog)
select
  'fk_venue_capability_grant_to_business_venue_management_relationship' as check_name,
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

-- venue_capability_grant does not reference venue directly
select
  'venue_capability_grant_no_direct_fk_to_venue' as check_name,
  not exists (
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
      and ref.relname = 'venue'
  ) as ok;

-- Distinct structures: claim, verification, management rights, grants are separate tables
select
  'claim_verification_rights_grants_are_distinct_tables' as check_name,
  (
    select
      count(*)
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name in (
        'venue_claim_request',
        'venue_verification_state',
        'venue_management_rights',
        'venue_capability_grant'
      )
  ) = 4 as ok;

-- business_venue_management_relationship links business and venue explicitly
select
  'bvm_relationship_fk_to_business_and_venue' as check_name,
  (
    select
      count(*)
    from
      pg_constraint c
      join pg_class rel on rel.oid = c.conrelid
      join pg_namespace n on n.oid = rel.relnamespace
      join pg_class ref on ref.oid = c.confrelid
      join pg_namespace nref on nref.oid = ref.relnamespace
    where
      n.nspname = 'public'
      and rel.relname = 'business_venue_management_relationship'
      and c.contype = 'f'
      and nref.nspname = 'public'
      and ref.relname in ('business', 'venue')
  ) >= 2 as ok;

-- Optional claim provenance column present on management relationship
select
  'bvm_relationship_has_source_claim_column' as check_name,
  exists (
    select
      1
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'business_venue_management_relationship'
      and column_name = 'source_venue_claim_request_id'
  ) as ok;
