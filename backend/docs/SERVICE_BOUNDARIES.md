
---

## File: `backend/docs/SERVICE_BOUNDARIES.md`

```md
# PubPlus Service Boundaries

## Purpose

Define clean backend service boundaries inside the Django application so PubPlus remains a modular monolith rather than collapsing into tangled endpoint-specific logic.

## Current stage

Architecture planning before implementation.

## Summary

PubPlus should be implemented as a **modular monolith** in Django.

This means:

- one backend application/project
- shared deployment/runtime
- shared database/system integrations
- clear internal domain boundaries
- no premature microservice split

The goal is to keep logic organized by domain responsibility without scattering business rules across views, serializers, models, or random utility files.

---

## Boundary principles

### 1. Keep the monolith modular

Use clear domain modules/apps and service layers so implementation remains understandable and scalable.

### 2. Put business logic in services, not in views

Views/controllers should mostly handle:
- request parsing
- auth entry
- calling services
- returning response shapes

They should not own complex ranking, filtering, open-now logic, or moderation rules.

### 3. Do not let database access patterns become the architecture

The existence of tables does not define service boundaries.

Boundaries should reflect product and backend responsibilities, not raw schema convenience.

### 4. Separate read orchestration from write safety logic

Public discovery reads, private-state writes, and moderation workflows are different domains and should not collapse into one generic service.

### 5. Shared logic must be explicit

If multiple surfaces depend on the same logic, create a shared service intentionally rather than duplicating query fragments across endpoints.

---

## Recommended backend module areas

Recommended top-level code shape:

```text
backend/src/
  apps/
  common/
  services/
  api/

Domain boundaries
1. Discovery domain
Responsibility

Support public venue discovery across:

Home
Search
Map
Venue Detail
Owns
published-truth venue read access
shared discovery filtering
ranking inputs
open-now computation inputs
venue card/detail shaping inputs
map/list result semantics
Does not own
saved-venue persistence
profile/preferences persistence
moderation decisions
owner/business logic
Likely components
apps/discovery/
services/discovery/
services/home_feed/
2. Venue read domain
Responsibility

Provide reusable venue read models from published truth.

Owns
canonical venue read loading
detail aggregation inputs
photo URL resolution
feature/special/event/drink highlight loading for public consumption
Does not own
ranking policy
save-state persistence
moderation workflow state
admin-only lookup semantics
Notes

This can live close to the discovery domain, but should remain conceptually distinct from ranking/orchestration.

3. Consumer private-state domain
Responsibility

Support authenticated user-specific state.

Owns
saved venues
profile basics
preferences
Does not own
public venue truth
moderation queue logic
owner/business/operator state
Notes

This domain must remain account-bound and consumer-scoped.

Likely components:

apps/saved/
apps/profile/
4. Submission domain
Responsibility

Handle consumer-originated write paths safely.

Owns
structured correction submissions
structured new venue suggestions
payload validation rules
routing to moderation/workflow state
submission attribution to consumer identity
Does not own
direct writes to published truth
final moderation decisions
owner claims/business actions

Likely components:

apps/submissions/
services/submissions/
5. Internal moderation domain
Responsibility

Support internal/admin operational workflows in MVP.

Owns
moderation queue
moderation item detail
decision application
audit notes
operator attribution
internal lookup helpers
Does not own
public mobile response contracts
consumer authentication flow
owner/business systems

Likely components:

apps/internal_tools/
services/moderation/
6. Auth and authorization domain
Responsibility

Provide common auth verification and access control helpers.

Owns
Supabase JWT verification
auth context extraction
consumer/private endpoint guards
internal/admin permission guards
Does not own
business-specific submission rules
discovery ranking
profile persistence logic itself

Likely components:

common/auth/
7. Storage/media domain
Responsibility

Provide controlled handling of storage URL generation and media metadata shaping.

Owns
photo URL resolution strategy
public vs signed URL decisions where needed
storage helper abstractions
Does not own
image moderation
image transformation pipeline unless later added
venue detail business logic itself

Likely components:

common/storage/
8. Common infrastructure domain
Responsibility

Support cross-cutting technical concerns.

Owns
DB/session helpers
shared error formatting
pagination helpers
settings/config helpers
time/location utility helpers where generic
Does not own
product logic
ranking policy
moderation policy

Likely components:

common/db/
common/errors/
common/pagination/
config/
Service interaction guidance
Home flow

Home endpoint should call a dedicated home orchestration service.

That service may depend on:

discovery query services
venue card shaping services
preference lookup services for light personalization

It should not directly embed SQL/query fragments in the view.

Search flow

Search endpoint should call the shared discovery query core in list mode.

This service should:

apply filters
compute open-now
apply ranking
load venue card data
annotate save state when authenticated
Map flow

Map endpoint should also call the shared discovery query core, but in viewport/map mode.

Differences from Search should be controlled through mode/presentation behaviour, not separate duplicated query stacks.

Venue detail flow

Venue detail endpoint should call a dedicated venue detail service that:

loads the canonical venue read model
aggregates subdomains like hours, photos, features, specials, events, drink/tap highlights
adds save state if authenticated
Save/unsave flow

Saved endpoints should call a consumer private-state service.

Do not hide save/unsave behaviour inside venue services.

Submission flow

Submission endpoints should call a submission service that:

validates structured payloads
enriches with user attribution
writes moderation-bound records
returns safe acknowledgement responses

Do not let public submission endpoints write directly into public venue read services.

Moderation flow

Internal moderation endpoints should call moderation services that:

read queue items
load item detail
record decisions
attach operator notes/attribution

Do not reuse public submission endpoints for moderation actions.

What should not happen
Anti-pattern 1: giant venue service doing everything

Avoid a single service that handles:

venue reads
saves
submissions
moderation
ranking
photos
owner logic
Anti-pattern 2: fat views

Avoid pushing ranking, filtering, auth branching, and moderation rules directly into view/controller functions.

Anti-pattern 3: serializer-driven business logic

Avoid hiding core product behaviour inside serializer validation or response classes.

Anti-pattern 4: direct table-to-endpoint coupling

Avoid one endpoint per table or raw CRUD thinking.

Anti-pattern 5: premature microservices

Do not split discovery, profile, moderation, and auth into separate deployable services in MVP.

Recommended initial code ownership map
apps/discovery/

Public search/map/home-facing query coordination

apps/venues/

Venue read models and venue detail aggregation support

apps/saved/

Save/unsave and saved listing behaviour

apps/profile/

Consumer profile and preference handling

apps/submissions/

Correction and new venue suggestion ingress

apps/internal_tools/

Internal/admin moderation and operational endpoints

common/auth/

JWT verification and permission gates

common/storage/

Photo/storage URL handling

services/discovery/

Shared query core and ranking helpers

services/home_feed/

Home orchestration

services/moderation/

Moderation decision and queue logic

Boundary between backend and database manager concerns

Backend owns:

how APIs use the schema
authorization logic
query orchestration
response shaping
service-layer behaviour

Database manager owns:

schema design
data boundaries
migration/state integrity
storage of truth/workflow/private/commercial domains

Backend should align to database architecture, not redefine it.

Boundary between backend and frontend concerns

Backend owns:

API contracts
business logic
computed truth
access control
ranking/orchestration

Frontend owns:

UI presentation
screen interactions
client state
request invocation
local UX behaviour

Frontend should not be forced to recreate backend rules such as open-now logic or moderation-safe writes.

Key decisions
PubPlus backend is a modular monolith
service boundaries should follow product domains, not raw tables
Search and Map share a discovery core
Home has dedicated orchestration
submissions and moderation are separate service domains
auth is a shared common domain, not spread ad hoc across endpoints
Assumptions
Django project structure is still being shaped
implementation team can follow domain-based code ownership
no immediate need for multiple deployable backend services
Open questions
exact app/module names
how much venue detail aggregation lives in apps/venues vs services/discovery

These are implementation details, not blockers.

Dependencies
BACKEND_ARCHITECTURE_OVERVIEW.md
AUTH_MODEL.md
API_ENDPOINT_OVERVIEW.md
database domain mapping
Downstream use

This document should guide:

backend repo structuring
worker-agent task scoping
code review standards
future refactor decisions