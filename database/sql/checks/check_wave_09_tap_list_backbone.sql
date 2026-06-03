-- PubPlus — Verification: Wave 9 (tap list backbone)
-- Run after migrations 0024–0026.
-- Reinforces: beverage reference vs venue offering; traits vs product identity; venue anchor;
-- validity/freshness vs discovery tiers; no implication that a tap row means strong current pour.

-- Core tables exist
select
  'beverage_brewery exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'beverage_brewery'
union all
select
  'beverage_style exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'beverage_style'
union all
select
  'beverage_product exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'beverage_product'
union all
select
  'venue_published_tap_offering exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_tap_offering'
union all
select
  'venue_published_tap_offering_validity exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_tap_offering_validity'
union all
select
  'venue_published_tap_offering_discovery_eligibility exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'venue_published_tap_offering_discovery_eligibility';

-- Product reference is not keyed by venue
select
  'beverage_product has no venue_id column' as check_name,
  count(*) = 0 as ok
from
  information_schema.columns
where
  table_schema = 'public'
  and table_name = 'beverage_product'
  and column_name = 'venue_id';

-- Tap offering anchors canonical venue
select
  'fk_tap_offering_to_venue' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
  join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
    and tc.table_schema = kcu.table_schema
where
  tc.table_schema = 'public'
  and tc.table_name = 'venue_published_tap_offering'
  and tc.constraint_type = 'FOREIGN KEY'
  and kcu.column_name = 'venue_id';

-- Brewery/style are separate tables from tap offering (not embedded trait storage)
select
  'brewery not merged into tap_offering' as check_name,
  count(*) = 0 as ok
from
  information_schema.columns
where
  table_schema = 'public'
  and table_name = 'venue_published_tap_offering'
  and column_name in ('brewery_id', 'brewery_display_name');

-- Offering traits columns exist on venue table, not on beverage_product
select
  'tap offering carries trait flags' as check_name,
  count(*) = 3 as ok
from
  information_schema.columns
where
  table_schema = 'public'
  and table_name = 'venue_published_tap_offering'
  and column_name in ('is_rotating', 'is_guest_tap', 'is_limited_run')
union all
select
  'beverage_product has no is_guest_tap' as check_name,
  count(*) = 0 as ok
from
  information_schema.columns
where
  table_schema = 'public'
  and table_name = 'beverage_product'
  and column_name in ('is_rotating', 'is_guest_tap', 'is_limited_run');

-- Validity companion is separate from discovery eligibility
select
  'validity and eligibility are different tables' as check_name,
  count(*) = 2 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name in (
    'venue_published_tap_offering_validity',
    'venue_published_tap_offering_discovery_eligibility'
  );

-- Discovery eligibility exposes multiple independent booleans (not a single is_active)
select
  'discovery_eligibility has four tier columns' as check_name,
  count(*) = 4 as ok
from
  information_schema.columns
where
  table_schema = 'public'
  and table_name = 'venue_published_tap_offering_discovery_eligibility'
  and column_name in (
    'safe_for_detail_display',
    'safe_for_card_or_list_row',
    'safe_for_filter_search',
    'safe_for_strong_current_tap_claim'
  );

-- Validity carries freshness-related columns distinct from catalog_record_status on parent
select
  'validity has freshness_signal_strength' as check_name,
  count(*) = 1 as ok
from
  information_schema.columns
where
  table_schema = 'public'
  and table_name = 'venue_published_tap_offering_validity'
  and column_name = 'freshness_signal_strength';

-- RLS enabled on tap + beverage reference tables (parity with Wave 8 / 0023)
select
  'rls enabled tap_offering' as check_name,
  c.relrowsecurity as ok
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'venue_published_tap_offering'
union all
select
  'rls enabled beverage_product' as check_name,
  c.relrowsecurity as ok
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'beverage_product';
