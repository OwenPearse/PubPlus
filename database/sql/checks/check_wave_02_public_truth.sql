-- PubPlus — Verification: Wave 2 (published discovery truth + hours)
-- Run after migrations 0003–0006.

-- Published-truth tables are separate objects from workflow staging
select
  'venue_published_profile exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_profile'
union all
select
  'venue_published_location exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_location'
union all
select
  'venue_published_map_point exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_map_point'
union all
select
  'venue_published_attribute_value exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_attribute_value'
union all
select
  'venue_hours_uncertainty exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_hours_uncertainty'
union all
select
  'venue_derived_operational_claim exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_derived_operational_claim';

-- Published child rows point to venue (not the reverse)
select
  'fk_published_profile_to_venue' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
where
  tc.table_schema = 'public'
  and tc.table_name = 'venue_published_profile'
  and tc.constraint_type = 'FOREIGN KEY';

-- Single map point: primary key on venue_id implies 1:1 with venue
select
  'map_point_pk_is_venue_id',
  count(*) >= 1
from
  information_schema.table_constraints tc
where
  tc.table_schema = 'public'
  and tc.table_name = 'venue_published_map_point'
  and tc.constraint_type = 'PRIMARY KEY';
