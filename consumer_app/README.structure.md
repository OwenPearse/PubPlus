# Consumer App Structure

This workspace is a pnpm monorepo.

## Current frontend app target

- The actual mobile app is `artifacts/mobile` (Expo Router, React Native).
- Consumer/frontend integration work should target this package directly.
- Do not treat full-width desktop web rendering as the product target; use Expo Go and mobile emulation.
- Local run and QA instructions are in `README.local-run.md`.

## Workspace packages

- `artifacts/mobile` - Production-target frontend app.
  - Integration foundation files:
    - `lib/env.ts` - Expo public env access for API/Auth config.
    - `lib/api.ts` - Shared API request helpers for public/private Django calls.
    - `lib/supabase.ts` - Supabase Auth bridge helpers + token/session access.
    - `lib/bootstrap.ts` - App startup bridge to connect auth token getter.
- `artifacts/api-server` - Local API package prototype/server implementation in this workspace.
- `lib/api-client-react` - Generated/react-query API client scaffolding used by mobile package.
- `lib/api-spec` - OpenAPI source + codegen config.
- `lib/api-zod` - Generated Zod types/schema package.
- `lib/db` - Database schema/helpers package for the local API package.

## Cleanup notes

- Replit root files and prompt artifacts have been removed.
- Replit artifact metadata directories were removed.
- Legacy `artifacts/mockup-sandbox` package has been removed during Stage 2C cleanup to keep workspace validation focused on active integration paths.
