# PubPlus Consumer App

Expo Router mobile app for PubPlus consumers. MVP screens call the **Django API** for discovery, auth-gated flows, profile, saved venues, and submissions.

## App location

| Item | Path |
|------|------|
| Mobile app | `artifacts/mobile` (`@workspace/mobile`) |
| Workspace root | `consumer_app/` (pnpm monorepo) |

## Stack

- Expo SDK ~54, Expo Router ~6
- React Native 0.81.5, React 19.1.0
- TypeScript ~5.9
- Supabase Auth (email/password; OAuth providers need external setup)
- API types from OpenAPI codegen (`@workspace/api-client-react`)

## Backend

The mobile app talks to the **Django API** at `EXPO_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).

`artifacts/api-server` is a **local Express prototype** in this workspace. It is **not** the production backend for the mobile MVP. Do not point the mobile app at it unless you are explicitly experimenting with that package.

## Quick start

From `consumer_app/`:

```bash
corepack pnpm install
```

1. Copy `artifacts/mobile/.env.example` → `artifacts/mobile/.env` and fill in **Supabase Dev** values (see [Environment strategy](./docs/environment-strategy.md)).
2. Start Django from `backend/` (see [Local run guide](./README.local-run.md)).
3. Start the app:

```bash
corepack pnpm run mobile:start    # Expo Go / dev server
corepack pnpm run mobile:web      # Web preview (mobile emulation recommended)
```

Full prerequisites, env details, simulators, and troubleshooting: **[README.local-run.md](./README.local-run.md)**.

## Documentation map

| Doc | Status | Purpose |
|-----|--------|---------|
| [README.local-run.md](./README.local-run.md) | Current | Install, env, run commands, validation, troubleshooting |
| [README.structure.md](./README.structure.md) | Current | Workspace packages and integration file map |
| [docs/environment-strategy.md](./docs/environment-strategy.md) | Current | Local/device/TestFlight env matrix, dev/prod Supabase split, backend alignment |
| [docs/native-testflight-readiness.md](./docs/native-testflight-readiness.md) | Current | EAS/TestFlight path, native config audit, iOS checklists (planning) |
| [../backend/docs/PRODUCTION_API_READINESS.md](../backend/docs/PRODUCTION_API_READINESS.md) | Current | Production Django API deploy readiness for TestFlight |
| [docs/auth-sso-runbook.md](./docs/auth-sso-runbook.md) | Current | Supabase Auth, Google/Facebook/Apple SSO, redirect URLs, testing matrix |
| Release / TestFlight checklist | Planned (Stage 6) | Store submission and prod smoke tests |
| [docs/integration-qa-checklists.md](./docs/integration-qa-checklists.md) | Reference | Historical stage manual verification checklists |

## Commands

Run from `consumer_app/` unless noted.

| Command | Purpose |
|---------|---------|
| `corepack pnpm install` | Install workspace dependencies |
| `corepack pnpm run mobile:start` | Expo dev server (Expo Go) |
| `corepack pnpm run mobile:web` | Expo web on localhost |
| `corepack pnpm run mobile:android` | Open on Android emulator |
| `corepack pnpm run mobile:ios` | Open on iOS simulator (macOS only) |
| `corepack pnpm run typecheck` | TypeScript across workspace + mobile |
| `corepack pnpm run openapi:lint` | Lint OpenAPI spec |
| `corepack pnpm run openapi:generate` | Regenerate API client types from spec |

There is **no mobile lint or test script** defined in this workspace today.

Equivalent scripts exist in `artifacts/mobile/package.json` (`start`, `web`, `android`, `ios`).

## Validation

After dependency or contract changes:

```bash
corepack pnpm run typecheck
corepack pnpm run openapi:lint
```

Backend integration tests (from `backend/`): see [README.local-run.md](./README.local-run.md).

## Environment and Supabase

Local setup, **dev/prod Supabase split** (PubPlus Dev / PubPlus Prod), physical-device API URLs, and backend JWT alignment are documented in **[docs/environment-strategy.md](./docs/environment-strategy.md)**.

TestFlight and production API URLs are **not finalised**; native/EAS planning: **[docs/native-testflight-readiness.md](./docs/native-testflight-readiness.md)**.

## Current limitations

- **EAS/native config not implemented** — planning in [native TestFlight readiness](./docs/native-testflight-readiness.md); `eas.json` and bundle IDs still absent.
- **SSO provider dashboards** — Google, Facebook, and Apple require manual setup (see [auth SSO runbook](./docs/auth-sso-runbook.md)); email/password works when Supabase env is set.
- **No EAS config** — `eas.json` is not present; TestFlight/App Store path is unknown until configured.
- **Replit scripts are legacy** — `artifacts/mobile` `dev` script, `scripts/build.js`, and `server/serve.js` target Replit deployment. Use `mobile:*` / `start` / `web` for local development unless Replit is explicitly confirmed still in use.
- **Physical devices** cannot reach `localhost` for the Django API — use a LAN IP or hosted backend URL (documented in local run guide).

## Product target

Mobile-first. Use Expo Go or device emulation for QA; full-width desktop web is not the primary layout target.
