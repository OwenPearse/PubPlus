# Owner venue API contract — Phase A (frozen)

## Purpose

Implementation-ready contract for Phase A owner venue onboarding APIs. Backend and frontend agents implement against this document without guessing DTOs or authorization rules.

## Current stage

**Stage 1 — frozen.** No implementation in Stage 1. Implement in Backend Phase A + Stages 2–3.

## Decisions

| Topic | Decision |
|-------|----------|
| Base path | `/api/v1/owner/venues` (plural, nested under owner namespace) |
| Auth guard | `require_owner_portal_auth` on all three endpoints (AAL1 OK) |
| Venue access proof | `owner_account` → `owner_business_membership` (`active`) → `business_venue_management_relationship` (`approved`) |
| Capability grants | **Phase A:** relationship check sufficient; log warning if no `submit_restricted_changes_for_review` grant. **Phase A+:** enforce grant when present in seed/prod. |
| Admin on owner routes | **No.** Admins use `/api/v1/internal/*`. Dual-access users follow existing portal role rules at `/access`, not owner venue APIs. |
| Response envelope | `{ "data": ... }` for success (match `GET /api/v1/venues/{id}` and reference routes) |
| Errors | `{ "error": { "code", "message", "details?" } }` via `apps.discovery.http.error_response` |
| Writes | One **core_details** bundle per request → one `venue_change_proposal` with targets `profile`, `geo`, `hours` |
| Draft vs submit | `intent: "draft"` → `lifecycle_status = staged`; `intent: "submit"` → `submitted_at = now()`, `lifecycle_status = in_review` |
| Upsert | Reuse open owner proposal for same venue (`actor_type=owner`, `channel=owner_portal`, terminal status not in closed set) when `intent=draft`; new proposal on `submit` if prior terminal |
| Direct publish | **None** in Phase A |
| Contact fields | **Not in Phase A payload** — schema deferred (see `DATA_CAPTURE_MODEL.md`) |

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
          "status": "deferred",
          "required": false,
          "available": false
        }
      ]
    },
    "sections_available": {
      "core_details": true,
      "events": false,
      "meal_specials": false,
      "tap_list": false,
      "features": false,
      "photos": false
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
| pending_review | Latest owner proposal with `submitted_at IS NOT NULL` and open/recent terminal status + `proposal_review` |

### Errors

| Status | code |
|--------|------|
| 401 | `unauthorized` |
| 403 | `forbidden` (not manager) |
| 404 | `not_found` |

---

## Endpoint 3: `POST /api/v1/owner/venues/{venue_id}/proposals`

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

## Field classification (core pub info)

| Field | Phase A | Classification | Storage today |
|-------|---------|----------------|---------------|
| `display_name` | ✅ | Review required | `venue_proposal_staging_profile` |
| `address_line_1`, `address_line_2`, `postal_code` | ✅ | Review required | `venue_proposal_staging_location` |
| `locality_id` | ✅ | Review required (canonical FK) | staging location |
| `country_code`, `latitude`, `longitude` | ✅ optional | Review required | staging location |
| `short_description`, `long_description` | ✅ | Review required | staging profile |
| `opening_hours` | ✅ | Review required | `venue_proposal_staging_hours` |
| `owner_confirms_management` | ✅ submit only | Validation gate | Not persisted (Phase A); optional `audit_event` on submit |
| `phone`, `email`, `website` | ❌ | Deferred — schema | See `DATA_CAPTURE_MODEL.md` § Contact |
| `contact_person_name`, `contact_person_role` | ❌ | Deferred | No table |
| `google_place_id` | ❌ | Forbidden | Internal only |

**Direct publish candidates (Phase A):** none.

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

## Frontend routing contract (Stages 2–3)

| Route | When |
|-------|------|
| `/owner` | Hub; if `meta.default_venue_id` from list, optional redirect to `/owner/venues/{id}` |
| `/owner/venues/:venueId` | Venue hub (checklist) |
| `/owner/venues/:venueId/basics` | Step 1 form |

**Do not** add dense sidebar nav.

### Stage 2 required calls

- `ownerAuthProbe()` (existing)
- `GET /api/v1/owner/venues`

### Stage 3 required calls

- `GET /api/v1/owner/venues/{venue_id}`
- `POST /api/v1/owner/venues/{venue_id}/proposals`
- `GET /api/v1/reference/localities` (picker)

### Copy tone

- Pending: “Your changes have been submitted and will be reviewed before they appear on your public listing.”
- Draft saved: “Saved. You can come back anytime to finish or submit.”
- No venue access: keep existing `NoVenueAccessState` copy; add support link if `VITE_PORTAL_SUPPORT_URL` set.

---

## Tests to add (implementation stages)

| File | Coverage |
|------|----------|
| `backend/tests/test_owner_venue_endpoints.py` (new) | list, detail, proposal, 403 scope |
| `backend/tests/test_owner_endpoints.py` | keep auth-probe |
| `web-portal/src/shared/lib/api.owner-venues.test.ts` (new) | client parsing |
| Stage 2–3 Vitest | hub + form |

---

## Claim API (out of Phase A)

**Recommendation D:** MVP uses admin-assigned venues; waiting state only. Claim request API deferred to separate workstream (`venue_claim_request` exists in DB only).
