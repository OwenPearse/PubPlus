-- PubPlus — Verification: Wave 1 (foundations / anchors + reference spine touched in migrations 0002–0003 partial)
-- Run against public after migrations apply. Expect all checks to pass.

-- Core anchor tables exist
select
  'venue exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue'
union all
select
  'consumer_account exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'consumer_account'
union all
select
  'owner_account exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'owner_account'
union all
select
  'admin_account exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'admin_account'
union all
select
  'business exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'business'
union all
select
  'geographic_region exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'geographic_region'
union all
select
  'locality exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'locality';

-- FK direction: locality -> geographic_region (child points to parent)
select
  'fk_locality_geographic_region' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
  join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
    and tc.table_schema = kcu.table_schema
where
  tc.table_schema = 'public'
  and tc.table_name = 'locality'
  and tc.constraint_type = 'FOREIGN KEY'
  and kcu.column_name = 'geographic_region_id';
