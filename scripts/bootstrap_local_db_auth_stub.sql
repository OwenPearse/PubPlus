-- Minimal auth stub so public schema migrations that reference auth.users (0002) apply on plain Postgres.
-- Not a Supabase replacement; for local migration + published-truth seed smoke tests only.
create schema if not exists auth;
create table if not exists auth.users (
  id uuid primary key
);
