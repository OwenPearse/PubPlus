# PubPlus Internal Admin Endpoints

## Purpose

Define the initial internal/admin backend endpoint scope for PubPlus so founder/admin moderation and lightweight operational support can function in MVP without requiring a separate service.

## Current stage

Architecture and endpoint planning before implementation.

## Summary

PubPlus MVP requires minimal but usable internal/admin backend support for:

- moderation queue management
- moderation item review
- moderation decisions
- lightweight audit notes
- operator attribution
- simple internal lookup and issue-handling support

These internal endpoints live inside the same Django project as the public API, but they must be protected by strict internal/admin authentication and authorization.

They are not public mobile endpoints.

---

## Core principles

### 1. Internal endpoints are a separate authorization domain

Even though they live inside the same Django project, internal/admin endpoints must not be treated as consumer endpoints with extra fields.

They require separate access control and stricter authorization checks.

### 2. Internal tools should support moderation-first operations

The MVP internal/admin surface exists primarily to support trust-preserving review of user submissions and operational triage.

It is not intended to be a full business back office in the first release.

### 3. Internal reads may be richer than public reads

Internal/admin endpoints may expose operational context that should never appear in public APIs, including:

- moderation state
- submitter attribution summaries
- internal notes
- decision history summaries where available
- workflow context

### 4. Internal tools should stay minimal in MVP

The backend should support the founder/admin team effectively, but avoid premature complexity such as:

- heavy queue automation
- advanced multi-role staff workflows
- broad operational dashboards
- owner/commercial admin systems

---

## Endpoint namespace

All internal/admin endpoints should live under:

- `/api/v1/internal/...`

This keeps the distinction explicit and future-safe.

---

## Internal/admin auth expectations

### Required behaviour

Internal endpoints must require:

- authenticated internal/admin identity
- positive authorization for internal tooling access
- request-level permission checks
- operator attribution on moderation actions

### Not acceptable

- relying on consumer auth alone
- exposing internal data to any logged-in consumer
- hiding internal access behind weak frontend gating only

---

## MVP internal endpoint families

## 1. Moderation queue

### `GET /api/v1/internal/moderation/queue`

#### Purpose

Return a queue/list of moderation-bound items awaiting review or otherwise relevant to internal operators.

#### Primary use cases

- founder/admin reviews newly submitted corrections
- founder/admin reviews newly suggested venues
- internal operator triages what to action next

#### Suggested response characteristics

Each queue item should provide enough information to decide whether to open it, including:

- internal item id
- item type/category
- submission type
- target venue reference where applicable
- proposed venue name where applicable
- submission timestamp
- current moderation status
- basic submitter attribution summary if appropriate
- lightweight priority/status flags if available

#### Notes

Avoid overbuilding queue intelligence in MVP.

Simple filtering and ordering is enough initially.

---

## 2. Moderation item detail

### `GET /api/v1/internal/moderation/items/{item_id}`

#### Purpose

Return the full internal detail for a moderation item.

#### Use cases

- review a correction submission in context
- review a new venue suggestion in detail
- inspect structured payload and optional note
- inspect enough surrounding context to make a safe decision

#### Correction detail should generally include

- moderation item id
- submission type/category
- target venue identity
- structured proposed changes
- optional submitter note
- submission timestamp
- submitter attribution summary
- relevant current published truth context where needed
- existing internal notes where appropriate
- current moderation status

#### New venue suggestion detail should generally include

- moderation item id
- structured proposed venue data
- optional submitter note
- submission timestamp
- submitter attribution summary
- current moderation status
- duplication-check support later if added

---

## 3. Moderation decisions

### `POST /api/v1/internal/moderation/items/{item_id}/decision`

#### Purpose

Apply a moderation decision to an item.

#### Required MVP actions

At minimum:

- approve
- reject

#### Request shape guidance

The request should be structured and may include:

- decision action
- optional note
- any explicit internal metadata needed for workflow routing

#### Behaviour rules

- operator identity must be recorded from authenticated internal context
- decision timestamp must be recorded
- optional note must be stored as internal-only audit context
- moderation/workflow state must be updated safely
- if approval results in published changes, it must follow the proper publish/workflow path rather than bypassing history

#### Important rule

This endpoint does not exist to mutate public truth directly through ad hoc shortcuts.

It exists to drive the formal review/publish flow safely.

---

## 4. Moderation notes

### `POST /api/v1/internal/moderation/items/{item_id}/notes`

#### Purpose

Attach an internal-only note to a moderation item.

#### Use cases

- leave a quick reasoning note
- document uncertainty
- record follow-up context
- preserve operator communication breadcrumbs in a lightweight way

#### Behaviour rules

- note author must be attributed from authenticated internal context
- notes are internal-only
- notes must never appear in public APIs
- note timestamps should be captured

---

## 5. Internal venue lookup

### `GET /api/v1/internal/venues/{venue_id}`

#### Purpose

Provide an internal lookup view for a venue to support moderation and issue handling.

#### Use cases

- inspect a venue while reviewing a correction
- inspect a venue’s public truth state during operational checks
- support simple manual troubleshooting

#### Internal lookup may include more than public detail

For example, where appropriate, it may include:

- internal identifiers
- moderation-relevant context
- operational metadata summaries
- selected freshness or workflow indicators

This data must remain internal-only.

---

## Optional near-term internal endpoints

These are not strictly required for the first MVP cut, but may be added if implementation remains simple and useful.

### Possible additions

- `GET /api/v1/internal/moderation/stats`
- `GET /api/v1/internal/submissions/{submission_id}`
- `GET /api/v1/internal/users/{user_id}` for narrow moderation context
- `POST /api/v1/internal/moderation/items/{item_id}/reassign` if internal workflows grow

These are not necessary to define as launch blockers.

---

## Internal response design principles

### 1. Prefer operational clarity over public polish

Internal endpoints should be clean and structured, but they do not need the same presentation-driven shape as consumer mobile endpoints.

### 2. Include operational identifiers safely

Internal tools may need ids, statuses, and decision metadata that public APIs should never expose.

### 3. Keep payloads task-oriented

Queue endpoints should support triage.

Detail endpoints should support decision-making.

Decision endpoints should support safe action-taking.

Do not overload every endpoint with every field.

---

## Moderation status guidance

The internal/admin endpoint layer should use explicit moderation/workflow statuses.

Exact taxonomy may depend on the database/workflow design, but likely concepts include:

- pending
- approved
- rejected
- possibly decisioned/published variants depending on workflow architecture

The exact status model should align with the migrated database design rather than inventing a conflicting overlay.

---

## Operator attribution requirements

Operator attribution should exist from day one on moderation actions.

### Minimum recorded fields

- operator identity
- action taken
- action timestamp
- optional note

This supports:

- accountability
- reviewability
- operational trust
- future auditability

---

## Security rules

### Required

- all internal endpoints require strict internal authorization
- internal data must never be exposed through public mobile endpoints
- moderation decisions must be auditable
- internal notes are never public
- operator attribution must come from authenticated internal context, not request body trust

### Avoid

- mixing consumer and internal routes
- allowing internal actions via public endpoints
- weak role checks hidden only in frontend UI
- exposing moderation data to venue detail or profile endpoints

---

## Suggested endpoint summary

### Moderation queue and detail

- `GET /api/v1/internal/moderation/queue`
- `GET /api/v1/internal/moderation/items/{item_id}`

### Moderation actions

- `POST /api/v1/internal/moderation/items/{item_id}/decision`
- `POST /api/v1/internal/moderation/items/{item_id}/notes`

### Operational support

- `GET /api/v1/internal/venues/{venue_id}`

---

## Relationship to public endpoints

Public endpoints are consumer-facing and must remain clean, safe, and browse-focused.

Internal/admin endpoints are operator-facing and may include:

- workflow state
- audit context
- operator actions
- internal notes

These concerns must remain separated even when they reference the same underlying venue or submission entities.

---

## Key decisions

- internal/admin endpoints live in the same Django project
- they are grouped under `/api/v1/internal/...`
- moderation queue/detail/decision/notes are MVP-required
- internal venue lookup is included for operational support
- internal endpoints are a separate authorization domain from consumer endpoints
- operator attribution and lightweight audit notes are included from day one

---

## Assumptions

- the founder/admin team is the primary internal operator group in MVP
- the database/workflow design can support moderation status and attribution
- a lightweight internal UI or admin client will consume these endpoints

---

## Open questions

- exact internal authentication mechanism
- exact moderation status taxonomy
- whether internal lookup needs additional entity families beyond venues in MVP

These do not block the endpoint scope definition.

---

## Dependencies

- `backend/docs/AUTH_MODEL.md`
- `backend/docs/API_ENDPOINT_OVERVIEW.md`
- `backend/docs/WRITE_PATHS_AND_MODERATION.md`
- moderation workflow/database mapping
- internal operator process definition

---

## Downstream use

This document should guide:

- internal tooling backend workers
- moderation API implementation
- auth/authorization workers for admin scope
- QA review of internal-only endpoint protection