# PubPlus

Monorepo layout:

| Path | Purpose |
|------|---------|
| `consumer_app/` | Consumer mobile app (Expo) — see [consumer_app/README.md](consumer_app/README.md) |
| `web-portal/` | Web portal (internal admin, future owner tools) |
| `backend/` | Django API |
| `database/` | Supabase migrations |

## Portal web (internal admin)

```bash
cd web-portal
cp .env.example .env
pnpm install
pnpm dev
```

Or: `corepack pnpm portal:dev` from the repo root.

See `web-portal/README.md` and `backend/docs/founder-venues/README.md`.