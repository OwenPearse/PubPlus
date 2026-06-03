# Stage 5C — Railway production database readiness

Guide for Owen: align Railway `DATABASE_URL` with the **single** Supabase project, apply PubPlus schema migrations, re-smoke DB-backed API routes, then plan **real import** data (not run in this stage unless explicitly requested).

**Related:** [backend/docs/RAILWAY_DEPLOYMENT.md](../../backend/docs/RAILWAY_DEPLOYMENT.md), [SQL_DRAFTING/MIGRATION_RUN_ORDER.md](./SQL_DRAFTING/MIGRATION_RUN_ORDER.md), [backend/docs/PRODUCTION_API_READINESS.md](../../backend/docs/PRODUCTION_API_READINESS.md).

**Production API (current):** `https://pubplus-production.up.railway.app`

---

## 1. Migration source of truth

| Item | Location |
|------|----------|
| Migration SQL files | `database/supabase/migrations/` |
| Count | **33** files: `0001_extensions_and_base_types.sql` … `0033_founder_venue_leads.sql` |
| Apply order | **Lexical filename order** (do not reorder) |
| Authoritative order table | [SQL_DRAFTING/MIGRATION_RUN_ORDER.md](./SQL_DRAFTING/MIGRATION_RUN_ORDER.md) |
| Django migrations | **None** — backend does not run `manage.py migrate` for PubPlus schema |
| Post-apply checks | `database/sql/checks/check_full_schema_readiness.sql` (after `0001`–`0033`) |

### Intended apply path (Supabase CLI)

From repo root (after [Supabase CLI](https://supabase.com/docs/guides/cli) install and login):

```bash
supabase link --project-ref <project-ref>
supabase db push
```

`supabase db push` applies pending migrations from `database/supabase/migrations/` to the **linked** remote database. This is the intended path when the project is linked to that folder (confirm `supabase` config / team convention).

**Alternative (repo script — dev-oriented):** `scripts/apply_seeds_to_database_url.py` applies the same migration files **plus all dev/demo seeds** from `database/.env`. **Do not use that script for Railway production** unless Owen explicitly wants demo seed data on production. Production strategy is **migrations first**, then **real import** (separate step).

**Not recommended for production:** `supabase db reset` (wipes data).

---

## 2. Supabase project alignment (Railway ↔ Supabase)

Before applying migrations, confirm Railway and Supabase refer to the **same** project.

1. **Supabase dashboard** → Project Settings → **General** → copy **Project ID** (`<project-ref>`).
2. **Railway** → service → **Variables** → inspect `DATABASE_URL` (do not paste into chat):
   - Pooler user often looks like `postgres.<project-ref>`
   - Direct host may look like `db.<project-ref>.supabase.co`
3. **Railway** → compare `SUPABASE_URL` host: `https://<project-ref>.supabase.co`
4. All of the above `<project-ref>` values must match.

If they differ, fix Railway env vars to point at the intended single Supabase project, redeploy, then apply migrations **on that project’s database**.

---

## 3. Schema verification (Owen — read-only)

### Dashboard

1. Open the linked Supabase project → **Table Editor** or **SQL Editor**.
2. Run read-only existence checks:

```sql
select to_regclass('public.locality') as locality;
select to_regclass('public.geographic_region') as geographic_region;
select to_regclass('public.venue') as venue;
select to_regclass('public.venue_published_profile') as venue_published_profile;
select to_regclass('public.venue_published_location') as venue_published_location;
select to_regclass('public.venue_published_map_point') as venue_published_map_point;
select to_regclass('public.venue_attribute_definition') as venue_attribute_definition;
select to_regclass('public.beverage_product') as beverage_product;
select to_regclass('public.venue_published_structured_special') as venue_published_structured_special;
select to_regclass('public.venue_published_tap_offering') as venue_published_tap_offering;
```

Non-null `to_regclass` → table exists. All null → migrations not applied (or wrong database).

Optional fuller check (after full apply): run `database/sql/checks/check_full_schema_readiness.sql` in SQL Editor; expect `ok = true` rows.

### CLI

```bash
supabase link --project-ref <project-ref>
supabase migration list
```

Confirm remote history includes `0001` … `0033` (or that `db push` reports nothing pending).

---

## 4. Required tables by smoke endpoint (from backend code)

### `GET /api/v1/reference/localities`

`services/reference/locality_reference.py`:

- `locality`, `geographic_region` (parent region for state code)
- `venue`, `venue_published_location`, `venue_published_profile`, `venue_published_map_point`

### `GET /api/v1/search/filters`

`services/discovery/filter_reference.py`:

- `venue_attribute_definition`
- `beverage_product`

(`meal_specials` filter chips are static in code; no table.)

### `GET /api/v1/search/venues` and `GET /api/v1/home`

`services/discovery/query.py` (list query) + `apps/venues/services/published_venue_read.py` (per-venue bundle):

**Discovery list (minimum):**

- `venue`, `venue_published_profile`, `venue_published_location`, `locality`, `venue_published_map_point`

**Optional filter SQL (when query params used):**

- `venue_published_attribute_value`, `venue_attribute_definition`
- `venue_published_structured_special` (home “specials tonight” section always passes meal filter)
- `venue_published_tap_offering`

**Per-venue card bundle (when list returns rows):**

- `venue_published_descriptive_copy`
- `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty`
- `venue_published_structured_special`, `venue_published_structured_special_marketing_copy`
- `venue_published_tap_offering`, `beverage_product`
- `venue_attribute_allowed_value` (via attribute join)

**Migrations that create the minimum spine:** `0002`, `0003`, `0004`, `0005`, `0006`, `0021`–`0023` (specials), `0024`–`0026` (beverage/taps), plus `0017` (RLS; backend `postgres` role typically bypasses RLS on Supabase).

---

## 5. Apply migrations (Owen — when explicitly ready)

**Preconditions**

- Confirmed `<project-ref>` matches Railway `DATABASE_URL` and `SUPABASE_*`.
- Snapshot/backup if the database already has data you care about.
- **Migrations before any import or dev seed on production.**

**Steps**

```bash
cd <path-to-PubPlus-repo>
supabase login
supabase link --project-ref <project-ref>
supabase db push
```

Re-run §3 verification SQL. Then optional: `check_full_schema_readiness.sql`.

**Warnings**

- Do not run against a different Supabase project than Railway uses.
- Do not confuse **404** on `/api/v1/search/` (wrong path) with **500** `db_error` (schema/SQL failure).
- Empty published data after schema → **200** with empty arrays, not `db_error`.

---

## 6. Post-migration API smoke (correct routes)

Replace host if Railway domain changes.

```bash
curl -i "https://pubplus-production.up.railway.app/api/v1/reference/localities"
curl -i "https://pubplus-production.up.railway.app/api/v1/search/filters"
curl -i "https://pubplus-production.up.railway.app/api/v1/search/venues"
curl -i "https://pubplus-production.up.railway.app/api/v1/home"
```

| Endpoint | Expected after schema |
|----------|------------------------|
| `/api/v1/reference/localities` | `200`, `data.localities` array (may be `[]`) |
| `/api/v1/search/filters` | `200`, `data` with filter reference arrays |
| `/api/v1/search/venues` | `200`, `data.venues` array (may be `[]`) |
| `/api/v1/home` | `200`, `data.sections` (venues may be empty) |

**Wrong path (expected 404):** `GET /api/v1/search/` — use **`/api/v1/search/venues`**.

If still `500` with `db_error` or `internal_error` after migrations: capture a **redacted** Railway request log stack trace (e.g. `relation "…" does not exist`, permission denied).

### SQL: published data present (after import, not required for 200)

```sql
select count(*) as eligible_published_venues
from public.venue_published_profile
where discovery_eligibility_status in ('eligible', 'limited');
```

Non-zero count + API 200 → discovery/localities can return content.

---

## 7. Real import data readiness (do not run in Stage 5C)

| Topic | Finding |
|-------|---------|
| Owner direction | **Real import data** for production smoke (not demo `seed.sql` for TestFlight path) |
| Source assets | `dataCollection/Pub_Australia.csv`, `dataCollection/melbourne_inner_seed_venues.json` |
| Dev/demo SQL seeds | `database/sql/seeds/dev_seed_*`, composed by `database/supabase/seed.sql` — **local/dev**; direct inserts into `venue_published_*` (not production publish lineage) |
| Melbourne apply doc | [backend/docs/MELBOURNE_SEED_APPLY.md](../../backend/docs/MELBOURNE_SEED_APPLY.md) |
| Local apply script | `scripts/apply_melbourne_seed_local_docker.ps1` (Docker Postgres only) |
| Dev DB script | `scripts/apply_seeds_to_database_url.py` — migrations **+ all dev seeds**; use only with explicit approval |
| Founder leads import | `python manage.py import_founder_venue_leads` — **founder_venue_leads** domain; **does not** populate consumer `venue_published_*` discovery truth |
| Production import pipeline | **Not fully automated in repo** for “real import” at publish-lineage quality; requires migrations first, then operator-run import/publish workflow (TBD / owner pipeline) |

**After schema works:** Owen runs the agreed real-import process (separate instruction). Verify with eligible venue count SQL above and non-empty `/api/v1/reference/localities` / `/api/v1/search/venues?suburb=...`.

**Do not** load full `database/supabase/seed.sql` on production unless explicitly choosing demo data for internal smoke.

---

## 8. Error interpretation quick reference

| Symptom | Meaning |
|---------|---------|
| `db_error` on localities/filters | SQL failure — usually **missing schema** or wrong DB, **not** empty data |
| `internal_error` on home/search/venues | Uncaught DB/runtime error during discovery — often same root cause |
| `200` + empty arrays | Schema OK; **import/data** needed for content |
| `404` on `/api/v1/search/` | **Route mismatch** only — use `/api/v1/search/venues` |
