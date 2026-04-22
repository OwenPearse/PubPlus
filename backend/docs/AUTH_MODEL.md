
---

## File: `backend/docs/AUTH_MODEL.md`

```md
# PubPlus Backend Auth Model

## Purpose

Define the authentication and authorization model for the PubPlus backend, including the boundary between Supabase Auth and Django.

## Current stage

Locked architecture guidance before implementation.

## Summary

PubPlus uses **Supabase Auth** as the identity provider.

The mobile app authenticates users via Supabase Auth, receives a session/JWT, and sends that JWT to Django for authenticated API requests.

Django does not perform primary credential authentication. Django verifies Supabase-issued JWTs and applies PubPlus-specific authorization and business logic.

---

## Core auth principles

### 1. Supabase Auth is the identity source

Supabase owns:

- sign-up
- sign-in
- password auth
- Google OAuth flow
- session issuance
- token lifecycle

Django owns:

- token verification
- user context mapping
- role/permission enforcement
- app-level access decisions

### 2. Public browsing is allowed

The following product areas must be accessible without login:

- Home
- Search
- Map
- Venue Detail

Unauthenticated users may browse public venue content.

### 3. Authentication is required for private actions

The following require authentication:

- save/unsave venue
- profile/preferences access and update
- submit correction
- suggest new venue
- any future user-private actions

### 4. Consumer identity is separate from future owner identity

Even if the same human later interacts with owner/business systems, backend architecture should keep:

- consumer identity context
- owner/business identity context
- admin/internal operator context

as distinct authorization domains.

MVP app scope is consumer only.

---

## Supported launch auth methods

### Required at launch

- email/password
- Google login via Supabase Auth

### Deferred

- Apple login
- Facebook login

Apple may be added later for store/compliance reasons.

---

## Request auth flow

### Authenticated request sequence

1. User signs in through Supabase Auth
2. Frontend stores current session token
3. Frontend sends request to Django with:
   - `Authorization: Bearer <supabase_jwt>`
4. Django verifies the JWT
5. Django resolves the authenticated subject/user identity
6. Django loads or creates app-level user context as needed
7. Django authorizes the action
8. Django executes business logic

---

## Token handling expectations

### Backend requirements

Django must:

- verify JWT authenticity
- verify token validity and expiry
- reject invalid or expired tokens
- extract stable user identity claims
- avoid trusting client-supplied identity fields beyond verified token claims

### Frontend requirements

Frontend should:

- send the Supabase JWT only on authenticated requests
- avoid inventing app-level auth state disconnected from the token
- treat unauthenticated browsing as a first-class mode

---

## App-level user model guidance

The backend should maintain a clean app-level user representation linked to Supabase identity.

Recommended concept:

- external identity source: Supabase Auth user ID
- internal app user/profile row: consumer-linked app state and preferences

This app-level model should support:

- profile basics
- preferences
- saved venues
- submission attribution
- future auditability

But it should not blur consumer identities into owner/admin identities.

---

## Authorization tiers

### Tier 1: Public

No auth required.

Applies to:

- Home
- Search
- Map
- Venue Detail

### Tier 2: Authenticated consumer

Requires valid Supabase JWT.

Applies to:

- Saved
- Profile basics
- Preferences
- Submissions

### Tier 3: Internal/admin operator

Requires internal/admin authentication and authorization.

Applies to:

- moderation queue
- moderation detail
- moderation decisions
- audit notes
- internal operational lookup

This exists inside the same Django project, but behind separate permission checks.

---

## Public vs authenticated response behaviour

Some public read endpoints may return slightly richer results when authenticated.

Example:

- venue cards may include `is_saved: true/false` when authenticated
- when unauthenticated, the API should consistently return either:
  - `is_saved: false`, or
  - omit the field entirely

This behaviour must be consistent across surfaces.

Current preferred direction:

- include save state inline when authenticated
- return false or omit consistently when unauthenticated

Implementation should pick one convention and keep it stable.

---

## Google login model

Google OAuth is handled fully by Supabase Auth.

Django should not implement its own Google OAuth flow for MVP.

Django responsibility begins after token issuance:

- verify Supabase JWT
- map identity to app-level user context
- continue with normal authorization

---

## Security design requirements

### Required

- verify all authenticated requests server-side
- never trust a frontend-only “logged in” state
- do not accept user IDs from request bodies as authority
- authorization decisions must be based on verified token identity plus backend rules
- internal/admin endpoints must be strictly gated
- future owner/business scopes must not be accidentally reachable through consumer auth paths

### Avoid

- duplicating auth systems inside Django
- allowing direct client authority over moderation state
- conflating authentication with authorization
- assuming database access rules alone are enough

---

## Suggested implementation components

Recommended modules:

- `backend/src/common/auth/`
  - JWT verification
  - auth context extraction
  - auth decorators / permission helpers

- `backend/src/apps/profile/`
  - app-level consumer profile resolution

- `backend/src/apps/internal_tools/`
  - internal/admin permission enforcement

---

## Error behaviour guidance

### Unauthenticated request to private endpoint

Return `401 Unauthorized`

### Authenticated but not permitted

Return `403 Forbidden`

### Invalid token

Return `401 Unauthorized`

### Internal/admin endpoint hit by non-admin user

Return `403 Forbidden`

---

## Key decisions

- Supabase Auth is the only identity provider in MVP
- Django verifies tokens and applies authorization
- public browsing is allowed without login
- private actions require login
- Google login is handled by Supabase, not Django
- consumer auth and internal/admin auth are separate authorization domains
- consumer identity remains separate from future owner identity

---

## Assumptions

- Supabase JWT verification strategy will be available to the Django app
- consumer profile/private-state tables are already present or planned in the DB
- internal/admin operator identities will be available for MVP moderation tooling

---

## Open questions

- exact internal/admin auth implementation details
- whether unauthenticated venue cards return `is_saved: false` or omit the field

Neither blocks stage planning.

---

## Dependencies

- Django settings/env strategy
- Supabase project config
- app-level user/profile schema mapping
- internal operator permission model

---

## Downstream use

This document should guide:

- auth implementation workers
- endpoint authorization workers
- frontend/backend session integration
- internal moderation tooling design