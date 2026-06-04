# Auth flow & role redirects

## Purpose

Specify session lifecycle, Supabase reuse, role-based redirects, and route guard expectations for owner vs admin portal areas.

## Current stage

**Stage 1 complete** — Stage 5 implementation **blocked** until Backend owner auth-probe exists.

## Decisions

| Item | Decision |
|------|----------|
| Identity provider | Supabase Auth only (`shared/lib/supabase.ts`) |
| Admin authorization (API) | Existing `GET /api/v1/internal/auth-probe` + JWT `pubplus_internal_admin` or allowlist |
| Owner authorization (API) | **TBD** — propose `GET /api/v1/owner/auth-probe` (name negotiable with Backend) |
| Entry route | Public `/access` — no probe before credentials |
| Admin redirect target | `/internal/founder-venues` (current default home) |
| Owner redirect target | `/owner` placeholder |
| Global wrapper | Replace monolithic admin-only `AuthGate` with composable guards |

## Assumptions

- Same Supabase user cannot be both owner and admin (domain separation); if JWT matches both probes, **product must define precedence**—default: deny and show support message until clarified.
- `api.ts` continues to attach Bearer token from `getAccessToken()`.

## Open questions

1. Owner probe response shape: `{ status, owner_account_id, businesses?, venues? }`?
2. Should frontend read `app_metadata` for role hints, or **only** backend probes? (**Prefer backend only** per Supabase security guidance.)
3. Admin 2FA requirement at portal entry?

## Dependencies

- Backend: owner auth-probe endpoint
- Backend: `owner_account` linkage on signup
- Supabase MFA project settings

## Next downstream use

Stages 4–5 (guards + redirects); Backend/Data Systems for API contract.

---

## Session lifecycle

```
1. App load → getCurrentSession()
2. onAuthStateChange keeps session in sync
3. If session null → public entry routes only
4. If session present:
   a. roleResolver(session) → admin | owner | none
   b. if owner → optional MFA posture reported via auth-probe (`aal`, `mfa_enabled`)
   c. navigate to section home or guard child routes (AAL1 allowed)
5. signOut → clear session, navigate /access
6. API 401 from probe → treat as expired, sign out optional
```

## Supabase functions to reuse (existing)

```text
getSupabaseClient, getCurrentSession, getAccessToken,
signInWithPassword, signOut, onAuthStateChange
```

## Functions to add (planned)

| Function | Location | Notes |
|----------|----------|-------|
| `signUpWithPassword` | `supabase.ts` | Mirror consumer app |
| `enrollMfaFactor` / `verifyMfaChallenge` | `supabase.ts` | Wrap Supabase MFA APIs per current docs |
| `getAuthenticatorAssuranceLevel` | `supabase.ts` | Or read from session JWT `aal` |

**Do not duplicate** consumer mobile package—copy pattern only.

## Role resolution (target)

```typescript
// owner/lib/resolvePortalRole.ts (illustrative — implement in stage 5)

type PortalRole = "admin" | "owner" | "none";

async function resolvePortalRole(): Promise<PortalRole> {
  // 1. Try internalAuthProbe — success → admin
  // 2. Else try ownerAuthProbe — success → owner
  // 3. Else none (signed in but not provisioned)
}
```

Until `ownerAuthProbe` exists, Stage 5 may stub with feature flag **only in dev** if Stage Manager approves—default **BLOCKED**.

## Redirect matrix

| Auth state | Role | MFA | Destination |
|------------|------|-----|-------------|
| Logged out | — | — | `/access` |
| Logged in | admin | n/a* | `/internal/founder-venues` |
| Logged in | owner | AAL1 (no MFA) | `/owner` (optional MFA prompt) |
| Logged in | owner | AAL2 | `/owner` |
| Logged in | none | — | `/access/denied` |
| Logged in | owner (auth only) | — | `/access` or awaiting-provisioning — **no `owner_account`** per `DATABASE_REPORT.md` |
| Logged in | owner | complete | `/owner` — may show `NoVenueAccessState` if `venue_count === 0` |

\*Admin MFA policy TBD.

## Route guard expectations

### Public routes

- `/access`, `/access/*` (MFA substeps if not inline)
- No `AuthGate` admin probe

### `AdminRouteGuard`

- Requires session
- `internalAuthProbe()` success
- Renders admin header chrome (may share `PortalShell`)
- Used as layout route for `/internal/*`

### `OwnerRouteGuard`

- Requires session
- `ownerAuthProbe()` success (when available)
- `ownerAuthProbe()` success; MFA optional (legacy `enroll_mfa` next_step does not block)
- Renders owner shell
- Used as layout route for `/owner/*`

### Expired session

- Probe returns 401 → redirect `/access?reason=session_expired`
- Clear misleading “access denied” copy for expired vs forbidden

## Logged-out / expired behaviour

| Trigger | Behaviour |
|---------|-----------|
| User clicks Sign out | `signOut()`, redirect `/access` |
| `getCurrentSession()` null on protected route | redirect `/access` |
| Probe 401 | optional toast + redirect |
| Probe 403 | stay on `/access/denied` with sign out |

## Admin entry: extend vs replace

**Recommendation: extend**

- Keep `internalAuthProbe` and admin routes.
- Remove admin-only assumption from global `AuthGate`.
- Admin section uses `AdminRouteGuard` identical in behaviour to today’s post-login check.

## Owner signup and `owner_account`

Frontend sign-up calls `auth.signUp` only. Linking `owner_account.auth_user_id` is **backend/DB responsibility**—frontend must not insert into `owner_account` directly.

**Database confirmation (PubApp):** `owner_account` RLS allows **SELECT only** for authenticated users—no INSERT policy. No triggers on `auth.users` create owner rows. See `DATABASE_REPORT.md`.

Post-sign-up, owner probe should return 403 until provisioning completes → show **awaiting access** state, not generic error.

## Testing expectations (logic)

- Unit: `resolvePortalRole` with mocked probes (admin success, owner success, both fail, both succeed).
- Unit: redirect helper picks path from role + MFA flag.
- Integration: protected route redirects when session null (mocked).

See `stages/STAGE_06_testing.md`.
