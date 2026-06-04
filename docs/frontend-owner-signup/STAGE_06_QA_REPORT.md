# Stage 6 — QA report & release readiness

## Purpose

Final regression and release-hardening record for the frontend owner signup & portal access workstream (`web-portal/`). Documents automated coverage, manual QA checklist, infra blockers, and sign-off status.

## Current stage

**Stage 6 complete (automated)** — manual QA checklist below is ready for a human pass in dev/staging. No Playwright/E2E suite exists in `web-portal/`; validation is Vitest + manual smoke.

## Decisions

- High-value unit/component tests only; no new E2E framework.
- `AuthGate` remains a deprecated re-export of `AdminRouteGuard` (zero imports outside `AuthGate.tsx`); safe to remove in a later cleanup PR.
- Manual MFA and live Supabase flows are out of scope for CI; documented as blockers.
- Release readiness = automated green + documented manual checklist, not full production sign-off without manual pass.

## Assumptions

- Backend owner endpoints from Stage 5 backend work are deployed to the environment under test.
- PubApp Supabase project matches `web-portal/.env` (`VITE_SUPABASE_URL`, publishable key).
- Domain separation prevents the same JWT from passing both admin and owner probes in normal operation; dual-access UI is defensive only.

## Open questions

- Product: require MFA for internal admin at `/access`? (Currently admin can continue after portal MFA step if session reaches AAL2.)
- When to remove deprecated `AuthGate` export after confirming no external packages import it.

## Dependencies

| Dependency | Status |
|------------|--------|
| Stages 2–5 merged in `web-portal/` | ✅ |
| `POST /api/v1/owner/provision` | Required for owner sign-up |
| `GET /api/v1/owner/auth-probe` | Required for owner routing |
| `GET /api/v1/internal/auth-probe` | Required for admin routing |
| Supabase MFA (TOTP) enabled | Required for MFA UI |
| `web-portal/.env` | API + Supabase + optional branding vars |

## Next downstream use

- QA / Release: execute manual checklist once per environment.
- Stage Manager: sign off workstream when manual rows are checked in dev.
- Future: optional Playwright smoke for `/access` → `/owner` with test users.

---

## Automated validation (Stage 6 agent run)

```bash
cd web-portal
pnpm typecheck   # pass
pnpm test        # pass (see test count in CI)
```

### Test matrix (Stages 2–6)

| Area | Automated | Notes |
|------|-----------|-------|
| `portalBrand` fallback / env | ✅ `portalBrand.test.ts` | |
| `/access` render & modes | ✅ `PortalEntryPage.test.tsx` | |
| Sign-in / sign-up / errors | ✅ `PortalEntryPage.test.tsx` | |
| MFA enroll / verify | ✅ `MfaEnrollStep.test.tsx`, `MfaVerifyStep.test.tsx`, `supabase.mfa.test.ts` | |
| `ownerProvision` / `ownerAuthProbe` | ✅ `api.owner.test.ts` | |
| `resolvePortalRole` | ✅ `portalRole.test.ts` | incl. dual-access |
| `portalRedirect` helpers | ✅ `portalRedirect.test.ts` | Stage 6 |
| `RootRedirect` | ✅ `RootRedirect.test.tsx` | Stage 6 |
| `AdminRouteGuard` | ✅ `AdminRouteGuard.test.tsx` | |
| `OwnerRouteGuard` | ✅ `OwnerRouteGuard.test.tsx` | incl. 401 → `/access` |
| Owner empty states | ✅ `OwnerHomePlaceholder.test.tsx`, `NoVenueAccessState.test.tsx` | Stage 6 |
| Access denied page | ✅ `AccessDeniedPage.test.tsx` | Stage 6 |
| App routing (public / admin / owner) | ✅ `App.test.tsx` | |
| Admin founder list/detail/regression | ✅ `src/admin/test/*` | unchanged suites |

### AuthGate audit

```
grep AuthGate web-portal → only web-portal/src/shared/components/AuthGate.tsx (deprecated re-export)
```

**Recommendation:** Remove `AuthGate.tsx` in a follow-up cleanup after release; not removed in Stage 6 to avoid unnecessary churn.

---

## Manual / infra blockers

1. **Supabase MFA (TOTP)** must be enabled in the PubApp dashboard. Until enabled, `auth.mfa_factors` stays empty and JWT remains `aal1`; enroll/verify UI cannot be completed end-to-end.
2. **Test accounts**
   - Owner (seeded): `owner1@demo.pubplus.local` / `demo-password-123` (see `backend/docs/OWNER_PORTAL_AUTH.md`)
   - Owner (new sign-up): disposable email for provision + MFA path
   - Admin: Supabase user with `pubplus_internal_admin` or allowlisted `sub`
   - Consumer-only JWT (optional): verify `/access/denied` copy
3. **Backend** must expose and allow CORS from portal origin:
   - `POST /api/v1/owner/provision`
   - `GET /api/v1/owner/auth-probe`
   - `GET /api/v1/internal/auth-probe`
4. **`web-portal/.env`**
   - `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`
   - Optional: `VITE_PORTAL_PRODUCT_NAME`, `VITE_PORTAL_PRODUCT_TAGLINE`, `VITE_PORTAL_SUPPORT_URL`
5. **No browser insert into `owner_account`** — provisioning is server-side only (verified by design).

---

## Manual QA checklist

Record results in PR or below (`[ ]` pending, `[x]` pass, `[!]` fail + note).

### Public entry

- [ ] `/access` loads logged out.
- [ ] Placeholder brand name/logo appears (`portalBrand` / `VITE_PORTAL_PRODUCT_NAME`).
- [ ] Sign-in mode renders.
- [ ] Create-account mode renders.
- [ ] Invalid credentials show error.
- [ ] Support link works if `VITE_PORTAL_SUPPORT_URL` is set.

### MFA

- [ ] Sign-in with AAL1 reaches MFA step.
- [ ] TOTP enrollment displays QR/manual secret.
- [ ] TOTP verification succeeds with valid code.
- [ ] Invalid code shows error.
- [ ] Sign-out works from MFA step.
- [ ] AAL2 session proceeds to routing / continue state.

### Owner

- [ ] New owner sign-up calls provisioning after MFA where applicable.
- [ ] Provisioned owner with no membership sees waiting-for-membership state.
- [ ] Owner with membership but no approved venue sees waiting-for-venue-access state.
- [ ] Owner with approved venue reaches owner placeholder home.
- [ ] AAL1 owner is returned to `/access` MFA flow when hitting `/owner`.
- [ ] Missing owner account shows clear provisioning or denied state.

### Admin

- [ ] Admin can sign in via `/access`.
- [ ] Admin lands at or can continue to `/internal/founder-venues`.
- [ ] Founder venues list renders.
- [ ] Founder venue detail renders.
- [ ] Admin sign-out works.

### Root / session

- [ ] `/` resolves based on session/role.
- [ ] Logged-out `/internal/*` and `/owner/*` redirect to `/access`.
- [ ] Expired session returns to `/access` (or session-expired query).
- [ ] Dual admin+owner state shows safe error/denied behaviour (if testable).

### Admin regression smoke

- [ ] Mark a test lead **called** on list or detail.
- [ ] Export CSV with active filters (confirm dialog).

---

## Manual QA execution log

| Date | Environment | Executor | Result |
|------|-------------|----------|--------|
| _pending_ | local dev | — | Not run in Stage 6 agent session (requires live Supabase + backend) |

---

## Release readiness summary

| Criterion | Status |
|-----------|--------|
| `pnpm typecheck` | ✅ Pass (agent) |
| `pnpm test` | ✅ Pass (agent) |
| Admin regression tests | ✅ Pass (agent) |
| High-value test gaps filled | ✅ Stage 6 additions |
| Manual checklist documented | ✅ This file |
| MFA / backend / env blockers documented | ✅ Above |
| No owner dashboard / claim-venue scope | ✅ |
| No `owner_account` browser insert | ✅ |

**Verdict:** Ready for **manual QA pass in dev** and Stage Manager sign-off. Not a substitute for staging smoke with real Supabase MFA and seeded accounts.
