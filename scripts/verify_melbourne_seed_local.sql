-- Verification queries for Melbourne seed (run via psql against DB that received dev_seed_melbourne_*)
\set ON_ERROR_STOP on

-- 1) Locality / suburb filter (Richmond)
SELECT count(*) AS melbourne_venues_richmond
FROM public.venue v
INNER JOIN public.venue_published_location vpl ON vpl.venue_id = v.id
INNER JOIN public.locality l ON l.id = vpl.locality_id
WHERE lower(l.name) = lower('Richmond')
  AND v.id::text LIKE 'f1111111-1111-4111-8111-0000%';

-- 2) Viewport (from melbourne_inner_seed_venues.json test_geography)
SELECT count(*) AS melbourne_venues_in_viewport
FROM public.venue v
INNER JOIN public.venue_published_map_point m ON m.venue_id = v.id
WHERE v.id::text LIKE 'f1111111-1111-4111-8111-0000%'
  AND m.latitude::float8 BETWEEN -37.87 AND -37.76
  AND m.longitude::float8 BETWEEN 144.92 AND 145.05;

-- 3) One venue read stack (fixed id index 1)
SELECT
  v.id,
  p.display_name,
  l.name AS suburb,
  m.latitude,
  m.longitude
FROM public.venue v
INNER JOIN public.venue_published_profile p ON p.venue_id = v.id
INNER JOIN public.venue_published_location vpl ON vpl.venue_id = v.id
INNER JOIN public.locality l ON l.id = vpl.locality_id
INNER JOIN public.venue_published_map_point m ON m.venue_id = v.id
WHERE v.id = 'f1111111-1111-4111-8111-000000000001';

-- 4) Late-night crosses_midnight (3 venues, indices 1-3)
SELECT v.id, h.crosses_midnight, h.opens_at, h.closes_at, h.day_of_week
FROM public.venue_hours_regular h
INNER JOIN public.venue v ON v.id = h.venue_id
WHERE v.id::text LIKE 'f1111111-1111-4111-8111-0000%'
  AND h.crosses_midnight = true
ORDER BY v.id;

-- 5) Exception rows
SELECT e.venue_id, e.exception_kind, e.start_date, e.end_date
FROM public.venue_hours_exception e
WHERE e.venue_id::text LIKE 'f1111111-1111-4111-8111-0000%'
ORDER BY e.venue_id;

-- 6) Sparse / partial uncertainty
SELECT u.venue_id, u.uncertainty_level, u.notes
FROM public.venue_hours_uncertainty u
WHERE u.venue_id::text LIKE 'f1111111-1111-4111-8111-0000%'
  AND u.uncertainty_level = 'partial'
ORDER BY u.venue_id;

-- 7) Structured specials (Melbourne block)
SELECT s.venue_id, s.structured_kind, s.short_label
FROM public.venue_published_structured_special s
WHERE s.venue_id::text LIKE 'f1111111-1111-4111-8111-0000%'
ORDER BY s.venue_id, s.structured_kind;

SELECT 'verify_done' AS status;
