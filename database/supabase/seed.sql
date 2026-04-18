-- PubPlus — Supabase seed entry point (local / dev / demo)
--
-- This file composes the minimal first-tranche seeds in dependency order:
--   1) reference geography + attribute defs + external source catalog
--   2) demo published venues (direct published-truth inserts — dev convenience only)
--   3) demo auth users + logical accounts + owner/business/authority + light consumer private rows
--
-- Paths use psql \ir (include relative), resolved relative to this file’s directory.
-- If your Supabase project keeps seed.sql elsewhere, copy these includes or run the three files
-- under database/sql/seeds/ manually in the same order.
--
-- Demo logins (when auth seed succeeds):
--   consumer1@demo.pubplus.local / demo-password-123
--   owner1@demo.pubplus.local / demo-password-123
--   admin1@demo.pubplus.local / demo-password-123

\echo 'PubPlus: loading dev_seed_reference_minimum.sql'
\ir ../sql/seeds/dev_seed_reference_minimum.sql

\echo 'PubPlus: loading dev_seed_demo_venues.sql'
\ir ../sql/seeds/dev_seed_demo_venues.sql

\echo 'PubPlus: loading dev_seed_demo_accounts_and_relationships.sql'
\ir ../sql/seeds/dev_seed_demo_accounts_and_relationships.sql

\echo 'PubPlus: seed composition finished.'
