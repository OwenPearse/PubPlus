# Stage 5 — Meal specials & menu

## Purpose

Optional onboarding step for meal specials; menu upload deferred (no menu schema).

## Current stage

Phase B — after Stage 3 and backend staging design for specials.

## Decisions

- Use `venue_published_structured_special.structured_kind` = `meal_special`, `happy_hour`, `venue_offer`
- Menu: static “add menu later” — no file upload in this stage
- Skip allowed; no blocking on basics complete

## Assumptions

- Backend adds owner proposal intake or admin-only publish path for specials before UI.

## Open questions

- Owner staging tables for specials vs admin-only v1.

## Dependencies

- `0021`, `0022`, `0023` migrations (published)
- Stage 3 complete

## Next downstream use

Stage 9 review includes specials summary.

---

## Frontend scope

- Simple list: add/edit/remove special cards (label, kind, recurring window)
- Map to API body agreed in Stage 1 Phase B

## Acceptance

- [ ] Owner can skip step
- [ ] Submitted data lands in workflow tables (not published) OR stage doc updated if admin-only
- [ ] No menu upload UI
