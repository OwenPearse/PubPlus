# Stage 4 — 2FA (Supabase MFA) frontend flow

## Purpose

Add MFA enrollment and verification UI plus Supabase helper wrappers so owner portal access can require 2FA before entering `/owner`.

## Current stage

**Ready for implementation** — confirm Supabase MFA enabled in project before merging.

## Decisions

- Implement in `src/owner/components/` (`MfaEnrollStep`, `MfaVerifyStep`).
- Extend `src/shared/lib/supabase.ts` with MFA wrappers (thin, documented).
- Flow: after password auth on entry, if role will be owner (or for all portal users until admin policy clarified), show MFA steps on `/access` or sub-routes `/access/mfa/enroll`, `/access/mfa/verify`.

## Assumptions

- TOTP factor via Supabase Auth MFA APIs (verify against current Supabase JS docs at implementation time).
- Session `aal` or `getSession()` indicates whether challenge is satisfied.

## Open questions

- Admins skip MFA at entry? If unknown, apply MFA to all signed-in users entering owner path only; admin-only path uses Stage 5 guards.

## Dependencies

- Supabase dashboard: MFA enabled on **PubApp** (`crvppftccfnkddfaodeh`) — currently 0 `auth.mfa_factors` per `DATABASE_REPORT.md`
- Stage 3 entry page exists
- TOTP only — **no SMS MFA** unless Product approves

## Next downstream use

Stage 5 `OwnerRouteGuard` checks MFA satisfied before rendering `/owner`.

---

## Cursor agent prompt

```
Implement Stage 4 MFA flow for web-portal owner portal access.

Read: auth-flow-and-role-redirects.md, AGENT_RULES.md

Tasks:
1. Research current @supabase/supabase-js MFA APIs; add to supabase.ts:
   - listFactors / enroll / challenge / verify (names per actual API)
   - helper: isMfaSatisfied(session): boolean
2. Create MfaEnrollStep and MfaVerifyStep components under src/owner/components/.
3. Wire PortalEntryPage (or /access/mfa/* routes) to:
   - After successful password sign-in, if MFA not satisfied → show verify or enroll
4. Error states: wrong code, enroll failure, cancel → sign out option
5. Tests with mocked supabase MFA functions

Do NOT implement ownerAuthProbe or /owner dashboard (Stage 5).

Acceptance:
- Manual dev test: enroll + verify with Supabase test user (document steps in PR description)
- Unit tests for isMfaSatisfied logic and component error display
- typecheck + test pass
```

## Acceptance criteria

- [ ] MFA helpers in `supabase.ts` with no duplicate client
- [ ] Enroll + verify UI reachable after sign-in
- [ ] User cannot proceed to `/owner` without satisfied MFA (stub redirect OK: navigate to `/owner` only when isMfaSatisfied true—full guard in Stage 5)
- [ ] Tests mock MFA paths

## Test requirements

- `isMfaSatisfied` unit tests (mock session/JWT claims as implemented)
- Component: verify step shows error on failed verify (mock)

## Risks

- Supabase MFA API changes — verify docs at implementation time.
- Project not MFA-enabled — escalate to infra.

## Files touched (expected)

- `web-portal/src/shared/lib/supabase.ts`
- `web-portal/src/owner/components/MfaEnrollStep.tsx`
- `web-portal/src/owner/components/MfaVerifyStep.tsx`
- `web-portal/src/owner/pages/PortalEntryPage.tsx` (wire-up)
- Tests alongside components
