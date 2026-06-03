# Railway Deployment — PubPlus Django API

Deploy the **PubPlus consumer Django backend** (`backend/`) to [Railway](https://railway.com) using the repo **Dockerfile** and **Gunicorn** WSGI server.

This document does **not** deploy the service for you. Owen creates the Railway project, sets variables, and triggers deploy.

Related:

- [PRODUCTION_API_READINESS.md](./PRODUCTION_API_READINESS.md) — TestFlight backend model, env inventory, smoke checklist
- [backend/README.md](../README.md) — local dev quick start

---

## Purpose

- Run production WSGI (`gunicorn config.wsgi:application`) on Railway’s `PORT`
- Expose `GET /api/v1/health` for platform health checks
- Document env vars and smoke steps for first **Railway-generated HTTPS domain** smoke (no custom domain required yet)

---

## Railway project / service setup

1. Create a Railway project (or use an existing one).
2. Add a **new service** from this GitHub repo.
3. Set the service **Root Directory** to **`backend`** (monorepo — not repo root).
4. Confirm Railway detects **`backend/railway.json`** and **`backend/Dockerfile`**.
5. Builder should be **Dockerfile** (configured in `railway.json`).
6. Do **not** set a custom start command in the Railway UI unless debugging — the image **CMD** runs Gunicorn.
7. Enable a **public domain** (Railway → service → Settings → Networking → Generate domain).
8. Copy the generated hostname (no `https://` scheme) for `DJANGO_ALLOWED_HOSTS`.

**Recommended service directory:** `backend/` (all paths in this doc are relative to that root).

---

## Stage 5B — Deploy config recheck

Verified against repo (no deploy attempted from Cursor).

| Check | Status |
| ----- | ------ |
| Service **root directory** | Must be **`backend`** (not monorepo root) |
| `railway.json` location | `backend/railway.json` — detected when root is `backend` |
| `dockerfilePath` | `Dockerfile` (relative to `backend/`) — correct |
| **Procfile** / duplicate start command | **None** — image CMD only; do not set Railway custom start unless debugging |
| Gunicorn target | `config.wsgi:application` → `DJANGO_SETTINGS_MODULE=config.settings` |
| Health check path | `/api/v1/health` in `railway.json` |
| Local dev | `docker-compose.yml` overrides CMD to `runserver` — unchanged |

### First deploy status (update after Owen smokes)

| Field | Value |
| ----- | ----- |
| **Agent deploy** | Not attempted |
| **Production URL** | *Not recorded yet* — use `https://<railway-generated-domain>` until Owen confirms |
| **Health** | Pending first deploy |
| **Smoke** | Pending |
| **Last build note** | If logs show **railpack** + `backend does not exist`, push deploy files to GitHub and set Dockerfile config (see troubleshooting). |

When health passes, Owen may optionally add the public hostname here (no secrets). Do not commit `DATABASE_URL` or keys.

---

## Stage 5B — Railway Variables checklist (copy into Railway)

Set in **Railway → service → Variables**. Use your existing **single Supabase project** for first smoke. Do **not** paste secrets into chat or git.

### Required for boot + JWT

| Railway variable name | Value to enter | Where Owen finds it |
| --------------------- | -------------- | ------------------- |
| `DJANGO_SECRET_KEY` | New long random string (unique to Railway) | Generate (password manager / `openssl rand -hex 32`) |
| `DJANGO_DEBUG` | `false` | Literal |
| `DJANGO_ENV` | `production` | Literal |
| `DJANGO_ALLOWED_HOSTS` | `<hostname>` only | Railway → Networking → public domain (e.g. `something.up.railway.app`) — **no** `https://` |
| `SUPABASE_URL` | `https://<project-ref>.supabase.co` | Supabase → Project Settings → API |
| `SUPABASE_ANON_KEY` | Anon / publishable key | Same API settings page |
| `SUPABASE_JWT_ISSUER` | `https://<project-ref>.supabase.co/auth/v1` | Derive from project ref (same as URL host) |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` | Literal |
| `SUPABASE_JWT_JWKS_URL` | `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json` | Derive from project ref |

### Database — pick **one** approach

**Option A — recommended on Railway:** single variable

| Railway variable name | Value to enter | Where Owen finds it |
| --------------------- | -------------- | ------------------- |
| `DATABASE_URL` | `postgresql://...` | Supabase → Project Settings → Database → connection string (URI). Prefer **pooler** if offered. Passwords with `@` or `:` are parsed via the last `@` before the host (see `config/env.py`). If the URL is still malformed, set **`DB_HOST` / `DB_*`** as well — Django falls back to those when `DATABASE_URL` cannot be parsed. |

You may set **both**: Django tries `DATABASE_URL` first and falls back to `DB_*` when the URL cannot be parsed.

**Option B — discrete vars** (from `backend/.env.example` pattern)

| Railway variable name | Value to enter |
| --------------------- | -------------- |
| `DB_HOST` | Supabase pooler host |
| `DB_PORT` | `5432` |
| `DB_NAME` | `postgres` |
| `DB_USER` | e.g. `postgres.<project-ref>` |
| `DB_PASSWORD` | Database password |
| `DB_SSLMODE` | `require` |

### Optional — skip for first smoke

| Variable | Notes |
| -------- | ----- |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only; not required for consumer API smoke |
| `SUPABASE_STORAGE_BUCKET_VENUES` | Defaults to `venues` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Only if testing Expo **web** against Railway |
| `INTERNAL_*` / `PUBPLUS_INTERNAL_ADMIN_SUBJECTS` | Consumer TestFlight path does not need these |

### Never put in Railway for mobile / EAS

- `EXPO_PUBLIC_*` — those belong in EAS later, not the API service
- Do not duplicate DB password or service role into mobile env

---

## Stage 5B — Manual setup (Owen)

1. **Create** a Railway project (or open existing).
2. **Add service** → Deploy from GitHub → select PubPlus repo.
3. **Settings → Root Directory** → set to **`backend`**.
4. Confirm **Builder: Dockerfile** (from `railway.json`); **do not** add a conflicting custom start command.
5. **Variables** → add all [required variables](#stage-5b--railway-variables-checklist-copy-into-railway). You can deploy once with a temporary `DJANGO_ALLOWED_HOSTS=localhost` only if needed to read logs — then fix hosts before real smoke.
6. **Deploy** (push to connected branch or manual deploy).
7. **Networking** → **Generate domain** (if not already).
8. Set **`DJANGO_ALLOWED_HOSTS`** to the exact generated hostname (no scheme).
9. **Redeploy** if you changed `DJANGO_ALLOWED_HOSTS` after the first deploy.
10. **Smoke** — browser or curl:

```text
https://<railway-generated-domain>/api/v1/health
```

Expected: `200` and `{"status":"healthy"}`.

**Before meaningful `/home` content:** apply `database/supabase/migrations/` and real import data to the same Supabase DB (outside this stage unless Owen explicitly requests agent help with credentials).

---

## Stage 5B — Smoke commands

Replace `<railway-domain>` with the public hostname (no trailing slash).

```bash
curl -i "https://<railway-domain>/api/v1/health"
curl -i "https://<railway-domain>/api/v1/auth-probe/public"
curl -i "https://<railway-domain>/api/v1/home"
```

| Check | Expected |
| ----- | -------- |
| `/api/v1/health` | `HTTP/1.1 200` — body `{"status":"healthy"}` |
| `/api/v1/auth-probe/public` | `200` — `{"status":"ok","authenticated":false}` (or `true` if Bearer sent) |
| `/api/v1/home` | `200` — may be sparse/empty if migrations or import data not loaded yet |

**Authenticated probe** (after Supabase sign-in; same project as Railway env):

```bash
curl -i "https://<railway-domain>/api/v1/auth-probe/private" \
  -H "Authorization: Bearer <access_token>"
```

| Result | Meaning |
| ------ | ------- |
| `200` | JWT issuer/JWKS/project alignment OK |
| `401` | Missing token, invalid token, or **wrong Supabase project** vs backend env |

Share with the agent (safe): status codes, redacted response bodies, Railway **deploy log excerpts** — not secrets or full tokens.

---

## Build and start behaviour

| Phase | Behaviour |
| ----- | --------- |
| **Build** | `docker build` from `backend/Dockerfile`: Python 3.12-slim, `pip install -r requirements.txt`, copy app |
| **Start** | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT` (`PORT` from Railway; defaults to `8000` if unset) |
| **Health check** | Railway `healthcheckPath`: `/api/v1/health` (expects `200` + `{"status":"healthy"}`) |
| **WSGI module** | `config.wsgi:application` → `DJANGO_SETTINGS_MODULE=config.settings` |

### Local Docker vs Railway image

`backend/docker-compose.yml` **overrides** the container command to `python manage.py runserver 0.0.0.0:8000` for local dev. Building the same image without that override uses Gunicorn (production path).

Local Python dev (no Docker): `python manage.py runserver 8000` — unchanged.

---

## Required environment variables

Set in Railway → service → **Variables**. Never commit secrets.

| Variable | Required | Example / notes |
| -------- | -------- | --------------- |
| `DJANGO_SECRET_KEY` | **Yes** | Long random string; unique per environment |
| `DJANGO_DEBUG` | **Yes** | `false` |
| `DJANGO_ENV` | Recommended | `production` |
| `DJANGO_ALLOWED_HOSTS` | **Yes** | Railway hostname only, **no scheme** — e.g. `pubplus-api-production.up.railway.app` (comma-separate if multiple) |
| `DATABASE_URL` | **Yes** (preferred on Railway) | Supabase Postgres connection URI (`postgresql://...`) |
| `DB_HOST` | Alt. to URL | Use **one** of `DATABASE_URL` or `DB_*` set |
| `DB_PORT` | Alt. | `5432` |
| `DB_NAME` | Alt. | `postgres` |
| `DB_USER` | Alt. | e.g. `postgres.<project-ref>` |
| `DB_PASSWORD` | Alt. | Supabase DB password |
| `DB_SSLMODE` | If using `DB_*` | `require` (recommended for Supabase) |
| `SUPABASE_URL` | **Yes** | `https://<project-ref>.supabase.co` |
| `SUPABASE_ANON_KEY` | **Yes** | Anon/publishable key for that project |
| `SUPABASE_JWT_ISSUER` | **Yes** | `https://<project-ref>.supabase.co/auth/v1` |
| `SUPABASE_JWT_AUDIENCE` | **Yes** | `authenticated` (default) |
| `SUPABASE_JWT_JWKS_URL` | **Yes** | `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json` |
| `SUPABASE_JWT_ALGORITHM` | No | `RS256` (default) |
| `SUPABASE_SERVICE_ROLE_KEY` | No | Backend-only; optional today |
| `SUPABASE_STORAGE_BUCKET_VENUES` | No | `venues` (default) |
| `DJANGO_CORS_ALLOWED_ORIGINS` | If web QA hits Railway | Comma-separated origins with scheme; native TestFlight does not need CORS |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | If browser admin later | Usually empty for mobile-only |
| `INTERNAL_ADMIN_ENABLED` | No | `false` for consumer API smoke |
| `INTERNAL_ADMIN_TOKEN` | No | Only if internal tools enabled |
| `INTERNAL_ADMIN_ALLOWED_IPS` | No | Optional |
| `PUBPLUS_INTERNAL_ADMIN_SUBJECTS` | No | Comma-separated Supabase user UUIDs |

Railway injects **`PORT`** automatically — do not hardcode it in variables.

### `DJANGO_ALLOWED_HOSTS` and Railway domain

After generating a public domain, set:

```text
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.up.railway.app
```

Optional: add your exact public hostname too. **Do not** include `https://`.

Railway injects `RAILWAY_PUBLIC_DOMAIN` and `RAILWAY_PRIVATE_DOMAIN`; Django **automatically appends** these to `ALLOWED_HOSTS` at boot.

Django also always allows **`healthcheck.railway.app`** — Railway’s health probe uses that `Host` header. Without it, Django returns **400** (`DisallowedHost`) and Railway reports **service unavailable** even when Gunicorn is listening.

If deploy fails with `DisallowedHost` in runtime logs, widen `DJANGO_ALLOWED_HOSTS` as above.

---

## Health check URL

```text
https://<railway-generated-domain>/api/v1/health
```

Expected: `200` and body `{"status": "healthy"}`.

Configure Railway health check path to `/api/v1/health` (already in `railway.json`).

---

## Stage 5C — Database readiness (migrations + smoke)

**Status:** Schema apply and re-smoke are **Owen-operated** unless explicitly delegated. Full checklist: [database/docs/RAILWAY_STAGE_5C_DB_READINESS.md](../../database/docs/RAILWAY_STAGE_5C_DB_READINESS.md).

**Current production host:** `https://pubplus-production.up.railway.app` (Stage 5B: health/auth OK; DB-backed routes failing until schema is on the linked Supabase DB).

### Align Supabase project with Railway

1. Supabase dashboard → Project Settings → note **Project ID** (`<project-ref>`).
2. Railway Variables → confirm `DATABASE_URL` and `SUPABASE_URL` refer to the **same** `<project-ref>` (do not paste secrets into chat).
3. Apply migrations only to that database.

### Apply schema (33 migrations)

Source: `database/supabase/migrations/` (`0001` … `0033`), lexical order — see [database/docs/SQL_DRAFTING/MIGRATION_RUN_ORDER.md](../../database/docs/SQL_DRAFTING/MIGRATION_RUN_ORDER.md).

```bash
supabase link --project-ref <project-ref>
supabase db push
```

Django does **not** run these. Do **not** use `scripts/apply_seeds_to_database_url.py` on production unless Owen explicitly wants **dev/demo seeds** loaded.

### Post-migration API smoke (correct paths)

```bash
curl -i "https://<railway-domain>/api/v1/reference/localities"
curl -i "https://<railway-domain>/api/v1/search/filters"
curl -i "https://<railway-domain>/api/v1/search/venues"
curl -i "https://<railway-domain>/api/v1/home"
```

Expect **HTTP 200** on all four after schema exists (payloads may be empty). **Not** a valid smoke path: `GET /api/v1/search/` (404 — no index route).

### Real import (after schema)

Load **real import** venue data per owner direction — **after** migrations. Do not run import in Stage 5C unless Owen explicitly asks. See Stage 5C doc §7 for seed vs import pointers.

---

## Stage 5D — Home feed performance (default limit)

**Problem:** Default `GET /api/v1/home` ran three discovery passes at **12 venues per section**, each loading full published-venue bundles — often **>30s** on Railway (worker timeout → HTML 500). `GET /api/v1/home?limit=3` succeeded.

**Fix (code):** Default home `limit` is **6** per section (max **12** via `?limit=`). Search/map keep their own defaults (up to 200). Railway logs emit `home_feed` timing per section (`home_feed start`, `home_feed section=…`, `home_feed done`).

**Re-smoke after deploy:**

```bash
curl -i "https://<railway-domain>/api/v1/health"
curl -i "https://<railway-domain>/api/v1/home"
curl -i "https://<railway-domain>/api/v1/home?limit=12"
```

Expect **200** JSON on both home URLs. Fallback while investigating: `?limit=5`.

**Note:** OpenAPI in `consumer_app/lib/api-spec/openapi.yaml` may still list home `default: 12` until regenerated — backend behavior is authoritative.

---

## Database and Supabase

### Schema and data (before meaningful smoke)

Railway deploy does **not** run migrations or imports. The target Postgres must already have:

1. **Schema** — apply `database/supabase/migrations/` to the Supabase project database (team workflow / Supabase CLI). See [Stage 5C](#stage-5c--database-readiness-migrations--smoke).
2. **Venue data** — **real import data** per owner direction (not demo seed for production smoke).

Empty **published** data after schema → API returns **200** with empty arrays, not `db_error`. `db_error` / `internal_error` on localities, filters, home, or search usually means **missing schema or wrong database**, not “no venues yet”.

### Single Supabase project (immediate smoke)

Owner currently has **one** Supabase project. For first Railway smoke:

- Point Railway `DATABASE_URL` (or `DB_*`) at that project’s Postgres.
- Set all `SUPABASE_*` JWT vars to **that same** project.
- Mobile smoke must use the **same** project URL and anon key (`EXPO_PUBLIC_SUPABASE_*`).

Backend and mobile **must** use the same Supabase project per environment or JWT verification returns **401**.

### Future Dev / Prod split

Before external TestFlight users / launch:

- Create **PubPlus Dev** and **PubPlus Prod** Supabase projects.
- Railway production service → **Prod** DB + JWT settings.
- Local dev → **Dev** project.
- Do not mix Dev tokens against Prod backend.

See [consumer_app/docs/environment-strategy.md](../../consumer_app/docs/environment-strategy.md).

---

## Smoke test checklist (after Owen deploys)

Replace `<railway-generated-domain>` with your public hostname (e.g. `pubplus-production.up.railway.app`).

**Infrastructure**

- [ ] `GET https://<railway-generated-domain>/api/v1/health` → `200`, `{"status":"healthy"}`
- [ ] Railway deploy logs show Gunicorn listening (no repeated crash loop)
- [ ] `DJANGO_DEBUG` is `false` in variables

**Database / schema (Stage 5C)**

- [ ] Railway `DATABASE_URL` and `SUPABASE_URL` share the same Supabase `<project-ref>`
- [ ] Migrations `0001`–`0033` applied (`supabase db push` or team workflow)
- [ ] `GET https://<railway-generated-domain>/api/v1/reference/localities` → `200` (not `db_error`)
- [ ] `GET https://<railway-generated-domain>/api/v1/search/filters` → `200`
- [ ] `GET https://<railway-generated-domain>/api/v1/search/venues` → `200` (not `/api/v1/search/`)
- [ ] `GET https://<railway-generated-domain>/api/v1/home` → `200` (empty sections OK before import)

**Database / content (after schema)**

- [ ] Real import data present (separate step; not required for 200-with-empty)
- [ ] Non-empty discovery: localities list and/or `/api/v1/search/venues` return venues

**Auth (same Supabase project as backend env)**

- [ ] Sign in via Supabase client; obtain access token
- [ ] `GET https://<railway-generated-domain>/api/v1/auth-probe/private` with `Authorization: Bearer <token>` → `200`
- [ ] Wrong-project token → `401`

**Mobile (later EAS stage)**

- [ ] `EXPO_PUBLIC_API_BASE_URL=https://<railway-generated-domain>`
- [ ] Matching `EXPO_PUBLIC_SUPABASE_URL` and anon key

---

## Rollback and troubleshooting

| Symptom | Likely cause | Action |
| ------- | ------------- | ------ |
| **502** / service unavailable | Container crash loop, Gunicorn never bound | Read deploy logs; fix env/DB; confirm root dir `backend` |
| **502** / upstream timeout | App hung on DB connect at request time | Check `DATABASE_URL`; test DB from Supabase dashboard |
| **400 Bad Request** / `DisallowedHost` in logs | `DJANGO_ALLOWED_HOSTS` missing Railway hostname | Add exact generated domain (no scheme); redeploy |
| **Health check failing** (Railway never goes healthy) | Wrong root dir, wrong port, crash on boot | Root=`backend`; no custom start overriding Gunicorn; check `Missing required environment variable` |
| **Build failed** (pip/Docker) | `requirements.txt` / Docker issue | Fix dependency pin; rebuild |
| **`railpack` … `backend does not exist`** | Wrong builder and/or config not on deploy branch | See [Railpack / `backend does not exist`](#railpack-error-backend-does-not-exist) below |
| **Gunicorn import error** | Wrong `WORKDIR` or missing `src` on path | Dockerfile copies full `backend/` tree — should not happen if root dir correct |
| `/health` **200** but `/home` **500** | DB URL, schema, or query error | Migrations not applied; check logs for psycopg errors |
| `db_error` on `/reference/localities` or `/search/filters` | Missing table/wrong DB | Apply `0001`–`0033` to the same project as `DATABASE_URL`; not caused by empty data alone |
| `internal_error` on `/home` or `/search/venues` | Discovery SQL failure | Same as above; capture Railway traceback |
| `404` on `/api/v1/search/` only | Wrong smoke path | Use `GET /api/v1/search/venues` |
| `/home` **500** (~30s, HTML error) | Home feed too slow (3× discovery + enrichment) | Deploy Stage **5D** (default `limit=6`); check logs for `home_feed section=… elapsed_ms` |
| `/home` **200** but empty | No real import data | Expected until data pipeline run |
| **`401` on `/auth-probe/private` only** | JWT issuer/JWKS/audience mismatch | Match `SUPABASE_JWT_*` to same `<project-ref>` as token source |
| **`401` on all private routes** | Same as above, or expired token | Refresh token; verify mobile/backend same Supabase project |
| **`AttributeError: 'Settings' object has no attribute 'ROOT_URLCONF'`** | `config/settings/__init__.py` missing from deploy (old `main`) | Deploy branch with `config/settings/__init__.py` **or** `config/wsgi.py` using `config.settings.base`; merge `development` → `main` |
| **Healthcheck "service unavailable"** (no ROOT_URLCONF in logs) | Wrong git branch, `ALLOWED_HOSTS`, or app not listening | Deploy latest `main`/`development`; set `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.up.railway.app,<exact-host>` |

**Do not paste** `DATABASE_URL`, `DJANGO_SECRET_KEY`, or Bearer tokens into issue chat — use redacted logs.

### Railpack error: `backend does not exist`

If build logs show **`railpack`** (not Docker) and:

```text
directory .../snapshot-target-unpack/backend does not exist
```

typical causes:

1. **`backend/railway.json` and Gunicorn `Dockerfile` are not on the Git branch Railway builds** — Railpack auto-detects the repo root `package.json` and does not use the Django Dockerfile. **Fix:** commit and push `backend/railway.json`, `backend/Dockerfile`, `backend/requirements.txt` (with `gunicorn`), then redeploy.
2. **Root Directory = `backend`** but **Config-as-code path** not set — Railway may ignore `railway.json`. **Fix:** Service → Settings → set **Railway config file** to **`/backend/railway.json`** (absolute from repo root). Confirm builder is **Dockerfile**.
3. **Root Directory empty** while expecting an isolated backend service — **Fix:** set **Root Directory** to **`backend`** (or `/backend` in UI).

After push, Settings should be:

| Setting | Value |
| ------- | ----- |
| Root Directory | `backend` |
| Config file (if shown) | `/backend/railway.json` |
| Builder | **Dockerfile** (from config; not Railpack) |
| Custom start command | **Empty** (use image CMD) |

**Rollback:** Railway → Deployments → redeploy a previous successful deployment, or revert Git and trigger a new build.

**Local regression:** `python manage.py check` and `docker compose up` (still uses runserver via compose override).

---

## What goes in Railway vs EAS

| Secret / value | Railway (backend) | EAS (mobile) |
| -------------- | ----------------- | ------------ |
| `DJANGO_SECRET_KEY` | Yes | No |
| `DATABASE_URL` / `DB_PASSWORD` | Yes | No |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | **Never** |
| `SUPABASE_ANON_KEY` | Yes (boot) | Yes (`EXPO_PUBLIC_SUPABASE_ANON_KEY`) |
| `EXPO_PUBLIC_API_BASE_URL` | No | Yes (`https://<railway-generated-domain>`) |
| `EXPO_PUBLIC_SUPABASE_URL` | No | Yes (same project as backend) |

Custom product domain, privacy policy URL, and store metadata are **out of scope** for this stage — use Railway’s generated domain until decided.

---

## Custom domain (later)

Not required for initial TestFlight backend smoke. When the product domain is chosen:

1. Add custom domain in Railway networking.
2. Append the new hostname to `DJANGO_ALLOWED_HOSTS`.
3. Update mobile `EXPO_PUBLIC_API_BASE_URL` in EAS production profile.

---

## Related files in repo

| File | Role |
| ---- | ---- |
| `backend/Dockerfile` | Production image; Gunicorn CMD |
| `backend/railway.json` | Dockerfile builder + health path |
| `backend/docker-compose.yml` | Local dev; overrides CMD to runserver |
| `backend/requirements.txt` | Includes `gunicorn` |
| `backend/config/wsgi.py` | WSGI entrypoint |
