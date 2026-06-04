# Production API Readiness — TestFlight Backend Deployment

Source of truth for deploying the **PubPlus Django backend** in a production-like configuration so **iOS TestFlight** can point at a real API, production database, and **PubPlus Prod Supabase**.

**Deployment config:** Railway + Gunicorn — see [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md). Owen still performs the actual deploy, env setup, migrations, and imports.

Related consumer docs:

- [consumer_app/docs/environment-strategy.md](../../consumer_app/docs/environment-strategy.md) — mobile env matrix and Supabase split
- [consumer_app/docs/native-testflight-readiness.md](../../consumer_app/docs/native-testflight-readiness.md) — EAS/TestFlight path (blocked until this work completes)
- [consumer_app/docs/auth-sso-runbook.md](../../consumer_app/docs/auth-sso-runbook.md) — OAuth provider setup (separate from backend deploy)

Backend local setup: [backend/README.md](../README.md), [ENVIRONMENT_AND_LOCAL_DEV.md](./ENVIRONMENT_AND_LOCAL_DEV.md).

---

## 1. Current backend deployment status

| Item | Repo finding |
| ---- | ------------ |
| **Production deployment config** | **Yes (Railway).** `backend/Dockerfile` (Gunicorn CMD), `backend/railway.json`, [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md). Local `docker-compose.yml` still overrides to `runserver`. |
| **Chosen hosting** | **Railway** (owner decision). Initial URL: Railway **generated domain** — `https://<railway-generated-domain>` (unknown until Owen deploys). Custom domain deferred. |
| **Production API URL** | **Unknown until Owen deploys.** Placeholder: `https://<railway-generated-domain>`. Record hostname in [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) § Stage 5B status after smoke (no secrets). |
| **First Railway deploy (5B)** | **Not attempted by agent.** Owen: follow [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) § Stage 5B checklist and smoke commands. |
| **Real production API service** | **Django app in `backend/`** — the consumer mobile MVP API under `/api/v1/...`. **Not** `consumer_app/artifacts/api-server` (local Express prototype). |
| **Local dev backend documented** | **Yes.** `backend/README.md`, `backend/docs/ENVIRONMENT_AND_LOCAL_DEV.md`, `consumer_app/README.local-run.md`. |
| **Health endpoints** | **Yes — liveness only.** `GET /api/v1/health` returns `{"status": "healthy"}`. No deep/readiness endpoint that checks DB, Supabase, or Redis. |
| **Auth probe endpoints** | **Yes.** `GET /api/v1/auth-probe/public` (optional auth), `GET /api/v1/auth-probe/private` (requires Bearer JWT). Useful for smoke tests. |
| **Supabase / JWT auth config visible** | **Yes.** `backend/config/settings/base.py`, `backend/.env.example`, `backend/src/common/auth/jwt_verifier.py`. |
| **Production database config visible** | **Partially.** Settings support Supabase Postgres via `DATABASE_URL` **or** `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` (+ optional `DB_SSLMODE`). `.env.example` shows individual `DB_*` vars only (no `DATABASE_URL` line). Example host is Supabase pooler format. |
| **Schema migrations** | **Supabase SQL migrations** in `database/supabase/migrations/` (33 files). **No Django app migrations** in `backend/`. Apply via Supabase CLI / team workflow — not `python manage.py migrate`. |
| **Production WSGI server** | **Configured.** `gunicorn` in `requirements.txt`; `Dockerfile` CMD binds `config.wsgi:application` to `0.0.0.0:${PORT:-8000}`. |
| **Static files / collectstatic** | **Minimal.** `STATIC_URL = "static/"` only. No `collectstatic` or WhiteNoise config found. Not a blocker for JSON API MVP. |
| **Email (Resend, etc.)** | **Not found** in backend env or dependencies. |
| **Redis / cache** | **Not found** in backend env or dependencies. |
| **Sentry / logging** | **Not found** in backend env or settings. |
| **PubPlus Prod Supabase project** | **Not split yet.** Owner has one Supabase project today; immediate Railway smoke may use it; create Dev/Prod split before external TestFlight users. |
| **Production venue data** | **Real import data** (owner decision). Must be loaded before meaningful discovery smoke; not run by deploy. |

---

## 2. Target TestFlight backend model

### TestFlight (production-like)

```text
TestFlight mobile app
  -> EXPO_PUBLIC_API_BASE_URL=https://<railway-generated-domain> (or future custom domain)
  -> deployed Django production backend (backend/)
  -> production Postgres (PubPlus Prod Supabase database or equivalent)
  -> PubPlus Prod Supabase JWT/auth config
```

Mobile sends `Authorization: Bearer <supabase_access_token>`. Django verifies JWT against Prod JWKS/issuer settings. See [AUTH_MODEL.md](./AUTH_MODEL.md).

### Local development

```text
Local mobile app
  -> EXPO_PUBLIC_API_BASE_URL=http://localhost:8000 or LAN/ngrok URL
  -> local Django backend (backend/)
  -> dev database (PubPlus Dev Supabase Postgres)
  -> PubPlus Dev Supabase JWT/auth config
```

There is **no third staging Supabase** for now (owner direction). TestFlight uses **Prod** Supabase + production backend, not Dev.

---

## 3. Required production environment variables

Variables below are taken from `backend/config/settings/base.py` and `backend/.env.example`. Boot fails at startup if required values are missing (`RuntimeError` from `get_env(..., required=True)`).

| Variable | Required for prod? | Purpose | Prod value source | Notes |
| -------- | -----------------: | ------- | ----------------- | ----- |
| `DJANGO_SECRET_KEY` | **Yes** | Django cryptographic signing | Generate new secret; store in host secret manager | Never commit. Must differ from dev. |
| `DJANGO_DEBUG` | **Yes** (set false) | Debug mode | `false` / `0` | Default in code is `false` if unset. Explicitly set `false` in prod. |
| `DJANGO_ENV` | Recommended | Environment label | e.g. `production` | Default `local`. Informational; not heavily branched in settings today. |
| `DJANGO_ALLOWED_HOSTS` | **Yes** | Host header validation | Railway generated hostname (no scheme), e.g. `*.up.railway.app` | Comma-separated. Custom domain can be added later. |
| `DJANGO_CORS_ALLOWED_ORIGINS` | **Yes** (if web clients hit prod API) | Browser CORS allow-list | Future web domain(s), optional localhost for internal QA | See [§6](#6-cors-csrf-and-allowed-hosts). Native Bearer requests do not use CORS. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Conditional | CSRF trusted origins for cookie/session flows | Future admin web portal origin(s) | Consumer mobile JWT APIs use `csrf_exempt`. Relevant for future browser admin tooling. |
| `TIME_ZONE` | No | Django timezone | `UTC` (default) | |
| `DATABASE_URL` | **One of DB paths** | Postgres connection (URL form) | Supabase Prod → Settings → Database → connection string (pooler or direct) | Supported in code; **not listed in `.env.example`**. Common on PaaS hosts. |
| `DB_HOST` | **One of DB paths** | Postgres host | Supabase pooler hostname | Required if `DATABASE_URL` unset. |
| `DB_PORT` | **One of DB paths** | Postgres port | `5432` (default) | |
| `DB_NAME` | **One of DB paths** | Database name | `postgres` (typical Supabase) | |
| `DB_USER` | **One of DB paths** | Postgres user | Supabase pooler user (e.g. `postgres.<project-ref>`) | |
| `DB_PASSWORD` | **One of DB paths** | Postgres password | Supabase database password | Backend-only secret. |
| `DB_SSLMODE` | Recommended for Supabase | SSL mode for individual `DB_*` config | e.g. `require` | In code only; add to prod env when using `DB_*` vars. |
| `SUPABASE_URL` | **Yes** | Supabase project URL (storage URL construction) | PubPlus Prod project URL | Must match mobile `EXPO_PUBLIC_SUPABASE_URL`. |
| `SUPABASE_ANON_KEY` | **Yes** | Loaded at startup | PubPlus Prod anon/publishable key | Required by settings; used for project alignment. **Not** sent to mobile from backend. |
| `SUPABASE_SERVICE_ROLE_KEY` | No (optional) | Service role key placeholder | PubPlus Prod service role | Default empty. Loaded in settings but **not referenced in application code** today. Keep server-side only if set. |
| `SUPABASE_JWT_ISSUER` | **Yes** | JWT `iss` validation | `https://<prod-project-ref>.supabase.co/auth/v1` | Must match Prod Supabase project. |
| `SUPABASE_JWT_AUDIENCE` | **Yes** (has default) | JWT `aud` validation | `authenticated` (default) | |
| `SUPABASE_JWT_JWKS_URL` | **Yes** | JWKS endpoint for RS256 verify | `https://<prod-project-ref>.supabase.co/auth/v1/.well-known/jwks.json` | |
| `SUPABASE_JWT_ALGORITHM` | No | JWT algorithm | `RS256` (default) | |
| `SUPABASE_STORAGE_BUCKET_VENUES` | No | Public venue photo bucket name | `venues` (default) | Used for `public_storage_object_url()`. |
| `MEDIA_URL` | No | Django media URL prefix | `/media/` (default) | Placeholder; MVP uses Supabase Storage URLs directly. |
| `INTERNAL_ADMIN_ENABLED` | No | Internal admin feature flag | `false` for TestFlight consumer path | Default `false`. |
| `INTERNAL_ADMIN_TOKEN` | No | Admin token placeholder | Generate if internal tools enabled | Not wired into consumer mobile path. |
| `INTERNAL_ADMIN_ALLOWED_IPS` | No | IP allow-list placeholder | Empty or operator IPs | |
| `PUBPLUS_INTERNAL_ADMIN_SUBJECTS` | No | Supabase JWT `sub` UUIDs for `/api/v1/internal/*` | Operator Supabase user UUIDs | Comma-separated. Consumer TestFlight does not need this. |
| `LOCAL_SETTINGS_MODULE` | No | Optional settings override module | Leave empty in prod | Local dev hook only. |

### Recommended future variables (not in repo today)

Do **not** set these until implementation adds support:

| Variable | Why |
| -------- | --- |
| `SENTRY_DSN` | Error tracking — not in settings or requirements |
| `RESEND_API_KEY` / email provider vars | No backend email integration found |
| `REDIS_URL` | No cache layer in backend |

---

## 4. Supabase Prod alignment

TestFlight requires **the same Supabase project** on mobile and backend.

| Layer | Mobile (EAS / TestFlight) | Backend (production deploy) | Must match |
| ----- | ------------------------- | ----------------------------- | ---------- |
| Project URL | `EXPO_PUBLIC_SUPABASE_URL` | `SUPABASE_URL` | **Yes** |
| Anon key | `EXPO_PUBLIC_SUPABASE_ANON_KEY` | `SUPABASE_ANON_KEY` | Same project (backend loads it at boot) |
| JWT issuer | (implicit from Supabase) | `SUPABASE_JWT_ISSUER` | `https://<prod-ref>.supabase.co/auth/v1` |
| JWT audience | (implicit) | `SUPABASE_JWT_AUDIENCE` | `authenticated` |
| JWKS | (implicit) | `SUPABASE_JWT_JWKS_URL` | Prod `.well-known/jwks.json` |
| Service role | **Never in mobile** | `SUPABASE_SERVICE_ROLE_KEY` (optional) | Backend-only; never `EXPO_PUBLIC_*` or EAS mobile secrets |

### Verification behaviour

JWT verification is in `backend/src/common/auth/jwt_verifier.py`: RS256 decode against `SUPABASE_JWT_JWKS_URL`, checking `iss`, `aud`, and `sub`.

**Mismatch symptom:** Supabase sign-in succeeds in the app, then Django returns **401** on authenticated routes (`/api/v1/saved/`, `/api/v1/profile/`, etc.).

### Storage alignment

Venue photos use public Supabase Storage URLs built from `SUPABASE_URL` + `SUPABASE_STORAGE_BUCKET_VENUES`. Prod backend must point at the Prod project where venue media buckets/objects exist.

### Auth redirect alignment

OAuth redirect URLs are configured in **Supabase Auth** and provider dashboards, not Django. See [auth-sso-runbook.md](../../consumer_app/docs/auth-sso-runbook.md). Prod project has a different `<project-ref>` than Dev.

---

## 5. Production database requirements

### Database technology

- **Supabase Postgres** is the system of record.
- Django connects via **`DATABASE_URL`** or discrete **`DB_*`** variables (`backend/config/settings/base.py`).
- `.env.example` shows Supabase pooler host pattern (`aws-1-ap-southeast-2.pooler.supabase.com`, user `postgres.<project-ref>`).

### Migrations

- Schema lives in **`database/supabase/migrations/`** (33 SQL migration files).
- Apply to **PubPlus Prod** database before TestFlight using team Supabase workflow (e.g. `supabase db push`, linked project, or managed CI).
- **Do not** rely on `python manage.py migrate` — no Django migration apps found under `backend/`.

### Seed / demo data

| Question | Finding |
| -------- | ------- |
| **Seed required for consumer app to show venues?** | **Yes, for meaningful discovery smoke.** Home, Search, Map, and Venue Detail read **published venue truth** from Postgres. Empty DB → empty feeds. |
| **Documented seed path** | `database/supabase/seed.sql` composes dev/demo seeds (reference data, Melbourne inner-city venues, demo accounts, specials). See [MELBOURNE_SEED_APPLY.md](./MELBOURNE_SEED_APPLY.md). |
| **Prod data policy** | **Real import data** (owner decision). Dev/demo seeds in `seed.sql` are not the production path. |
| **Admin / owner data for consumer TestFlight** | **Not required** for consumer browsing and auth-gated flows. Internal admin (`/api/v1/internal/*`) needs `PUBPLUS_INTERNAL_ADMIN_SUBJECTS` — out of TestFlight consumer scope. |
| **PubPlus Prod DB confirmed** | **Unknown** — project may not exist yet. |

---

## 6. CORS, CSRF, and allowed hosts

### `ALLOWED_HOSTS` (`DJANGO_ALLOWED_HOSTS`)

Production must include the **deployed API hostname** (exact host Django sees in `Host` header):

- Placeholder: `api.<future-domain>` or PaaS default hostname (e.g. `*.up.railway.app` if Railway chosen later).
- If using a reverse proxy, include the public hostname clients call.
- For LAN dev against local Django, include `localhost`, `127.0.0.1`, and LAN IP — already in `.env.example` for local.

### CORS (`DJANGO_CORS_ALLOWED_ORIGINS`)

Configured via `django-cors-headers` — explicit origin list only (no `CORS_ALLOW_ALL` in settings).

| Client | Needs CORS on prod API? |
| ------ | ------------------------ |
| **Native iOS (TestFlight)** | **No** — React Native `fetch` with Bearer token is not subject to browser CORS. |
| **Expo web / browser testing** | **Yes** — if testers hit production API from `http://localhost:8081` or a hosted web app, those origins must be in `DJANGO_CORS_ALLOWED_ORIGINS`. |
| **Future production web app** | **Yes** — add `https://<future-production-web-domain>` when known. |

Local `.env.example` already includes:

- `http://localhost:8081`, `http://127.0.0.1:8081`
- `http://localhost:8082`, `http://127.0.0.1:8082`
- `http://localhost:3010`, `http://localhost:3000` (legacy web tooling)

Production CORS list is **unknown** until final web domain is chosen. Native TestFlight alone does not require CORS entries.

### CSRF (`DJANGO_CSRF_TRUSTED_ORIGINS`)

- Consumer authenticated endpoints use **`require_consumer_auth_api`** → **`csrf_exempt`** because auth is `Authorization: Bearer`, not cookies (`backend/src/common/auth/guards.py`).
- Internal admin endpoints also use Bearer + `csrf_exempt`.
- CSRF matters for **future cookie-based browser admin** or Django session forms — not for mobile JWT flows.
- `.env.example` CSRF origins target localhost admin/web ports; update for production admin portal when it exists.

---

## 7. Health checks and smoke checks

### Endpoints found in repo

| Endpoint | Auth | Response | Checks |
| -------- | ---- | -------- | ------ |
| `GET /api/v1/health` | Public | `200` + `{"status": "healthy"}` | **Process liveness only** — no DB/Supabase |
| `GET /api/v1/auth-probe/public` | Optional Bearer | `200` + `{"status": "ok", "authenticated": bool}` | Auth middleware smoke |
| `GET /api/v1/auth-probe/private` | Required Bearer | `200` + subject, or `401` | JWT verification smoke |
| `GET /api/v1/home` | Public | Home feed JSON (default **3** venues/section, max **6**; three sections) | DB + published venue data |
| `GET /api/v1/search/venues` | Public | Search results (default limit 50, max 200) | DB + discovery layer |
| `GET /api/v1/reference/localities` | Public | Locality reference | DB |

There is **no** `/health/deep`, `/ready`, or dependency-check endpoint in code today.

### Production pre-TestFlight smoke checklist

Run against deployed production API base URL after env is configured.

**Infrastructure**

- [ ] `GET /api/v1/health` → `200`, body `{"status": "healthy"}`
- [ ] Process logs show clean startup (no repeated env/DB connection errors)
- [ ] TLS/HTTPS reachable from internet (TestFlight devices)

**Database / content**

- [ ] `GET /api/v1/home` → `200` (default limit **3**/section after Stage **5E**; optional `?limit=6`; `?limit=7` → `400 invalid_limit`)
- [ ] `GET /api/v1/search/venues` returns expected shape
- [ ] Migrations applied to Prod DB (`database/supabase/migrations/`)

**Auth boundary**

- [ ] Create or use test user in **PubPlus Prod** Supabase (email/password)
- [ ] Obtain Supabase access token (client sign-in)
- [ ] `GET /api/v1/auth-probe/private` with `Authorization: Bearer <token>` → `200`
- [ ] Same request with Dev token against Prod backend → **401** (confirms alignment)
- [ ] Authenticated consumer route, e.g. `GET /api/v1/profile/` → `200` (not 401)

**CORS (if Expo web QA against prod)**

- [ ] Browser preflight from allowed origin succeeds for a public GET

**Mobile integration (after EAS prod profile exists)**

- [ ] TestFlight build has `EXPO_PUBLIC_API_BASE_URL` = production URL
- [ ] TestFlight build has Prod Supabase URL + anon key
- [ ] Sign-in + saved venues / profile works end-to-end

---

## 8. Deployment platform notes

### Chosen platform: Railway

| Artifact | Purpose |
| -------- | ------- |
| `backend/Dockerfile` | Production image; **Gunicorn** CMD on `$PORT` |
| `backend/railway.json` | Dockerfile builder + health check `/api/v1/health` |
| [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) | Owen’s deploy steps, env table, smoke checklist |
| `backend/docker-compose.yml` | **Local only** — overrides CMD to `runserver` |
| `backend/config/wsgi.py` | WSGI entry (`config.wsgi:application`) |
| `backend/requirements.txt` | Includes `gunicorn` |

### Production start command (in image)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
```

Railway injects `PORT`. Supabase migrations and data import run **outside** the container — see [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md).

### Initial public URL

Use Railway’s **generated HTTPS domain** for first TestFlight backend smoke:

```text
https://<railway-generated-domain>
```

Custom product domain waits until app name/domain is decided.

### Not in repo yet

- Live deployed service / confirmed production URL
- `collectstatic` / CDN static pipeline (not required for JSON API MVP)
- CI/CD deploy workflow
- Deep health endpoint (DB/Supabase checks)

---

## 9. Secrets handling

### Where secrets should live

| Environment | Storage |
| ----------- | ------- |
| **Local dev** | `backend/.env` (gitignored) from `.env.example` |
| **Production** | Hosting platform secret manager / env dashboard (Railway variables, Render env, etc.) |
| **TestFlight mobile** | **EAS secrets** / build profile env — not git |

### Never commit

- Populated `backend/.env`
- `DJANGO_SECRET_KEY`, `DB_PASSWORD`, `SUPABASE_SERVICE_ROLE_KEY`
- Supabase anon keys in backend repo (mobile anon key is public-by-design but still injected via EAS for prod builds)
- `INTERNAL_ADMIN_TOKEN`

### Backend-only secrets

- `DJANGO_SECRET_KEY`
- `DB_PASSWORD` / full `DATABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (if ever used)
- `INTERNAL_ADMIN_TOKEN`
- Database credentials

### Frontend-safe (mobile)

- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`
- `EXPO_PUBLIC_API_BASE_URL`
- `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME`

### EAS relationship (later stage)

EAS production profile injects mobile `EXPO_PUBLIC_*` at build time. Backend prod secrets stay on the **API host only**. Service role key must **never** appear in EAS mobile env.

---

## 10. Risks and blockers

| Blocker | Impact |
| ------- | ------ |
| **Production API URL unknown** | Cannot set TestFlight `EXPO_PUBLIC_API_BASE_URL` until Railway deploy + generated domain |
| **Production backend not deployed** | Owen must create Railway service, set env vars, deploy |
| **Supabase Dev/Prod split not done** | Single project OK for internal smoke; split required before external TestFlight |
| **Production DB migrations / import** | Schema + real import data must exist before meaningful discovery smoke |
| **SSO provider setup incomplete** | Launch-day requirement; separate from API deploy but blocks full TestFlight auth validation |
| **Final domain / privacy / support URLs unknown** | Store listings and OAuth consent; not Django env but blocks launch |
| **No deep health check** | Load balancers cannot verify DB connectivity automatically |
| **`DATABASE_URL` not in `.env.example`** | Operators may miss PaaS-standard config path (code supports it) |
| **`SUPABASE_SERVICE_ROLE_KEY` unused in code** | Low risk today; avoid over-permissioning until needed |
| **No Sentry/logging config** | Harder to diagnose prod issues post-TestFlight |

---

## 11. Recommended implementation stages

| Stage | Focus | Status |
| ----- | ----- | ------ |
| **5** | Production API readiness documentation | Done |
| **5A** | Railway + Gunicorn deploy config in repo | Done — [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) |
| **5B** | Owen: Railway project, env vars, first deploy, smoke | **In progress** — guided checklist in [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) § Stage 5B |
| **5C** | Apply `database/supabase/migrations/`; re-smoke DB routes; plan **real import** (import not run in 5C) | **Guided** — [database/docs/RAILWAY_STAGE_5C_DB_READINESS.md](../../database/docs/RAILWAY_STAGE_5C_DB_READINESS.md), [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) § Stage 5C |
| **5D** | Home default `limit` first Railway tuning (6/12) | Done — superseded by **5E** on production |
| **5E** | Home MVP reliability: default **3**, max **6** per section; re-smoke `/api/v1/home` | Done — [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) § Stage 5E |
| **5F** | Home/search batch card loading; discovery timing logs; re-smoke latency | Done in code — [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) § Stage 5F; Owen: deploy + curl |
| **5G** | Create PubPlus Dev + Prod Supabase split (before external TestFlight) | Pending |
| **5H** | Point TestFlight EAS at Railway URL + matching Supabase (native stages) | Pending |

---

## 12. Owner checklist (Owen)

- [x] Choose **backend hosting target** — Railway
- [x] Add **production WSGI deploy config** in repo (Gunicorn + Railway)
- [ ] Create Railway service (root directory `backend`) — [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
- [ ] Configure **Railway env vars** (see [§3](#3-required-production-environment-variables) and Railway doc)
- [ ] Set `DJANGO_ALLOWED_HOSTS` to Railway generated hostname (no scheme)
- [ ] Apply **Supabase migrations** to target database
- [ ] Load **real import** venue data
- [ ] **Deploy** to Railway; confirm generated **HTTPS** domain
- [ ] Plan **PubPlus Dev / Prod** Supabase split before external TestFlight
- [ ] Confirm `GET /api/v1/health` and auth smoke ([§7](#7-health-checks-and-smoke-checks))
- [ ] Confirm **TestFlight** will use that URL in EAS prod profile
- [ ] Keep **service role** and DB passwords **out of mobile / EAS**
- [ ] Complete **SSO provider** setup on Prod Supabase when ready for TestFlight auth validation ([auth-sso-runbook.md](../../consumer_app/docs/auth-sso-runbook.md))

---

## Related backend documentation

| Doc | Topic |
| --- | ----- |
| [AUTH_MODEL.md](./AUTH_MODEL.md) | Supabase JWT, public vs authenticated routes |
| [API_ENDPOINT_OVERVIEW.md](./API_ENDPOINT_OVERVIEW.md) | `/api/v1` surface |
| [ENVIRONMENT_AND_LOCAL_DEV.md](./ENVIRONMENT_AND_LOCAL_DEV.md) | Local env principles |
| [MELBOURNE_SEED_APPLY.md](./MELBOURNE_SEED_APPLY.md) | Dev seed application |
| [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) | Railway deploy steps and env vars |
