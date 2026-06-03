# PubPlus Backend Architecture Overview

## Purpose

Define the high-level backend architecture for PubPlus so downstream stage managers and worker agents can implement against a clear, stable foundation.

## Current stage

Architecture planning locked before backend implementation staging.

## Summary

PubPlus uses:

- **Frontend:** React Native with Expo
- **Backend application layer:** Django
- **System of record:** Supabase Postgres
- **Authentication provider:** Supabase Auth
- **Storage:** Supabase Storage
- **Public API style:** Versioned REST under `/api/v1/...`

The backend is the controlled application layer that connects the mobile app to structured venue data, consumer-private state, moderation workflows, and future owner/commercial systems.

Django is the **only public application API** for app data and product logic. The mobile app should not directly query application tables for product behaviour.

---

## Core backend responsibilities

The backend is responsible for:

- public read APIs for Home, Search, Map, Venue Detail
- authenticated APIs for Saved, Profile basics, and consumer submissions
- verification of Supabase JWTs
- app-level authorization and role checks
- ranking and orchestration logic
- open-now computation using published hours and exception truth
- search/filter orchestration
- moderation-safe write paths
- minimal internal/admin endpoints for moderation and ops
- preserving separation between public truth, private state, workflow state, and future business/commercial domains

---

## Architectural principles

### 1. Django is the application logic boundary

Django owns:

- request validation
- response shaping
- ranking logic
- authorization decisions
- submission rules
- moderation path rules
- shared query orchestration

Supabase/Postgres owns:

- persistent storage
- schema integrity
- relational constraints
- queryable data foundation
- RLS where useful as a guardrail, but not as the only product rule layer

### 2. Public truth and workflow must stay separate

The backend must never collapse:

- published/public venue truth
- staged/workflow data
- moderation history
- consumer-private state
- owner/business/commercial state

into one convenience model.

### 3. Read models and write paths are different concerns

Read APIs are optimized for:

- speed
- stable client contracts
- UI-driven payload shapes
- ranking/filtering

Write APIs are optimized for:

- safety
- trust
- structured validation
- moderation-first behaviour

### 4. Backend-computed truth beats frontend inference

High-trust product logic such as:

- open now
- save state
- ranking
- eligibility of surfaced specials/events
- moderation state handling

must be computed in backend, not inferred in the client.

### 5. Future readiness without premature overbuild

The backend should leave room for:

- owner claims
- business/operator relationships
- subscriptions and entitlements
- promotions
- analytics
- richer moderation tooling

but should not implement these as heavyweight systems in MVP unless required.

---

## High-level system shape

### Public mobile flows

Unauthenticated and authenticated mobile users consume Django APIs for:

- Home feed
- Search results
- Map results
- Venue Detail

Authenticated users additionally use Django APIs for:

- Saved venues
- Profile/preferences
- Submit correction
- Suggest new venue

### Authentication flow

1. User signs in with Supabase Auth in the mobile app
2. Frontend receives Supabase session/JWT
3. Frontend calls Django with Supabase JWT in the Authorization header
4. Django verifies the JWT
5. Django maps the authenticated identity into app-level user context
6. Django applies authorization and returns data or accepts safe writes

### Storage/media flow

- Venue photos are stored in Supabase Storage
- Backend returns direct asset URLs
- Use public URLs where safe
- Use signed URLs only if protection is required
- Django does not proxy media by default

---

## Primary backend domains

### 1. Public venue discovery

Supports:

- Home
- Search
- Map
- Venue Detail

Core concerns:

- published venue truth only
- performant filtering
- ranking
- open-now computation
- viewport and distance querying
- card/detail response shaping

### 2. Consumer private state

Supports:

- saved venues
- profile basics
- preferences

Core concerns:

- authenticated-only access
- account-bound state
- no guest save system
- future-safe structure for saved lists later

### 3. Consumer submissions

Supports:

- correction to existing venue
- new venue suggestion

Core concerns:

- structured-first payloads
- moderation-first routing
- no direct mutation of published truth
- lightweight auditability

### 4. Internal/admin moderation support

Supports:

- queue/list/detail views
- decisions
- audit notes
- operator attribution
- operational lookup

Core concerns:

- internal-only auth and authorization
- safe interaction with workflow state
- no exposure to public mobile clients

### 5. Future business/owner/commercial compatibility

Not MVP delivery scope, but backend must preserve clean future boundaries for:

- owner claims
- business/operator entities
- subscriptions
- entitlements
- promotions
- analytics

---

## API shape overview

Base path:

- `/api/v1/...`

Top-level groups expected:

- `/api/v1/home/...`
- `/api/v1/search/...`
- `/api/v1/map/...`
- `/api/v1/venues/...`
- `/api/v1/saved/...`
- `/api/v1/profile/...`
- `/api/v1/submissions/...`
- `/api/v1/internal/...`

Exact endpoint definitions will be documented separately.

---

## Query architecture principles

### Shared discovery query core

Search and Map should use one shared discovery query service.

This service should:

- query published venue truth
- apply common filters
- compute open-now
- support location and viewport constraints
- support explicit ranking rules
- optionally annotate authenticated save state

Search and Map then diverge at the presentation layer:

- Search emphasizes list/card ordering and facets
- Map emphasizes viewport result sets and map-friendly payloads

### Home feed orchestration

Home should use dedicated orchestration logic rather than pretending to be plain search.

MVP Home should blend:

- nearby venues
- open now
- specials tonight
- events tonight
- light preference matching

while remaining simple and explicit.

---

## Authorization model summary

### Public endpoints

Browsable without login.

### Consumer-authenticated endpoints

Require valid Supabase JWT and app-level consumer authorization.

### Internal/admin endpoints

Require strict internal/admin auth and authorization inside the same Django project.

### Future owner/business endpoints

Deferred, but public API contracts should not make them difficult later.

---

## Environment assumptions

Current reality:

- one Supabase project exists now
- development-first delivery
- Docker-friendly local development required

Backend docs and layout should still assume future separation for:

- local
- dev
- staging
- production

---

## Recommended initial backend repo shape

```text
backend/
  docs/
  config/
  src/
    apps/
    common/
    services/
    api/
  tests/