# Stage 7 — Venue features (attributes)

## Purpose

Optional boolean feature toggles from MVP taxonomy—low overwhelm (~8 keys).

## Current stage

After Stage 3 (reuse attribute proposal path).

## Decisions

- Expose only seed keys: `beer_garden`, `rooftop`, `live_music`, `dog_friendly`, `sports_screens`, `pool_table`, `late_night`, `vegan_options`
- Defer TAB/pokies/gambling attributes
- Tri-state = unset vs true/false via staging rows

## Assumptions

- `GET /api/v1/reference/attributes` or static list from owner venue read.

## Open questions

- None for MVP set.

## Dependencies

- Stage 3 `attributes` proposal family
- `0005_discovery_attribute_foundations.sql`

## Next downstream use

Completeness checklist in Stage 9.

---

## Frontend scope

- Toggle list with `display_label` from definition
- Save → `venue_proposal_staging_attribute`

## Acceptance

- [ ] Toggles persist as staged proposals
- [ ] No hardcoded keys outside seed/stable_key set
- [ ] Skip allowed
