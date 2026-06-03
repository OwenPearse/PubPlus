-- PubPlus — Tranche 1 / Migration 0001
-- Extensions and base types used by later migrations.
-- RLS: not enabled here; apply in later security-focused migrations.

-- UUID primary keys use gen_random_uuid() (core Postgres; available on Supabase).
-- Add optional extensions (pg_trgm, postgis, etc.) only when features require them.
