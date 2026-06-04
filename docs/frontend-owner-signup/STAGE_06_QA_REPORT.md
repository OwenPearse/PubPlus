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

### MFA (optional — 2026-06-04 policy)

- [ ] Sign-in with AAL1 does **not** force MFA; routes to owner/admin continue.
- [ ] Optional “Set up two-step verification” on post-auth owner panel.
- [ ] Optional MFA prompt on `/owner` (Maybe later dismisses).
- [ ] TOTP enrollment displays QR/manual secret when user opts in.
- [ ] TOTP verification succeeds with valid code.
- [ ] Invalid code shows error.
- [ ] Sign-out works from MFA step.

### Owner

- [ ] New owner sign-up calls provisioning after password auth (no MFA gate).
- [ ] Provisioned owner with no membership sees waiting-for-membership state.
- [ ] Owner with membership but no approved venue sees waiting-for-venue-access state.
- [ ] Owner with approved venue reaches owner placeholder home.
- [ ] AAL1 owner reaches `/owner` without MFA redirect.
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

## Auth smoke blockers — root cause (2026-06-04)

| Symptom | Root cause | Fix |
|---------|------------|-----|
| `Database error querying schema` on sign-in | SQL-seeded `auth.users` rows had **NULL** token columns (`confirmation_token`, etc.). GoTrue scans them as non-nullable strings. Auth log: `confirmation_token: converting NULL to string is unsupported`. | Run `database/sql/dev/repair_auth_users_null_tokens.sql` on dev/staging. Seed file updated to insert `''` for token columns. |
| `Unable to process request` on forgot-password | Same NULL token columns on `/recover`. | Same repair SQL. |
| MFA duplicate-friendly-name dead-end after sign-in | Stale **unverified** `auth.mfa_factors` row + factor list lag after login. | Clear stale factors in dev if needed; frontend now retries factor list (`listTotpFactorsWithRetry`) and maps duplicate errors to Restart setup. |

**Docs:** `docs/frontend-owner-signup/sql/repair-seeded-auth-users.md`

## Auth fix smoke (MFA recovery + forgot password)

**E2E framework:** No web-portal Playwright/Cypress setup; manual browser smoke only where noted.

| Scenario | Automated (Vitest) | Manual / live (post-fix) |
|----------|-------------------|-------------------------|
| New sign-up → MFA without duplicate-factor dead-end | ✅ | ⚠️ Sign-up rate-limited; use seeded QA users |
| Existing verified TOTP → verify step | ✅ | ⏭️ Not run (no verified factor on test user) |
| Stale unverified TOTP → resume / restart setup | ✅ | ✅ After repair + factor clear, fresh enroll shows QR |
| Forgot password → reset email + success copy | ✅ | ⚠️ `email rate limit exceeded` (infra; not schema error) |
| `/access?mode=reset` set-new-password UI | ✅ | ✅ Form + mismatch validation |
| Seeded owner/admin sign-in | — | ✅ `owner1` / `admin1` @ `demo.pubplus.local` after repair SQL |
| Admin `/access` → `/internal/founder-venues` | ✅ | See optional-MFA smoke below |
| Owner AAL1 `/access` → `/owner` (no forced MFA) | ✅ | See optional-MFA smoke below |

**QA helpers:**

- `database/sql/dev/repair_auth_users_null_tokens.sql` — required once for legacy seeded auth rows
- `database/sql/dev/confirm_test_user_email.sql` — email confirm for new sign-ups only

**Password reset completion:** `/access?mode=reset` UI verified. End-to-end reset link not completed (rate limit + no recovery session in browser).

## Manual QA execution log

| Date | Environment | Executor | Result |
|------|-------------|----------|--------|
| 2026-06-04 | local dev | Cursor agent | Vitest green; live Supabase/browser smoke not run (credentials/env) |
| 2026-06-04 | local dev (browser) | Cursor agent | Partial pass — see detailed log below |

### Browser smoke — 2026-06-04

| Field | Value |
|-------|--------|
| Frontend URL | `http://localhost:3011/access` (`pnpm dev`; port 3010 was in use) |
| Backend URL | `http://localhost:8000` (reachable; auth-probe returned 401 without JWT) |
| Supabase project | PubApp (`crvppftccfnkddfaodeh`, ap-southeast-2) |
| Disposable sign-up attempted | `owner-smoke-20260604@test.com` |
| Seeded account used for sign-in | `owner1@demo.pubplus.local` (pre-existing; not created this run) |
| SQL helper run | **No** — not needed for seeded account; sign-up never completed |

#### Step results

| # | Step | Result | Notes |
|---|------|--------|-------|
| 1 | Open `/access` | ✅ Pass | Sign-in / create-account tabs render |
| 2 | Create disposable account | ❌ Fail | `@demo.pubplus.local` rejected as invalid email; `@test.com` hit Supabase **email rate limit exceeded** |
| 3 | Confirm email via SQL helper | ⏭️ Skip | No new user created |
| 4 | Sign in (seeded owner) | ❌ Fail | `owner1@demo.pubplus.local` + seed password → **Database error querying schema** (Supabase Auth) |
| 5 | MFA enroll / duplicate-factor | ⏭️ Blocked | No successful sign-in session |
| 6 | Owner provision after MFA | ⏭️ Blocked | — |
| 7 | Owner landing state | ⏭️ Blocked | — |
| 8 | Sign out / re-sign-in MFA verify | ⏭️ Blocked | DB shows no TOTP factors for `owner1` |
| 9 | Forgot-password request UI | ✅ Pass | Form renders; submit attempted |
| 10 | Forgot-password email send | ❌ Fail | **Unable to process request** (Supabase) |
| 11 | `/access?mode=reset` form | ✅ Pass | “Set a new password”, new/confirm fields, Update password |
| 12 | Reset password mismatch validation | ✅ Pass | “Passwords do not match.” |
| 13 | Reset password submit (recovery session) | ⏭️ Not run | Requires valid reset email link session |
| 14 | Admin → founder-venues | ⏭️ Not run | Sign-in blocked |

#### Blockers (explicit) — superseded by retry below

Resolved: schema error via `repair_auth_users_null_tokens.sql`. Remaining: email rate limits, MFA completion needs real TOTP.

---

### Browser smoke retry — 2026-06-04 (after Auth repair)

| Field | Value |
|-------|--------|
| Frontend URL | `http://localhost:3011/access` |
| Backend URL | `http://localhost:8000` (auth-probe 401 without JWT — reachable) |
| Supabase project | PubApp `crvppftccfnkddfaodeh` |
| Test account | `owner1@demo.pubplus.local` (seeded; password per `OWNER_PORTAL_AUTH.md`) |
| SQL helper: repair tokens | ✅ `repair_auth_users_null_tokens.sql` applied via Supabase SQL (4 demo users fixed) |
| SQL helper: confirm email | ⏭️ Not needed for seeded owner |
| Disposable sign-up | ❌ `@demo.pubplus.local` invalid on signup; `@test.com` rate-limited |

#### Step results (retry)

| # | Step | Result | Notes |
|---|------|--------|-------|
| 1 | `/access` loads | ✅ | |
| 2 | Create disposable account | ❌ | Rate limit / invalid `.local` on signup |
| 3 | Sign in seeded owner | ✅ | After token repair SQL |
| 4 | MFA enroll (no stale factor) | ✅ | QR + manual secret; no duplicate dead-end |
| 5 | MFA verify → provision → `/owner` | ⏭️ | Requires entering live TOTP code |
| 6 | Sign out / re-sign-in MFA verify | ⏭️ | Not run |
| 7 | Forgot-password send | ⚠️ | `email rate limit exceeded` (was schema error before repair) |
| 8 | `/access?mode=reset` | ✅ | |
| 9 | Admin sign-in | ✅ | Reaches MFA enroll (same as owner) |
| 10 | `/internal/founder-venues` | ⏭️ | Blocked at MFA without TOTP |

#### Remaining blockers

1. **Supabase email rate limit** — wait before retrying signup/forgot-password sends.
2. **MFA completion** — smoke agent cannot enter TOTP; human pass required for provision/probe/`/owner`.
3. **Reset link E2E** — needs recovery email + session.

#### Screenshots

Not captured (no project convention in repo for QA image artifacts).

---

### Optional MFA policy smoke — 2026-06-04

| Field | Value |
|-------|--------|
| Policy | Owner portal access at **AAL1**; MFA is optional |
| Frontend | `http://localhost:3011/access` |
| Backend | `http://localhost:8000` (restarted; `localhost:3011` added to `DJANGO_CORS_ALLOWED_ORIGINS`) |
| Seeded owner | `owner1@demo.pubplus.local` / `demo-password-123` |
| **E2E test account (labeled)** | `e2e-optional-mfa-20260604@demo.pubplus.local` / `demo-password-123` — sign-up **not created** (Supabase rejected or error; no `auth.users` row) |
| SQL email bypass | Not run (no new user row) |

| Step | Result | Notes |
|------|--------|-------|
| Owner sign-in | ✅ | No forced MFA enroll step |
| Post-auth panel | ✅ | “Signed in”, **Continue to owner portal**, **Set up two-step verification** (optional) |
| Navigate `/owner` | ⚠️ | Brief `/owner` then session/probe flake back to `/access` in automation; re-test manually |
| Admin sign-in | ⏭️ | Not re-run this pass |
| E2E sign-up + SQL confirm | ❌ | Labeled account above did not persist in Auth |

**Vitest (this change):** `pnpm typecheck` ✅ · `pnpm test` ✅ (114) · `python manage.py test tests.test_owner_endpoints tests.test_auth_boundary` ✅ (21)

---

### E2E owner signup smoke — 2026-06-04 (email confirm + optional MFA)

| Field | Value |
|-------|--------|
| Date/time | 2026-06-04 ~23:00 UTC |
| Frontend URL | `http://localhost:3011/access` |
| Backend URL | `http://localhost:8000` |
| Supabase project | PubApp `crvppftccfnkddfaodeh` |
| **Labeled E2E test account** | `e2e-optional-mfa-20260604@sharklasers.com` / `demo-password-123` |
| Auth user id | `3459875b-4f62-46ef-93a1-73677a706fcc` |
| Owner account id | `513c5206-6688-46de-b225-78a9b5d8cf97` |

#### Sign-up / SQL

| Step | Result | Notes |
|------|--------|-------|
| Sign-up `@test.com` | ❌ | Supabase: `Email address … is invalid` |
| Sign-up `@sharklasers.com` | ✅ | `auth.users` row created; “Check your email” UI |
| SQL email confirm | ✅ | 1 row returned (`email_confirmed_at` set; `confirmed_at` generated) |
| Helper SQL fix | ✅ | Removed `confirmed_at` from `UPDATE` (generated column on PubApp) |

#### Owner flow (no mandatory MFA)

| Step | Result | Notes |
|------|--------|-------|
| Sign-in | ✅ | No MFA enroll/verify gate |
| ownerProvision | ✅ | “Complete owner setup” → provision succeeded (DB row confirmed) |
| ownerAuthProbe | ✅ | `200`, `next_step: owner_waiting_for_membership`, `aal: aal1`, `mfa_required: false` |
| Final route | ✅ | `/owner` — “Awaiting business access” + optional MFA prompt (Set up 2FA / Maybe later) |
| MFA blocking | ✅ | Optional only; access not blocked at AAL1 |

#### Admin regression

| Step | Result | Notes |
|------|--------|-------|
| `admin1@demo.pubplus.local` sign-in | ⚠️ | Pre-fix: post-auth panel sometimes showed “Session expired” (race: role resolve before session persisted). Session-race fix landed; **browser re-check pending** (Vite not running on 3011 at handoff). |
| Direct `/internal/founder-venues` | ✅ | Founder venue leads list loads; admin shell shows `admin1@demo.pubplus.local` |
| Infra fix applied | ✅ | Added seeded admin `sub` to local `PUBPLUS_INTERNAL_ADMIN_SUBJECTS`; set `pubplus_internal_admin` in `app_metadata` for dev QA |

#### Session-race fix (admin post-auth flake)

**Symptom:** After sign-in, `PostAuthPanel` showed “Session expired” even though the Supabase session existed in `localStorage` and manual `internal/auth-probe` returned `200`.

**Cause:** `resolvePortalRole()` and `apiRequest()` each called `getAccessToken()` independently; the second call could run before Supabase persisted the session after `signInWithPassword()`.

**Fix (web-portal):**

| File | Change |
|------|--------|
| `src/shared/lib/supabase.ts` | `waitForAccessToken()` — poll up to 6×100ms after sign-in |
| `src/shared/lib/portalRole.ts` | Use `waitForAccessToken()`; `withUnauthorizedRetry()` (300ms) on internal/owner probes |
| `src/shared/lib/api.ts` | `apiRequest` uses `waitForAccessToken()` instead of one-shot `getAccessToken()` |
| `portalRole.test.ts`, `api.owner.test.ts` | Mock `waitForAccessToken` |

```bash
cd web-portal && pnpm typecheck  # ✅
cd web-portal && pnpm test      # ✅ (114)
```

**Manual re-check (when Vite is up):** hard-refresh `/access`, sign in `admin1@demo.pubplus.local`, confirm “Continue to operator workspace” (not “Session expired”), click through to `/internal/founder-venues`.

#### Remaining blockers

1. `@test.com` / `@demo.pubplus.local` unreliable for Supabase sign-up in PubApp.
2. Admin post-auth panel: code fix in place; **one clean browser pass still needed** after dev server restart + hard refresh.
3. Seeded `admin1` requires dev allowlist or `app_metadata.pubplus_internal_admin` for internal auth-probe.

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
