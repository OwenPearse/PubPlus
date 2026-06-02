# Founder venue leads

## Purpose

Founder venue leads are an **internal research and outreach workspace** for identifying pubs and bars to invite onto PubPlus before consumer launch. The tool supports:

- importing purchased or prepared lead datasets
- normalizing and deduplicating venue contact data
- enrichment with auditable source provenance (later stages)
- founder-fit scoring and outreach/compliance status tracking
- CSV export for manual outreach (later stages)

This is **not** a bulk email or scraping product. It must stay conservative, auditable, and compliant.

## Separate from published venue truth

PubPlus separates domains for trust and access control:

| Domain | Tables (examples) | Role |
|--------|-------------------|------|
| **Published truth** | `venue`, `venue_published_*` | Consumer discovery after moderation/publish |
| **Workflow** | `venue_change_proposal`, staging, `raw_venue_intake_record` | Submissions and moderation |
| **Founder leads** | `founder_venue_leads`, `founder_venue_lead_sources`, … | Pre-launch CRM-style research only |

Founder lead rows may optionally link to `venue.id` when matched, but **must not** write into `venue_published_*` directly. A future “convert to venue candidate” path will create workflow/proposal records for the existing moderation pipeline.

## Stage 2 — CSV import

### Run import (management command)

From `backend/`:

```bash
python manage.py import_founder_venue_leads path/to/file.csv \
  --source-type csv_import \
  --source-name "Pub Australia CSV"
```

Options:

| Flag | Description |
|------|-------------|
| `--source-type` | `csv_import`, `purchased_dataset`, etc. (default: `csv_import`) |
| `--source-name` | Label stored on source rows |
| `--source-url` | Optional provenance URL |
| `--update-existing` | On **strong** duplicate, fill empty lead fields only |
| `--dry-run` | Compute summary without writing |
| `--limit N` | Process at most N data rows |

Example dry run:

```bash
python manage.py import_founder_venue_leads tests/fixtures/founder_venues_sample.csv --dry-run
```

### Programmatic import

```python
from apps.founder_venues.services.import_service import import_founder_venue_leads_csv

result = import_founder_venue_leads_csv(
    csv_text,
    source_type="csv_import",
    source_name="My dataset",
    update_existing=False,
    dry_run=False,
)
```

Returns `FounderVenueImportResult` with counts, `invalid_rows`, `duplicates_needing_review`, and `errors`.

### Supported CSV columns

Headers are matched case-insensitively (spaces/hyphens → underscores). One canonical field per row; first matching alias wins.

| Field | Accepted headers |
|-------|------------------|
| name | `name`, `venue_name`, `business_name`, `business`, `company`, `trading_name` |
| category | `category`, `type`, `business_type`, `venue_type`, `industry` |
| address_line | `address`, `street`, `street_address`, `address_line`, `business_address` |
| suburb | `suburb`, `city`, `town`, `locality` |
| state | `state`, `region` |
| postcode | `postcode`, `postal_code`, `zip` |
| phone | `phone`, `business_phone`, `telephone`, `contact_phone` |
| website | `website`, `business_website`, `url`, `site` |
| email | `email`, `business_email`, `contact_email` |
| instagram_url | `instagram`, `instagram_url` |
| facebook_url | `facebook`, `facebook_url` |
| latitude | `latitude`, `lat` |
| longitude | `longitude`, `lng`, `lon` |
| contact_name | `contact_name`, `manager_name`, `owner_name` |
| contact_role | `contact_role`, `role` |

**Required:** a venue name column. Rows without a name are invalid.

Rows may omit email, phone, website, and coordinates (name + suburb + state is enough).

### Dry-run behavior

Dry run parses and normalizes all rows, runs duplicate lookups against the database, and returns the same summary fields **without** inserting leads, sources, attributions, or events.

### Dedupe behavior

**Strong duplicate** (no new lead; skipped or merged with `--update-existing`):

- Same normalized website host
- Same normalized AU phone
- Same normalized email
- Same `dedupe_key`

**Probable duplicate** (new lead still created with `enrichment_status = needs_review`):

- Same `normalized_name` + `postcode`, or
- Same `normalized_name` + `suburb` + `state`

Probable matches are listed in `duplicates_needing_review` for admin follow-up. No fuzzy matching.

### Source provenance

Each created/updated lead gets:

- `founder_venue_lead_sources` — full CSV row in `raw_payload`, import `source_type` / `source_name` / `source_url`, confidence
- `founder_venue_lead_field_attributions` — per populated field (`raw_value`, `normalized_value`, email `contact_safety_class`)
- `founder_venue_lead_events` — `import_created`, `import_updated`, `import_duplicate_skipped`, or `import_needs_review`

### Contact permission defaults

| Condition | `contact_permission_status` |
|-----------|-------------------------------|
| Imported row has phone and/or email | `public_business_contact` |
| Otherwise | `unknown` |

Import does **not** set `opted_in`, `requested_info_*`, or send email.

### Email safety (import)

Emails are classified for attribution (`generic_business_contact`, `role_based_contact`, `personal_business_contact`, `likely_personal_or_unsafe`). Unsafe/personal emails do not receive the +10 confidence bonus but are not rejected.

### Initial confidence score (import only)

Starts at 30; bonuses for phone, website, business email, social link, full address, coordinates; capped at 80 (70 for `purchased_dataset` without phone/website). This is separate from founder-fit score (Stage 3).

## Stage 3 — Founder-fit scoring and ranking

Founder-fit scores are **prioritisation aids** for founder outreach — not published truth labels. Scores are deterministic, explainable, and safe to recompute.

### How scoring works

`compute_founder_fit_score(lead)` in `services/scoring.py` returns a 0–100 score and JSON breakdown stored in `founder_fit_breakdown`.

| Component | Max | What it measures |
|-----------|-----|------------------|
| Location | 25 | Launch geography (inner Melbourne priority suburbs, VIC metro/regional, other AU states) |
| Category | 20 | Pub/bar/brewery fit vs unrelated categories |
| Contactability | 20 | Phone, website, safe business email, social links |
| Data quality | 15 | Import confidence, address completeness, coordinates, provenance |
| Product fit | 15 | Keywords in name/category/notes (trivia, live music, events, etc.) |
| Strategic | ± | Independent venue bonus; penalties for do-not-contact, suppressed, etc. |

Penalties apply for `do_not_contact`, `opted_out`, `rejected` outreach, and `suppressed_at`.

**Stage 3 note:** scoring uses lead fields and `source_summary` (including website signals after Stage 6 enrichment). Unenriched leads include an import-only warning in the breakdown.

### Recompute scores

```bash
cd backend

python manage.py recompute_founder_venue_scores --state VIC --limit 500 --dry-run --show-top

python manage.py recompute_founder_venue_scores --state VIC --limit 500 --show-top --top-limit 20
```

Options: `--state`, `--lead-id` (repeatable), `--limit`, `--dry-run`, `--show-top`, `--top-limit`.

Writes `founder_fit_score`, `founder_fit_breakdown`, and event `founder_fit_score_recomputed`.

### List top venues (CLI ranking)

```bash
python manage.py list_top_founder_venues --state VIC --limit 20
```

Excludes suppressed leads and do-not-contact / opted-out by default. Ordered by founder-fit score, then confidence, then updated_at.

### Programmatic use

```python
from apps.founder_venues.services.scoring import compute_founder_fit_score
from apps.founder_venues.services.founder_fit_db import (
    recompute_founder_fit_scores,
    get_top_founder_venue_leads,
)
```

## Stage 4 — Internal API

All routes require `@require_internal_admin_auth` (Bearer JWT + `pubplus_internal_admin` claim or allowlisted subject).

Base path: `/api/v1/internal/founder-venues/`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/leads` | List/filter leads (paginated) |
| GET | `/leads/{id}` | Detail + sources + attributions + events |
| PATCH | `/leads/{id}` | Manual field update + recompute score |
| POST | `/leads/{id}/mark-do-not-contact` | Set DNC statuses (no `suppressed_at`) |
| POST | `/import` | CSV import (`csv_text`, max 5MB) |
| POST | `/recompute-scores` | Batch founder-fit recompute |
| GET | `/top` | Ranked top leads |
| GET | `/export.csv` | Filtered CSV export (Stage 5) |
| POST | `/leads/{id}/enrich` | Website enrichment (Stage 6) |

### Example: import

```http
POST /api/v1/internal/founder-venues/import
Authorization: Bearer <internal-admin-jwt>
Content-Type: application/json

{
  "csv_text": "business_name,suburb,state\nExample Pub,Fitzroy,VIC",
  "source_type": "csv_import",
  "source_name": "Manual upload",
  "update_existing": false,
  "dry_run": false
}
```

### Example: list

```http
GET /api/v1/internal/founder-venues/leads?state=VIC&sort=founder_fit_score_desc&limit=50
Authorization: Bearer <internal-admin-jwt>
```

### Validation

- UUID lead ids
- Enum status values (enrichment, outreach, contact permission)
- `sort` whitelist only (no raw SQL sort injection)
- `limit` max 200 (list), recompute max 1000
- Patch allows only documented editable fields

### Do-not-contact decision

`mark-do-not-contact` sets `outreach_status` and `contact_permission_status` to `do_not_contact` but **does not** set `suppressed_at`, so internal history remains visible unless filtered by list defaults (`include_do_not_contact=false`).

Scores are prioritisation aids, not published truth.

## Stage 5 — CSV export

Filtered CSV export for manual calling sheets or CRM import. No messages are sent.

### Default safety behavior

By default, export:

- excludes `outreach_status = do_not_contact`
- excludes `contact_permission_status` in (`opted_out`, `do_not_contact`)
- excludes rows with `suppressed_at` set
- includes only outreach-safe emails (`generic_business_contact`, `role_based_contact`)
- redacts `personal_business_contact` and `likely_personal_or_unsafe` emails (blank `email`, reason in `email_redacted_reason`)
- truncates `notes` into `notes_summary` (200 chars); full `notes` only with `include_raw_notes=true`

Even when `include_do_not_contact=true`, emails stay redacted unless `include_unsafe_emails=true`; status columns still show DNC/opt-out.

### Email redaction (`email_redacted_reason`)

| Value | Meaning |
|-------|---------|
| *(blank)* | Email exported as-is |
| `personal_business_contact` | Redacted (unsafe class) |
| `likely_personal_or_unsafe` | Redacted (unsafe class) |
| `do_not_contact` | Redacted (DNC status) |
| `opted_out` | Redacted (opt-out) |
| `suppressed` | Redacted (suppression) |

Classification uses latest `founder_venue_lead_field_attributions` row for `email`, else `contact_safety.classify_email_contact_safety`.

### Export command

```bash
cd backend

python manage.py export_founder_venue_leads \
  --state VIC \
  --score-min 60 \
  --limit 500 \
  --output /tmp/pubplus_founder_venues_vic.csv
```

Without `--output`, CSV is written to stdout. The command prints row count, filters applied, and exclusion/redaction summary.

Options mirror list filters plus:

| Flag | Description |
|------|-------------|
| `--include-do-not-contact` | Include DNC/opt-out rows (email still redacted by default) |
| `--include-suppressed` | Include suppressed rows |
| `--include-unsafe-emails` | Export personal/unsafe emails |
| `--include-raw-notes` | Add full `notes` column |
| `--limit` | Default 1000, max 5000 |
| `--offset` | Pagination offset |

### API export

```http
GET /api/v1/internal/founder-venues/export.csv?state=VIC&score_min=60&limit=500
Authorization: Bearer <internal-admin-jwt>
```

Response: `text/csv` with `Content-Disposition: attachment; filename="pubplus_founder_venues_YYYYMMDD.csv"`.

Query params match the export service (`include_unsafe_emails`, `include_raw_notes`, etc.).

### CSV columns (default)

`founder_venue_lead_id`, `venue_name`, `suburb`, `state`, `postcode`, `category`, `phone`, `email`, `email_redacted_reason`, `website`, `instagram_url`, `facebook_url`, `founder_fit_score`, `confidence_score`, `enrichment_status`, `outreach_status`, `contact_permission_status`, `source_summary`, `notes_summary`, `last_contacted_at`, `last_contact_channel`.

Ordered by founder-fit score (desc), then confidence, then updated_at.

### Audit events

Each exported lead (up to the export limit) gets `founder_venue_lead_events.event_type = lead_exported` with metadata: `export_type`, `filters_applied`, inclusion flags.

### CRM / calling workflow

1. Filter and export a ranked list (e.g. VIC pubs, `score_min=60`).
2. Import CSV into your CRM or use as a call sheet.
3. Update lead status via internal API (`PATCH`, `mark-do-not-contact`) after contact.
4. Re-export only when needed; prior exports are auditable via events.

## Stage 6 — Website enrichment

Conservative enrichment from each lead’s **own known website** — not a broad internet scraper.

### Purpose

Improve lead quality by filling missing contact/social fields and capturing PubPlus-relevant product signals (trivia, live music, functions, etc.) with full provenance.

### Fetch policy

| Rule | Value |
|------|--------|
| Pages per lead | Homepage + up to 4 same-origin allowlisted paths (max 5 total) |
| Timeout | 8 seconds per request |
| Max body size | ~1 MB per page |
| Content types | `text/html`, `application/xhtml+xml` only |
| Same-origin only | Links must match venue website host |
| Path keywords | contact, about, functions, events, whats-on, bookings, sport, trivia, live-music, … |
| Not fetched | PDFs/images, social hosts (Instagram/Facebook URLs recorded, not fetched), non-http(s) |

Sequential processing with ~1 second minimum interval per domain in batch runs. No headless browser, no login bypass, no third-party site crawling.

Leads whose `website` is a Facebook/Instagram URL are **excluded from batch enrichment** (social profiles are not fetched). Single-lead enrich returns `website_not_fetchable` with a clear warning.

### Auto-promotion vs review

| Field | Auto-promote when |
|-------|-------------------|
| Email | Empty and `generic_business_contact` or `role_based_contact` on venue/group domain |
| Phone / Instagram / Facebook | Empty and extracted with sufficient confidence |
| Product signals | Appended to `source_summary` (not raw notes) |

| Situation | Result |
|-----------|--------|
| `personal_business_contact` / `likely_personal_or_unsafe` email | Attribution only; `needs_review` if no safe email |
| Conflicting existing email/phone/social | `enrichment_status = needs_review` |
| Successful safe enrichment | `enrichment_status = enriched` + founder-fit recompute |

### Management command

```bash
cd backend

python manage.py enrich_founder_venue_websites \
  --state VIC \
  --missing-email \
  --limit 25 \
  --dry-run

python manage.py enrich_founder_venue_websites --lead-id <uuid> --limit 1
```

Options: `--lead-id` (repeatable), `--state`, `--suburb`, `--missing-email`, `--missing-phone`, `--missing-socials`, `--score-min`, `--limit` (default 10, max 100), `--dry-run`.

### API

```http
POST /api/v1/internal/founder-venues/leads/{lead_id}/enrich
Authorization: Bearer <internal-admin-jwt>
Content-Type: application/json

{ "dry_run": true }
```

Returns JSON summary (candidates, signals, warnings, errors) — not raw HTML.

### Provenance

Each run adds:

- `founder_venue_lead_sources` (`source_type = venue_website`, `raw_payload.fetched_urls`)
- `founder_venue_lead_field_attributions` per candidate
- Event `website_enrichment_completed` or `website_enrichment_failed`

Uses stdlib `urllib` (no new HTTP dependencies).

## Stage 6.5 — Social URL cleanup

Many purchased datasets store Facebook/Instagram URLs in `business_website`. Stage 6.5 routes them to the correct fields and cleans existing data.

### Import behavior (new rows)

`url_classification.apply_import_url_routing()` runs during CSV import:

| Website column classifies as | Stored in |
|------------------------------|-----------|
| `facebook` | `facebook_url` (if empty) |
| `instagram` | `instagram_url` (if empty) |
| `website` | `website` (normalized) |
| `other_social` / `invalid` | not stored as `website` |

Existing `facebook_url` / `instagram_url` values are never overwritten. Original CSV values are kept in field attributions.

Google Maps, Linktree, TripAdvisor, login/share URLs are **not** treated as venue websites.

### Cleanup command (existing leads)

```bash
cd backend

python manage.py cleanup_founder_venue_social_urls \
  --state VIC \
  --limit 500 \
  --dry-run

python manage.py cleanup_founder_venue_social_urls --state VIC --limit 500
```

Options: `--lead-id`, `--state`, `--limit`, `--dry-run`, `--no-recompute`.

Each updated lead gets `social_url_cleanup_applied` event, source row, and attributions. Founder-fit scores recompute by default.

### Impact

- Website enrichment batch no longer wastes slots on Facebook URLs
- `website` completeness reflects real venue domains
- Social links populate `facebook_url` / `instagram_url` for export and scoring

## Stage 6 does not include

- Headless browser / search-engine lookup
- Google Places, Apify, data brokers
- Broad crawling or parallel batch fetch
- Admin UI, bulk email, automated outreach
- Convert-to-venue-candidate or publishing to `venue_published_*`

## Stage 5 does not include

- Website enrichment (see Stage 6)
- Admin UI
- Bulk email, outreach automation
- Convert-to-venue-candidate
- Publishing to `venue_published_*`

## Stage 4 does not include

- Website enrichment or external APIs
- Admin UI / CSV export (see Stage 5)
- Bulk email, outreach automation
- Convert-to-venue-candidate
- Publishing to `venue_published_*`

## Stage 7 — Internal admin UI

Web UI for operators (Vite + React). Lives in `portal_web/` (dedicated portal app, separate from the consumer mobile app).

### Run locally

```bash
cd portal_web
cp .env.example .env
# VITE_API_BASE_URL=http://localhost:8000
# VITE_SUPABASE_URL / VITE_SUPABASE_PUBLISHABLE_KEY (internal-admin JWT)
pnpm install
pnpm dev
```

Or from the repo root: `pnpm portal:dev` (requires root `package.json` scripts).

Open `http://localhost:3010` → `/internal/founder-venues`.

Full UI guide: `portal_web/README.md`.

### UI capabilities

- List/filter leads (default VIC, founder-fit sort)
- Quick queues: VIC 80+, VIC 60+ missing email, needs review, no contact channels
- Lead detail: score breakdown, sources, attributions, events
- PATCH editable fields (server recomputes score)
- Website enrich dry-run / apply
- Mark do-not-contact
- Export filtered CSV (safe defaults)

### Stage 7.2 — Outreach workflow UI

Manual call-sheet mode, outreach quick actions (called/emailed/replied/rejected/signed up), DNC with confirmation, outreach notes, next-best-lead navigation, expanded quick filters, and optional batch status updates (queued/called/emailed/rejected only). State changes use existing `PATCH` and `POST .../mark-do-not-contact` — no messaging from the portal.

See `portal_web/README.md` for operator workflows and status definitions.

### Stage 7.3 — Outreach operations polish

- **List DTO:** `last_contacted_at`, `last_contact_channel`, `notes_summary` (truncated; not full notes).
- **List filters:** `contacted_before`, `contacted_after`, `last_contact_channel`, `outreach_status_in` (comma-separated).
- **Summary:** `GET /api/v1/internal/founder-venues/summary` — workspace outreach/enrichment counts for dashboard cards.
- **Portal:** dashboard cards, follow-up quick filters, call-sheet polish (full phone, status badges, button actions), export confirm dialog, grouped outreach panel, readable activity log.

Final portal-focused stage before pausing portal work for a TestFlight-ready consumer app prototype.

### Stage 7 does not include

- Bulk email, automated outreach, publishing, convert-to-venue-candidate
- New enrichment sources or broad crawling
- Service-role keys in the browser

## Tests

```bash
cd backend
python manage.py test \
  tests.test_founder_venue_normalization \
  tests.test_founder_venue_import \
  tests.test_founder_venue_scoring \
  tests.test_founder_venue_internal_api \
  tests.test_founder_venue_export \
  tests.test_founder_venue_enrichment \
  tests.test_founder_venue_social_cleanup \
  --noinput -v 2
```

API tests use mocks for service layer; DB integration tests for import/scoring skip when migration `0033` is not applied.
