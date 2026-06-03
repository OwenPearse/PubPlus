# PubPlus portal web

Web portal for PubPlus operator and (future) venue-owner experiences. Today it hosts the **internal founder venue lead admin** UI under `src/admin/`; shared utilities live in `src/shared/`; owner dashboards will go in `src/owner/`.

The consumer mobile app (`consumer_app/`) stays separate and does not include admin or owner portal code.

## Prerequisites

- Django backend running (default `http://localhost:8000`)
- `DJANGO_CORS_ALLOWED_ORIGINS` includes `http://localhost:3010`
- Supabase project configured (same as consumer app)
- Operator JWT with internal admin access (`pubplus_internal_admin: true` claim or allowlisted `sub` in `PUBPLUS_INTERNAL_ADMIN_SUBJECTS`)

## Local run

```bash
cd web-portal
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
| `/internal/founder-venues` | Filterable list, call-sheet mode, outreach quick actions, export |
| `/internal/founder-venues/:leadId` | Detail, outreach panel, contact shortcuts, enrichment, edit |

## Workflows

### Daily outreach (recommended order)

1. Check **dashboard cards** and outreach status counts at the top of the list.
2. Work **High score, not contacted** or **VIC 80+ not contacted** in **call sheet mode**.
3. Mark outcomes as you go (**called** / **emailed** / **replied** / **rejected**).
4. End of day: run **Follow up** (called/emailed with no reply for 7+ days).
5. **Export CSV** only after reviewing the active filter summary (confirm dialog shows safe defaults).

### Dashboard and follow-up queues

The list loads workspace counts from `GET /api/v1/internal/founder-venues/summary` (VIC totals, outreach buckets, missing email, needs review).

| Quick filter | Meaning |
|--------------|---------|
| Follow up | `called` or `emailed`, last contacted more than 7 days ago |
| Called, no reply | `outreach_status=called` |
| Emailed, no reply | `outreach_status=emailed` |
| High score, not contacted | VIC, score ≥ 80, `not_contacted` |
| Missing email | VIC workspace rows missing email |

List rows now include `last_contacted_at`, `last_contact_channel`, and truncated `notes_summary` from the API.

### Call-sheet outreach (manual only)

Use **Call sheet mode** on the list for an operator-focused table: venue, suburb, score, phone, email indicator, website/social links, outreach status, last contacted, and per-row actions.

Quick actions (**Mark called**, **Mark emailed**, etc.) update the lead via the internal API. They record that *you* contacted the venue — the portal does **not** send email, SMS, or automated messages.

- **Mark called** → `outreach_status=called`, `last_contact_channel=phone`, `last_contacted_at=now`
- **Mark emailed** → `outreach_status=emailed`, `last_contact_channel=email`, `last_contacted_at=now`
- **Mark replied** / **Mark rejected** / **Mark signed up** → status + timestamp (deliberate per lead)
- **Mark DNC** → `POST .../mark-do-not-contact` (confirmation required; not PATCH)

**Open next best lead** opens the first row in the current filtered list with `not_contacted` or `queued`, excluding `do_not_contact`, `rejected`, and `signed_up`.

On the detail page, the **Outreach** panel shows status, permission, last contact, notes, the same actions, and **Save notes** / **Save notes + mark …** combos.

Contact legend on list and detail: **P** = phone, **W** = website, **E** = email, **S** = Instagram or Facebook.

### Quick filters

| Filter | Meaning |
|--------|---------|
| VIC 80+ not contacted | VIC, score ≥ 80, `not_contacted`, sort by founder fit |
| VIC 60+ missing email | VIC, score ≥ 60, missing email |
| VIC phone-first | VIC, score ≥ 60, `not_contacted` (use phone column in call sheet) |
| VIC needs review | `needs_review`, VIC |
| Already called / Replied / Signed up / Rejected / DNC | Filter by `outreach_status` |

An **active filter summary** line describes the current list so export and outreach match what you see.

Optional **batch update** (call-sheet mode, selected rows): mark **queued**, **called**, **emailed**, or **rejected** only. Batch **signed up** and **DNC** are intentionally excluded.

### Outreach status definitions

| Status | Meaning |
|--------|---------|
| `not_contacted` | No outreach logged yet |
| `queued` | Planned for outreach |
| `called` | Phone contact attempted or completed |
| `emailed` | Email outreach logged (not sent by PubPlus) |
| `replied` | Venue responded |
| `signed_up` | Converted / signed (manual confirmation) |
| `rejected` | Not interested or not a fit |
| `do_not_contact` | Do not contact (DNC endpoint; excluded from default export) |

### Top leads

Default list: **VIC**, sorted by founder fit. Use quick filter **VIC 80+** or **VIC 80+ not contacted** for high-score outreach.

### Needs review

Quick filter **VIC needs review** (`needs_review=true`, state VIC). Review duplicates and enrichment conflicts, then patch or reject.

### Enrich one lead

1. Open lead detail (or use **Enrich dry-run** on the list).
2. **Dry-run** — preview fetched URLs, candidates, product signals, warnings.
3. **Apply enrichment** — writes only after you review the dry-run (`dry_run: false`).

Requires a fetchable venue website (not social URLs).

### Patch lead

Edit venue/contact fields on the detail page and **Save changes**. Outreach notes and status are managed in the **Outreach** panel. The API recomputes founder-fit score server-side when venue fields change.

### Export CSV

**Export CSV** shows a confirmation with the active filter summary and safe-default reminders before download.

By default:

- excludes do-not-contact leads
- redacts unsafe personal emails
- does not include raw notes

Enable **Include do-not-contact** to export DNC rows.

### Mark do-not-contact

**Mark DNC** on list or detail prompts for an optional reason, requires confirmation, and calls the DNC endpoint (not PATCH).

## Safe manual outreach rules

- The portal records outreach state only; operators contact venues outside the app (phone, email client, social DMs).
- Use **Mark emailed**, not “send email”.
- Do not mark high-value leads DNC or signed up unless intentional.
- Default call-sheet / next-lead queues exclude DNC, rejected, and signed-up leads.
- DNC leads remain visible when filtered explicitly; they are never hidden without a filter.

## Commands

```bash
pnpm dev
pnpm build
pnpm typecheck
pnpm test
```

## What this app does not do

- Send email, SMS, or in-app messages
- Automated dialling, follow-up sequences, or bulk email
- CRM integration or convert-to-venue-candidate
- Venue owner portal or public venue publishing
- Broad web crawling / new enrichment sources
- Service-role or backend-secret access from the browser

## Manual verification checklist

1. Sign in with an internal-admin Supabase user.
2. Confirm VIC list loads; contact legend (**P/W/E/S**) is visible.
3. Click **VIC 80+ not contacted**; confirm active filter summary updates.
4. Enable **Call sheet mode**; confirm phone/links and outreach actions appear.
5. Mark a **test** lead **called**; confirm status and last contacted update.
6. Open detail — **Outreach** panel, contact shortcuts (`tel:` / `mailto:` / new tab links).
7. Save outreach notes; try **Mark replied** or **Mark rejected** on a test lead.
8. **Mark DNC** on a disposable lead — confirm prompt + confirmation.
9. Export CSV with current filters; file downloads.
10. Dry-run enrichment on a lead with a real website URL (optional).

## Related docs

- Founder venue API: `backend/docs/founder-venues/README.md`
- Internal API overview: `backend/docs/INTERNAL_ADMIN_ENDPOINTS.md`
