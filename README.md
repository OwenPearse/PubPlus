# PubPlus

Monorepo layout:

| Path | Purpose |
|------|---------|
| `consumer_app/` | Consumer mobile app (Expo) |
| `portal_web/` | Web portal (internal admin, future owner tools) |
| `backend/` | Django API |
| `database/` | Supabase migrations |

## Portal web (internal admin)

```bash
cd portal_web
cp .env.example .env
pnpm install
pnpm dev
```

Or: `corepack pnpm portal:dev` from the repo root.

See `portal_web/README.md` and `backend/docs/founder-venues/README.md`.