-- PubPlus — minimal demo commercial/subscription rows (local/dev)
-- Depends on: dev_seed_demo_accounts_and_relationships.sql (businesses + BVM rows)
-- Included from database/supabase/seed.sql last when migrations through 0032 are applied (see WAVE_12_FINAL_READINESS_REVIEW.md).
-- Does not simulate webhooks, invoices, or full billing — only exercises Wave 11 tables.

begin;

insert into public.subscription_plan_reference (id, plan_code, display_name, is_active, sort_order)
values
  (
    'pp000001-0001-4001-8001-000000000001',
    'pub_plus_standard',
    'PubPlus Standard',
    true,
    10
  ),
  (
    'pp000002-0002-4002-8002-000000000002',
    'pub_plus_growth',
    'PubPlus Growth',
    true,
    20
  )
on conflict (plan_code) do nothing;

insert into public.business_subscription (
  id,
  business_id,
  subscription_plan_id,
  subscription_status,
  billing_provider,
  external_customer_id,
  external_subscription_id,
  current_period_start,
  current_period_end
)
select
  'sb000001-0001-4001-8001-000000000001',
  'bb000001-0001-4001-8001-000000000001',
  spr.id,
  'active',
  'manual',
  'cus_demo_harbour',
  'sub_demo_harbour_001',
  date_trunc('day', now ()),
  date_trunc('day', now ()) + interval '30 days'
from
  public.subscription_plan_reference spr
where
  spr.plan_code = 'pub_plus_standard'
on conflict (business_id) do update set
  subscription_plan_id = excluded.subscription_plan_id,
  subscription_status = excluded.subscription_status,
  billing_provider = excluded.billing_provider,
  external_customer_id = excluded.external_customer_id,
  external_subscription_id = excluded.external_subscription_id,
  current_period_start = excluded.current_period_start,
  current_period_end = excluded.current_period_end,
  updated_at = now ();

insert into public.business_entitlement (id, business_id, entitlement_code, entitlement_payload)
values
  (
    'be000001-0001-4001-8001-000000000001',
    'bb000001-0001-4001-8001-000000000001',
    'venues.max_managed',
    '{"limit": 25}'::jsonb
  ),
  (
    'be000002-0002-4002-8002-000000000002',
    'bb000001-0001-4001-8001-000000000001',
    'portal.feature.advanced_insights',
    '{"enabled": true}'::jsonb
  )
on conflict (business_id, entitlement_code) do nothing;

insert into public.business_venue_commercial_overlay (
  id,
  business_venue_management_relationship_id,
  overlay_scope,
  overlay_payload,
  overlay_status
)
values
  (
    'vo000001-0001-4001-8001-000000000011',
    'rm000001-0001-4001-8001-000000000011',
    'default',
    '{"listing_highlight": true}'::jsonb,
    'active'
  )
on conflict (business_venue_management_relationship_id, overlay_scope) do update set
  overlay_payload = excluded.overlay_payload,
  overlay_status = excluded.overlay_status,
  updated_at = now ();

insert into public.commercial_overlay_reference (id, overlay_kind_code, display_name, is_active, sort_order)
values
  (
    'cr000001-0001-4001-8001-000000000001',
    'map_pin_sponsor',
    'Map pin sponsorship (demo)',
    true,
    1
  )
on conflict (overlay_kind_code) do nothing;

insert into public.business_commercial_overlay_attachment (
  id,
  business_id,
  venue_id,
  commercial_overlay_reference_id,
  attachment_status,
  valid_from,
  valid_to,
  external_campaign_ref
)
select
  'ca000001-0001-4001-8001-000000000001',
  'bb000001-0001-4001-8001-000000000001',
  'f1111111-1111-4111-8111-111111111101',
  cor.id,
  'active',
  date_trunc('day', now ()),
  date_trunc('day', now ()) + interval '90 days',
  'cmp_demo_map_001'
from
  public.commercial_overlay_reference cor
where
  cor.overlay_kind_code = 'map_pin_sponsor'
on conflict (id) do nothing;

commit;
