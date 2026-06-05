# Stage 3 — Core pub info (required)

## Purpose

Implement required onboarding step: display name, address/locality, hours, descriptions—with save-as-you-go via owner proposals API.

## Current stage

Ready for implementation. Requires Backend Phase A `GET` detail + `POST` proposals per contract.

## Decisions

- Route: `/owner/venues/:venueId/basics` (per `UX_FLOW.md`)
- Request: `{ section: "core_details", intent, payload }` per `OWNER_VENUE_API_CONTRACT.md`
- Hide phone/website/email until contact schema exists
- `owner_confirms_management: true` required on submit

## Assumptions

- `GET /api/v1/owner/venues/{venue_id}` returns current published values + pending flags.

## Open questions

- Hours UI: weekly grid component vs JSON editor for v1.

## Dependencies

- Stage 2 hub + active venue context
- `OWNER_VENUE_API_CONTRACT.md` § Endpoints 2–3 + validation
- Backend: `owner_venue_service` (recommended) mirroring `submission_intake_service`

## Next downstream use

Stages 5–7 optional steps; Stage 9 review.

---

## Backend scope

- `GET /api/v1/owner/venues/{venue_id}`
- `POST /api/v1/owner/venues/{venue_id}/proposals` for `profile`, `location`, `hours` (and descriptive copy if separate)
- Venue scope authorization helper (shared with list)
- Tests in `backend/tests/test_owner_endpoints.py` + proposal row assertions

## Frontend scope

- Form pages with validation
- `ErrorBanner`, save + continue
- Locality select (reference data endpoint or static list from API)

## Acceptance

- [ ] Owner can save basics; data appears in `venue_change_proposal` staging (verified via test or SQL)
- [ ] No direct update to `venue_published_*` on save
- [ ] Cannot access other owner’s `venue_id` (403)
- [ ] Hub marks “Pub details” in progress / complete
