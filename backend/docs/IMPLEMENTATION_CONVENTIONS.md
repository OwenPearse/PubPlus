# PubPlus Backend Implementation Conventions

## Purpose

Define the implementation conventions for the PubPlus backend so stage managers and worker agents build consistently across modules, endpoints, services, auth handling, validation, and internal structure.

## Current stage

Pre-implementation ruleset locked before staged backend execution.

## Summary

PubPlus backend implementation should optimize for:

- clarity over cleverness
- modular consistency over ad hoc patterns
- explicit business logic over implicit framework magic
- stable API contracts over convenience-driven drift
- small focused files over large mixed-responsibility files

The backend is a Django modular monolith connected to Supabase Postgres, Supabase Auth, and Supabase Storage.

Implementation should preserve the architecture already locked in the backend planning docs.

---

## Core implementation principles

### 1. Prefer explicitness

Important backend behaviour should be easy to find in code.

Do not hide core product logic in:

- model side effects
- serializer magic
- signals
- undocumented middleware branching
- framework-default behaviour that workers have to guess

### 2. Keep files focused

Each file should have one clear responsibility.

Prefer:

- smaller views
- focused services
- narrow validators
- domain-specific serializers/schemas

Avoid giant files that mix:

- endpoint handling
- auth logic
- query construction
- ranking
- persistence
- response shaping

### 3. Business logic belongs in services

Views/controllers should mainly do four things:

- parse request
- establish auth context
- call service layer
- return response

Business rules such as ranking, submission handling, open-now logic, save-state rules, and moderation decisions belong in service/domain code.

### 4. Contracts are intentional

Response and request payloads are product contracts, not temporary implementation details.

Do not casually rename or reshape fields once a contract is introduced unless the change is coordinated and justified.

### 5. Do not let raw schema shape the API

The database is the source of truth, but the API should not mirror tables directly.

The backend must translate database structure into product-oriented contracts.

---

## Code organization conventions

## Recommended root structure

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

  This can evolve slightly, but all implementation should remain consistent with a modular monolith shape.

Recommended domain app structure

Under backend/src/apps/, keep domain ownership explicit.

Suggested areas:

discovery/
venues/
saved/
profile/
submissions/
internal_tools/

These app areas should align to backend responsibilities, not raw tables.

Common/shared structure

Use backend/src/common/ for cross-cutting technical concerns, such as:

auth verification
permission helpers
error shaping
pagination
time/location utilities
storage URL helpers
DB utility helpers

Do not place product-specific business logic in common/.

Service layer structure

Use backend/src/services/ for shared service logic that is broader than a single app or clearly represents a backend domain service.

Examples:

services/discovery/
services/home_feed/
services/moderation/

A service should have a clear domain purpose, not become a generic dumping ground.

API/controller conventions
Endpoint grouping

Public and internal APIs must be explicitly grouped under versioned paths.

Examples:

/api/v1/home
/api/v1/search/venues
/api/v1/map/venues
/api/v1/venues/{id}
/api/v1/saved/venues
/api/v1/profile
/api/v1/submissions/...
/api/v1/internal/...

The route structure should stay aligned to the API planning docs.

View/controller responsibilities

Views/controllers should:

authenticate request context where needed
validate incoming parameters/body
call service layer
return stable response shape
map domain errors to HTTP responses consistently

Views/controllers should not:

contain long ranking logic
perform large query orchestration inline
embed moderation workflow decisions inline
perform deep raw DB transformations inline
Request validation conventions
General rule

Validate input explicitly and close to the boundary.

Requirements
query params should be validated
request bodies should be validated
enums and categories should be explicit
unknown fields should not silently create behaviour
invalid inputs should return stable error shapes
Avoid
accepting arbitrary blobs when structured shape is expected
relying on downstream DB errors as the primary validation layer
partial silent coercion that hides bad input
Response shaping conventions
General rule

Responses should be shaped deliberately for the consuming surface.

Requirements
use stable field names
keep card payloads compact
keep detail payloads richer but still intentional
use consistent semantics across surfaces for shared fields
keep internal-only fields out of public responses
Avoid
returning raw DB columns without meaningfully shaping them
allowing different endpoints to use different meanings for the same field
returning null-heavy payloads full of unused fields by default
Error handling conventions
Standard error shape

Use a consistent error envelope across the API.

Recommended baseline:

{
  "error": {
    "code": "validation_error",
    "message": "One or more fields are invalid.",
    "details": {
      "field_name": ["This field is required."]
    }
  }
}
HTTP code guidance
400 for malformed or invalid requests
401 for missing/invalid auth
403 for authenticated but unauthorized
404 for missing resource
409 for meaningful conflicts
422 only if the implementation intentionally distinguishes semantic validation failures from malformed requests

Choose a consistent approach and apply it everywhere.

Auth implementation conventions
Supabase Auth boundary

Supabase Auth is the source of identity.

Django must:

verify Supabase JWTs
extract trusted identity context
apply app-level authorization
never trust client-supplied identity fields as authority
Public vs private endpoints
public endpoints must work without login
private endpoints must require verified consumer auth
internal endpoints must require verified internal/admin authorization

Do not mix these rules loosely.

Authorization conventions
Consumer auth checks

Use explicit consumer-auth guards for:

saved endpoints
profile endpoints
submission endpoints
Internal/admin checks

Use explicit internal/admin guards for:

moderation queue
moderation detail
moderation decisions
moderation notes
internal lookup endpoints
Rule

Authorization decisions must be easy to audit in code.

Do not hide permission-critical branching in obscure utility wrappers.

Query and persistence conventions
Public reads

Public read paths should:

use published truth only
compute open_now via approved backend logic
support optional authenticated enrichment such as save-state
avoid leaking workflow/internal/commercial state
Private-state writes

Private-state writes should:

be account-bound
validate target resources
be idempotent where appropriate
remain separate from moderation workflows
Moderation-bound writes

Submission writes should:

be structured-first
never mutate published truth directly
create moderation/workflow-bound records
include authenticated attribution
return safe acknowledgement responses
Naming conventions
Files and modules

Prefer descriptive names over vague generic ones.

Good examples:

venue_detail_service.py
search_query_service.py
supabase_jwt.py
moderation_decision_service.py

Avoid vague names like:

helpers.py
utils.py
misc.py
stuff.py

Generic helper files tend to become unmaintainable.

Field naming in APIs

Prefer stable, readable JSON field names.

Examples:

open_now
hero_photo_url
feature_badges
distance_m
is_saved

Use consistent naming conventions across all endpoints.

Do not mix naming styles arbitrarily.

Time and location conventions
Time

Backend logic involving time should be explicit and consistent.

Important time-sensitive domains include:

open-now computation
hours exceptions
specials/events eligibility
moderation timestamps
audit notes

Use one consistent timezone strategy and document it during implementation.

Do not let different modules make conflicting time assumptions.

Location

Location-related logic such as:

distance computation
radius filtering
viewport filtering

should be implemented in shared domain services where possible, not duplicated across endpoints.

Logging and observability conventions

Implementation should include enough logging to support debugging and operational review, especially around:

auth failures
endpoint errors
moderation actions
unexpected validation issues
critical discovery/query failures

Do not log secrets or sensitive tokens.

Logs should support troubleshooting without exposing private data unnecessarily.

Testing conventions

Tests should follow domain boundaries and endpoint risk.

Minimum expectations
auth verification tests
endpoint authorization tests
search/map filter logic tests
open-now logic tests
save/unsave tests
submission validation tests
moderation decision permission tests
Test shape guidance

Prefer a mix of:

service-level tests for business logic
endpoint/API tests for contracts and auth behaviour

Do not rely only on manual testing for trust-sensitive logic.

Documentation conventions

When backend workers create docs, they should:

place them under backend/docs/
keep them focused and domain-specific
update relevant planning docs if implementation decisions meaningfully clarify or lock a detail
avoid giant catch-all docs

Stage-manager and worker-facing documents should clearly state:

purpose
current stage
key decisions
assumptions
open questions
dependencies
downstream use
What to avoid
Avoid 1: framework-driven magic architecture

Do not let Django conventions replace architecture thinking.

Avoid 2: giant shared utility files

Do not centralize unrelated logic into utils.py.

Avoid 3: endpoint-specific duplicated business logic

If Search and Map share discovery rules, they should share service logic.

Avoid 4: direct frontend-to-Supabase product logic

Django is the application logic boundary.

Avoid 5: public/internal boundary leakage

Do not reuse public payloads for internal operations by just “adding fields.”

Avoid 6: raw CRUD mentality

The backend is not a thin wrapper around tables.

Review checklist for workers

Before a backend change is accepted, workers should be able to answer:

Is the responsibility of this file/module clear?
Does the logic belong in the service layer rather than the view?
Does this change preserve public/private/internal domain separation?
Does it keep API contracts stable and intentional?
Does it avoid hidden behaviour and unnecessary magic?
Does it align with the backend architecture docs?
Is the implementation small and understandable?
Key decisions
backend implementation must remain a modular monolith
business logic belongs in services, not views
request and response validation must be explicit
public/private/internal boundaries must remain clear
file/module naming should be descriptive, not generic
API contracts are intentional and should not drift casually
shared logic should be centralized deliberately, not duplicated
Assumptions
the backend repo is being created now and conventions can still shape it cleanly
stage managers and worker agents will be implementing in parallel later
consistent conventions now will reduce rework and code drift
Open questions
exact Django package layout
exact testing framework conventions
exact timezone/config standard for all time-sensitive logic

These are implementation-level refinements, not blockers for this conventions document.

Dependencies
backend/docs/BACKEND_ARCHITECTURE_OVERVIEW.md
backend/docs/SERVICE_BOUNDARIES.md
backend/docs/API_ENDPOINT_OVERVIEW.md
backend/docs/AUTH_MODEL.md
Downstream use

This document should guide:

backend stage managers
worker agents implementing Django code
code review standards
refactor decisions
QA review of implementation consistency