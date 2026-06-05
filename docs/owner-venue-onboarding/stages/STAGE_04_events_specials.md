# Stage 4 — Events & recurring activities (deferred)

## Purpose

Placeholder stage for live/recurring events—**not implementation-ready** (no events table in schema).

## Current stage

**Deferred** — see `STAGE_PLAN.md`.

## Decisions

- MVP hub shows “Events — coming soon” with skip.
- Do not invent `venue_published_event` in this workstream without Data migration stage.

## Assumptions

- Product may later model recurring activities as `venue_published_structured_special` or dedicated events domain.

## Open questions

- Happy hour overlap with Stage 5 specials (`happy_hour` kind exists).

## Dependencies

- Future schema migration for calendar/recurring events

## Next downstream use

Revise this doc when events migration lands.

---

## If implementing later

- Reuse specials recurring pattern (`0022`) where appropriate
- Owner proposal target family TBD
- Stage 10 QA adds event fixtures

## Acceptance (when un-deferred)

- [ ] TBD after schema design
