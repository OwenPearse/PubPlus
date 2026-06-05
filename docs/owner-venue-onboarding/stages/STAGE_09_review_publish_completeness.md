# Stage 9 — Review, publish status & completeness

## Purpose

Review step summarizing staged changes, submit for review messaging, and client-side completeness checklist.

## Current stage

After Stage 3; partial without live publish pipeline.

## Decisions

- Copy: changes reviewed before going live (accurate)
- Completeness = checklist not server score
- Required: basics step complete; optional sections tracked as `skipped` | `started` | `done` (local or server flags)

## Assumptions

- `GET owner/venues/{id}` exposes `pending_proposals` or equivalent.

## Open questions

- Poll moderation outcome in owner UI v1?

## Dependencies

- Stages 3–7 as applicable
- Publish pipeline (enhancement when available)

## Next downstream use

Stage 10 QA.

---

## Frontend scope

- `/owner/onboarding/review` summary page
- Submit all pending staged proposals (if batch endpoint) or per-family status display
- Link back to incomplete required step

## Completeness (feasible fields)

| Signal | Source |
|--------|--------|
| Display name present | published or staged profile |
| Locality + address | published or staged location |
| Hours | regular hours or uncertainty row |
| Description | descriptive copy |
| Features | any staged/published boolean attrs |
| Specials/taps | count > 0 optional |

## Acceptance

- [ ] Owner sees pending vs no pending states
- [ ] No “Publish live” button that bypasses moderation
- [ ] Checklist matches `UX_FLOW.md`
