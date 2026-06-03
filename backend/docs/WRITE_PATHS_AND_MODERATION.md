# PubPlus Write Paths and Moderation

## Purpose

Define the backend rules for authenticated consumer write paths and internal moderation handling so PubPlus preserves trust, auditability, and clean separation from published public truth.

## Current stage

Implemented MVP write-path safety and Stage D moderation decision/notes flows, now in release-hardening.

## Summary

For MVP, consumer-originated writes are limited to:

- save/unsave venue
- profile/preferences updates
- correction submission
- new venue suggestion submission

Among these, the trust-sensitive write paths are submissions.

All consumer submissions must be moderation-first and must never directly mutate published public venue truth.

Internal/admin endpoints must support a minimal but usable moderation flow including:

- queue/list
- detail
- decision
- audit notes
- operator attribution

---

## Core principles

### 1. Published truth is write-protected from consumer actions

No consumer-facing endpoint may directly write to published venue truth.

This includes:
- correction submissions
- new venue suggestions
- structured updates about specials/events/taps under correction flow

These must enter workflow/moderation state first.

### 2. Structured-first payloads

Submission payloads should bias strongly toward structured fields.

Optional free-text notes may provide context, but they should not be the primary submission model.

### 3. All trust-sensitive writes require explicit rule handling

Do not treat submissions as generic form blobs.

Validation and routing rules should be explicit.

### 4. Auditability matters in MVP

Even lightweight moderation should preserve:
- who submitted
- when they submitted
- what structured data they provided
- what decision was made
- who made the decision
- what note was attached, if any

### 5. Save/profile writes are different from moderation-bound writes

Not all writes need moderation.

The backend should clearly separate:
- consumer-private writes
- moderation-bound public-data suggestions

---

## Write domain breakdown

## 1. Saved venues write path

### Product behaviour
Authenticated consumer can save or unsave a venue.

### Backend rules
- requires valid consumer auth
- only affects consumer-private state
- must not affect public venue truth
- must be idempotent where practical
- should be simple in MVP product behaviour
- should remain structurally compatible with future saved lists/collections

### Recommended operations
- save venue
- unsave venue

### Notes
This is not a moderation domain.

---

## 2. Profile/preferences write path

### Product behaviour
Authenticated consumer can update profile basics and preferences.

### MVP profile fields (implemented)
- `display_name`, `avatar_storage_ref` (`consumer_profile`)
- `default_locality_id`, `default_geographic_region_id` (`consumer_default_location_preference`)
- notification opt-ins and quiet hours (`consumer_notification_settings`)

### Deferred preference areas (not in PATCH allowlist)
- distance preference
- favourite drink types
- favourite venue features
- event interests
- rich personalization / Home `for_you`

### Backend rules
- requires valid consumer auth
- only updates account-bound private state
- payload should be structured
- validation should be explicit
- unknown/unsupported keys should not silently create ad hoc schema behaviour

### Notes
This is not a moderation domain.

---

## 3. Correction submission write path

### Product behaviour
Authenticated consumer submits a correction to an existing venue.

### Mandatory characteristics
- linked to existing venue identity
- structured-first payload
- optional contextual free-text notes
- moderation-bound
- no direct mutation of published truth

### Types of correction content
May include:
- incorrect hours
- incorrect address/contact data
- feature inaccuracies
- specials/event/tap inaccuracies
- other structured venue-data corrections

### Recommended request shape principles
Payload should separate:
- target venue identity
- correction domain/category
- structured proposed values
- optional note
- optional evidence metadata later if added

### Backend handling
- validate payload
- attribute to authenticated consumer
- create workflow/moderation submission record
- return acknowledgement response
- do not publish directly

---

## 4. New venue suggestion write path

### Product behaviour
Authenticated consumer suggests a new venue not currently in the system.

### Mandatory characteristics
- structured-first payload
- optional contextual free-text notes
- moderation-bound
- no automatic creation of published public venue truth

### Suggested required structured fields for MVP
At minimum, aim for structured capture of:
- venue name
- venue type
- address
- suburb
- contact or link data where available

### Backend handling
- validate structured minimums
- attribute to authenticated consumer
- create workflow/moderation-bound record
- return acknowledgement response
- do not publish directly

---

## Submission acknowledgement behaviour

For MVP, submission responses should confirm receipt without promising publication.

Recommended response pattern:

```json
{
  "status": "received",
  "message": "Your submission has been received and will be reviewed."
}
```

Avoid exposing complex workflow state in the consumer app for MVP unless it is added later intentionally.

Internal moderation scope

MVP moderation backend should support:

queue/list of items awaiting review
item detail
moderation decision actions
lightweight audit notes
operator attribution
internal venue lookup support where useful

This should be enough for founder/admin manual moderation.

Moderation queue model

Queue/list endpoints should support at least:

pending items
item type/category
submission time
target venue reference where applicable
submitting user reference summary if appropriate
lightweight status/priority indicators if available

Avoid overbuilding advanced queue tooling for MVP.

Moderation item detail model

Internal detail view should expose enough context to make a safe decision.

For corrections, detail should include:

target venue
structured proposed changes
optional submitter note
existing public truth context where needed
relevant timestamps
submitter attribution summary
prior internal notes if any

For new venue suggestions, detail should include:

proposed venue structured fields
optional note
duplication-check support later if needed
submitter attribution summary
Moderation decisions
Required MVP decisions

At minimum:

approve
reject
Optional later decisions

Potential later additions:

request more information
merge into existing item
mark duplicate

These are not required for MVP.

Decision handling principles
record operator identity
record timestamp
record optional note
update workflow/moderation state accordingly
if approved, invoke the proper publish/workflow path rather than shortcutting history
Operator attribution and notes

Every moderation decision should support:

operator identity
decision timestamp
optional lightweight audit note

Notes should be internal-only.

Notes are not consumer-facing content.

Stage D implementation lock
- moderation decisions are limited to `approve` / `reject`
- moderation decision endpoint updates workflow review state only (`proposal_review` + `venue_change_proposal` + audit)
- moderation decision endpoint does not directly mutate `venue_published_*` or write publish-lineage rows
- moderation notes are append-only internal audit notes and are never public endpoint fields
- operator attribution requires internal JWT subject mapping to `admin_account`

Operator precondition
- internal operators must be provisioned with an `admin_account` row linked to JWT `sub`
- missing mapping is an operator-environment readiness issue surfaced as `409 operator_resolution_failed`

Test caveat (infrastructure)
- DB-backed tests for workflow/published-table behavior may skip when those fixtures are unavailable in test DB
- those skips are infrastructure-only and do not indicate an endpoint runtime contract failure

Separation rules
Rule 1: Consumer submissions are not moderation decisions

Submission endpoints only ingest suggested changes.

They do not:

approve changes
mutate published truth
alter moderation status outside the initial intake state
Rule 2: Moderation endpoints are internal only

No public mobile endpoint should expose moderation controls.

Rule 3: Private-state writes stay outside moderation workflow

Save/unsave and profile/preferences writes should not enter moderation.

Rule 4: Trust-sensitive publication must follow proper workflow

If a moderation action results in published changes, this must happen through the established workflow/publish architecture from the database design, not by ad hoc overwrite logic.

Suggested endpoint families
Consumer-private writes
POST /api/v1/saved/venues
DELETE /api/v1/saved/venues/{venue_id}
PATCH /api/v1/profile
Consumer moderation-bound submissions
POST /api/v1/submissions/corrections
POST /api/v1/submissions/new-venues
Internal moderation
GET /api/v1/internal/moderation/queue
GET /api/v1/internal/moderation/items/{item_id}
POST /api/v1/internal/moderation/items/{item_id}/decision
POST /api/v1/internal/moderation/items/{item_id}/notes
Validation guidance
Submission validation

Validate:

required structured fields
allowed categories/domains
target venue presence for corrections
field type correctness
supported value formats
note length constraints if present
Private-state validation

Validate:

allowed profile/preference fields
allowed data types and enums
venue existence for save operations
Avoid
accepting arbitrary JSON blobs without structure
silently discarding critical fields
allowing client-defined workflow state
Idempotency and duplicate handling
Save/unsave

Should be idempotent where practical.

Submissions

Exact duplicate prevention is not essential for MVP, but the backend should be designed so duplicate detection can be added later without redesigning the public contract.

New venue suggestions

Internal moderation may later need duplicate/merge support, but MVP can begin with manual review.

Security and trust rules
authenticated consumer identity must come from verified Supabase JWT
submission attribution must not rely on client-supplied user identifiers
internal moderation actions must require strict admin/internal authorization
public endpoints must never expose internal notes
moderation actions must be auditable
published truth mutation must never be possible through public submission endpoints
Key decisions
submissions are moderation-first only
save/profile writes are private-state writes, not moderation flows
submission payloads are structured-first with optional notes
moderation must support queue/detail/decision/notes/operator attribution from day one
public truth remains protected from direct consumer mutation
Assumptions
the migrated DB includes or will support workflow/moderation entities aligned to this flow
founder/admin team is sufficient for MVP moderation load
frontend submission UIs can support structured field capture
Open questions
exact structured field sets for each correction category
exact moderation item schema and decision taxonomy
whether evidence attachments are deferred entirely in MVP

These are important for implementation but do not block the architecture rules.

Dependencies
BACKEND_ARCHITECTURE_OVERVIEW.md
AUTH_MODEL.md
API_ENDPOINT_OVERVIEW.md
database workflow/moderation design
internal moderation process expectations
Downstream use

This document should guide:

submission API workers
moderation/internal tooling workers
backend validation design
QA review for write-path safety