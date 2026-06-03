# Product Definition / Taxonomy Closeout

## Status

**completed**

Stages 0–12 resolved the MVP product-definition and taxonomy contract issues that were deferred after initial backend/mobile integration. Stage 13 documents the final state for leadership handoff and future agents.

---

## Executive summary

This workstream established stable, honest MVP semantics for PubPlus discovery, search, locality, profile preferences, venue detail, and attribute correction. The backend now exposes canonical reference endpoints (`/search/filters`, `/reference/localities`), Search enforces validated filter contracts (`q`, suburb, radius triplet, feature keys, drink UUIDs, meal kinds), and the consumer app aligns to those contracts with generated OpenAPI types on high-risk surfaces.

Events, taste preferences, event/drink/special correction UI, full-text search ranking, and several profile editing flows remain intentionally deferred. The product no longer misrepresents unavailable capabilities (no fake event counts, no event filter chips, no static suburb lists in production paths).

---

## Final MVP product decisions

### Search `q`

- **Decision:** MVP text search is limited to published venue display name and locality/suburb name. No semantic search over events, specials, drinks, attributes, or internal content.
- **Implemented behaviour:**
  - Case-insensitive partial match (`ILIKE`) on venue name + locality name.
  - Trimmed input; whitespace-only ignored (not sent).
  - Max 100 characters; longer values return `400 invalid_q`.
  - Combines with structured filters (`venue_features`, `drink_types`, etc.).
  - No relevance ranking beyond existing discovery ordering.
  - Consumer Search placeholder: “Search by venue or suburb”.
- **Deferred behaviour:** Full-text search, FTS indexing, relevance ranking, cross-domain semantic search (events/specials/drinks/attributes).

### Search filters

- **Decision:** Filter chips render from backend reference data; clients send canonical values to `/search/venues`, not display labels.
- **Implemented behaviour:**
  - `GET /api/v1/search/filters` returns labels + canonical keys/ids.
  - Search sends `venue_features` as stable keys, `drink_types` as beverage product UUIDs, `meal_specials` as structured kind strings, `open_now=true` only (false rejected).
  - Feature filter efficacy requires seeded published boolean attribute values (`dev_seed_mvp_feature_attribute_values.sql`).
  - Event filter chips must not render when `event_filters` is empty.
- **Canonical values:**
  - `venue_features[].key` — attribute `stable_key` (e.g. `beer_garden`)
  - `venue_features[].definition_id` — attribute definition UUID (corrections only)
  - `drink_types[].id` — `beverage_product.id` UUID
  - `meal_specials[].key` — structured special kind (MVP: `meal_special` only)
  - `event_filters` — `[]` (empty until event catalog exists)

### Location and locality

- **Decision:** Suburb filtering uses exact backend locality name (case-insensitive). Radius search requires a valid coordinate origin. Locality pickers use the reference endpoint, not static lists.
- **Implemented behaviour:**
  - `suburb` — exact match on published venue locality name (`lower(l.name) = lower(suburb)`); no aliases (use `Melbourne`, not `CBD`); locality UUIDs not accepted as filter values.
  - `radius_m` — valid only with `lat` + `lng` together; radius-only requests return `400 location_incomplete`.
  - Consumer app disables distance chips when no valid origin exists; never sends `radius_m` without coordinates.
  - Search and Profile suburb pickers load from `GET /api/v1/reference/localities`.
  - Scope: localities with at least one discovery-eligible published venue (not a national suburb directory).
- **Current discovery origin priority:**

  ```text
  device GPS → selected Search locality → profile default locality → none
  ```

  - GPS is session/local only; **not persisted** to backend/profile.
  - Profile default locality (`default_locality_id` + `default_geographic_region_id`) **is persisted** via `PATCH /api/v1/profile`.
  - Locality centroids (`latitude`/`longitude` on reference rows) supply Search radius origin when device GPS unavailable.

### Events

- **Decision:** No event catalog in MVP. Do not surface fake or placeholder event discovery.
- **Implemented behaviour:**
  - `event_filters: []` on `/search/filters`.
  - `events=true` (or equivalent `require_published_events`) returns `400 events_unavailable`.
  - Home excludes `events_tonight` section.
  - Search renders no event filter chips.
  - Venue detail: `events.items: []`, `events.not_implemented: true`.
  - Map popup and card mappers only show events when API returns non-empty published data.
- **Deferred behaviour:** Event catalog, event taxonomy, event filters, Home `events_tonight`, event correction UI, event interest profile preferences.

### Attribute taxonomy

- **Decision:** Boolean discovery-driving venue attributes use stable keys for Search filtering and definition UUIDs for structured corrections.
- **Implemented behaviour:**
  - Attributes loaded from `venue_attribute_definition` where `is_discovery_driving = true` and `value_shape = 'boolean'`.
  - Search filters by `stable_key`; detail surfaces features with stable_key + label + value fields.
  - Optional UI grouping on filter reference (spaces, entertainment, food, etc.) — display only, not part of filter contract.
- **Canonical identifiers:**
  - Search/filter: `stable_key` (e.g. `beer_garden`, `rooftop`, `dog_friendly`)
  - Correction submissions: `attribute_definition_id` (UUID)

### Attribute lookup/reference data

- **Decision:** Reuse `/search/filters` as the canonical public reference for boolean venue features and drink/meal filter options; no separate attribute lookup endpoint for MVP.
- **Implemented endpoints:**
  - `GET /api/v1/search/filters` — venue features (key + definition_id + label), drink types, meal specials, empty event_filters
  - `GET /api/v1/reference/localities` — supported discovery localities for Search/Profile pickers

### Profile preferences

- **Decision:** Profile shows only real, persisted MVP settings. Remove/defer taste and personalization chips until models exist.
- **Implemented behaviour:**
  - Default locality/region picker (from `/reference/localities`, persisted via PATCH).
  - Notification toggles: push, email marketing, SMS marketing (and transactional opt-ins on backend PATCH allowlist).
  - Quiet hours displayed when set (read-only in UI).
  - Display name shown from profile or email fallback (read-only in UI).
- **Deferred behaviour:**
  - Taste preferences (favourite drinks, venue features, event interests, distance preference).
  - Home `for_you` / personalization sections.
  - Quiet hours editor UI.
  - Display name / avatar edit UI (backend PATCH fields exist but consumer edit UI deferred).

### Attribute correction UX

- **Decision:** Structured attribute corrections use tri-state feature picker backed by filter reference; note-only attribute corrections not supported.
- **Implemented behaviour:**
  - Correction domains: `profile`, `location`, `attributes`, `hours`.
  - “Features & amenities” domain with tri-state picker: **No change**, **Present**, **Not present**.
  - Feature options loaded from `/search/filters` (`venue_features[].definition_id` + labels).
  - Submit payload: `domain=attributes`, `proposed_values.items[]` with `attribute_definition_id` + `value_boolean` (not `stable_key`).
  - At least one feature must be marked Present or Not present; note is optional.
  - Backend validates definition UUIDs and creates moderation-bound staging rows.
- **Deferred behaviour:**
  - Drinks/taps correction UI.
  - Events correction UI.
  - Specials correction UI.
  - Note-only attribute corrections.
  - Correction submission history/status UI.

---

## Implemented API contracts

| Endpoint | Auth | Current semantics |
|----------|------|-------------------|
| `GET /api/v1/health` | Public | Service alive check |
| `GET /api/v1/home` | Public (+ optional auth enrichment) | Sections: nearby, open now, specials tonight. No `events_tonight`. Optional `lat`/`lng` from discovery origin. |
| `GET /api/v1/search/venues` | Public | Structured filters + `q`; `suburb` exact locality name; radius triplet; `limit` 1–200 (default 50); no offset/cursor pagination; `events` → `400 events_unavailable` |
| `GET /api/v1/search/filters` | Public | Canonical filter reference; `event_filters: []` |
| `GET /api/v1/reference/localities` | Public | Supported localities with id, name, state, region, optional centroid; `Cache-Control: public, max-age=300` |
| `GET /api/v1/map/venues` | Public | Viewport bounds required; shared filter family with Search; events deferred |
| `GET /api/v1/venues/{venue_id}` | Public | Blocked detail response; `events.not_implemented: true`; `contact.not_implemented: true` when empty |
| `GET /api/v1/saved/venues` | Auth | User saved list |
| `POST /api/v1/saved/venues` | Auth | Save venue |
| `DELETE /api/v1/saved/venues/{venue_id}` | Auth | Unsave venue |
| `GET /api/v1/profile` | Auth | Profile + preferences |
| `PATCH /api/v1/profile` | Auth | Allowlisted fields only; unknown keys → `400` |
| `POST /api/v1/submissions/corrections` | Auth | Domains: profile, location, attributes, hours; moderation-bound; `201` acknowledgement |
| `POST /api/v1/submissions/new-venues` | Auth | Structured new venue suggestion; moderation-bound |
| `GET /api/v1/internal/moderation/*` | Internal | Queue, detail, decision, notes (Stage D) |

Machine-readable contract: `consumer_app/lib/api-spec/openapi.yaml`.

Human-readable companion: `backend/docs/API_ENDPOINT_OVERVIEW.md`.

---

## Frontend behaviours now locked

### Search

- Text input debounced; sends `q` only when normalized non-empty.
- Suburb picker from `/reference/localities`; sends locality `name` as `suburb`.
- Distance chips enabled only when `resolveDiscoveryOrigin` yields valid coordinates; sends `lat`, `lng`, `radius_m` together.
- Filter chips for meal specials, drink types, venue features from `/search/filters`.
- **No event filter chips** (no rendering path for `event_filters`).
- Uses generated `SearchVenuesResponse` / filter types via `@workspace/api-client-react`.

### Home

- Loads `/api/v1/home` with discovery origin coordinates when available.
- Filters out any section whose id starts with `events`.
- Uses generated `HomeFeedResponse` types in mappers.

### Map

- Viewport derived from discovery origin (`mapViewportAroundOrigin`).
- Shared filter semantics with Search where applicable.
- Event line in popup only when mapped venue has non-empty events array.

### Profile

- Default suburb picker from `/reference/localities`; PATCH sends `default_locality_id` + `default_geographic_region_id`.
- Notification toggles persist via PATCH.
- Taste/personalization sections removed; helper copy defers future controls.
- Quiet hours and display name read-only in UI.
- Profile types remain **hand-written** (`useProfile.ts`) due to optional-field normalization needs.

### Venue Detail

- Loads `/api/v1/venues/{id}`; maps to UI `Venue` via `mappers.ts`.
- Events block hidden unless `events.items` non-empty.
- Save toggle from `authenticated_actions`.
- Uses generated `VenueDetailResponse` types.

### Correction flow

- Route: `/venue/[id]/correction`.
- Domain picker: Basic info, Location, Features & amenities, Opening hours.
- Attributes domain uses `AttributeFeatureCorrectionPicker` + `/search/filters`.
- Submits via `useSubmissions` with generated correction attribute types.
- No event/drink/special correction domains in UI.

### Discovery origin

- Centralized in `DiscoveryOriginContext` + `discoveryOrigin.ts`.
- Priority: device GPS → selected Search locality → profile default locality → none.
- GPS never PATCHed to profile.

---

## Generated types/codegen status

| Area | Status |
|------|--------|
| OpenAPI spec | `consumer_app/lib/api-spec/openapi.yaml` — implemented consumer paths only; Redocly lint passes (warnings only) |
| Orval codegen | `openapi:generate` produces `@workspace/api-client-react` and `@workspace/api-zod` |
| Adopted generated types | Home, Search, Map, Saved, Venue Detail, Search filters, Correction attribute payloads |
| Runtime fetch layer | Intentionally unchanged — `publicApiRequest` / `privateApiRequest` (not generated React Query hooks) |
| Hand-written types | Profile (`useProfile.ts`), UI-normalised `Venue`/`Event`/`Special` in `mappers.ts`, legacy mockData shapes for rendering |
| Deferred | Profile generated type alignment; React Query hook migration |

Workflow documented in `consumer_app/README.local-run.md` (OpenAPI codegen section).

---

## Known remaining gaps

Real gaps only — not reopening completed MVP scope:

1. **Events** — No published event catalog, filters, or Home section; detail block stubbed.
2. **Profile taste/personalization** — No favourite drinks/features/events, distance preference, or Home personalization.
3. **Profile editing** — Display name, avatar, and quiet hours have backend PATCH support but no consumer edit UI.
4. **Correction coverage** — No drinks, events, or specials correction UI; hours domain is note/context only.
5. **Search quality** — No FTS, relevance ranking, or alias/suburb normalization (e.g. CBD → Melbourne).
6. **Pagination** — Search uses `limit` only; no offset/cursor.
7. **open_now=false** — Backend rejects; clients can only filter “open now” positively.
8. **Feature filter data dependency** — Boolean feature filters require seeded `venue_published_attribute_value` rows in dev/demo DBs.
9. **Locality scope** — Reference localities limited to areas with published venues; not exhaustive AU suburb directory.
10. **Moderation publish path** — Stage D decisions update workflow state only; approved proposals do not auto-publish to `venue_published_*` yet.
11. **README.local-run.md stale note** — “Known Deferred UI” section still mentions attribute correction UX as deferred; Stage 12 implemented it (doc drift, not product gap).
12. **OpenAPI minor warnings** — Missing 4xx on some read endpoints; unused `CorrectionAttributesProposedValues` component reference.

---

## Deferred future workstreams

### Events Manager

- Published event read model and catalog
- Event taxonomy and `event_filters` reference population
- Search `events` filter support
- Home `events_tonight` section
- Venue detail events block (`not_implemented: false`)
- Event correction UI and event interest profile preferences

### Profile Settings Manager

- Taste/personalization preference models and PATCH allowlist expansion
- Quiet hours editor UI
- Display name and avatar edit UI
- Generated Profile type alignment
- Home `for_you` section when preferences exist

### Search Quality Manager

- Full-text search / FTS indexing
- Relevance ranking and search analytics
- Suburb alias normalization (CBD, etc.)
- Pagination (offset/cursor)
- `open_now=false` support if product requires it

### Moderation/Admin Manager

- Consumer submission history/status endpoints
- Moderation decision → publish pipeline (write to `venue_published_*`)
- Owner/admin moderation UI beyond internal API
- Correction history in consumer app

### Native Release Manager

- Expo dev build vs Expo Go validation matrix
- OAuth provider end-to-end on physical devices
- App store release configuration

### Data/Locality Expansion Manager

- Broader locality coverage beyond discovery-eligible areas
- National suburb directory vs curated discovery areas decision
- Additional boolean/feature attribute definitions and seed data
- Drink/meal special taxonomy expansion beyond MVP kinds

---

## Launch-readiness notes

Manual checks before launch:

1. **Search filters efficacy** — Re-seed DB; confirm boolean feature filters return results (Beer garden + Brunswick).
2. **Radius contract** — With GPS denied and no profile suburb, distance chips disabled; no orphan `radius_m` requests.
3. **Radius contract** — With GPS or profile/suburb origin, confirm `lat` + `lng` + `radius_m` sent together.
4. **Locality pickers** — Search and Profile lists match `GET /reference/localities`; PATCH persists default locality.
5. **Events honesty** — No event chips on Search; no fake event counts on Home/cards/detail/map.
6. **`q` search** — Partial venue name and suburb name matching works; 100-char limit enforced server-side.
7. **Attribute correction** — Tri-state picker submits `attribute_definition_id` + `value_boolean`; receives `201`.
8. **OpenAPI/codegen** — Run `openapi:lint`, `openapi:generate`, `typecheck` after any contract change.
9. **Auth flows** — Saved venues and corrections require valid Supabase JWT.
10. **CORS/origins** — Backend trusted origins include Expo web port (8081) for local QA.

Backend integration test suite (representative):

```bash
cd backend
python manage.py test --keepdb --noinput tests.test_auth_boundary tests.test_saved_venues_endpoints tests.test_profile_endpoints tests.test_reference_localities tests.test_submission_endpoints tests.test_discovery_public_endpoints tests.test_home_and_venue_detail_endpoints tests.test_search_filters_endpoint tests.test_stage4_events_honesty
```

---

## Do not regress

Future agents **must preserve**:

1. **`q` scope** — Venue name + locality name only; no expanded semantic search without explicit product decision.
2. **`suburb` semantics** — Exact locality name from reference endpoint; case-insensitive; no UUID-as-suburb; no CBD alias in MVP.
3. **Radius triplet** — Never send or accept `radius_m` without `lat` and `lng`; frontend must disable distance UI when origin missing.
4. **`venue_features` keys** — Search sends `stable_key`; corrections send `attribute_definition_id`.
5. **`event_filters` guard** — Do not render event filter chips when array is empty.
6. **`events` rejection** — Backend `400 events_unavailable` until event catalog ships.
7. **Events UI honesty** — No fake event counts, “0 events”, or placeholder event sections.
8. **Locality source** — Search/Profile pickers from `/reference/localities`; no static production suburb lists.
9. **Discovery origin priority** — device GPS → Search locality → profile default → none; GPS not persisted to profile.
10. **Profile honesty** — Do not show taste/personalization controls until backend models and PATCH allowlist exist.
11. **Correction moderation** — Submissions never mutate published truth directly.
12. **Attributes correction structure** — Tri-state picker; `value_boolean` required; note-only attributes submissions not supported.
13. **Generated type discipline** — Regenerate from OpenAPI after contract changes; do not hand-edit `*/generated/` files.
14. **Fetch layer** — Do not silently migrate to generated React Query hooks unless explicitly scoped.

---

## Files changed across workstream

High-level categories (Stages 0–12):

| Category | Examples |
|----------|----------|
| Backend discovery | `backend/src/services/discovery/filters.py`, `filter_reference.py`, `q_text.py`, discovery views |
| Backend reference | `backend/src/services/reference/` (localities) |
| Backend submissions | `backend/src/apps/submissions/services/submission_intake_service.py` |
| Backend venue detail | `backend/src/apps/venues/public_read/detail.py` |
| Backend tests | `test_search_filters_endpoint.py`, `test_reference_localities.py`, `test_discovery_public_endpoints.py`, `test_stage4_events_honesty.py`, submission/profile tests |
| API docs | `backend/docs/API_ENDPOINT_OVERVIEW.md`, `REAL_MODEL_STRATEGY.MD`, `WRITE_PATHS_AND_MODERATION.md` |
| OpenAPI + codegen | `consumer_app/lib/api-spec/openapi.yaml`, `api-client-react/src/generated/`, `api-zod/src/generated/` |
| Mobile Search/Map/Home | `app/(tabs)/search.tsx`, `map.tsx`, `index.tsx`, `hooks/useSearchFilters.ts` |
| Mobile locality/origin | `hooks/useLocalities.ts`, `contexts/DiscoveryOriginContext.tsx`, `lib/discoveryOrigin.ts` |
| Mobile Profile | `app/(tabs)/profile.tsx`, `hooks/useProfile.ts` |
| Mobile corrections | `app/venue/[id]/correction.tsx`, `components/AttributeFeatureCorrectionPicker.tsx`, `hooks/useSubmissions.ts` |
| Mobile mappers/types | `lib/mappers.ts` |
| Run/verification docs | `consumer_app/README.local-run.md` |

---

## Recommended next action

**Close this workstream.** The MVP product-definition and taxonomy baseline is complete and documented.

Start a deferred workstream only when leadership prioritizes one of: Events Manager, Profile Settings Manager, Search Quality Manager, Moderation/Admin Manager, Native Release Manager, or Data/Locality Expansion Manager.

---

## Key reference files for future agents

| Document / path | Purpose |
|-----------------|---------|
| `backend/docs/API_ENDPOINT_OVERVIEW.md` | Endpoint semantics and filter contracts |
| `backend/docs/REAL_MODEL_STRATEGY.MD` | Read model strategy across surfaces |
| `backend/docs/WRITE_PATHS_AND_MODERATION.md` | Submission and moderation rules |
| `consumer_app/lib/api-spec/openapi.yaml` | Machine-readable consumer contract |
| `consumer_app/README.local-run.md` | Local run, manual verification checklists, codegen workflow |
| `consumer_app/artifacts/mobile/lib/discoveryOrigin.ts` | Discovery origin priority implementation |
| `consumer_app/artifacts/mobile/lib/mappers.ts` | API → UI normalisation |
| `backend/src/services/discovery/filters.py` | Filter validation rules |
| `backend/src/services/discovery/filter_reference.py` | Filter reference payload builder |

---

*Stage 13 closeout — Product Definition / Taxonomy workstream. No runtime changes in this stage.*
