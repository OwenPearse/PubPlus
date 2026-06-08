# Stage 6 — Tap list & drinks

## Purpose

Let verified owners directly manage simple public-facing drink/tap list items for their approved venue. This is **listing content**, not inventory or POS.

## Current stage

**Stage 6 complete.** Owner portal tap list page and CRUD API shipped.

## Decisions

- **Direct edit:** writes `venue_published_tap_offering` (+ validity/eligibility satellites); no proposal/staging/admin review
- **Free-text owner rows:** owner-created drinks use `unstructured_line_label` for `drink_name` with `beverage_product_id = NULL` (no canonical product picker in MVP)
- **Extra display fields** (`brewery_or_brand`, `drink_type`, `abv`, `price_text`, `notes`, `availability`) stored in `venue_published_tap_offering_discovery_eligibility.tier_notes` as JSON (`owner_meta=…`) alongside existing `owner_sort_order=` prefix
- **Availability mapping:** `permanent` → trait flags off; `rotating` → `is_rotating`; `seasonal`/`limited` → `is_limited_run`
- **Deactivate:** `catalog_record_status = retired` (soft delete); no hard delete
- **Reference data:** free-text `drink_type` with length validation — no beverage catalog UI required
- **Skip allowed:** tap list checklist row is optional (`required: false`)

## Schema mapping

| Owner field | Published storage |
|-------------|-------------------|
| `drink_name` | `venue_published_tap_offering.unstructured_line_label` |
| `availability` | `is_rotating`, `is_limited_run` (+ round-trip in tier_notes meta) |
| `active` | `catalog_record_status` (`active` / `retired`) |
| `sort_order` | `sort_order` column + `owner_sort_order=` in tier_notes |
| `brewery_or_brand`, `drink_type`, `abv`, `price_text`, `notes` | `tier_notes` JSON (`owner_meta=`) on discovery_eligibility satellite |
| `beverage_product_id` | Not set by owner MVP create — existing seeded/import rows remain readable via product join |

Satellites on create/update:

- `venue_published_tap_offering_validity` — conservative defaults (`weak`, `uncertain`, suppress strong current-tap claim)
- `venue_published_tap_offering_discovery_eligibility` — detail + list row safe; filter/search and strong current-tap claim withheld for owner free-text lines

## Assumptions

- Migrations `0024`–`0026` applied (`beverage_product`, `venue_published_tap_offering`, validity/eligibility)
- Owners with `manage_published_venue_operations` may CRUD tap lines for approved venues

## Out of scope

- Inventory, stock, keg tracking, suppliers, POS
- Beverage product catalog search UI
- Admin review for tap list edits
- Photos, menus, events, contact schema

## Dependencies

- Stage 4.1 direct-edit + audit pattern
- Stage 2 owner hub / routing

## Acceptance

- [x] Owner hub Tap list row active with link to `/owner/venues/:venueId/tap-list`
- [x] Owner can add, edit, deactivate drink items
- [x] Writes go directly to published tap offering tables
- [x] `audit_event` with `field_family = tap_list`
- [x] Missing capability returns 403
- [x] No proposal/staging rows created

## Next downstream use

Stage 9 review/completeness may treat tap list as optional completeness signal (≥1 active item → `complete`).
