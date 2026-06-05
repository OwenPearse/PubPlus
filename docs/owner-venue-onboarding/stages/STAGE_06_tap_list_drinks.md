# Stage 6 — Tap list & drinks

## Purpose

Optional step to capture tap offerings using beverage reference data.

## Current stage

Phase B — after Stage 5 or parallel if API ready.

## Decisions

- Prefer structured lines: `beverage_product_id` + `unstructured_line_label` for guest taps
- Allow skip
- Reference breweries/styles optional in v1 (product picker minimum)

## Assumptions

- `database/sql/seeds/dev_seed_mvp_filter_taxonomy.sql` beverage rows exist in dev.

## Open questions

- Free-text fallback row without `beverage_product_id` for MVP speed.

## Dependencies

- `0024`, `0025` migrations
- Owner intake API for tap proposals (TBD in Stage 1 Phase B)

## Next downstream use

Stage 9 review.

---

## Acceptance

- [ ] Owner can add/remove tap lines and skip step
- [ ] Uses `beverage_product` reference, not ad-hoc duplicate products in UI
- [ ] No published direct write from client
