# Stage 5 — Meal specials direct edit

## Status

**Complete.** Owners with `manage_published_venue_operations` can add, edit, and deactivate recurring meal specials via owner portal CRUD APIs. Writes go directly to published structured specials tables — no proposal/admin review.

## Objective

Let verified owners manage simple recurring food specials (parma night, steak night, Sunday roast, etc.) for their approved venue.

## Product rules

- Direct edit — live on PATCH/POST success
- No admin review for normal meal specials
- No menu PDF upload in this stage
- No drink specials / happy hour drinks in this stage
- Happy hour **food** specials may use `structured_kind = meal_special`

## API endpoints

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/owner/venues/{venue_id}/meal-specials` | List owner-editable meal specials |
| POST | `/api/v1/owner/venues/{venue_id}/meal-specials` | Create |
| PATCH | `/api/v1/owner/venues/{venue_id}/meal-specials/{special_id}` | Update (incl. `active: false`) |
| DELETE | `/api/v1/owner/venues/{venue_id}/meal-specials/{special_id}` | Soft deactivate (`catalog_record_status = retired`) |

**Guards:** `require_owner_portal_auth`, approved relationship, `manage_published_venue_operations`.

## Schema mapping (owner API → published tables)

| Owner API field | Storage |
|-----------------|---------|
| `title` | `venue_published_structured_special.short_label` |
| `description` | `venue_published_structured_special_marketing_copy.body` |
| `price_text` | `venue_published_structured_special_marketing_copy.headline` |
| `conditions` | `venue_published_structured_special_marketing_copy.terms_and_conditions` |
| `days_available` | `venue_published_special_recurring_pattern.recurring_days_of_week` |
| `start_time` / `end_time` | `recurring_pattern.window_*_time_local` |
| `active` | `venue_published_structured_special.catalog_record_status` (`active` / `retired`) |
| `sort_order` | `venue_published_structured_special_discovery_eligibility.tier_notes` prefix `owner_sort_order=N` |

Fixed on create:

- `structured_kind = meal_special`
- `schedule_class = recurring`
- `anchor_timezone = Australia/Melbourne` (MVP default)
- Validity + discovery eligibility satellite rows with strong timing defaults

## Audit

Each write inserts `audit_event` with `action = owner_direct_edit`, `field_family = meal_specials`, bounded before/after `meal_specials` snapshots.

## Frontend

- Route: `/owner/venues/:venueId/meal-specials`
- Component: `OwnerVenueMealSpecialsPage`
- Hub checklist row `meal_specials` active; complete when ≥1 active meal special

## Out of scope

Tap list, photos, menus, events, contact schema, drink specials, admin review queue, billing.

## Tests

- `backend/tests/test_owner_venue_endpoints.py` — CRUD, validation, audit, capability 403
- `web-portal/src/owner/pages/OwnerVenueMealSpecialsPage.test.tsx`
- `web-portal/src/shared/lib/api.owner-venues.test.ts`
