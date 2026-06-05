# API requirements — Owner venue onboarding

## Purpose

Specify backend endpoints for owner venue onboarding. **Normative edit policy:** `OWNER_EDIT_POLICY.md`. **DTO detail:** `OWNER_VENUE_API_CONTRACT.md`.

## Current stage

**Stage 4.1 complete.** Direct PATCH endpoints implemented. Restricted `POST restricted-change-requests` planned for 4.2.

## Decisions

- **Read APIs unchanged:** `GET /api/v1/owner/venues`, `GET /api/v1/owner/venues/{venue_id}`
- **Direct writes (new):** `PATCH` operational endpoints write published tables after capability check
- **Restricted writes:** `POST .../restricted-change-requests` (proposal/staging only for identity/location)
- **`POST .../proposals`:** Deprecated for operational fields; compatibility shim until 4.3
- `require_owner_portal_auth` on all owner venue routes
- Response envelope: `{ "data": ... }`
- Claim API: **deferred** (admin-assigned venues for MVP)

### Superseded (pre–Stage 4)

> ~~Writes use bundled `core_details` proposal for all fields~~ — operational fields move to PATCH; proposals restricted-only.

## Assumptions

- Service module `owner_venue_service` extended with direct-write helpers + audit
- Django service role for published table mutations (RLS bypass)
- Reuse validation patterns from existing `_validate_core_payload` where fields overlap

## Open questions

- Exact deprecation timeline for `POST .../proposals` shim (default: remove Stage 4.3)
- Whether `PUT` or `PATCH` for replace-set endpoints (specials, taps) — see contract

## Dependencies

- `OWNER_EDIT_POLICY.md`
- `OWNER_VENUE_API_CONTRACT.md`
- `STAGING_REVIEW_PUBLISH_AUDIT.md`
- Existing: `POST/GET /api/v1/owner/provision`, `auth-probe`

## Next downstream use

Stage 4.1 backend tickets; `web-portal/src/shared/lib/api.ts` client additions in 4.2.

---

## Existing (unchanged)

| Method | Path |
|--------|------|
| POST | `/api/v1/owner/provision` |
| GET | `/api/v1/owner/auth-probe` |

## Read (keep — adjust meta semantics Stage 4.1)

| Method | Path | Summary |
|--------|------|---------|
| GET | `/api/v1/owner/venues` | List manageable venues; `pending_proposal_count` = **restricted** proposals only |
| GET | `/api/v1/owner/venues/{venue_id}` | Published snapshot + restricted draft/pending + `edit_policy` block |

## Direct edit (Stage 4.1 — implemented)

| Method | Path | Summary | Stage |
|--------|------|---------|-------|
| PATCH | `/api/v1/owner/venues/{venue_id}/operational-profile` | Descriptions (+ contact when schema exists) | ✅ 4.1 |
| PATCH | `/api/v1/owner/venues/{venue_id}/hours` | Opening hours bundle | ✅ 4.1 |
| PATCH | `/api/v1/owner/venues/{venue_id}/attributes` | Feature toggles | 7 |
| PUT | `/api/v1/owner/venues/{venue_id}/specials` | Meal specials replace-set | 5 |
| PUT | `/api/v1/owner/venues/{venue_id}/tap-list` | Tap offerings replace-set | 6 |

**Guard:** `manage_published_venue_operations` required (enforce in 4.1).

## Restricted change requests (Stage 4.1–4.2)

| Method | Path | Summary |
|--------|------|---------|
| POST | `/api/v1/owner/venues/{venue_id}/restricted-change-requests` | Identity/location proposal → `in_review` |
| POST | `/api/v1/owner/venues/{venue_id}/restricted-change-requests` with `intent: draft` | Staged restricted draft (optional) |

**Guard:** `submit_restricted_changes_for_review` required.

**Payload:** `display_name`, address fields, `locality_id`, `latitude`/`longitude` only.

## Legacy (deprecate)

| Method | Path | Disposition |
|--------|------|-------------|
| POST | `/api/v1/owner/venues/{venue_id}/proposals` | Shim: accept `section: core_details` but reject operational-only saves after 4.2; redirect authors to PATCH |

## Reference (frontend picker)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/reference/localities` | Locality picker for restricted address zone |

## Internal (admin only)

| Path | Use |
|------|-----|
| `/api/v1/internal/moderation/*` | Review **restricted** owner proposals |
| Publish worker (TBD) | Apply approved restricted staging → published profile/geo |

## Guards

| Guard | Routes |
|-------|--------|
| `require_owner_portal_auth` | All owner venue routes |
| `assert_owner_manages_venue` | All routes with `venue_id` |
| `manage_published_venue_operations` | Direct PATCH/PUT routes |
| `submit_restricted_changes_for_review` | Restricted POST routes |

## Tests (when implemented)

- `backend/tests/test_owner_venue_endpoints.py` — extend for PATCH + restricted POST
- `web-portal/src/shared/lib/api.owner-venues.test.ts` — new client methods
- Assert published tables mutate on direct PATCH; proposals do **not** mutate published on restricted staging
