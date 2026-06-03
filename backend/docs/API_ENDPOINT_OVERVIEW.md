# PubPlus API Endpoint Overview

## Purpose

Define the initial REST API surface for the PubPlus backend so frontend integration and backend implementation can proceed against a stable contract direction.

## Current stage

Implemented MVP backend contract baseline with Stage D internal/admin moderation endpoints.

## API principles

- All public application APIs are served by Django
- API is versioned from day one under `/api/v1/...`
- Public browsing endpoints do not require authentication
- Consumer-private actions require a valid Supabase JWT
- Internal/admin endpoints live in the same Django project but behind strict internal authorization
- Public read endpoints expose published truth only
- Trust-sensitive computed fields such as `open_now` are computed in backend
- Endpoint contracts should remain future-safe for later owner/business APIs

---

## Base path

- `/api/v1`

---

## Response conventions

### Success

Use conventional HTTP success codes:

- `200 OK` for reads and updates
- `201 Created` for creates
- `204 No Content` for deletes/toggle actions where no body is needed

### Errors

Use conventional error codes:

- `400 Bad Request` for invalid input
- `401 Unauthorized` for missing/invalid auth on private endpoints
- `403 Forbidden` for authenticated but unauthorized access
- `404 Not Found` for missing resources
- `409 Conflict` where conflict semantics are appropriate
- `422 Unprocessable Entity` if the implementation distinguishes validation failures from malformed requests

### Error body shape

Recommended baseline:

```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more fields are invalid.",
    "details": {
      "field_name": ["This field is required."]
    }
  }
}
```


Public endpoint groups
1. Health / status
GET /api/v1/health
Purpose

Basic backend health/smoke-check endpoint.

Auth

Public

Notes

Should confirm the Django service is alive. Keep simple.

2. Home
GET /api/v1/home
Purpose

Return the Home feed response used by the app home screen.

Auth

Public, with optional authenticated enrichment

Expected behaviour

Returns an orchestrated home payload. **Current MVP sections:** nearby, open now, specials tonight. **`events_tonight` is not returned** until a published public event catalog exists (future read model).

Future section concepts may also include:

events tonight
light preference-aware suggestions
Query parameters

Possible initial parameters:

lat
lng
suburb
optional lightweight personalization context if authenticated
Notes

Home is not just generic search. It should return sectioned content.

3. Search
GET /api/v1/search/venues
Purpose

Return venue search results in list/card mode.

Auth

Public, with optional authenticated enrichment

Required MVP filters

Support query parameters for:

suburb
lat
lng
radius_m (must be sent together with `lat` and `lng`; radius-only requests are invalid)
open_now
meal_specials
drink_types
venue_features
q (venue name + suburb/locality text search)
events — **deferred** (`400 events_unavailable`; no published event catalog for Search filtering yet)
Optional pagination parameters
limit
offset or cursor-based pagination later
Notes

Search uses the shared discovery query core.

GET /api/v1/search/filters
Purpose

Return public reference metadata for Search filter chips so the consumer app can render labels while sending canonical filter values to `/api/v1/search/venues`.

Auth

Public

Response shape

```json
{
  "data": {
    "venue_features": [
      { "key": "beer_garden", "label": "Beer garden", "group": "spaces" }
    ],
    "drink_types": [
      { "id": "uuid", "label": "Craft beer" }
    ],
    "meal_specials": [
      { "key": "meal_special", "label": "Meal specials tonight" }
    ],
    "event_filters": []
  }
}
```

Semantics

- `venue_features[].key` — attribute `stable_key` accepted by `venue_features` on Search (boolean discovery-driving definitions).
- `drink_types[].id` — `beverage_product.id` UUID accepted by `drink_types` on Search.
- `meal_specials[].key` — structured special kind accepted by `meal_specials` on Search (MVP: `meal_special` only).
- `event_filters` — intentionally empty until a published public events catalog exists. **Clients must not render event filter chips unless this array is non-empty.**

Search venues filter parameters

- `venue_features` — canonical `stable_key` values (not display labels).
- `drink_types` — `beverage_product` UUIDs.
- `meal_specials` — supported kind values (currently `meal_special`).
- `lat`, `lng`, `radius_m` — radius search requires all three parameters. Clients must not send `radius_m` without valid `lat` and `lng`.

Dev/demo note: feature filter efficacy depends on seeded `venue_published_attribute_value` rows with `value_boolean = true` for the MVP boolean definitions (`dev_seed_mvp_feature_attribute_values.sql`).
- `events` — deferred (`400 events_unavailable`).
- `q` — MVP text search over published **venue display name** and **locality/suburb name** only (case-insensitive partial `ILIKE` match). Does not search events, specials, drinks, attributes, or internal/moderation content. Trimmed; whitespace-only is ignored; max 100 characters (`400 invalid_q` if longer). Combines with structured filters. No relevance ranking beyond existing discovery ordering.

Notes

Values are schema-backed from reference tables where available. Response is cache-friendly and public.

4. Map
GET /api/v1/map/venues
Purpose

Return venues for map rendering using viewport-based querying.

Auth

Public, with optional authenticated enrichment

Required MVP query parameters
north
south
east
west
Supported filters

Same logical filter family as Search where applicable:

open_now
meal_specials
drink_types
venue_features
events — deferred (same as Search)
suburb or locality filters if supported in map mode
Notes

Map and Search share the same core discovery service but produce different response shapes.

Map payload should be optimized for:

marker rendering
lightweight popup/card previews
result counts or clustering later if needed
5. Venue detail
GET /api/v1/venues/{venue_id}
Purpose

Return the full venue detail payload.

Auth

Public, with optional authenticated enrichment

Must include for MVP
name
type
address
suburb
map coordinates
hours
open_now
photos
venue features
specials
events
tap/drink highlights where available
contact links
save state if authenticated
correction/new-submission entry affordance data if useful
Notes

Freshness/provenance should remain mostly internal in MVP, with only light user-facing freshness messaging where useful.

Consumer-authenticated endpoint groups
6. Saved venues
GET /api/v1/saved/venues
Purpose

List the authenticated user’s saved venues.

Auth

Consumer auth required

POST /api/v1/saved/venues
Purpose

Save a venue for the authenticated user.

Auth

Consumer auth required

Recommended request body
{
  "venue_id": "uuid-or-stable-id"
}
DELETE /api/v1/saved/venues/{venue_id}
Purpose

Unsave a venue for the authenticated user.

Auth

Consumer auth required

Notes

MVP product behaviour is simple save/unsave, but implementation should preserve future path to lists/collections later.

7. Profile and preferences
GET /api/v1/profile
Purpose

Return profile basics and stored preferences for the authenticated consumer.

Auth

Consumer auth required

PATCH /api/v1/profile
Purpose

Update profile basics and/or preferences.

Auth

Consumer auth required

MVP profile fields (PATCH allowlist — unknown keys return `400`):

- `display_name`, `avatar_storage_ref`
- `default_locality_id`, `default_geographic_region_id` (FK-valid UUIDs or `null`)
- `email_marketing_opt_in`, `email_transactional_opt_in`, `push_notifications_opt_in`
- `sms_marketing_opt_in`, `sms_transactional_opt_in`
- `quiet_hours_start_local`, `quiet_hours_end_local` (both null or both set)

Deferred until persistence and personalization models exist: distance preference, favourite drink types, favourite venue features, event interests, and rich Home personalization.

Notes

Keep payload structured; reject unsupported keys explicitly.

8. Submissions
POST /api/v1/submissions/corrections
Purpose

Submit a correction for an existing venue.

Auth

Consumer auth required

Behaviour
structured-first payload: `venue_id` (UUID), `domain` (`profile` | `location` | `attributes` | `hours`), and domain-specific `proposed_values`; `note` optional (bounded)
domains outside that set are rejected until staging models exist for them
`201` response body is acknowledgement-only: `{ "status": "received", "message": "…" }` (no internal workflow or moderation state)
routes to moderation/workflow state
must not mutate published truth directly
POST /api/v1/submissions/new-venues
Purpose

Suggest a new venue.

Auth

Consumer auth required

Behaviour
structured minimum: `name`, `address_line_1` required; `address_line_2`, `locality_id`, `geographic_region_id`, `postcode`, `latitude`, `longitude`, `country_code`, `note` optional; locality/region are FK-validated; region must match the locality when both are sent
creates a canonical `venue` shell plus `venue_change_proposal` + `venue_proposal_target` (profile, geo) + profile/location staging only — not `venue_published_*` discovery truth
`201` acknowledgement body as for corrections; no internal moderation data in the response
routes to moderation/workflow state
must not directly create published public truth
Deferred endpoints

Potential later endpoints, not required for MVP:

GET /api/v1/submissions
GET /api/v1/submissions/{submission_id}

These would support user-visible submission history/status later.

Internal/admin endpoint groups
9. Internal moderation

All internal endpoints should live under:

/api/v1/internal/...

They must be protected by strict internal/admin authentication and authorization.

GET /api/v1/internal/moderation/queue
Purpose

Return moderation queue items for admin/operator use.
Current implementation notes
- canonical `item_id` is `venue_change_proposal.id`
- required filters supported: `status`, `domain`, `venue_id`
- optional filters supported: `created_before`, `created_after` (ISO datetime)
- `domain=location` maps to workflow target family `geo`
- default queue scope is open items (`staged`, `in_review`)
- compact response only (no full staging payload dump)

GET /api/v1/internal/moderation/items/{item_id}
Purpose

Return moderation item detail.
Current implementation notes
- `{item_id}` resolves directly to `venue_change_proposal.id`
- includes proposal header, target families, staging payloads (profile/location/attributes/hours), and read-only review rows
- includes bounded published-venue context when available
- does not mutate lifecycle/workflow state

POST /api/v1/internal/moderation/items/{item_id}/decision
Purpose

Apply moderation decision.
Current implementation notes
- accepts JSON body: `decision` (`approve` or `reject`) and optional `reason`
- canonical `{item_id}` is `venue_change_proposal.id` (UUID)
- validates internal operator by resolving JWT `sub` to `admin_account.id` before write
- writes formal review row in `proposal_review` with reviewer attribution and sequence
- transitions `venue_change_proposal.lifecycle_status` to `approved` or `rejected` and sets `closed_at`
- rejects re-decision of terminal proposals with `409 conflict`
- appends bounded `audit_event` action `moderation_decision`
- does **not** write `venue_publish_event` or `venue_published_*` rows in this stage
- requires internal operator JWT `sub` to resolve to `admin_account.id`; missing mapping returns conflict-style failure (`operator_resolution_failed`)

POST /api/v1/internal/moderation/items/{item_id}/notes
Purpose

Add lightweight audit/operator note.
Current implementation notes
- accepts JSON body: `body` (required, non-empty, max 2000 chars)
- stores append-only note in `audit_event` with action `internal_note`
- note is attached to `venue_change_proposal` item only (not venue-level)
- internal moderation detail now includes these notes under `internal_notes`
- notes are internal-only and are not exposed by public `/api/v1/venues/{venue_id}` responses

GET /api/v1/internal/venues/{venue_id}
Purpose

Internal lookup endpoint for operations/moderation support.
Current implementation notes
- reuses published venue read bundle when present
- shell/unpublished venues return a fallback view based on latest proposal staging data
- includes light workflow summary (`open_proposal_count`, `latest_open_proposal_id`) only

Notes

Can expose richer internal context than public venue detail, but only to authorized internal users.

### Stage D test caveat (DB-backed suites)

- Some Stage D and discovery/venue-detail tests are intentionally DB-backed.
- In environments where workflow/published fixture tables are unavailable, those tests skip.
- Those skips indicate test-infrastructure readiness gaps, not a runtime contract blocker in the implemented endpoints.

Auth behaviour on public endpoints

Public endpoints should work without login.

When authenticated, some public endpoints may return enriched fields such as:

is_saved
preference-aware section ordering
light personalization

When unauthenticated, behaviour should be consistent across the API:

either omit is_saved
or return false

One convention should be chosen and applied everywhere.

Suggested high-level response shapes
Venue card shape

Used by Home/Search/Map previews.

Recommended fields:

id
name
venue_type
suburb
address_short
latitude
longitude
hero_photo_url
open_now
distance_m when applicable
feature_badges
specials_summary
events_summary — empty in MVP (no published event catalog); reserved for future compact event labels
drink_highlights
is_saved when authenticated or consistently represented otherwise
Venue detail shape

Recommended sections:

identity block
location block
hours/open-now block
photos block
features block
specials block
events block — `items` empty and `not_implemented: true` until a published event catalog exists
drinks/taps highlights block
contact links block
authenticated actions block
Pagination guidance

MVP can begin with simple limit/offset pagination for list-based endpoints if needed.

Map endpoints should prioritize bounded viewport result handling over traditional pagination.

Avoid oversized payloads on Home, Search, and Map.

Key decisions
API is versioned under /api/v1
Django is the only public application API
public and internal endpoints live in one Django project with separate authorization
Search and Map are separate endpoint surfaces on top of a shared discovery core
Home has its own orchestration endpoint
Saved/Profile/Submissions are authenticated consumer endpoints
moderation/internal tools live under /api/v1/internal
Assumptions
frontend can adapt to backend-defined contract shapes with minimal UI change
database foundation can support these endpoint domains without major schema redesign
internal admin tooling needs are minimal in MVP
Open questions
exact field names for all payloads
pagination details
whether search/filters is implemented immediately or deferred
exact internal moderation action taxonomy

These are implementation-level, not planning blockers.

Dependencies
BACKEND_ARCHITECTURE_OVERVIEW.md
AUTH_MODEL.md
frontend screen review
DB domain mapping
moderation workflow mapping
Downstream use

This document should guide:

backend API implementation workers
frontend integration planning
QA endpoint acceptance criteria
internal/admin tooling integration