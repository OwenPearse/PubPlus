-- PubPlus — Wave 4 / Migration 0010
-- Minimal consumer profile (display/support only; not a personalization anchor) + structured private preferences (default location, notifications).
-- Consumer domain remains separate from published truth, owner/admin accounts, and workflow payloads.
-- RLS: deferred; enforce consumer-only access at application/service layer until policy migration.

-- ---------------------------------------------------------------------------
-- Minimal consumer profile / support-facing identity (not a personalization anchor)
-- ---------------------------------------------------------------------------
create table public.consumer_profile (
  consumer_account_id uuid primary key references public.consumer_account (id) on delete cascade,
  display_name text,
  avatar_storage_ref text,
  updated_at timestamptz not null default now ()
);

comment on table public.consumer_profile is
'Minimal display/support fields only; richer profile, history, and social features stay deferred per MVP scope — not a catch-all prefs blob (DL-023).';

-- ---------------------------------------------------------------------------
-- Default discovery location (first-class; not embedded in profile JSON)
-- ---------------------------------------------------------------------------
create table public.consumer_default_location_preference (
  consumer_account_id uuid primary key references public.consumer_account (id) on delete cascade,
  default_locality_id uuid references public.locality (id) on delete set null,
  default_geographic_region_id uuid references public.geographic_region (id) on delete set null,
  updated_at timestamptz not null default now ()
);

comment on table public.consumer_default_location_preference is
'Structured default locality/region for discovery UX; distinct from any venue published address (Worker B).';

create index idx_consumer_default_location_locality on public.consumer_default_location_preference (default_locality_id)
where
  default_locality_id is not null;

create index idx_consumer_default_location_region on public.consumer_default_location_preference (default_geographic_region_id)
where
  default_geographic_region_id is not null;

-- ---------------------------------------------------------------------------
-- Notification + consent (explicit columns; not an opaque settings blob)
-- ---------------------------------------------------------------------------
create table public.consumer_notification_settings (
  consumer_account_id uuid primary key references public.consumer_account (id) on delete cascade,
  email_marketing_opt_in boolean not null default false,
  email_transactional_opt_in boolean not null default true,
  push_notifications_opt_in boolean not null default true,
  sms_marketing_opt_in boolean not null default false,
  sms_transactional_opt_in boolean not null default true,
  quiet_hours_start_local time without time zone,
  quiet_hours_end_local time without time zone,
  updated_at timestamptz not null default now (),
  constraint consumer_notification_settings_quiet_hours_pair check (
    (
      quiet_hours_start_local is null
      and quiet_hours_end_local is null
    )
    or (
      quiet_hours_start_local is not null
      and quiet_hours_end_local is not null
    )
  )
);

comment on table public.consumer_notification_settings is
'Structured notification toggles and consent flags; channel bodies and cross-user messaging do not belong here (Worker B).';
