# PubPlus portal web

Web portal for PubPlus operator and (future) venue-owner experiences. Today it hosts the **internal founder venue lead admin** UI; owner dashboards and additional tools will be added here over time.

The consumer mobile app (`consumer_app/`) stays separate and does not include admin or owner portal code.

## Prerequisites

- Django backend running (default `http://localhost:8000`)
- `DJANGO_CORS_ALLOWED_ORIGINS` includes `http://localhost:3010`
- Supabase project configured (same as consumer app)
- Operator JWT with internal admin access (`pubplus_internal_admin: true` claim or allowlisted `sub` in `PUBPLUS_INTERNAL_ADMIN_SUBJECTS`)

## Local run

```bash
cd portal_web
cp .env.example .env
# Set VITE_API_BASE_URL, VITE_SUPABASE_URL, VITE_SUPABASE_PUBLISHABLE_KEY
pnpm install
pnpm dev
```

From the repo root (if using root `package.json` scripts):

```bash
pnpm portal:dev
```

Open [http://localhost:3010](http://localhost:3010).

## Routes (internal admin)

| Path | Purpose |
|------|---------|
| `/` | Redirect → founder venue list |
| `/internal/founder-venues` | Filterable lead list, export, quick queues |
| `/internal/founder-venues/:leadId` | Detail, edit, enrichment, do-not-contact |

## Workflows

### Top leads

Default list: **VIC**, sorted by founder fit. Use quick filter **VIC 80+** for high-score outreach.

### Needs review

Quick filter **VIC needs review** (`needs_review=true`, state VIC). Review duplicates and enrichment conflicts, then patch or reject.

### Enrich one lead

1. Open lead detail (or use **Enrich dry-run** on the list).
2. **Dry-run** — preview fetched URLs, candidates, product signals, warnings.
3. **Apply enrichment** — writes only after you review the dry-run (`dry_run: false`).

Requires a fetchable venue website (not social URLs).

### Patch lead

Edit allowed fields on the detail page and **Save changes**. The API recomputes founder-fit score server-side.

### Export CSV

**Export CSV** on the list uses current filters. By default:

- excludes do-not-contact leads
- redacts unsafe personal emails
- does not include raw notes

Enable **Include do-not-contact** to export DNC rows.

### Mark do-not-contact

**Mark DNC** on list or detail sets outreach/permission to do-not-contact (not the same as suppression).

## Commands

```bash
pnpm dev
pnpm build
pnpm typecheck
pnpm test
```

## What this app does not do (yet)

- Venue owner portal
- Bulk email or automated outreach
- Public venue publishing
- Convert-to-venue-candidate
- Broad web crawling / new enrichment sources
- Service-role or backend-secret access from the browser

## Manual verification checklist

1. Sign in with an internal-admin Supabase user.
2. Confirm VIC list loads with scores and contact indicators.
3. Open a high-score lead — score breakdown, sources, attributions, events render.
4. Dry-run enrichment on a lead with a real website URL.
5. Patch **notes**, save, confirm success and refetch.
6. Export CSV with current filters; file downloads.
7. Mark a **test** lead do-not-contact (not production outreach targets).

## Related docs

- Founder venue API: `backend/docs/founder-venues/README.md`
- Internal API overview: `backend/docs/INTERNAL_ADMIN_ENDPOINTS.md`
