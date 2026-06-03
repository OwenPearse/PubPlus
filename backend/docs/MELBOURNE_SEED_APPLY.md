# Applying the Melbourne dev seed to a database

The frozen selection and idempotent SQL live under `dataCollection/melbourne_inner_seed_venues.json` and `database/sql/seeds/dev_seed_*melbourne*`. The normal project entry point is [database/supabase/seed.sql](../../database/supabase/seed.sql), which includes Melbourne after reference data and the Sydney demo shell.

## Option A — Supabase (linked project or local Supabase)

When the [Supabase CLI](https://supabase.com/docs/guides/cli) is installed and the project is linked, apply everything the backend expects:

1. `cd` to the repo (or the directory that contains `supabase/config.toml` if you keep it elsewhere).
2. Ensure migrations are applied, then run seeds as your workflow defines (e.g. `supabase db reset` for a disposable local instance, or `supabase db push` + seed only in managed environments per team policy).
3. Confirm `seed.sql` actually ran (it must load `dev_seed_reference_melbourne_localities.sql`, `dev_seed_melbourne_inner_venues.sql`, and `dev_seed_melbourne_inner_specials.sql` in order).

**Shared dev Supabase** requires network access, project credentials, and org approval; the agent environment cannot do this on your behalf.

## Option B — Local Docker Postgres (no Supabase stack)

Use this when you only need a **local** database with the **same public schema and Melbourne rows** for SQL-level checks. This path runs **migrations** plus `dev_seed_reference_minimum` and the three Melbourne seed files. It does **not** run the full `seed.sql` (Sydney demo venues, auth `auth.users` inserts, taps, etc.), because full seeds expect the Supabase `auth` schema and `extensions` used in production.

**Prereqs:** Docker Engine running (e.g. Docker Desktop on Windows).

**Apply:**

```powershell
cd C:\path\to\PubPlus
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\apply_melbourne_seed_local_docker.ps1
```

Override port or container name if needed: `$env:PGPORT="54334"`; `$env:PGCONTAINER="my-pg"`.

**Verify (same container name as the script, default `pubplus-mel-seed-pg`):**

```powershell
Get-Content scripts\verify_melbourne_seed_local.sql -Raw | docker exec -i pubplus-mel-seed-pg psql -U postgres -d postgres -v ON_ERROR_STOP=1
```

A successful run shows non-zero counts for Richmond, viewport, late-night `crosses_midnight` rows, exception rows, `partial` uncertainty, and nine Melbourne structured specials.

**Connection string for tools:** `postgresql://postgres:postgres@127.0.0.1:54333/postgres` (default `PGPORT=54333` from the script).

## Backend DSN

Point Django (or any client) at the same database you seeded. Use `backend/.env` from your team; there is no committed secret. For Option B, set the DB URL to the Docker URL above for local testing only.
