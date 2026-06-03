-- PubPlus — Supabase seed entry point (local / dev / demo)
--
-- Composed seed order (each file documents its own dependencies):
--   1) reference geography + attribute defs + external source catalog
--   1b) Victoria + inner-Melbourne localities (for Melbourne published venue rows)
--   2) demo published venues (direct published-truth inserts — dev convenience only)
--   3) demo auth users + logical accounts + owner/business/authority + light consumer private rows
--   3b) Melbourne inner-city test venues (Stage 3 discovery / open-now)
--   4) demo structured specials (requires migrations through 0023)
--   4b) Melbourne structured specials (same migration level as 4)
--   5) demo tap list (requires migrations through 0026)
--   6) demo commercial/subscription adjacency (requires migrations through 0032 + step 3)
--
-- Paths use psql \ir (include relative), resolved relative to this file’s directory
-- (database/supabase/ → database/sql/seeds/).
-- If your Supabase project keeps seed.sql elsewhere, copy these includes or run the files
-- under database/sql/seeds/ manually in the same order.
--
-- Comment out steps 4–6 if your database has not applied the extended migrations yet.
--
-- Demo logins (when auth seed succeeds):
--   consumer1@demo.pubplus.local / demo-password-123
--   owner1@demo.pubplus.local / demo-password-123
--   admin1@demo.pubplus.local / demo-password-123

\echo 'PubPlus: loading dev_seed_reference_minimum.sql'
\ir ../sql/seeds/dev_seed_reference_minimum.sql

\echo 'PubPlus: loading dev_seed_mvp_filter_taxonomy.sql (Search filter reference rows)'
\ir ../sql/seeds/dev_seed_mvp_filter_taxonomy.sql

\echo 'PubPlus: loading dev_seed_reference_melbourne_localities.sql (VIC + inner suburbs)'
\ir ../sql/seeds/dev_seed_reference_melbourne_localities.sql

\echo 'PubPlus: loading dev_seed_demo_venues.sql'
\ir ../sql/seeds/dev_seed_demo_venues.sql

\echo 'PubPlus: loading dev_seed_demo_accounts_and_relationships.sql'
\ir ../sql/seeds/dev_seed_demo_accounts_and_relationships.sql

\echo 'PubPlus: loading dev_seed_melbourne_inner_venues.sql'
\ir ../sql/seeds/dev_seed_melbourne_inner_venues.sql

\echo 'PubPlus: loading dev_seed_mvp_feature_attribute_values.sql (Search feature filter QA)'
\ir ../sql/seeds/dev_seed_mvp_feature_attribute_values.sql

\echo 'PubPlus: loading dev_seed_demo_specials.sql'
\ir ../sql/seeds/dev_seed_demo_specials.sql

\echo 'PubPlus: loading dev_seed_melbourne_inner_specials.sql'
\ir ../sql/seeds/dev_seed_melbourne_inner_specials.sql

\echo 'PubPlus: loading dev_seed_demo_taps.sql'
\ir ../sql/seeds/dev_seed_demo_taps.sql

\echo 'PubPlus: loading dev_seed_demo_commercial.sql'
\ir ../sql/seeds/dev_seed_demo_commercial.sql

\echo 'PubPlus: seed composition finished.'
