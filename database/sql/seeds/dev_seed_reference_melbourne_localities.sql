-- PubPlus — VIC + Melbourne inner suburbs (dev seed, idempotent).
-- Source list from dataCollection/melbourne_inner_seed_venues.json

begin;

insert into public.geographic_region (
  id,
  parent_region_id,
  name,
  region_code,
  region_level
)
values (
  '11111111-1111-4111-8111-111111111103',
  '11111111-1111-4111-8111-111111111101',
  'Victoria',
  'VIC',
  'state'
)
on conflict (id) do update set
  parent_region_id = excluded.parent_region_id,
  name = excluded.name,
  region_code = excluded.region_code,
  region_level = excluded.region_level;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000001',
  '11111111-1111-4111-8111-111111111103',
  'Abbotsford',
  'abbotsford'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000002',
  '11111111-1111-4111-8111-111111111103',
  'Brunswick',
  'brunswick'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000003',
  '11111111-1111-4111-8111-111111111103',
  'Brunswick West',
  'brunswick-west'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000004',
  '11111111-1111-4111-8111-111111111103',
  'Carlton',
  'carlton'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000005',
  '11111111-1111-4111-8111-111111111103',
  'Carlton North',
  'carlton-north'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000006',
  '11111111-1111-4111-8111-111111111103',
  'Collingwood',
  'collingwood'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000007',
  '11111111-1111-4111-8111-111111111103',
  'Cremorne',
  'cremorne'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000008',
  '11111111-1111-4111-8111-111111111103',
  'Docklands',
  'docklands'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000009',
  '11111111-1111-4111-8111-111111111103',
  'Fitzroy',
  'fitzroy'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-00000000000a',
  '11111111-1111-4111-8111-111111111103',
  'Fitzroy North',
  'fitzroy-north'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-00000000000b',
  '11111111-1111-4111-8111-111111111103',
  'Hawthorn',
  'hawthorn'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-00000000000c',
  '11111111-1111-4111-8111-111111111103',
  'Melbourne',
  'melbourne'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-00000000000d',
  '11111111-1111-4111-8111-111111111103',
  'Port Melbourne',
  'port-melbourne'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-00000000000e',
  '11111111-1111-4111-8111-111111111103',
  'Prahran',
  'prahran'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-00000000000f',
  '11111111-1111-4111-8111-111111111103',
  'Richmond',
  'richmond'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000010',
  '11111111-1111-4111-8111-111111111103',
  'South Melbourne',
  'south-melbourne'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000011',
  '11111111-1111-4111-8111-111111111103',
  'South Yarra',
  'south-yarra'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000012',
  '11111111-1111-4111-8111-111111111103',
  'St Kilda',
  'st-kilda'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000013',
  '11111111-1111-4111-8111-111111111103',
  'West Melbourne',
  'west-melbourne'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

insert into public.locality (
  id,
  geographic_region_id,
  name,
  slug
)
values (
  '22222222-2222-4222-8222-000000000014',
  '11111111-1111-4111-8111-111111111103',
  'Windsor',
  'windsor'
)
on conflict (id) do update set
  geographic_region_id = excluded.geographic_region_id,
  name = excluded.name,
  slug = excluded.slug;

commit;
