# Local Run Guide — Consumer Mobile App

Run the Expo app at `artifacts/mobile` against the Django backend. All commands below assume your shell is in **`consumer_app/`** unless noted.

For workspace layout and integration files, see [README.structure.md](./README.structure.md). Entry point: [README.md](./README.md).

## Prerequisites

- **Node.js** with Corepack enabled: `corepack enable`
- **pnpm** via Corepack (workspace enforces pnpm on install)
- **Python/Django backend** configured from `backend/.env.example`
- **Supabase project** with email/password auth enabled
- Optional: Google/Facebook/Apple providers in Supabase (external dashboard setup required — see [Known gaps](#known-gaps))

For Android emulator: Android Studio + AVD. For iOS simulator: macOS + Xcode (not available on Windows).

## Install

```bash
corepack pnpm install
```

## Environment (mobile)

**Dev/prod Supabase split, physical-device URLs, TestFlight placeholders, and backend alignment:** [docs/environment-strategy.md](./docs/environment-strategy.md).

Copy the example env file:

```bash
cp artifacts/mobile/.env.example artifacts/mobile/.env
```

Edit `artifacts/mobile/.env`. Use only frontend-safe `EXPO_PUBLIC_*` variables.

| Variable | Required | Notes |
|----------|----------|-------|
| `EXPO_PUBLIC_API_BASE_URL` | Yes | Django origin, e.g. `http://localhost:8000` |
| `EXPO_PUBLIC_SUPABASE_URL` | Yes | **Supabase Dev** project URL for local/Expo Go work |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Yes | **Dev** anon/publishable key only — never service role |
| `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` | No | Defaults to `pubplus` |
| `EXPO_PUBLIC_DOMAIN` | No | Legacy Replit variable; ignore for local Cursor dev |

Populated env files are gitignored. Do not commit secrets.

OAuth redirect URLs are listed in `artifacts/mobile/.env.example`. Provider setup and testing: **[docs/auth-sso-runbook.md](./docs/auth-sso-runbook.md)**.

## Backend

The mobile MVP expects Django running locally:

```bash
cd ../backend
python manage.py runserver 8000
```

Configure backend env from `backend/.env.example`. For Expo **web** on port 8081, CORS should include `http://localhost:8081` and `http://127.0.0.1:8081` (already in the example file).

MVP screens use live API calls (`publicApiRequest` / `privateApiRequest` in `artifacts/mobile/lib/api.ts`) — Home, Search, Map, Profile, Saved, venue detail, submissions, and corrections.

## Run — web preview

```bash
corepack pnpm run mobile:web
```

Open in Chrome and enable DevTools **mobile device emulation**. The app is mobile-first; wide desktop layout is not the QA target.

If Metro reports a port conflict, pick a free port:

```bash
corepack pnpm --filter @workspace/mobile exec expo start --web --localhost --port 8082 --clear
```

Add the matching origin (e.g. `http://localhost:8082`) to backend CORS and Supabase auth allow-list if you use OAuth on web.

## Run — Expo Go (simulator or physical device)

```bash
corepack pnpm run mobile:start
```

Scan the QR code with **Expo Go**. Equivalent from `artifacts/mobile/`: `corepack pnpm run start`.

If LAN discovery fails on a physical phone, use tunnel mode:

```bash
corepack pnpm --filter @workspace/mobile exec expo start --tunnel
```

### Physical device backend URL

`EXPO_PUBLIC_API_BASE_URL=http://localhost:8000` works for simulators and web on the same machine. On a **physical device**, `localhost` refers to the phone — set `EXPO_PUBLIC_API_BASE_URL` to a backend origin the device can reach (LAN IP, e.g. `http://192.168.x.x:8000`, or a hosted staging URL). Ensure Django `ALLOWED_HOSTS` and CORS permit that origin if using web tooling.

## Run — Android / iOS simulator

```bash
corepack pnpm run mobile:android
corepack pnpm run mobile:ios
```

## Validation

### Frontend (from `consumer_app/`)

```bash
corepack pnpm run typecheck
corepack pnpm run openapi:lint
```

After OpenAPI spec changes:

```bash
corepack pnpm run openapi:generate
corepack pnpm run typecheck
```

OpenAPI source: `lib/api-spec/openapi.yaml`. Generated outputs under `lib/api-client-react/src/generated/` and `lib/api-zod/src/generated/` — do not hand-edit.

### Backend integration tests (from `backend/`)

```bash
python manage.py test --keepdb --noinput tests.test_auth_boundary tests.test_saved_venues_endpoints tests.test_profile_endpoints tests.test_reference_localities tests.test_submission_endpoints tests.test_discovery_public_endpoints tests.test_home_and_venue_detail_endpoints
```

### Manual QA reference

Historical stage-by-stage verification checklists: [docs/integration-qa-checklists.md](./docs/integration-qa-checklists.md).

## Troubleshooting

| Symptom | Likely cause | What to try |
|---------|--------------|-------------|
| Port already in use | Stale Expo/Metro process | Stop other Expo instances; rerun with `--port 8082 --clear` |
| Blank web page | Bundle failed or wrong viewport | Confirm Metro logs show `Web Bundled`; check console; use mobile emulation |
| API errors on physical device | `localhost` backend URL | Point `EXPO_PUBLIC_API_BASE_URL` at LAN/hosted Django |
| Auth screen shows config warning | Missing Supabase env | Set `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY` in `artifacts/mobile/.env`; restart Metro |
| OAuth fails | Provider not configured | Email/password works without SSO; see [auth SSO runbook](./docs/auth-sso-runbook.md) |
| CORS errors on web | Backend origin mismatch | Add your Expo web origin to `DJANGO_CORS_ALLOWED_ORIGINS` in backend `.env` |

## Legacy / Replit scripts

Do **not** use these for normal local development:

- `artifacts/mobile/package.json` → `dev` script (Replit env vars)
- `artifacts/mobile/scripts/build.js` and `server/serve.js` (Replit static deploy)

Use `mobile:start`, `mobile:web`, `mobile:android`, `mobile:ios`, or the equivalent `start` / `web` scripts in `artifacts/mobile/`.

Whether Replit deployment remains a supported path is **unconfirmed** — treat as legacy until Owen confirms.

## Known gaps

- **No mobile lint or test script** in workspace `package.json` today.
- **SSO** (Google, Facebook, Apple) requires Supabase and external provider setup — [auth SSO runbook](./docs/auth-sso-runbook.md).
- **Native dev builds / EAS / TestFlight** — not documented yet (Stage 4–6). Expo Go is the current local device path.
- **Event discovery UI** is deferred when API returns empty event data.
- **Profile taste preferences** (drinks, features, etc.) are deferred; default suburb and notification toggles are supported.
