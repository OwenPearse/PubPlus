-- PubPlus — Verification: Wave 4 (consumer private state, saved lists, consumer submissions)
-- Run after migrations 0010–0012.
-- Reinforces: profile vs default location vs notifications are explicit; lists are list-native; venue membership uses canonical venue; consumer submissions are not public truth.

-- Expected consumer-private tables exist
select
  'consumer_profile exists' as check_name,
  count(*) = 1 as ok
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'consumer_profile'
union all
select
  'consumer_default_location_preference exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'consumer_default_location_preference'
union all
select
  'consumer_notification_settings exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'consumer_notification_settings'
union all
select
  'saved_list exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'saved_list'
union all
select
  'saved_list_membership exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'saved_list_membership'
union all
select
  'consumer_submission_extension exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'consumer_submission_extension'
union all
select
  'consumer_workflow_submission exists',
  count(*) = 1
from
  information_schema.tables
where
  table_schema = 'public'
  and table_name = 'consumer_workflow_submission';

-- No flat favorites shortcut table in this tranche
select
  'no_consumer_favorite_flag_table' as check_name,
  not exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name in (
        'consumer_favorite_venue',
        'saved_venue_flat',
        'consumer_venue_favorite'
      )
  ) as ok;

-- Default location preference uses structured FK columns (not a single prefs json blob column)
select
  'default_location_has_structured_fk_columns' as check_name,
  (
    select
      count(*)
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'consumer_default_location_preference'
      and column_name in ('default_locality_id', 'default_geographic_region_id')
  ) = 2 as ok;

-- Notification settings expose explicit consent/channel columns
select
  'notification_settings_has_explicit_consent_columns' as check_name,
  (
    select
      count(*)
    from
      information_schema.columns
    where
      table_schema = 'public'
      and table_name = 'consumer_notification_settings'
      and column_name in (
        'email_marketing_opt_in',
        'email_transactional_opt_in',
        'sms_marketing_opt_in',
        'sms_transactional_opt_in',
        'push_notifications_opt_in'
      )
  ) = 5 as ok;

-- Saved list membership references canonical venue (Postgres catalog)
select
  'fk_saved_list_membership_to_venue' as check_name,
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
      and rel.relname = 'saved_list_membership'
      and c.contype = 'f'
      and nref.nspname = 'public'
      and ref.relname = 'venue'
  ) as ok;

-- Submissions tranche does not introduce published-truth tables
select
  'consumer_submissions_not_named_as_published_truth' as check_name,
  not exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name in (
        'consumer_workflow_submission_published',
        'venue_published_consumer_submission'
      )
  ) as ok;

-- Profile is not merged into notification settings (split tables)
select
  'profile_and_notification_settings_are_split' as check_name,
  exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name = 'consumer_profile'
  )
  and exists (
    select
      1
    from
      information_schema.tables
    where
      table_schema = 'public'
      and table_name = 'consumer_notification_settings'
  ) as ok;
