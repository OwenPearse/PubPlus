# Stage 6 — Testing & validation

## Purpose

Consolidate automated tests and manual QA for owner signup/access workstream; harden edge cases before release.

## Current stage

**Ready after Stages 2–5** (run incrementally as earlier stages land).

## Decisions

- Test runner: existing Vitest + Testing Library in `web-portal/`
- Owner tests live in `src/owner/test/` or colocated `*.test.tsx`
- Extend `vitest.config.ts` setup if owner tests need shared mocks

## Assumptions

- CI runs `pnpm test` and `pnpm typecheck` in web-portal

## Open questions

- E2E with Playwright deferred unless QA requests

## Dependencies

- Stages 2–5 code merged

## Next downstream use

QA / Release manual checklist; Stage Manager sign-off.

---

## Cursor agent prompt

```
Implement Stage 6 testing hardening for frontend-owner-signup.

Tasks:
1. Ensure test coverage per matrix below; fill gaps from stages 2-5.
2. Add src/owner/test/setup.ts only if needed for shared mocks.
3. Update web-portal README.md (short section: portal entry, env vars, test accounts)—minimal.
4. Document manual QA checklist in this file's Acceptance section results.

Run: pnpm typecheck && pnpm test in web-portal/
```

## Test matrix

| Area | Automated | Manual |
|------|-----------|--------|
| Portal entry render | ✅ render `/access` | Visual check branding |
| Sign-in vs sign-up modes | ✅ toggle | Real Supabase sign-in |
| Loading state on submit | ✅ | — |
| Auth error display | ✅ mock failure | Wrong password |
| Session loading | ✅ mock getCurrentSession pending | Refresh page logged in |
| `portalBrand` fallback | ✅ | Change env name |
| MFA enroll/verify UI | ✅ mock | Real TOTP device |
| `resolvePortalRole` admin | ✅ mock probe | Admin JWT e2e |
| `resolvePortalRole` owner | ✅ mock | Owner JWT e2e |
| Admin route guard 403 | ✅ | Non-admin JWT |
| Owner guard without MFA | ✅ | — |
| Redirect admin → `/internal/...` | ✅ mock | Admin login |
| Redirect owner → `/owner` | ✅ mock | Owner login |
| Access denied (no role) | ✅ | Consumer-only JWT? |
| Unprovisioned owner (auth user, no `owner_account`) | ✅ copy/render | Sign-up before Backend provisioning |
| Session expired → `/access` | optional mock 401 | Expire token |
| No venue / awaiting access | ✅ render state | — |
| Admin regression: founder list | ✅ existing admin tests | Load list logged in |

## Acceptance criteria

- [ ] All matrix rows marked implemented or N/A with ticket
- [ ] `pnpm test` and `pnpm typecheck` green
- [ ] No regression in existing `src/admin/test/*`
- [ ] Manual checklist executed once in dev (note results in PR)

## Manual QA checklist

1. Open `/access` logged out — entry page with placeholder brand.
2. Sign up new owner test user — appropriate confirmation/continue messaging.
3. Sign in owner — MFA enroll if first time; verify with authenticator app.
4. Land on `/owner` placeholder — no venue copy if applicable.
5. Sign out — return to `/access`.
6. Sign in internal admin — redirect to founder venues list; list loads.
7. Sign in user without admin/owner — access denied, can sign out.
8. Hit `/internal/founder-venues` logged out — redirect to `/access`.
9. Change `VITE_PORTAL_PRODUCT_NAME` — UI updates after restart.
10. Admin regression: mark test lead called (existing smoke).

## Files touched (expected)

- `web-portal/src/owner/**/*.test.tsx`
- `web-portal/src/owner/lib/resolvePortalRole.test.ts`
- `web-portal/vitest.config.ts` (if setup path extended)
- `web-portal/README.md` (brief)

## Out of scope

- Visual regression / Percy
- Load testing
