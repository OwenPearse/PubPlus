# Stage 5 — Role redirects & route guards

## Purpose

Refactor routing so admin and owner areas use separate guards, shared portal entry resolves role, and redirects match product rules.

## Current stage

**BLOCKED on Backend** until owner auth-probe (or agreed contract) exists.

**Do not merge production owner redirects without a real probe.**

Optional `VITE_OWNER_AUTH_PROBE_STUB=owner|none` is **dev-only** and requires explicit Stage Manager approval—default: do not implement stub.

## Decisions

- Decompose `AuthGate` → `AdminRouteGuard` + public entry; do not keep admin probe on global app root.
- `src/owner/lib/resolvePortalRole.ts` centralizes probe calls.
- `src/owner/pages/OwnerHomePlaceholder.tsx` + `NoVenueAccessState.tsx`
- Admin default redirect: `/internal/founder-venues`

## Assumptions

- `ownerAuthProbe()` added to `api.ts` when Backend ships `GET /api/v1/owner/auth-probe` (path TBD).

## Open questions

- Dual-role JWT handling (deny vs precedence).

## Dependencies

- **Backend:** owner auth-probe endpoint + owner_account provisioning on signup
- Stages 2–4 complete

## Next downstream use

Stage 6 regression tests.

---

## Cursor agent prompt

```
Implement Stage 5 route guards and role redirects in web-portal.

BLOCKER: If owner auth-probe API does not exist, implement resolvePortalRole with:
- internalAuthProbe → admin
- owner probe stub returning 404 → document BLOCKED; optional dev-only env VITE_OWNER_AUTH_PROBE_STUB=owner|none

Read: auth-flow-and-role-redirects.md, STAGE_0_DISCOVERY.md, AGENT_RULES.md

Tasks:
1. Add ownerAuthProbe() to api.ts when endpoint available (else stub module ownerAuthProbe.stub.ts gated by env).
2. Create resolvePortalRole.ts in src/owner/lib/.
3. Create AdminRouteGuard.tsx (admin/) or shared if thin—requires session + internalAuthProbe.
4. Create OwnerRouteGuard.tsx in owner/—session + owner probe + isMfaSatisfied.
5. Refactor App.tsx routes:
   - Public: /access
   - /internal/* → AdminRouteGuard → existing admin pages
   - /owner/* → OwnerRouteGuard → OwnerHomePlaceholder
   - / → redirect logic: if session, resolve role; else /access
6. OwnerHomePlaceholder: portalBrand header, sign out, NoVenueAccessState when probe returns owner without venues (if API signals) or generic awaiting access.
7. AccessDeniedPage for role none.
8. Remove hardcoded "PubPlus Portal" from old AuthGate—delete or reduce AuthGate to re-export guards.

Acceptance:
- Admin user: / → internal founder venues (regression)
- Owner user (when probe works): / → /owner after MFA
- Signed-in no role: access denied page
- Logged out hitting /owner or /internal → /access
- typecheck + tests

Tests:
- resolvePortalRole with mocked api probes
- AdminRouteGuard redirects when probe fails (mock)
- OwnerRouteGuard redirects when MFA not satisfied (mock)
```

## Acceptance criteria

- [ ] No global admin-only gate blocking `/access`
- [ ] Admin routes behave as before for admin JWT
- [ ] Owner routes protected by owner guard + MFA
- [ ] Role redirect matrix implemented (see auth-flow doc)
- [ ] `AuthGate` admin-only UX removed or replaced
- [ ] Uses `portalBrand` in shells

## Test requirements

- Unit: `resolvePortalRole` cases (admin ok, owner ok, neither, both—document expected behavior)
- Component: OwnerRouteGuard redirects unauthenticated to `/access`

## Files touched (expected)

- `web-portal/src/App.tsx`
- `web-portal/src/shared/components/AuthGate.tsx` (refactor/delete)
- `web-portal/src/owner/lib/resolvePortalRole.ts`
- `web-portal/src/owner/components/OwnerRouteGuard.tsx`
- `web-portal/src/admin/components/AdminRouteGuard.tsx` (or shared)
- `web-portal/src/owner/pages/OwnerHomePlaceholder.tsx`
- `web-portal/src/owner/components/NoVenueAccessState.tsx`
- `web-portal/src/shared/lib/api.ts`

## Backend request (for Stage Manager)

Proposed endpoint for Backend/Data Systems:

```http
GET /api/v1/owner/auth-probe
Authorization: Bearer <supabase_jwt>

200 { "status": "ok", "owner_account_id": "...", "venue_count": 0 }
403/404 if not an owner account
```

Signup provisioning: create `owner_account` row linked to `auth.users.id` on owner registration.

**Database:** RLS has no INSERT on `owner_account` for authenticated clients—provisioning must use service role / Django (see `DATABASE_REPORT.md`).
