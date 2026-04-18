-- PubPlus — Wave 4 / Migration 0011
-- List-native saved venues: named lists/folders and membership in canonical venue identity only.
-- No parallel flat “favorites” shortcut (DL-016).
-- RLS: deferred.

-- ---------------------------------------------------------------------------
-- User-owned lists / folders
-- ---------------------------------------------------------------------------
create table public.saved_list (
  id uuid primary key default gen_random_uuid (),
  consumer_account_id uuid not null references public.consumer_account (id) on delete cascade,
  name text not null,
  sort_order integer not null default 0,
  is_archived boolean not null default false,
  created_at timestamptz not null default now (),
  updated_at timestamptz not null default now ()
);

comment on table public.saved_list is
'Consumer-owned named list/folder; shared/collaborative lists deferred.';

create index idx_saved_list_consumer on public.saved_list (consumer_account_id);

create index idx_saved_list_consumer_sort on public.saved_list (consumer_account_id, sort_order);

-- ---------------------------------------------------------------------------
-- Membership: list ↔ canonical venue (no source-defined venue identity here)
-- ---------------------------------------------------------------------------
create table public.saved_list_membership (
  saved_list_id uuid not null references public.saved_list (id) on delete cascade,
  venue_id uuid not null references public.venue (id) on delete cascade,
  position integer,
  added_at timestamptz not null default now (),
  primary key (saved_list_id, venue_id)
);

comment on table public.saved_list_membership is
'List membership anchored to canonical venue identity only; list-native saved state (DL-016).';

create index idx_saved_list_membership_venue on public.saved_list_membership (venue_id);
