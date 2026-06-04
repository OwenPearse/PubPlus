# Signup & portal access — overview

## Purpose

One-page map of the venue manager entry experience: screens, states, and how it fits the existing web portal.

## Current stage

**Stage 1 complete** — map is locked for Stages 2–6 implementation.

## Decisions

- **Unified portal entry** at `/access` (recommended path; confirm with Admin Dashboard Manager).
- **Mode toggle** on entry: Sign in | Create account (same page).
- **Post-password flow:** Role resolution → redirect; optional 2FA for owners (non-blocking at AAL1).

## Assumptions

- Owner home v1 is a **placeholder** route with “awaiting venue access” empty state.
- Venue switching is post-login inside `/owner`, not at signup.

## Open questions

- Exact path: `/access` vs `/login` vs `/`.
- Whether admins must pass 2FA at portal entry (owner 2FA is optional; admin TBD).

## Dependencies

- `auth-flow-and-role-redirects.md`
- `branding-placeholder-strategy.md`
- Backend role probe API

## Next downstream use

Stage 3–5 implementation agents; UX copy review by Product.

---

## Flow diagram

```mermaid
flowchart TD
  A[Visitor opens /access] --> B{Supabase configured?}
  B -->|no| C[Config error screen]
  B -->|yes| D{Session exists?}
  D -->|no| E[Entry: sign-in or sign-up]
  E --> F[Password auth via supabase.ts]
  F --> G{Role probe}
  G -->|admin| H[internalAuthProbe OK?]
  H -->|yes| I[/internal/founder-venues]
  H -->|no| J[Access denied]
  G -->|owner| N[/owner home placeholder]
  N --> O{Optional 2FA prompt}
  O -->|Set up 2FA| P[MFA enroll / verify at /access]
  O -->|Maybe later| N
  G -->|unknown| J
  D -->|yes| G
```

## Screen inventory

| Screen | Route | Module |
|--------|-------|--------|
| Config missing | any | `shared` env check |
| Portal entry | `/access` | `owner/pages/PortalEntryPage` |
| MFA enroll | `/access/mfa/enroll` or inline step | `owner/components/MfaEnrollStep` |
| MFA verify | `/access/mfa/verify` or inline step | `owner/components/MfaVerifyStep` |
| Access denied | `/access/denied` or inline | `owner/pages/AccessDeniedPage` |
| Session loading | — | `owner/components/AuthLoadingState` |
| Owner shell | `/owner` | `owner/pages/OwnerHomePlaceholder` |
| No venue yet | `/owner` (branch) | `owner/components/NoVenueAccessState` |
| Admin shell | `/internal/*` | existing `admin/pages/*` |

## States to handle

| State | User-visible behavior |
|-------|----------------------|
| `auth.loading` | Neutral spinner / skeleton |
| `auth.unauthenticated` | Entry form |
| `auth.signUpSuccess` | Confirm email message OR continue to MFA |
| `auth.error` | Inline error + retry |
| `auth.mfaRequired` | TOTP input |
| `auth.mfaEnrollRequired` | QR / secret display |
| `role.resolving` | “Checking access…” |
| `role.admin` | Redirect internal |
| `role.owner` | Redirect owner |
| `role.denied` | Signed in but no portal role |
| `owner.unprovisioned` | Supabase session exists; no `owner_account` row yet — awaiting provisioning copy |
| `owner.noVenue` | Owner probe OK; zero venues/memberships — `NoVenueAccessState` |
| `session.expired` | Redirect entry + optional banner |

## Secondary paths

| Path | When |
|------|------|
| Request access / Contact support | Footer link on entry and no-venue state; URL from `VITE_PORTAL_SUPPORT_URL` |
| Sign out | Header on owner/admin shells; clears Supabase session |

## What we are not building here

- Owner dashboard navigation, venue editor, team settings.
- Admin list/detail feature changes (except entry guard refactor).

## Relation to existing admin UI

Today operators hit `/` → founder venues after **admin-only** `AuthGate`. Target: operators still reach the same pages, but only after **admin role** resolution at shared entry—not by blocking all users at the global gate before routing.
