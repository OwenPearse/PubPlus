-- PubPlus — Wave 11 / Migration 0032
-- Minimal sponsored/commercial overlay adjacency (DL-030): adjacent to truth, not merged into specials/taps/profile.
-- No campaign/redemption/analytics engine — attachment rows + lifecycle only.
-- RLS: business-private + admin read; default deny mutations for API roles (service_role orchestrates billing).

-- ---------------------------------------------------------------------------
-- Small vocabulary for future placement/sponsorship kinds (extend by insert)
-- ---------------------------------------------------------------------------
create table public.commercial_overlay_reference (
  id uuid primary key default gen_random_uuid (),
  overlay_kind_code text not null unique,
  display_name text not null,
  is_active boolean not null default true,
  sort_order int not null default 0,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint commercial_overlay_kind_code_format check (
    overlay_kind_code ~ '^[a-z][a-z0-9_]*$'
  )
);

comment on table public.commercial_overlay_reference is
'Catalog of commercial overlay product kinds; separate from venue_published_* and from workflow/moderation objects (DL-030).';

-- ---------------------------------------------------------------------------
-- Business-level attachment; optional venue scope for per-location placement intent
-- ---------------------------------------------------------------------------
create table public.business_commercial_overlay_attachment (
  id uuid primary key default gen_random_uuid (),
  business_id uuid not null references public.business (id) on delete cascade,
  venue_id uuid references public.venue (id) on delete cascade,
  commercial_overlay_reference_id uuid not null references public.commercial_overlay_reference (id) on delete restrict,
  attachment_status text not null default 'draft' check (
    attachment_status in ('draft', 'scheduled', 'active', 'paused', 'ended')
  ),
  valid_from timestamptz,
  valid_to timestamptz,
  external_campaign_ref text,
  notes text,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now (),
  constraint business_commercial_overlay_valid_window check (
    valid_from is null
    or valid_to is null
    or valid_from <= valid_to
  )
);

comment on table public.business_commercial_overlay_attachment is
'Future-ready commercial placement/sponsorship intent; not discovery truth, not confidence, not approval — serving layers must join explicitly (DL-030).';

comment on column public.business_commercial_overlay_attachment.venue_id is
'Optional venue scope; when set, service logic should ensure the business manages the venue via business_venue_management_relationship — not enforced here to avoid brittle circular DDL.';

create index idx_business_commercial_overlay_attachment_business on public.business_commercial_overlay_attachment (
  business_id
);

create index idx_business_commercial_overlay_attachment_venue on public.business_commercial_overlay_attachment (
  venue_id
);

create index idx_business_commercial_overlay_attachment_ref on public.business_commercial_overlay_attachment (
  commercial_overlay_reference_id
);

-- ---------------------------------------------------------------------------
-- RLS: Wave 11 commercial domain (private to business members + admin reads)
-- ---------------------------------------------------------------------------
alter table public.subscription_plan_reference enable row level security;

create policy subscription_plan_reference_select_authenticated on public.subscription_plan_reference for
select
  to authenticated using (true);

alter table public.business_subscription enable row level security;

create policy business_subscription_select_member_or_admin on public.business_subscription for
select
  to authenticated using (
    public.owner_is_member_of_business (business_subscription.business_id)
    or public.is_admin_session ()
  );

alter table public.business_entitlement enable row level security;

create policy business_entitlement_select_member_or_admin on public.business_entitlement for
select
  to authenticated using (
    public.owner_is_member_of_business (business_entitlement.business_id)
    or public.is_admin_session ()
  );

alter table public.business_venue_commercial_overlay enable row level security;

create policy business_venue_commercial_overlay_select_member_or_admin on public.business_venue_commercial_overlay for
select
  to authenticated using (
    exists (
      select
        1
      from
        public.business_venue_management_relationship bvm
      where
        bvm.id = business_venue_commercial_overlay.business_venue_management_relationship_id
        and (
          public.owner_is_member_of_business (bvm.business_id)
          or public.is_admin_session ()
        )
    )
  );

alter table public.commercial_overlay_reference enable row level security;

create policy commercial_overlay_reference_select_authenticated on public.commercial_overlay_reference for
select
  to authenticated using (true);

alter table public.business_commercial_overlay_attachment enable row level security;

create policy business_commercial_overlay_attachment_select_member_or_admin on public.business_commercial_overlay_attachment for
select
  to authenticated using (
    public.owner_is_member_of_business (business_commercial_overlay_attachment.business_id)
    or public.is_admin_session ()
  );
