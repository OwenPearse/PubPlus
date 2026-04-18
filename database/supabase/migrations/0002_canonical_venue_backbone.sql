-- PubPlus — Tranche 1 / Migration 0002
-- Canonical venue identity + logical account-domain anchors + business org anchor.
-- No published field payloads here (those are separate tables).
-- Consumer private feature tables (profile, lists, prefs) are deferred to a later tranche.

-- ---------------------------------------------------------------------------
-- Canonical venue identity (root anchor for all venue-linked state)
-- ---------------------------------------------------------------------------
create table public.venue (
  id uuid primary key default gen_random_uuid (),
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.venue is
'Canonical venue identity: durable, source-agnostic; one row per real venue at one physical location.';

-- ---------------------------------------------------------------------------
-- Logical account domains (separate tables per architecture; auth is not the permission model)
-- ---------------------------------------------------------------------------
create table public.consumer_account (
  id uuid primary key default gen_random_uuid (),
  auth_user_id uuid not null unique references auth.users (id) on delete cascade,
  created_at timestamptz not null default now ()
);

comment on table public.consumer_account is
'Consumer domain identity; links to auth subject. Not a permission store.';

create table public.owner_account (
  id uuid primary key default gen_random_uuid (),
  auth_user_id uuid not null unique references auth.users (id) on delete cascade,
  created_at timestamptz not null default now ()
);

comment on table public.owner_account is
'Owner portal domain identity; links to auth subject.';

create table public.admin_account (
  id uuid primary key default gen_random_uuid (),
  auth_user_id uuid not null unique references auth.users (id) on delete cascade,
  created_at timestamptz not null default now ()
);

comment on table public.admin_account is
'Internal reviewer/admin identity; used by Stage-2 reviews and future authority decisions.';

-- ---------------------------------------------------------------------------
-- Business entity (first-class org anchor; commercial detail deferred)
-- ---------------------------------------------------------------------------
create table public.business (
  id uuid primary key default gen_random_uuid (),
  display_name text not null,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.business is
'Operator/business anchor; subscriptions and team structures attach here in later tranches.';

create index idx_business_display_name on public.business (display_name);
