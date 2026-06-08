-- PubPlus — Migration 0034
-- Owner-managed venue photos: metadata in Postgres, files in Supabase Storage (venue-media bucket).

-- ---------------------------------------------------------------------------
-- Published venue media metadata (profile + gallery images)
-- ---------------------------------------------------------------------------
create table public.venue_published_media (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venue (id) on delete cascade,
  storage_bucket text not null,
  storage_path text not null,
  media_kind text not null default 'image' check (media_kind in ('image')),
  purpose text not null check (purpose in ('profile', 'gallery')),
  caption text,
  alt_text text,
  sort_order int not null default 0,
  catalog_record_status text not null default 'active' check (
    catalog_record_status in ('active', 'retired')
  ),
  uploaded_by_owner_account_id uuid references public.owner_account (id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint venue_published_media_storage_path_unique unique (storage_bucket, storage_path)
);

comment on table public.venue_published_media is
'Published venue image metadata; binary assets live in Supabase Storage (venue-media bucket).';

create index idx_venue_published_media_venue_id on public.venue_published_media (venue_id);

create index idx_venue_published_media_venue_active on public.venue_published_media (venue_id, catalog_record_status)
where
  catalog_record_status = 'active';

-- ---------------------------------------------------------------------------
-- Backend-issued upload intents (prevents arbitrary storage path writes)
-- ---------------------------------------------------------------------------
create table public.owner_venue_media_upload_intent (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venue (id) on delete cascade,
  owner_account_id uuid not null references public.owner_account (id) on delete cascade,
  purpose text not null check (purpose in ('profile', 'gallery')),
  storage_bucket text not null,
  storage_path text not null,
  content_type text not null,
  expires_at timestamptz not null,
  committed_at timestamptz,
  created_at timestamptz not null default now()
);

comment on table public.owner_venue_media_upload_intent is
'Short-lived owner upload intents; consumed when metadata row is committed after Storage upload.';

create index idx_owner_venue_media_upload_intent_venue on public.owner_venue_media_upload_intent (venue_id, owner_account_id);

-- ---------------------------------------------------------------------------
-- RLS: published media readable; writes via Django service role only
-- ---------------------------------------------------------------------------
alter table public.venue_published_media enable row level security;

create policy venue_published_media_select_public on public.venue_published_media for
select
  to anon,
  authenticated using (catalog_record_status = 'active');

alter table public.owner_venue_media_upload_intent enable row level security;

-- No client policies on upload intents — backend service role only.

-- ---------------------------------------------------------------------------
-- Supabase Storage bucket (public read for consumer listing images)
-- Writes are not open to browser clients; owners upload via backend-signed URLs.
-- If storage schema is unavailable (plain Postgres test DB), skip gracefully.
-- ---------------------------------------------------------------------------
do $$
begin
  if exists (
    select 1
    from information_schema.schemata
    where schema_name = 'storage'
  ) then
    insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
    values (
      'venue-media',
      'venue-media',
      true,
      5242880,
      array['image/jpeg', 'image/png', 'image/webp']
    )
    on conflict (id) do update
    set
      public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;
  end if;
end
$$;
