-- PubPlus — Verification: Wave 11 (commercial / subscription adjacency)
-- Run after migrations 0030–0032.
-- Reinforces: business-first attachment; overlays via management junction; no truth/authority coupling;
-- commercial overlay adjacency separate from published discovery tables.

-- Core tables exist
select
  'subscription_plan_reference exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'subscription_plan_reference'
union all
select
  'business_subscription exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'business_subscription'
union all
select
  'business_entitlement exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'business_entitlement'
union all
select
  'business_venue_commercial_overlay exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'business_venue_commercial_overlay'
union all
select
  'commercial_overlay_reference exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'commercial_overlay_reference'
union all
select
  'business_commercial_overlay_attachment exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'business_commercial_overlay_attachment';

-- Subscription attaches to business, not owner user
select
  'business_subscription has no owner_account_id column' as check_name,
  count(*) = 0 as ok
from
  information_schema.columns
where
  table_schema = 'public'
  and table_name = 'business_subscription'
  and column_name = 'owner_account_id';

select
  'business_subscription fk to business' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
  join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
    and tc.table_schema = kcu.table_schema
where
  tc.table_schema = 'public'
  and tc.table_name = 'business_subscription'
  and tc.constraint_type = 'FOREIGN KEY'
  and kcu.column_name = 'business_id';

-- Entitlements attach to business
select
  'business_entitlement fk to business' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
  join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
    and tc.table_schema = kcu.table_schema
where
  tc.table_schema = 'public'
  and tc.table_name = 'business_entitlement'
  and tc.constraint_type = 'FOREIGN KEY'
  and kcu.column_name = 'business_id';

-- Venue overlay uses management junction, not published-truth tables as parent
select
  'business_venue_commercial_overlay fk to bvm' as check_name,
  count(*) >= 1 as ok
from
  information_schema.table_constraints tc
  join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
    and tc.table_schema = kcu.table_schema
where
  tc.table_schema = 'public'
  and tc.table_name = 'business_venue_commercial_overlay'
  and tc.constraint_type = 'FOREIGN KEY'
  and kcu.column_name = 'business_venue_management_relationship_id';

-- Commercial overlay attachment does not reference published specials/taps (adjacency only)
select
  'business_commercial_overlay_attachment no fk to venue_published_structured_special' as check_name,
  count(*) = 0 as ok
from
  information_schema.table_constraints tc
  join information_schema.constraint_column_usage ccu on tc.constraint_name = ccu.constraint_name
    and tc.table_schema = ccu.table_schema
where
  tc.table_schema = 'public'
  and tc.table_name = 'business_commercial_overlay_attachment'
  and tc.constraint_type = 'FOREIGN KEY'
  and ccu.table_name = 'venue_published_structured_special';

select
  'business_commercial_overlay_attachment no fk to venue_published_tap_offering' as check_name,
  count(*) = 0 as ok
from
  information_schema.table_constraints tc
  join information_schema.constraint_column_usage ccu on tc.constraint_name = ccu.constraint_name
    and tc.table_schema = ccu.table_schema
where
  tc.table_schema = 'public'
  and tc.table_name = 'business_commercial_overlay_attachment'
  and tc.constraint_type = 'FOREIGN KEY'
  and ccu.table_name = 'venue_published_tap_offering';

-- RLS enabled on commercial tables (Supabase posture)
select
  'rls business_subscription' as check_name,
  c.relrowsecurity as ok
from
  pg_class c
  join pg_namespace n on n.oid = c.relnamespace
where
  n.nspname = 'public'
  and c.relname = 'business_subscription';
