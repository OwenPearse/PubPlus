# Owner portal auth — provisioning & auth-probe

## Purpose

Server-side owner identity provisioning and routing state for the web portal (`/access` → `/owner`), without browser inserts into `owner_account`.

## Base path

- `/api/v1/owner/`

All endpoints require:

```http
Authorization: Bearer <supabase_access_jwt>
```

CSRF-exempt (Bearer API, same as consumer private routes).

---

## POST `/api/v1/owner/provision`

Creates or confirms `public.owner_account` for the verified JWT `sub`.

### Success responses

| Status | When |
|--------|------|
| `201 Created` | New `owner_account` row inserted |
| `200 OK` | Row already existed (idempotent) |

### Body (201 / 200)

```json
{
  "authenticated": true,
  "owner_account_exists": true,
  "owner_account_id": "uuid",
  "provisioned": true,
  "created": true,
  "next_step": "enroll_mfa"
}
```

`created` is `false` on `200 OK`.

### Errors

| Status | Code | When |
|--------|------|------|
| `401` | `unauthorized` | Missing / invalid / expired JWT |
| `403` | `owner_provisioning_disallowed` | Valid JWT but provisioning blocked (admin-linked subject, or `PUBPLUS_OWNER_PROVISION_DISABLED=true`) |

### Behaviour

- Does **not** create `owner_business_membership` or venue relationships.
- Uses Django DB role (bypasses owner SELECT-only RLS), same pattern as `consumer_account` auto-provision.
- Rejects provisioning when `admin_account` already exists for the same `auth_user_id` (domain separation).

---

## GET `/api/v1/owner/auth-probe`

Single source of truth for owner portal routing after sign-in.

### Success `200 OK`

Owner row exists. Body includes membership/venue counts and `next_step`:

```json
{
  "authenticated": true,
  "owner_account_exists": true,
  "owner_account_active": true,
  "mfa_required": true,
  "aal": "aal2",
  "has_active_business_membership": true,
  "has_approved_managed_venue_relationship": true,
  "business_count": 1,
  "venue_count": 2,
  "owner_account_id": "uuid",
  "next_step": "portal_home"
}
```

### `403 Forbidden` — not provisioned

No `owner_account` for this JWT. Frontend should call `POST .../provision` after sign-up.

```json
{
  "authenticated": true,
  "owner_account_exists": false,
  "owner_account_active": false,
  "mfa_required": true,
  "aal": null,
  "has_active_business_membership": false,
  "has_approved_managed_venue_relationship": false,
  "business_count": 0,
  "venue_count": 0,
  "owner_account_id": null,
  "next_step": "complete_owner_provisioning",
  "error": {
    "code": "owner_not_provisioned",
    "message": "Owner account is not provisioned for this identity."
  }
}
```

### `401 Unauthorized`

Missing / invalid / expired JWT.

### `next_step` values

| Value | Meaning |
|-------|---------|
| `complete_owner_provisioning` | No `owner_account` (403) |
| `enroll_mfa` | Owner exists; JWT `aal` is not `aal2` |
| `owner_waiting_for_membership` | AAL2; no `active` `owner_business_membership` |
| `owner_waiting_for_venue_access` | AAL2; membership but no `approved` managed venue |
| `portal_home` | AAL2; ready for `/owner` shell (venue UI may still show empty state) |

### Venue access counting

Venues count only via:

`owner_account` → `owner_business_membership` (`active`) → `business` → `business_venue_management_relationship` (`approved`).

Membership alone does **not** imply venue access.

### `owner_account_active`

Always `true` when a row exists (no status column on `owner_account` today).

---

## MFA / AAL2 enforcement

| Layer | Policy |
|-------|--------|
| **Auth-probe** | Returns `200` with `aal` and `next_step` (e.g. `enroll_mfa` for AAL1). Does **not** use `403 mfa_required`. |
| **Future owner-protected routes** | `require_owner_portal_auth`: JWT + `owner_account` + `aal === aal2` → else `403` (`mfa_required` or `owner_not_provisioned`). |

Frontend owns Supabase TOTP enroll/challenge UI. Backend reads `aal` from verified JWT claims.

**Infra checklist (PubApp):** enable Supabase Auth MFA + TOTP in dashboard; until users enroll, `auth.mfa_factors` stays empty and JWT remains `aal1`.

---

## Settings

| Variable | Default | Purpose |
|----------|---------|---------|
| `PUBPLUS_OWNER_PROVISION_DISABLED` | `false` | Kill-switch for signup provisioning |

---

## Frontend integration

1. `signUp` → `POST /api/v1/owner/provision`
2. `GET /api/v1/owner/auth-probe` for guards / redirects
3. MFA UI until session JWT shows `aal2`
4. Use `next_step` and counts for empty states (no membership / no venue)

Pair with existing `GET /api/v1/internal/auth-probe` for admin role resolution.

---

## Manual QA (dev seed)

| Email | Password | Notes |
|-------|----------|-------|
| `owner1@demo.pubplus.local` | `demo-password-123` | Pre-provisioned owner |
| `owner2@demo.pubplus.local` | `demo-password-123` | Second owner |

New sign-ups: provision endpoint required before auth-probe returns `200`.
