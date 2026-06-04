# PRD — Venue owner signup & portal access (web-portal)

## Purpose

Define the frontend product scope for venue manager **signup, sign-in, 2FA-aware access, and role-based entry** into the shared PubPlus web portal—without building the full owner dashboard.

## Current stage

**Stage 1 complete** — planning package verified; implementation starts at `stages/STAGE_02_branding.md`.

## Decisions

- **Surface:** Existing `web-portal/` React + TypeScript app only.
- **Audience:** Venue operators (owners) and internal admins using the **same portal entry**.
- **Post-auth routing:** Owner → `/owner/*`; Admin → `/internal/*` (existing founder-venues admin).
- **Identity:** Supabase Auth only; no parallel auth system in the portal.
- **2FA:** Optional security add-on for owners (Supabase MFA); normal `/owner` access allowed at AAL1; AAL2 may be required later for sensitive actions.
- **Branding:** Placeholder name/logo via config—no locked product name in source.
- **Out of scope:** Full owner dashboard, claim-venue workflows, backend auth implementation, role model changes.

## Assumptions

- Owners may eventually manage multiple venues; venue switcher lives **inside** owner portal after entry (not in this PRD).
- Admin users signing in through the same entry are redirected to admin routes without seeing owner onboarding.
- Session restore on refresh re-runs role probe and MFA satisfaction checks.

## Open questions

See `STAGE_0_DISCOVERY.md` § Open questions (owner_account provisioning, role API, 2FA enforcement level).

## Dependencies

| Dependency | Owner | Blocks |
|------------|-------|--------|
| Owner auth-probe API | Backend | Stage 5 redirects |
| `owner_account` provisioning on signup | Backend/Data | Owner role after sign-up |
| Supabase MFA (PubApp) | Infra | Stage 4 |
| `internalAuthProbe` | Backend | Admin routes (exists) |
| `DATABASE_REPORT.md` | Data | Sign-up UX copy / awaiting-access states |
| Admin Dashboard Manager | Frontend | `/access` path alignment |

Read `DATABASE_REPORT.md` before implementing sign-up success or owner empty states.

## Next downstream use

- `stage-plan.md` and per-stage agent prompts
- Acceptance criteria in each `stages/STAGE_*.md`

---

## Problem

Venue managers need a trustworthy web entry to create an account, sign in, optionally enable 2FA, and reach an owner workspace. Internal operators already use the same portal codebase for founder-venue admin but with an admin-only gate that blocks owners today.

## Goals

1. **Owner sign up** — email/password account creation (extensible to OAuth later).
2. **Owner sign in** — same entry as admin.
3. **2FA (optional)** — enroll/verify available from `/access` or `/owner`; does not block owner area access at AAL1.
4. **Role redirect** — owner → owner section; admin → admin section.
5. **Session UX** — loading, error, expired session, access denied states.
6. **Placeholder branding** — swap product name/logo without wide refactors.

## Non-goals

- **Full owner dashboard** (navigation, editing, analytics).
- **Claim-venue workflow** (requests, verification, business onboarding).
- Owner content editing, specials, tap lists, team management UI.
- Admin dashboard features beyond existing internal routes.
- Consumer mobile auth changes.
- Backend auth implementation or role-model changes.
- Parallel auth system or second Supabase client.

## Users & roles

| Role | Entry | After auth |
|------|-------|------------|
| Owner | Shared portal entry | `/owner` (placeholder shell); future venue switcher inside |
| Admin | Same entry | `/internal/...` (existing) |

**Rule:** One logical domain per account (owner vs admin vs consumer)—no multi-role account in v1 UI.

## User stories

### US-1 — Owner sign up

As a venue operator, I can create an account with email and password so I can access the owner portal later.

**Acceptance**

- Sign-up form validates email/password.
- Success shows clear next step (email confirm if required, or proceed to owner portal).
- Errors are human-readable (duplicate email, weak password, network).

### US-2 — Owner sign in

As a returning owner, I can sign in with email and password.

**Acceptance**

- Sign-in and sign-up reachable from same entry (tabs or mode toggle).
- Successful password auth proceeds to role resolution and owner home (MFA not mandatory).

### US-3 — 2FA (optional)

As a portal user, I can enable two-step verification to protect my account.

**Acceptance**

- Optional setup from post-sign-in continue panel or `/owner` security prompt.
- If MFA not enrolled: enrollment UI (QR / manual code per Supabase).
- If enrolled: TOTP challenge step when user chooses to set up or verify.
- Failed challenge shows error; can retry; can sign out.
- Owner routes remain accessible at AAL1 without MFA.

### US-4 — Admin redirect

As an internal admin, when I use the same login entry I am sent to the admin section without owner onboarding.

**Acceptance**

- After auth + role resolution, navigate to `/internal/founder-venues` (or admin home).
- Existing `internalAuthProbe` behavior preserved for admin routes.

### US-5 — Access denied / no venue / unprovisioned

As a signed-in user without portal role, or an owner without venue linkage, I see a clear state—not a broken dashboard.

**Acceptance**

- **No role:** access denied + sign out (`role.none`).
- **Owner provisioned, no venues:** `NoVenueAccessState` on `/owner` (awaiting access / contact support).
- **Auth user without `owner_account` row** (sign-up before Backend provisioning): awaiting-provisioning copy, not generic 500 (see `DATABASE_REPORT.md`).
- Optional secondary link: request access / support (`VITE_PORTAL_SUPPORT_URL`).

### US-6 — Logged out / expired session

As a user with an expired JWT, I am returned to portal entry with a message.

**Acceptance**

- Protected routes redirect to `/access` (or chosen path).
- Optional banner: session expired.

## UX principles

- Web-first, minimal, professional, trustworthy.
- Low friction without skipping security (2FA visible, not hidden).
- Clear primary CTA per step; one main action per screen.

## Technical constraints

- Code layout: `src/owner/` primary; `src/shared/` for shared Supabase/env/primitives only.
- Reuse `shared/lib/supabase.ts` and `api.ts` patterns.
- Do not move owner business logic into `shared/`.

## Success metrics (qualitative for v1)

- Owner can complete sign-up → 2FA → land on owner placeholder route in dev.
- Admin login regression: founder-venues list still loads.
- No hardcoded final product name in TSX (uses brand config).

## Release / QA

See `stages/STAGE_06_testing.md` for test matrix and manual checklist.
