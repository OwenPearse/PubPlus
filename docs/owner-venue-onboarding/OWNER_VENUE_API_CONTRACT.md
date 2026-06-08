# Owner venue API contract — Owner venue APIs

## Purpose

Implementation-ready contract for owner venue onboarding APIs. Backend and frontend agents implement against this document without guessing DTOs or authorization rules.

**Edit policy (normative):** `OWNER_EDIT_POLICY.md` — direct operational PATCH vs restricted proposals.

## Current stage

**Stage 8 complete.** Photos/media GET + upload-intent + metadata CRUD direct-edit endpoints shipped. Tap list (Stage 6), meal specials (Stage 5), features (Stage 7) unchanged.

## Decisions

| Topic | Decision |
|-------|----------|
| Base path | `/api/v1/owner/venues` (plural, nested under owner namespace) |
| Auth guard | `require_owner_portal_auth` on all three endpoints (AAL1 OK) |
| Venue access proof | `owner_account` → `owner_business_membership` (`active`) → `business_venue_management_relationship` (`approved`) |
| Capability grants | **Stage 4.1+:** enforce `manage_published_venue_operations` on direct PATCH; `submit_restricted_changes_for_review` on restricted POST. Phase A logged warnings only. |
| Admin on owner routes | **No.** Admins use `/api/v1/internal/*`. Dual-access users follow existing portal role rules at `/access`, not owner venue APIs. |
| Response envelope | `{ "data": ... }` for success (match `GET /api/v1/venues/{id}` and reference routes) |
| Errors | `{ "error": { "code", "message", "details?" } }` via `apps.discovery.http.error_response` |
| Operational writes | **PATCH** → published tables + `audit_event` (Stage 4.1+) |
| Restricted writes | **POST** `restricted-change-requests` → proposal staging (`profile`, `geo` targets only) |
| Legacy writes | `POST .../proposals` `section: core_details` — **superseded** for operational fields; shim until 4.3 |
| Direct publish | **Operational fields only** — immediate on PATCH success |
| Contact fields | **Not in schema** — deferred; extend `operational-profile` PATCH when migrated |

## Assumptions

- Django service role DB connection for inserts (same as `submission_intake_service`).
- `GET /api/v1/reference/localities` exists for locality picker (`backend/src/api/v1/reference/views.py`).
- Owner reads published data via server-side `published_venue_read` bundle, not Supabase client.

## Open questions

- Max age for “open draft” proposal before auto-supersede (default: none in Phase A).
- Whether moderation queue should pick up `staged` owner proposals without `in_review` (today consumer sets `submitted_at` immediately).

## Dependencies

- `STAGING_REVIEW_PUBLISH_AUDIT.md` (workflow tables)
- `owner_access_service.load_owner_access_counts` pattern for list query
- New module: `backend/src/apps/owner/services/owner_venue_service.py` (recommended)

## Next downstream use

Backend Phase A implementation ticket; `web-portal/src/shared/lib/api.ts` types; Stages 2–3.

---

## Authorization

### Table chain (confirmed)

```text
auth.users.id
  = owner_account.auth_user_id
  → owner_business_membership (membership_status = 'active')
  → business
  → business_venue_management_relationship (relationship_lifecycle = 'approved')
  → venue.id
```

Optional (recommended later):

```text
venue_capability_grant (
  business_venue_management_relationship_id,
  owner_account_id,
  capability_code IN (
    'submit_restricted_changes_for_review',
    'manage_published_venue_operations'
  ),
  grant_status = 'active'
)
```

### `assert_owner_manages_venue(auth, venue_id) -> ResolvedVenueAccess`

Returns `403` `forbidden` if chain fails. Returns `404` `not_found` if `venue` row missing (do not leak existence to non-managers).

### Auth-probe states (unchanged)

| Condition | `next_step` | Phase A venue APIs |
|-----------|-------------|-------------------|
| No owner account | `complete_owner_provisioning` | 403 / not reachable after guard |
| No membership | `owner_waiting_for_membership` | List empty; detail 403 |
| No approved venue | `owner_waiting_for_venue_access` | List empty; detail 403 |
| ≥1 approved venue | `portal_home` | List populated |

---

## Endpoint 1: `GET /api/v1/owner/venues`

**Guard:** `require_owner_portal_auth`

### Response `200`

```json
{
  "data": {
    "venues": [
      {
        "venue_id": "uuid",
        "display_name": "The Example Hotel",
        "locality_name": "Fitzroy",
        "state_code": "VIC",
        "relationship_lifecycle": "approved",
        "onboarding_status": "not_started",
        "pending_proposal_count": 0,
        "completeness_percent": 25,
        "required_basics_complete": false
      }
    ],
    "meta": {
      "total": 1,
      "default_venue_id": "uuid"
    }
  }
}
```

### `OwnerVenueListItem` (TypeScript)

```ts
type OwnerVenueListItem = {
  venue_id: string;
  display_name: string;
  locality_name: string | null;
  state_code: string | null;
  relationship_lifecycle: "approved"; // only approved rows returned
  onboarding_status:
    | "not_started"
    | "in_progress"
    | "submitted"
    | "needs_changes"
    | "complete";
  pending_proposal_count: number;
  completeness_percent: number; // 0–100, server-derived
  required_basics_complete: boolean;
};
```

### `meta.default_venue_id`

Set to sole `venue_id` when `total === 1` (frontend may auto-navigate). Omit or `null` when `total !== 1`.

### `onboarding_status` derivation (normative)

| Status | Rule |
|--------|------|
| `not_started` | No owner `core_details` proposal ever; published basics incomplete |
| `in_progress` | Open draft (`staged`) exists OR published partial basics |
| `submitted` | Latest owner proposal `in_review` or `staged` with `submitted_at` set, no rejection |
| `needs_changes` | Latest owner proposal `rejected` (or `changes_requested` when review outcome used) |
| `complete` | `required_basics_complete` and no blocking open proposal |

### Empty list

`200` with `venues: []` — not an error (owner waiting for venue uses auth-probe UI before calling this).

---

## Endpoint 2: `GET /api/v1/owner/venues/{venue_id}`

**Guard:** `require_owner_portal_auth` + venue scope

### Response `200`

```json
{
  "data": {
    "venue_id": "uuid",
    "display_name": "The Example Hotel",
    "listing": {
      "discovery_eligibility_status": "eligible",
      "operational_status": "open"
    },
    "relationship": {
      "lifecycle": "approved",
      "business_id": "uuid",
      "capabilities": ["submit_restricted_changes_for_review"]
    },
    "published": {
      "profile": {
        "display_name": "The Example Hotel",
        "slug": "the-example-hotel",
        "operational_status": "open"
      },
      "location": {
        "locality_id": "uuid",
        "locality_name": "Fitzroy",
        "state_code": "VIC",
        "address_line_1": "1 Example St",
        "address_line_2": null,
        "postal_code": "3065",
        "country_code": "AU",
        "latitude": -37.8,
        "longitude": 144.98
      },
      "descriptions": {
        "short_description": "Neighbourhood pub.",
        "long_description": null
      },
      "hours": {
        "uncertainty_level": "resolved_confident",
        "regular": [
          {
            "day_of_week": 5,
            "opens_at": "12:00",
            "closes_at": "23:00",
            "crosses_midnight": false
          }
        ],
        "exceptions": []
      },
      "contact": {
        "supported": false,
        "phone": null,
        "email": null,
        "website": null
      }
    },
    "draft": {
      "proposal_id": "uuid | null",
      "lifecycle_status": "staged | null",
      "last_saved_at": "ISO-8601 | null",
      "payload_preview": {
        "display_name": "string | null",
        "address_line_1": "string | null",
        "locality_id": "uuid | null"
      },
      "core_details_payload": {
        "display_name": "string | null",
        "address_line_1": "string | null",
        "address_line_2": "string | null",
        "postal_code": "string | null",
        "locality_id": "uuid | null",
        "country_code": "AU",
        "latitude": "number | null",
        "longitude": "number | null",
        "short_description": "string | null",
        "long_description": "string | null",
        "opening_hours": {
          "uncertainty_level": "resolved_confident | unknown | partial | weak_stale | disputed | null",
          "regular_hours_json": [],
          "exceptions_json": [],
          "notes": "string | null"
        }
      }
    },
    "pending_review": {
      "proposal_id": "uuid | null",
      "lifecycle_status": "in_review | staged | null",
      "submitted_at": "ISO-8601 | null",
      "reviewed_at": "ISO-8601 | null",
      "review_outcome": "approved | rejected | changes_requested | null"
    },
    "completeness": {
      "percent": 40,
      "required_basics_complete": false,
      "sections": [
        {
          "key": "core_details",
          "label": "Pub details",
          "status": "partial",
          "required": true,
          "available": true
        },
        {
          "key": "events",
          "label": "Events",
          "status": "deferred",
          "required": false,
          "available": false
        },
        {
          "key": "meal_specials",
          "label": "Meal specials",
          "status": "missing",
          "required": false,
          "available": false
        },
        {
          "key": "tap_list",
          "label": "Tap list",
          "status": "missing",
          "required": false,
          "available": false
        },
        {
          "key": "features",
          "label": "Features",
          "status": "missing",
          "required": false,
          "available": false
        },
        {
          "key": "photos",
          "label": "Photos",
          "status": "missing",
          "required": false,
          "available": true
        }
      ]
    },
    "sections_available": {
      "core_details": true,
      "events": false,
      "meal_specials": false,
      "tap_list": true,
      "features": true,
      "photos": true
    }
  }
}
```

### Published field sources (confirmed)

| Block | Tables / service |
|-------|------------------|
| profile | `venue_published_profile` |
| descriptions | `venue_published_descriptive_copy` (via bundle) |
| location | `venue_published_location`, `locality`, `venue_published_map_point` |
| hours | `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty` |
| contact | **Not implemented** — `ContactLinksBlock.not_implemented` in `detail.py` |

### Pending / draft sources

| Block | Tables |
|-------|--------|
| draft | Latest owner proposal `lifecycle_status IN ('staged')` + staging rows |
| draft.core_details_payload | Full staged `core_details` from `venue_proposal_staging_profile`, `_location`, `_hours` (Phase A.1) |
| pending_review | Latest owner proposal with `submitted_at IS NOT NULL` and open/recent terminal status + `proposal_review` |

When no open staged draft exists, `draft.core_details_payload` is `null`. `payload_preview` remains for backwards compatibility.

### Duplicate in-review guard (Phase A.1)

| Action | Behaviour |
|--------|-----------|
| `intent: submit` while `in_review` exists | `200` with existing proposal; message: *Your changes are already submitted for review.* No new proposal created. |
| `intent: draft` while `in_review` exists | `409` `proposal_already_in_review` — editing blocked until review outcome. |

One open submitted `core_details` proposal per owner + venue at a time.

### Errors

| Status | code |
|--------|------|
| 401 | `unauthorized` |
| 403 | `forbidden` (not manager) |
| 404 | `not_found` |

---

## Legacy Endpoint 3 (Phase A — superseded): `POST /api/v1/owner/venues/{venue_id}/proposals`

> **Superseded for operational fields (Stage 4).** Shim until Stage 4.3. Use PATCH + `restricted-change-requests` for new code.

**Guard:** `require_owner_portal_auth` + venue scope

### Request body

```json
{
  "section": "core_details",
  "intent": "draft",
  "payload": {
    "display_name": "The Example Hotel",
    "address_line_1": "1 Example St",
    "address_line_2": null,
    "postal_code": "3065",
    "locality_id": "uuid",
    "country_code": "AU",
    "latitude": null,
    "longitude": null,
    "short_description": "Neighbourhood pub.",
    "long_description": null,
    "opening_hours": {
      "uncertainty_level": "resolved_confident",
      "regular_hours_json": [
        {
          "day_of_week": 5,
          "opens_at": "12:00",
          "closes_at": "23:00",
          "crosses_midnight": false
        }
      ],
      "exceptions_json": [],
      "notes": null
    },
    "owner_confirms_management": true
  }
}
```

### TypeScript types

```ts
type OwnerVenueProposalRequest = {
  section: "core_details";
  intent: "draft" | "submit";
  payload: OwnerCoreDetailsPayload;
};

type OwnerCoreDetailsPayload = {
  display_name?: string;
  address_line_1?: string;
  address_line_2?: string | null;
  postal_code?: string;
  locality_id?: string;
  country_code?: string;
  latitude?: number | null;
  longitude?: number | null;
  short_description?: string;
  long_description?: string | null;
  opening_hours?: OwnerOpeningHoursPayload;
  owner_confirms_management?: boolean;
  // Phase A+ after schema migration:
  // phone?: string;
  // email?: string;
  // website?: string;
  // contact_person_name?: string;
  // contact_person_role?: string;
};

type OwnerOpeningHoursPayload = {
  uncertainty_level?:
    | "unknown"
    | "partial"
    | "weak_stale"
    | "disputed"
    | "resolved_confident";
  regular_hours_json?: Array<{
    day_of_week: number; // 0=Sun … 6=Sat
    opens_at: string; // HH:MM
    closes_at: string;
    crosses_midnight?: boolean;
    sort_order?: number;
  }>;
  exceptions_json?: Array<Record<string, unknown>>; // defer strict shape in Phase A
  notes?: string | null;
};
```

### Response `201`

```json
{
  "data": {
    "proposal_id": "uuid",
    "venue_id": "uuid",
    "section": "core_details",
    "intent": "draft",
    "lifecycle_status": "staged",
    "submitted_at": null,
    "message": "Draft saved. You can continue editing or submit for review when ready."
  }
}
```

On `intent: "submit"`, `lifecycle_status` is `in_review`, `submitted_at` set, message references admin review.

Re-submit while an owner `core_details` proposal is already `in_review` returns `200` with the existing proposal (no duplicate). Draft saves while `in_review` returns `409` `proposal_already_in_review`.

### Internal mapping (normative)

| Payload field | Staging table / column |
|---------------|------------------------|
| `display_name`, descriptions | `venue_proposal_staging_profile` |
| address, locality, lat/lng | `venue_proposal_staging_location` |
| `opening_hours` | `venue_proposal_staging_hours` |
| — | `venue_change_proposal.actor_type = 'owner'` |
| — | `venue_change_proposal.channel = 'owner_portal'` |
| — | `venue_proposal_target`: `profile`, `geo`, `hours` |

**Do not** set `discovery_eligibility_status` / `operational_status` from owner payload in Phase A (admin/import only).

---

## Field classification (Stage 4+)

| Field | Classification | Write path | Storage |
|-------|----------------|------------|---------|
| `short_description`, `long_description` | **Direct edit** | PATCH `operational-profile` | `venue_published_descriptive_copy` |
| `opening_hours` | **Direct edit** | PATCH `hours` | `venue_hours_*` |
| `phone`, `email`, `website` | **Direct edit** (when schema exists) | PATCH `operational-profile` | `venue_published_contact` *(planned)* |
| `display_name` | **Restricted** | POST `restricted-change-requests` | staging → `venue_published_profile` |
| `address_line_*`, `postal_code`, `country_code` | **Restricted** | POST restricted | staging → `venue_published_location` |
| `locality_id`, `latitude`, `longitude` | **Restricted** | POST restricted | staging → location / map_point |
| `owner_confirms_management` | Restricted submit gate | First restricted request only | `audit_event` optional |
| `contact_person_name`, `contact_person_role` | Deferred | — | No table |
| `google_place_id` | Forbidden | — | Internal only |
| `discovery_eligibility_status`, `operational_status` | Admin only | — | `venue_published_profile` |

### Superseded (Phase A)

> All fields above were `Review required` via bundled `POST .../proposals` — see legacy Endpoint 3 below.

---

## Validation rules (core_details)

| Field | Rules |
|-------|--------|
| `display_name` | Required on `intent=submit`. Trim. Length 2–120. |
| `address_line_1` | Required on submit. Trim. Length 3–200. |
| `address_line_2` | Optional. Max 200. |
| `postal_code` | Optional. If present: trim, max 12, alphanumeric + space/hyphen. |
| `locality_id` | Required on submit. Valid UUID; must exist in `public.locality`. |
| `country_code` | Optional; default `AU` if omitted. Two-letter ISO. |
| `latitude` / `longitude` | Optional pair; if one set, both required; lat −90..90, lng −180..180. |
| `short_description` | Required on submit. Trim. Max **500** chars. |
| `long_description` | Optional. Max **2000** chars. |
| `opening_hours` | On submit: at least one of: non-empty `regular_hours_json`, non-empty `exceptions_json`, `uncertainty_level` not `resolved_confident` with explicit unknown path, or `notes` min 10 chars. Each regular row: `day_of_week` 0–6, `opens_at`/`closes_at` match `^([01]\d|2[0-3]):[0-5]\d$`. |
| `owner_confirms_management` | Required `true` on first ever `intent=submit` for venue+owner; optional `true` on drafts. |
| `phone` | Phase A+: trim; length 8–20; allow `+`, digits, spaces, hyphens, parentheses. |
| `email` | Phase A+: RFC5322 pragmatic regex; max 254. |
| `website` | Phase A+: http/https URL; max 500; strip trailing spaces. |

Validation errors: `400` `validation_error` with `details: { field: ["message"] }` (match submissions API).

---

## Frontend routing contract (Stages 2–4.2)

| Route | When |
|-------|------|
| `/owner` | Hub; if `meta.default_venue_id` from list, optional redirect to `/owner/venues/{id}` |
| `/owner/venues/:venueId` | Venue hub (checklist) |
| `/owner/venues/:venueId/basics` | Step 1 — operational + restricted zones |

**Do not** add dense sidebar nav.

### Required API calls (Stage 4.2)

- `ownerAuthProbe()` (existing)
- `GET /api/v1/owner/venues`
- `GET /api/v1/owner/venues/{venue_id}`
- `PATCH /api/v1/owner/venues/{venue_id}/operational-profile` — Save changes (descriptions)
- `PATCH /api/v1/owner/venues/{venue_id}/hours` — Save changes (hours)
- `POST /api/v1/owner/venues/{venue_id}/restricted-change-requests` — Request change
- `GET /api/v1/reference/localities` — restricted zone picker

### Copy tone (Stage 4.2)

- Operational saved: “Saved. These updates are now reflected on your listing.”
- Restricted requested: “Change request submitted. We'll review it before updating your listing.”
- Restricted pending: banner on restricted zone only
- No venue access: `NoVenueAccessState` + support link if `VITE_PORTAL_SUPPORT_URL` set

### Superseded copy (Phase A)

> “Your changes have been submitted and will be reviewed before they appear on your public listing.” — applies to **restricted** requests only, not operational Save.

---

## Tests to add (implementation stages)

| File | Coverage |
|------|----------|
| `backend/tests/test_owner_venue_endpoints.py` | list, detail, legacy proposal, PATCH direct edit, restricted POST, 403 scope |
| `backend/tests/test_owner_endpoints.py` | keep auth-probe |
| `web-portal/src/shared/lib/api.owner-venues.test.ts` | client parsing + PATCH/restricted methods |
| Stage 2–4.2 Vitest | hub + split basics form |

---

## Stage 4.1 — Endpoint 4: `PATCH /api/v1/owner/venues/{venue_id}/operational-profile`

**Guard:** `require_owner_portal_auth` + venue scope + `manage_published_venue_operations`

### Request body

```json
{
  "short_description": "Neighbourhood pub.",
  "long_description": "Optional longer copy."
}
```

Partial PATCH allowed — omitted keys unchanged.

### Response `200`

```json
{
  "data": {
    "venue_id": "uuid",
    "updated": {
      "short_description": "Neighbourhood pub.",
      "long_description": "Optional longer copy."
    },
    "message": "Changes saved."
  }
}
```

### Side effects

1. Upsert `venue_published_descriptive_copy`
2. Insert `audit_event` (`action = 'owner_direct_edit'`, `field_family = 'descriptions'`)
3. Optional: `venue_published_row_history` snapshot of prior row (Stage 4.1b)

### Validation

| Field | Rules |
|-------|--------|
| `short_description` | If present: trim; max **500** chars; may be required for completeness elsewhere but not enforced on every PATCH |
| `long_description` | If present: trim; max **2000** chars; null to clear |

### Errors

| Status | code |
|--------|------|
| 400 | `validation_error` |
| 403 | `forbidden` (not manager or missing capability) |
| 404 | `not_found` |

---

## Stage 4.1 — Endpoint 5: `PATCH /api/v1/owner/venues/{venue_id}/hours`

**Guard:** same as Endpoint 4

### Request body

```json
{
  "uncertainty_level": "resolved_confident",
  "regular_hours_json": [
    {
      "day_of_week": 5,
      "opens_at": "12:00",
      "closes_at": "23:00",
      "crosses_midnight": false
    }
  ],
  "exceptions_json": [],
  "notes": null
}
```

Reuses `OwnerOpeningHoursPayload` shape from Phase A.

### Response `200`

```json
{
  "data": {
    "venue_id": "uuid",
    "hours": {
      "uncertainty_level": "resolved_confident",
      "regular": [],
      "exceptions": [],
      "notes": null
    },
    "message": "Opening hours saved."
  }
}
```

### Side effects

1. Transactional replace: delete existing `venue_hours_regular` / `_exception` rows for venue; insert new; upsert `venue_hours_uncertainty`
2. `audit_event` with `field_family = 'hours'`
3. Optional row history snapshots

### Validation

Same rules as Phase A `_validate_opening_hours` with `submit=true` (hours must be materially present).

---

## Stage 5 — Meal specials CRUD

**Guard:** `require_owner_portal_auth` + venue scope + `manage_published_venue_operations`

### GET `/api/v1/owner/venues/{venue_id}/meal-specials`

```json
{
  "data": {
    "venue_id": "uuid",
    "meal_specials": [
      {
        "id": "uuid",
        "title": "Thursday Parma Night",
        "description": "$20 parmas every Thursday.",
        "days_available": [4],
        "start_time": "17:00",
        "end_time": "21:00",
        "price_text": "$20",
        "conditions": "Dine-in only",
        "active": true,
        "sort_order": 0
      }
    ]
  }
}
```

### POST / PATCH body (`OwnerMealSpecialInput`)

```ts
type OwnerMealSpecialInput = {
  title: string;
  description?: string | null;
  days_available?: number[];
  start_time?: string | null;
  end_time?: string | null;
  price_text?: string | null;
  conditions?: string | null;
  active?: boolean;
  sort_order?: number;
};
```

### Validation

| Field | Rules |
|-------|--------|
| `title` | Required on POST; trim; 2–120 chars |
| `description` | Max 500 |
| `days_available` | Integers 0–6; empty → all days |
| `start_time` / `end_time` | HH:MM pair or both omitted |
| `price_text` | Max 80 |
| `conditions` | Max 300 |
| `sort_order` | 0–999 |
| Unknown keys | Rejected |

### DELETE

Soft deactivate: `catalog_record_status = retired` (same as PATCH `active: false`).

### Side effects

1. Write `venue_published_structured_special` (`structured_kind = meal_special`, `schedule_class = recurring`) + marketing copy + recurring pattern + validity + discovery eligibility
2. `audit_event` (`action = owner_direct_edit`, `field_family = meal_specials`)
3. No proposal/staging rows

### Schema mapping

| API | Column / table |
|-----|----------------|
| `title` | `short_label` |
| `description` | `marketing_copy.body` |
| `price_text` | `marketing_copy.headline` |
| `conditions` | `marketing_copy.terms_and_conditions` |
| `days_available` | `recurring_pattern.recurring_days_of_week` |
| `start_time` / `end_time` | `recurring_pattern.window_*_time_local` |
| `active` | `catalog_record_status` |
| `sort_order` | `discovery_eligibility.tier_notes` (`owner_sort_order=N`) |

---

## Stage 6 — Tap list CRUD

**Guard:** `require_owner_portal_auth` + venue scope + `manage_published_venue_operations`

### GET `/api/v1/owner/venues/{venue_id}/tap-list`

```json
{
  "data": {
    "venue_id": "uuid",
    "tap_list": [
      {
        "id": "uuid",
        "drink_name": "Stone & Wood Pacific Ale",
        "brewery_or_brand": "Stone & Wood",
        "drink_type": "Pale ale",
        "abv": "4.4%",
        "price_text": "$12 schooner",
        "availability": "permanent",
        "notes": null,
        "active": true,
        "sort_order": 0
      }
    ]
  }
}
```

### POST / PATCH body (`OwnerTapListItemInput`)

```ts
type OwnerTapListItemInput = {
  drink_name: string;
  brewery_or_brand?: string | null;
  drink_type?: string | null;
  abv?: string | null;
  price_text?: string | null;
  availability?: "permanent" | "rotating" | "seasonal" | "limited" | null;
  notes?: string | null;
  active?: boolean;
  sort_order?: number;
};
```

### Validation

| Field | Rules |
|-------|--------|
| `drink_name` | Required on POST; trim; 2–120 chars; no HTML/script markup |
| `brewery_or_brand` | Max 120 |
| `drink_type` | Max 80 (free text) |
| `abv` | Max 20 |
| `price_text` | Max 80 |
| `notes` | Max 300 |
| `availability` | Enum if supplied |
| `sort_order` | 0–999 |
| Unknown keys | Rejected |

### DELETE

Soft deactivate: `catalog_record_status = retired`.

### Side effects

1. Write `venue_published_tap_offering` (+ validity/eligibility satellites)
2. `audit_event` (`action = owner_direct_edit`, `field_family = tap_list`)
3. No proposal/staging rows

### Schema mapping

| API | Column / table |
|-----|----------------|
| `drink_name` | `unstructured_line_label` |
| `availability` | `is_rotating`, `is_limited_run` (+ meta in tier_notes) |
| `active` | `catalog_record_status` |
| `sort_order` | `sort_order` + `tier_notes` (`owner_sort_order=N`) |
| `brewery_or_brand`, `drink_type`, `abv`, `price_text`, `notes` | `discovery_eligibility.tier_notes` (`owner_meta={json}`) |
| Owner create | `beverage_product_id = NULL` (free-text display row) |

---

## Stage 7 — Endpoint 7: `GET/PATCH /api/v1/owner/venues/{venue_id}/features`

**Guard:** `require_owner_portal_auth` + venue scope + `manage_published_venue_operations`

### GET response

```json
{
  "data": {
    "venue_id": "uuid",
    "features": [
      {
        "attribute_definition_id": "uuid",
        "stable_key": "beer_garden",
        "label": "Beer garden",
        "value_shape": "boolean",
        "group": "spaces",
        "value": true
      }
    ]
  }
}
```

Only MVP boolean definitions from `dev_seed_mvp_filter_taxonomy.sql` are exposed. Missing published rows return `value: false`.

### PATCH request

```json
{
  "features": [
    { "attribute_definition_id": "uuid", "value_boolean": true },
    { "attribute_definition_id": "uuid", "value_boolean": false }
  ]
}
```

### PATCH response

Same shape as GET plus `message`: “Features saved. These updates are now reflected on your listing.”

### Side effects

1. Upsert `venue_published_attribute_value` (`value_boolean`) — no proposal/staging rows
2. `audit_event` with `action = owner_direct_edit`, `field_family = attributes`

### Validation

- Reject unknown or non-allowlisted `attribute_definition_id`
- Reject non-boolean definitions
- At least one feature object required

---

## Stage 4.2 — Endpoint 6: `POST /api/v1/owner/venues/{venue_id}/restricted-change-requests`

**Guard:** `require_owner_portal_auth` + venue scope + `submit_restricted_changes_for_review`

### Request body

```json
{
  "section": "identity_location",
  "payload": {
    "display_name": "The Example Hotel",
    "address_line_1": "1 Example St",
    "address_line_2": null,
    "postal_code": "3065",
    "locality_id": "uuid",
    "country_code": "AU",
    "latitude": null,
    "longitude": null
  }
}
```

**Must not** include `short_description`, `long_description`, `opening_hours`, contact fields, or `google_place_id` — return `400` if present.

At least one restricted field must be supplied and changed from published values.

### Response `201` (new proposal) or `200` (duplicate in-review)

```json
{
  "data": {
    "proposal_id": "uuid",
    "venue_id": "uuid",
    "section": "identity_location",
    "lifecycle_status": "in_review",
    "submitted_at": "ISO-8601",
    "message": "Change request submitted. We'll review it before updating your listing."
  }
}
```

Duplicate in-review (`200`): same shape; `message`: “Your change request is already waiting for review.”

### Internal mapping

| Payload field | Staging |
|---------------|---------|
| `display_name` | `venue_proposal_staging_profile.proposed_display_name` only |
| address, locality, lat/lng | `venue_proposal_staging_location` |
| — | `venue_proposal_target`: `profile`, `geo` (no `hours`) |

Duplicate in-review guard: same semantics as Phase A.1 (one open restricted proposal per owner+venue).

---

## Stage 4.1 — Detail GET additions

Extend `GET /api/v1/owner/venues/{venue_id}` with:

```json
{
  "edit_policy": {
    "operational_direct_edit": true,
    "restricted_proposal_required": true,
    "capabilities_required": {
      "direct_edit": "manage_published_venue_operations",
      "restricted_request": "submit_restricted_changes_for_review"
    }
  },
  "restricted_draft": {
    "proposal_id": "uuid | null",
    "lifecycle_status": "staged | null",
    "payload": { }
  },
  "restricted_pending_review": {
    "proposal_id": "uuid | null",
    "lifecycle_status": "in_review | null",
    "submitted_at": "ISO-8601 | null",
    "review_outcome": null
  }
}
```

Deprecate over time: `draft.core_details_payload` operational fields; keep for shim compatibility through 4.2.

Adjust `onboarding_status`: `submitted` when `restricted_pending_review` open; operational PATCH does not set `submitted`.

---

## Stage 8 — Venue photos / media

**Guard:** `require_owner_portal_auth` + venue scope + `manage_published_venue_operations`

### GET `/api/v1/owner/venues/{venue_id}/media`

```json
{
  "data": {
    "venue_id": "uuid",
    "media": [
      {
        "id": "uuid",
        "purpose": "profile",
        "media_kind": "image",
        "url": "https://{project}.supabase.co/storage/v1/object/public/venue-media/venues/{venue_id}/profile/{id}.jpg",
        "storage_bucket": "venue-media",
        "storage_path": "venues/{venue_id}/profile/{id}.jpg",
        "caption": null,
        "alt_text": "Front bar",
        "sort_order": 0,
        "active": true
      }
    ]
  }
}
```

Public bucket → `url` is a stable public Storage URL (no signed read URL in MVP).

### POST `/api/v1/owner/venues/{venue_id}/media/upload-intent`

Request: `purpose`, `file_name`, `content_type` (jpeg/png/webp), `file_size_bytes` (max 5MB).

Response: `media_id`, `storage_bucket`, `storage_path`, `signed_upload_url`, `expires_in_seconds`.

Backend stores `owner_venue_media_upload_intent` row; path must match `venues/{venue_id}/{purpose}/{media_id}.{ext}`.

### POST `/api/v1/owner/venues/{venue_id}/media`

Commit metadata after Storage upload. Verifies intent, path scope, and object existence (HEAD via service role).

Profile purpose: retires other active profile rows for the venue.

### PATCH / DELETE `/api/v1/owner/venues/{venue_id}/media/{media_id}`

PATCH: `caption`, `alt_text`, `sort_order`, `purpose`, `active`.

DELETE: soft retire (`catalog_record_status = retired`).

### Side effects

1. Write `venue_published_media`
2. `audit_event` (`action = owner_direct_edit`, `field_family = media`, `entity_table = venue_published_media`)
3. Consumer listing reads via `published_venue_read` + `venue_media`

### Out of scope

Menu PDFs, event posters, videos, moderation queue, arbitrary Storage paths.

---

## Claim API (out of scope)

**Recommendation D:** MVP uses admin-assigned venues; waiting state only. Claim request API deferred to separate workstream (`venue_claim_request` exists in DB only).
