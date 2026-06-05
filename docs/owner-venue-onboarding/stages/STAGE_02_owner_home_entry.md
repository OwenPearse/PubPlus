# Stage 2 — Owner home entry

## Purpose

Replace `OwnerHomePlaceholder` “future release” with onboarding hub and venue picker when owner has approved venue access.

## Current stage

Ready for implementation. Blocked on Backend Phase A `GET /api/v1/owner/venues` unless using contract mocks.

## Decisions

- `portal_home` + `venue_count > 0` → hub, not empty placeholder.
- `venue_count > 1` → venue picker before hub.
- Keep `NoVenueAccessState` for membership/venue waiting steps unchanged.

## Assumptions

- `OwnerRouteGuard` unchanged; hub lives at `/owner` index or `/owner/home`.

## Open questions

- Persist `activeVenueId` in sessionStorage vs URL param.

## Dependencies

- Stage 1 ✅ — `OWNER_VENUE_API_CONTRACT.md` § Endpoint 1
- `GET /api/v1/owner/venues`
- `UX_FLOW.md` § Stage 2

## Next downstream use

Stage 3 links from hub CTA “Complete pub details.”

---

## Implementation scope

**Files (expected):**

- `web-portal/src/owner/pages/OwnerHomePlaceholder.tsx` → rename or split to `OwnerOnboardingHubPage.tsx`
- `web-portal/src/owner/components/VenuePicker.tsx` (new)
- `web-portal/src/shared/lib/api.ts` — `listOwnerVenues()`
- `web-portal/src/App.tsx` — optional child routes under `/owner`

**UI:**

- Progress checklist (required + recommended rows) per `UX_FLOW.md`
- Loading/error/retry via `ErrorBanner`

## Tests

- Extend `OwnerHomePlaceholder.test.tsx` or new hub tests
- Mock `listOwnerVenues` in API tests

## Acceptance

- [ ] Approved owner sees hub with venue name(s)
- [ ] Waiting states still show `NoVenueAccessState`
- [ ] `pnpm typecheck` + Vitest pass
- [ ] No admin route changes
