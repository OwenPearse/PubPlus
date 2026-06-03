# Consumer App Workspace Structure

pnpm monorepo rooted at `consumer_app/`. Entry point for onboarding: [README.md](./README.md). Local run commands: [README.local-run.md](./README.local-run.md).

## Production mobile app

| Item | Path |
|------|------|
| App package | `artifacts/mobile` (`@workspace/mobile`) |
| Router entry | `expo-router/entry` |
| App routes | `artifacts/mobile/app/` |

Consumer and frontend integration work should target **`artifacts/mobile` directly**.

Do not treat full-width desktop web as the product target — use Expo Go, simulators, or mobile browser emulation.

## Workspace packages

| Package | Path | Role |
|---------|------|------|
| `@workspace/mobile` | `artifacts/mobile` | **Production-target** Expo Router app |
| `@workspace/api-server` | `artifacts/api-server` | Local Express **prototype** API — **not** the Django backend the mobile MVP uses |
| `@workspace/api-client-react` | `lib/api-client-react` | Generated OpenAPI types + fetch helpers used by mobile |
| `@workspace/api-spec` | `lib/api-spec` | OpenAPI source (`openapi.yaml`) + codegen config |
| `@workspace/api-zod` | `lib/api-zod` | Generated Zod schemas from the same spec |
| `@workspace/db` | `lib/db` | Database schema/helpers for `api-server` prototype |
| (scripts) | `scripts/` | Workspace tooling |

The mobile app connects to **Django** via `EXPO_PUBLIC_API_BASE_URL`. It does not call `@workspace/api-server` in the MVP integration path.

## Key integration files (`artifacts/mobile`)

| File | Purpose |
|------|---------|
| `lib/env.ts` | Read `EXPO_PUBLIC_*` config (API base URL, Supabase, auth redirect scheme) |
| `lib/api.ts` | `publicApiRequest` / `privateApiRequest` / `healthCheck` → Django `/api/v1/*` |
| `lib/supabase.ts` | Supabase Auth client, email/password, OAuth helpers, session/token access |
| `lib/bootstrap.ts` | Startup: wire API base URL + auth token getter into `@workspace/api-client-react` |

Supporting hooks and mappers under `hooks/`, `lib/mappers.ts`, and screen files consume these helpers for live API data.

## API contract and codegen

- Spec: `lib/api-spec/openapi.yaml` (implemented consumer `/api/v1` paths)
- Generate: `corepack pnpm run openapi:generate` from workspace root
- Mobile imports types from `@workspace/api-client-react`; runtime fetch remains in `lib/api.ts` (not generated React Query hooks)

## `data/mockData.ts`

This file still exists and exports shared **UI types** (e.g. `Venue`) and constants such as `DISTANCE_OPTIONS`. Components and mappers import types from it.

It also contains historical mock venue data. **That does not mean the app is mock-data-only** — MVP screens load data from the Django API. The filename is legacy; a future refactor may rename or split types out.

## Legacy / non-local paths

Replit-oriented artifacts remain under `artifacts/mobile/`:

- `package.json` → `dev` script
- `scripts/build.js`, `server/serve.js`

Use local scripts documented in [README.local-run.md](./README.local-run.md). Replit deploy status is unconfirmed — treat as legacy.

Removed from workspace (historical): Replit root artifacts, `artifacts/mockup-sandbox`.

## Planned documentation (later stages)

- Environment matrix and Supabase dev/prod split — [docs/environment-strategy.md](./docs/environment-strategy.md) (current)
- Native build and EAS — Stage 4
- Auth / SSO / deep-link runbook — Stage 5
- Release and TestFlight checklist — Stage 6
