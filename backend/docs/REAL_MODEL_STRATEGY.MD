# PubPlus Read Model Strategy

## Purpose

Define how the backend should shape and serve public read models for the PubPlus consumer app so Home, Search, Map, and Venue Detail can all operate against stable, performant, trust-aware backend contracts.

## Current stage

Architecture and read-path planning before implementation.

## Summary

PubPlus is a discovery-first consumer product. The backend read layer must therefore do more than expose raw venue records.

The backend must provide read models that are:

- optimized for frontend consumption
- derived from published public truth only
- consistent across surfaces
- able to include backend-computed fields such as `open_now`
- capable of light authenticated enrichment such as `is_saved`
- future-safe for later owner/business/commercial expansion without polluting MVP payloads

The read model strategy should distinguish between:

- canonical data truth in the database
- backend read aggregation and computation
- UI-facing payload shapes

The backend should not expose raw database structure directly to the client.

---

## Core principles

### 1. Read models are product-facing contracts, not table dumps

The frontend should receive payloads shaped around user experiences such as:

- venue cards
- map markers
- home sections
- venue detail blocks

The API should not force the frontend to reconstruct product meaning out of loosely related raw fields.

### 2. Public read models must use published truth only

All public read APIs must operate from published/canonical public truth.

They must not leak:

- workflow state
- moderation history
- internal confidence details unless intentionally surfaced
- private consumer state beyond safe per-user enrichment
- future owner/business/commercial state

### 3. Shared fields should remain consistent across surfaces

A venue shown on:

- Home
- Search
- Map popup
- Saved list
- Venue Detail entry point

should preserve a consistent identity and core field semantics.

For example, `open_now`, `hero_photo_url`, `venue_type`, and `is_saved` should mean the same thing wherever they appear.

### 4. Backend-computed fields belong in the read layer

The frontend should not compute high-trust behaviour such as:

- `open_now`
- distance calculations used for ranking/display
- whether a saved-state indicator should be shown
- which specials/events are eligible to surface in current contexts

These belong in backend read orchestration.

### 5. Different surfaces may have different payload densities

Even though they use a shared read foundation, different surfaces have different needs:

- Search needs compact ranked cards
- Map needs lightweight marker/popup payloads
- Home needs sectioned content
- Venue Detail needs full aggregation

The backend should support this intentionally rather than overusing one oversized generic payload.

---

## Read model layers

## Layer 1 — Canonical published truth

This is the stable public data foundation stored in Supabase/Postgres.

Examples include:

- venue identity
- suburb/address/location
- published hours and exceptions
- published features
- published specials
- published events
- published drink/tap highlights
- published media references
- published contact details

This layer is the source of truth, but it is not the direct API contract.

---

## Layer 2 — Backend domain read aggregation

This is where Django assembles and computes usable product read state.

Examples include:

- resolving a venue card from multiple public truth domains
- computing `open_now`
- resolving media URLs
- deriving surface-friendly summaries
- preparing home sections
- joining authenticated save-state where applicable

This layer should be implemented in services, not in raw views.

---

## Layer 3 — UI-facing API payloads

This is the final contract returned to the app.

Examples include:

- home section payloads
- search venue card lists
- map marker/card payloads
- full venue detail objects

This layer should remain stable enough that frontend screens can depend on it confidently.

---

## Public read surfaces

## 1. Home read model

### Purpose

Provide an orchestrated, sectioned discovery response for the app Home screen.

### Characteristics

Home is not just “search with defaults.”

It should blend multiple discovery intents into a single curated payload such as:

- nearby venues
- open now
- specials tonight
- events tonight
- light preference-aware suggestions

### Home payload requirements

The response should:

- be section-based
- use compact venue card structures
- support optional location/suburb context
- support light personalization when authenticated or preference data is available
- remain useful when unauthenticated

### Recommended response shape direction

A home payload should contain:

- metadata/context block
- ordered sections
- each section containing a list of compact venue cards

Example section concepts:

- `nearby`
- `open_now`
- `specials_tonight`
- `events_tonight`
- `for_you`

These are product-facing section names and may later be refined.

---

## 2. Search read model

### Purpose

Provide ranked list/card results for structured venue discovery.

### Characteristics

Search should return:

- compact but useful venue cards
- stable filter-compatible fields
- backend-computed `open_now`
- distance when location-aware
- optional save-state enrichment

### Search read model requirements

Search should support:

- suburb filtering
- distance/radius filtering
- open-now filtering
- specials filtering
- drink-type filtering
- venue-feature filtering
- event filtering
- eventual text query support if needed by UI

### Search payload guidance

The response should prioritize:

- fast list rendering
- stable card semantics
- pagination discipline
- minimal overfetching

The Search response should not send full detail payloads.

---

## 3. Map read model

### Purpose

Provide lightweight, viewport-aware venue data for map rendering.

### Characteristics

Map and Search share the same discovery core, but Map has different payload and performance needs.

Map should support:

- viewport-based querying
- lightweight marker payloads
- optional small popup preview fields
- shared filter logic with Search
- backend-computed `open_now`

### Map payload guidance

Map payloads should be smaller than Search payloads where possible.

A Map response may include:

- marker coordinates
- venue id
- venue name
- compact badge/highlight data
- open-now state
- hero image preview if needed
- save-state enrichment if authenticated

Avoid sending full venue detail content in the map result set.

---

## 4. Venue Detail read model

### Purpose

Provide the full venue detail response for a single venue page.

### Characteristics

Venue Detail is the richest public read surface in MVP.

It should aggregate the practical information a user needs to decide where to go.

### Required MVP detail sections

The detail payload must be able to support:

- name
- venue type
- address
- suburb
- map coordinates
- hours
- `open_now`
- photos
- venue features
- specials
- events
- drink/tap highlights where available
- contact links
- authenticated save action state
- correction/new-submission entry point support

### Freshness/provenance handling

For MVP, provenance/freshness should remain mostly internal.

Only light user-facing freshness messaging should be surfaced where useful.

Do not expose heavy internal provenance structures directly in the public detail model.

---

## Shared card model strategy

The backend should define a common compact venue card model used across:

- Home sections
- Search results
- Saved list
- Map popup previews where suitable

This helps keep frontend rendering logic simpler and product semantics more consistent.

### Recommended compact card fields

A shared venue card should generally support:

- `id`
- `name`
- `venue_type`
- `suburb`
- `address_short`
- `latitude`
- `longitude`
- `hero_photo_url`
- `open_now`
- `distance_m` when applicable
- `feature_badges`
- `specials_summary`
- `events_summary`
- `drink_highlights`
- `is_saved` if authenticated, or consistently represented otherwise

Not every surface must show every field, but semantics should remain aligned.

---

## Authenticated enrichment strategy

Public read endpoints remain browseable without login.

When authenticated, the backend may enrich public responses with per-user context such as:

- `is_saved`
- light preference-aware ordering or section prioritization

### Rules

- enrichment must never be required for the endpoint to work
- public contracts should remain valid when unauthenticated
- the API should consistently represent `is_saved` for authenticated and unauthenticated states according to one chosen convention
- private-state joins must not distort public truth semantics

---

## Open-now strategy in read models

`open_now` is a backend-computed field and should appear consistently across read models where relevant.

### Rules

- compute from published hours and valid exceptions only
- unknown must not silently become false-closed unless that is genuinely the business meaning
- frontend should not recompute or override it
- Search, Map, Home, and Venue Detail should use the same underlying logic

### Representation guidance

A simple boolean may be enough for MVP product display, but the backend may internally preserve richer operational state.

If richer public representation is later needed, it should be an additive contract evolution.

---

## Specials, events, and drink/tap highlight strategy

Dynamic venue subdomains such as specials, events, and drink/tap highlights should be read-model aware.

### Rules

- only include published/currently eligible content
- summaries on compact cards should stay short
- richer lists/details belong in Venue Detail
- avoid dumping raw, uncurated arrays into Search/Map cards

### Surface guidance

- Home/Search/Map cards: small summary/highlight form
- Venue Detail: fuller structured representation

---

## Media/photo strategy in read models

The backend should return direct asset URLs from Supabase Storage.

### Rules

- prefer public URLs where appropriate
- use signed URLs only where protection is required
- do not proxy media through Django by default
- present a clear primary hero image where available
- keep detail payloads ready for multiple photos

### Card vs detail behaviour

- card surfaces typically use one hero image
- detail may expose a photo collection

---

## Distance and location strategy

Location-aware surfaces may include computed distance values.

### Rules

- backend computes and returns distance when applicable
- Search and Home may use radius or lat/lng context
- Map primarily uses viewport bounds but may still include distance where useful
- frontend should treat returned distance as display-ready backend truth

---

## Ranking vs read model separation

Ranking logic influences which records appear and in what order, but ranking itself is not the read model.

The read model should remain the stable output structure after ranking/orchestration has selected candidate records.

This helps keep:

- ranking policy
- read aggregation
- API serialization

cleanly separated.

---

## Performance guidance

Read models must be designed with performance in mind because the most latency-critical MVP surfaces are:

- Search
- Map
- Home
- Venue Detail

### Practical guidance

- keep card payloads compact
- avoid unnecessary joins for list/map surfaces
- aggregate only what each surface needs
- reuse shared read foundations where possible
- review authenticated enrichment costs such as save-state joins
- avoid returning detail-grade nested structures in high-volume list endpoints

---

## Future-readiness requirements

The public read model strategy must leave room for later:

- owner-verified overlays
- promotions
- subscription-driven owner tooling
- analytics-driven internal logic
- richer freshness messaging

But MVP public read models should not expose these domains prematurely.

---

## Key decisions

- public read models are shaped by product surfaces, not raw tables
- Home, Search, Map, and Venue Detail each have intentionally different payload density
- Search and Map share a common discovery core
- compact venue cards should be semantically consistent across surfaces
- `open_now` is backend-computed only
- authenticated enrichment such as `is_saved` is additive and lightweight
- dynamic subdomains such as specials/events/drinks should be summarized on compact surfaces and expanded on detail surfaces

---

## Assumptions

- the migrated Supabase schema contains the public truth needed to assemble these read models
- frontend can align to backend-defined payload structures with only small payload-driven adjustments
- authenticated save-state annotation is acceptable on public reads when logged in

---

## Open questions

- exact final field names for card/detail payloads
- whether unauthenticated `is_saved` is omitted or consistently false
- how much text search behaviour is included in MVP Search beyond structured filtering

These are implementation questions, not blockers for read model strategy.

---

## Dependencies

- `backend/docs/BACKEND_ARCHITECTURE_OVERVIEW.md`
- `backend/docs/API_ENDPOINT_OVERVIEW.md`
- `backend/docs/SERVICE_BOUNDARIES.md`
- database public truth domain mapping
- frontend screen integration review

---

## Downstream use

This document should guide:

- discovery API workers
- venue detail workers
- response serializer/contract design
- performance review for public read endpoints
- frontend/backend contract review