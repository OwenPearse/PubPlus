# Stage 7 — Venue features (attributes)

## Purpose

Optional boolean feature toggles from MVP taxonomy—low overwhelm (~8 keys).

## Current stage

**Stage 7 complete.** Direct owner PATCH to `venue_published_attribute_value`; no admin review for MVP boolean toggles.

## Decisions

- Expose only seed keys: `beer_garden`, `rooftop`, `live_music`, `dog_friendly`, `sports_screens`, `pool_table`, `late_night`, `vegan_options`
- Defer TAB/pokies/gambling attributes
- Direct save (not proposal/staging) with `manage_published_venue_operations`
- Boolean values default to `false` when unset in GET

## Assumptions

- Definitions loaded from `venue_attribute_definition` (MVP seed taxonomy)
- `GET/PATCH /api/v1/owner/venues/{venue_id}/features`

## Open questions

- None for MVP set.

## Dependencies

- `0005_discovery_attribute_foundations.sql`
- `dev_seed_mvp_filter_taxonomy.sql`
- Stage 4 direct-edit capability model

## Next downstream use

Completeness checklist in Stage 9.

---

## Frontend scope

- Toggle list with `display_label` from definition
- Save → direct PATCH (published attribute values)

## Acceptance

- [x] Toggles persist as published attribute values
- [x] No hardcoded keys outside seed/stable_key set
- [x] Skip allowed
- [x] Audit `owner_direct_edit` written on save
