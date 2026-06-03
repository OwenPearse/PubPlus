# PubPlus Backend Stage Plan

## Purpose

Define the staged backend delivery plan so implementation can proceed in a controlled order aligned to product-critical paths.

## Current stage

Initial execution planning.

## Planning posture

PubPlus should prefer a slightly slower but cleaner long-term backend architecture over short-term hacks.

This stage plan reflects that posture while still prioritizing MVP-critical user flows.

---

## Delivery priorities

### MVP-critical launch flows

Must work end to end:

- Home
- Search
- Map
- Venue Detail
- Saved
- Profile basics
- Submit correction
- Suggest new venue

### Not required for launch

- submission history/status UI
- advanced personalization
- notifications
- richer admin tooling
- owner flows

---

## Recommended implementation sequence

## Stage 0 — Backend foundation and repo setup

### Purpose

Establish the backend project structure and baseline integration rules before product endpoints are built.

### Scope

- initialize Django backend structure
- establish settings/environment approach
- configure Docker-friendly local development
- define app/module structure
- wire Supabase connectivity assumptions
- establish API versioning foundation under `/api/v1`
- add baseline health/status endpoint
- define common response/error conventions

### Output

- working backend skeleton
- documented environment model
- stable folder structure
- shared base utilities

### Dependencies

- architecture overview
- auth model
- environment decisions

---

## Stage 1 — Auth integration and request identity

### Purpose

Allow Django to verify Supabase JWTs and apply consumer-authenticated access rules.

### Scope

- verify Supabase JWT in Django
- resolve authenticated user context
- support public vs authenticated endpoint modes
- define auth decorators/permission helpers
- create app-level consumer identity/profile bootstrap if needed
- define internal/admin auth gating baseline

### Output

- authenticated requests work safely
- private endpoints can be protected
- internal/admin endpoints can be permission-gated

### Dependencies

- Stage 0 complete

---

## Stage 2 — Public venue read API foundation

### Purpose

Deliver the foundational public read layer used by Home, Search, Map, and Venue Detail.

### Scope

- define venue read serializers/contracts
- build published-truth-only venue access layer
- implement venue card/detail payload shaping
- establish photo URL delivery strategy
- support optional authenticated save-state annotation
- ensure no workflow/private/commercial leakage into public payloads

### Output

- reusable venue read domain
- stable card/detail payload contracts

### Dependencies

- Stage 1 complete
- DB table/domain mapping available

---

## Stage 3 — Shared discovery query core

### Purpose

Create the shared backend query engine for Search and Map.

### Scope

- build shared discovery query service
- support filters:
  - suburb
  - distance
  - open now
  - meal specials
  - drink type
  - venue features
  - events
- support viewport-based map querying
- implement backend-only open-now computation
- define explicit MVP ranking strategy
- keep list and map presentation concerns separate from core query logic

### Output

- one shared query core for Search and Map
- performance-aware discovery foundation

### Dependencies

- Stage 2 complete

---

## Stage 4 — Home feed orchestration

### Purpose

Deliver Home as an orchestrated discovery surface rather than a plain search endpoint.

### Scope

- design Home feed sections/response shape
- combine nearby, open now, specials tonight, events tonight
- add light preference matching using suburb/preferences
- keep ranking explicit and understandable
- avoid behavioural-personalization dependence

### Output

- MVP Home feed backend
- sectioned home response contract

### Dependencies

- Stage 2 complete
- Stage 3 preferably complete

---

## Stage 5 — Saved venues and profile basics

### Purpose

Deliver authenticated consumer-private state APIs.

### Scope

- save/unsave venue API
- saved venue listing API
- profile basics read/update API
- preference storage for:
  - default suburb
  - distance preference
  - favourite drink types
  - favourite venue features
  - event interests
  - notification preference placeholders
- keep implementation account-bound only
- preserve future path for lists/collections without exposing them in MVP UI

### Output

- working Saved screen backend
- working basic Profile/preferences backend

### Dependencies

- Stage 1 complete
- Stage 2 complete

---

## Stage 6 — Consumer submission write paths

### Purpose

Safely support user-submitted corrections and new venue suggestions.

### Scope

- structured-first correction payloads
- structured-first new venue suggestion payloads
- optional contextual free-text notes
- create moderation-bound submission records
- ensure no direct mutation of published truth
- support attribution to authenticated consumer
- validate payload shape strongly

### Output

- correction submission API
- new venue suggestion API
- moderation-safe ingestion path

### Dependencies

- Stage 1 complete
- moderation/workflow table mapping available

---

## Stage 7 — Internal/admin moderation endpoints

### Purpose

Support founder/admin manual moderation in MVP.

### Scope

- moderation queue/list endpoints
- moderation detail endpoint
- approve/reject/decision endpoints
- lightweight audit notes
- operator attribution
- internal lookup/issue-handling support
- strict internal auth/authorization checks

### Output

- minimal usable moderation backend
- auditable decision flow

### Dependencies

- Stage 1 complete
- Stage 6 complete

---

## Stage 8 — Performance hardening and query review

### Purpose

Review backend behaviour under realistic MVP load and tighten slow paths.

### Scope

- review Search and Map latency
- review Venue Detail response shape/performance
- optimize query hotspots
- confirm filtering/index expectations with DB manager if needed
- review authenticated annotation costs such as save-state joins
- review pagination and payload size discipline

### Output

- performance-tuned MVP backend surfaces

### Dependencies

- Stages 2–7 substantially complete

---

## Stage 9 — QA/release readiness

### Purpose

Make backend delivery testable, reviewable, and ready for coordinated release.

### Scope

- endpoint acceptance criteria pass
- error behaviour review
- auth/access review
- environment documentation pass
- internal/admin path review
- API contract review against frontend
- release checklist inputs for QA/Release manager

### Output

- backend release-readiness package

### Dependencies

- all MVP implementation stages substantially complete

---

## Cross-cutting rules across all stages

### Rule 1: Do not bypass Django

App data logic should not be pushed into direct frontend-to-database usage.

### Rule 2: Published truth only for public reads

Public endpoints must not leak workflow/private/internal/commercial state.

### Rule 3: All consumer write paths are rule-bound

No “quick insert” mentality for submissions, saves, or profile writes.

### Rule 4: Keep modules small and explicit

Prefer focused apps/services over giant utility files.

### Rule 5: Build for future owner/business compatibility without shipping owner systems now

Avoid public contracts that would force painful rewrites later.

---

## Suggested backend stage-manager breakdown

### Stage Manager A — Backend foundation and auth
Owns:
- Stage 0
- Stage 1

### Stage Manager B — Public read APIs and discovery
Owns:
- Stage 2
- Stage 3
- Stage 4

### Stage Manager C — Consumer private state and submissions
Owns:
- Stage 5
- Stage 6

### Stage Manager D — Internal/admin moderation and release hardening
Owns:
- Stage 7
- Stage 8
- Stage 9

This may be adjusted later depending on implementation velocity and repo size.

---

## Key decisions

- backend work should proceed in staged layers, not endpoint chaos
- auth and public read foundations come before submission and moderation tooling
- Search and Map share a discovery core
- Home is a separate orchestration surface
- internal moderation support is MVP-required but minimal
- performance review is a dedicated stage, not an afterthought

---

## Assumptions

- development Supabase project already contains the migrated schema baseline
- frontend can adapt to backend contracts with minimal UI change
- founder/admin team is sufficient for MVP moderation operations

---

## Open questions

- exact stage-manager staffing
- exact endpoint list and payload shapes
- exact admin auth mechanism

These do not block the stage framework.

---

## Dependencies

- `BACKEND_ARCHITECTURE_OVERVIEW.md`
- `AUTH_MODEL.md`
- database domain mapping
- frontend screen/API contract review

---

## Downstream use

This document should be used to:

- create backend stage-manager prompts
- sequence worker-agent implementation
- track backend progress against MVP launch flows