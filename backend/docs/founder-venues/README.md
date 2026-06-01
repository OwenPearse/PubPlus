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

**Stage 3 limitation:** scoring uses **imported fields only** — no website enrichment yet. Every breakdown includes a warning: imported data only.

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

## Stage 4 does not include

- Website enrichment or external APIs
- Admin UI / CSV export
- Bulk email, outreach automation
- Convert-to-venue-candidate
- Publishing to `venue_published_*`

## Tests

```bash
cd backend
python manage.py test \
  tests.test_founder_venue_normalization \
  tests.test_founder_venue_import \
  tests.test_founder_venue_scoring \
  tests.test_founder_venue_internal_api \
  --noinput -v 2
```

API tests use mocks for service layer; DB integration tests for import/scoring skip when migration `0033` is not applied.
