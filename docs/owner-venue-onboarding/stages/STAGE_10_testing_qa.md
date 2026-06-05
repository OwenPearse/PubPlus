# Stage 10 — Testing & QA

## Purpose

End-to-end validation of owner onboarding paths, permission boundaries, and regression on admin/owner separation.

## Current stage

Final stage after 2–9 (or 2–3 + 9 for minimal MVP).

## Decisions

- Use demo owners from `database/sql/seeds/dev_seed_demo_accounts_and_relationships.sql`
- Manual QA matrix + automated tests required for touched code

## Assumptions

- Local stack: web-portal `:3010`, Django API, Supabase dev.

## Open questions

- E2E Playwright — only if team already maintains; not required by default.

## Dependencies

- All implemented stages complete

## Next downstream use

Release notes; production readiness checklist.

---

## Automated tests

| Area | Files |
|------|-------|
| Owner guard | `OwnerRouteGuard.test.tsx` |
| Hub | `OwnerHomePlaceholder.test.tsx` or hub successor |
| API | `api.owner.test.ts`, `backend/tests/test_owner_endpoints.py` |
| Proposals | `backend/tests/test_submission_endpoints.py` (pattern), new owner tests |
| Admin regression | `AdminRouteGuard.test.tsx`, founder detail tests |

## Manual matrix

| Actor | Scenario | Expected |
|-------|----------|----------|
| `owner1@demo.pubplus.local` | `portal_home` | Hub + picker if multi |
| New signup | no membership | membership wait state |
| Owner + no venue | venue wait | no edit forms |
| Wrong `venue_id` | API tamper | 403 |
| Admin user | `/owner` | blocked or redirected per dual-access rules |
| Owner | submit basics | staging rows only |

## Acceptance

- [ ] `pnpm typecheck` + owner Vitest green
- [ ] `pytest` owner/submission tests green
- [ ] QA report markdown optional in `docs/owner-venue-onboarding/` if team wants

## Out of scope

- Production load testing
