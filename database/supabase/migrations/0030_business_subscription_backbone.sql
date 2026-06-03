-- PubPlus — Wave 11 / Migration 0030
-- Business-level subscription backbone (DL-024, DL-030): attaches to business, not owner users or venue truth.
-- No billing event/webhook ingestion — external references are opaque identifiers for provider reconciliation only.
-- RLS: deferred to migration 0032.

-- ---------------------------------------------------------------------------
-- Plan catalog (reference rows; not consumer “truth” and not authority)
-- ---------------------------------------------------------------------------
create table public.subscription_plan_reference (
  id uuid primary key default gen_random_uuid (),
  plan_code text not null unique,
  display_name text not null,
  is_active boolean not null default true,
  sort_order int not null default 0,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.subscription_plan_reference is
'Internal plan catalog for portal/billing UI; does not imply published venue truth, discovery confidence, or management rights (DL-023, DL-030).';

-- ---------------------------------------------------------------------------
-- One current subscription row per business (v1 read model; history deferred)
-- ---------------------------------------------------------------------------
create table public.business_subscription (
  id uuid primary key default gen_random_uuid (),
  business_id uuid not null unique references public.business (id) on delete cascade,
  subscription_plan_id uuid references public.subscription_plan_reference (id) on delete set null,
  subscription_status text not null default 'none' check (
    subscription_status in (
      'none',
      'trialing',
      'active',
      'past_due',
      'paused',
      'canceled',
      'expired'
    )
  ),
  billing_provider text check (
    billing_provider is null
    or billing_provider in ('stripe', 'manual', 'other')
  ),
  external_customer_id text,
  external_subscription_id text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  canceled_at timestamptz,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.business_subscription is
'Business-scoped commercial subscription state; does not grant venue management rights or truth-editing power — authority remains on business_venue_management_relationship and grants (DL-021, DL-024).';

comment on column public.business_subscription.subscription_status is
'Commercial lifecycle only; orthogonal to publish/moderation/truth lifecycles (see state_lifecycle_model_summary commercial/subscription section).';

comment on column public.business_subscription.billing_provider is
'Coarse provider label for reconciliation; no webhook/event tables in this tranche.';

create index idx_business_subscription_plan on public.business_subscription (subscription_plan_id);

create index idx_business_subscription_status on public.business_subscription (subscription_status);

comment on table public.business is
'Operator/business anchor; primary attachment point for subscription_plan_reference-backed business_subscription rows (Wave 11).';
