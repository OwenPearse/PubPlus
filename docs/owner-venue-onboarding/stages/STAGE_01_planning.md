# Stage 1 — Planning + backend contract freeze

## Purpose

Turn Stage 0 discovery into a precise, implementation-ready contract for Phase A owner venue onboarding (list, read, core-details proposal)—without building UI or endpoints.

## Current stage

**Stage 1 — complete.** Contract frozen in `OWNER_VENUE_API_CONTRACT.md`. Ready for Backend Phase A and Stage 2–3.

## Decisions

| Topic | Decision |
|-------|----------|
| Phase A endpoints | `GET /api/v1/owner/venues`, `GET /api/v1/owner/venues/{venue_id}`, `POST /api/v1/owner/venues/{venue_id}/proposals` |
| Write model | One `core_details` bundle → one `venue_change_proposal` + targets `profile`, `geo`, `hours` |
| Publish | Review required; no direct publish; moderation approve does not apply to published tables yet |
| Contact fields | Deferred until `venue_published_contact` + staging migration (documented, not in Phase A API) |
| Claim API | **Out of Phase A** — admin assigns venues; waiting state only |
| Multi-venue | List + `meta.default_venue_id`; frontend may auto-route when `total === 1` |
| Staging simplification | Application-layer bundle only; **no** table drops |
| Admin on owner routes | No |

## Assumptions

- Stage Manager signs off contract before Backend Phase A merge.
- Publish worker is a separate workstream after moderation.

## Open questions

1. Enforce `venue_capability_grant` on every write in Phase A or Phase A+?
2. Auto-move consumer proposals to `in_review` on create — align owner submit behaviour with queue filters?

## Dependencies

- Stage 0 docs (complete)
- `STAGING_REVIEW_PUBLISH_AUDIT.md`
- `OWNER_VENUE_API_CONTRACT.md`

## Next downstream use

- **Backend:** implement `owner_venue_service` + routes + `test_owner_venue_endpoints.py`
- **Frontend Stage 2:** hub + list + optional single-venue redirect
- **Frontend Stage 3:** basics form against contract DTOs

---

## Deliverables (completed)

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | API contract with DTOs, auth, validation | `OWNER_VENUE_API_CONTRACT.md` |
| 2 | Staging/review/publish audit + recommendation | `STAGING_REVIEW_PUBLISH_AUDIT.md` |
| 3 | Updated API requirements | `API_REQUIREMENTS.md` |
| 4 | Updated data capture + contact schema plan | `DATA_CAPTURE_MODEL.md` |
| 5 | Updated UX + routing for Stages 2–3 | `UX_FLOW.md` |
| 6 | Updated stage plan (Stage 1 done) | `STAGE_PLAN.md` |
| 7 | Field classification + validation rules | Contract + DATA_CAPTURE_MODEL |

## Acceptance checklist

- [x] Backend can implement Phase A without guessing
- [x] Frontend can build hub + Step 1 against stable DTOs
- [x] Staging complexity audited; simplification path documented
- [x] Supported vs deferred fields explicit (contact, events, photos, menus)
- [x] No self-approval or direct published writes in contract
- [x] Claim API scope = deferred

## Out of scope (confirmed)

- Implementation (frontend, backend, migrations, RLS)
- Admin review UI changes
- Publish worker
- Optional sections (specials, taps, features, photos)

## Ticket breakdown

| Ticket | Owner | Blocked by |
|--------|-------|------------|
| T1 Backend Phase A APIs | Backend | — |
| T2 Stage 2 owner hub | Frontend | T1 list endpoint (can mock) |
| T3 Stage 3 core form | Frontend | T1 read + POST |
| T4 Publish worker | Backend/Data | Moderation (future) |
| T5 Contact schema migration | Data | — (parallel planning) |
