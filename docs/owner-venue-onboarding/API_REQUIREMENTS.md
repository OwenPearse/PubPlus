# API requirements — Owner venue onboarding

## Purpose

Specify backend endpoints for owner venue onboarding. **Phase A contract is frozen in `OWNER_VENUE_API_CONTRACT.md`** — this file is the requirements index.

## Current stage

**Stage 1 complete.** Phase A ready for implementation. Phase B unchanged (optional sections).

## Decisions

- Phase A paths confirmed: `/api/v1/owner/venues`, `/api/v1/owner/venues/{venue_id}`, `/api/v1/owner/venues/{venue_id}/proposals`
- `require_owner_portal_auth` on all Phase A routes
- Writes use bundled `core_details` proposal (not three separate consumer-style POSTs)
- `intent`: `draft` | `submit` controls `lifecycle_status` and `submitted_at`
- Response envelope: `{ "data": ... }`
- Claim API: **deferred** (not Phase A)

## Assumptions

- New service module `owner_venue_service` (recommended) beside `owner_access_service`
- Reuse validation patterns from `submission_intake_service.py`

## Open questions

- See `OWNER_VENUE_API_CONTRACT.md` § Open questions

## Dependencies

- `OWNER_VENUE_API_CONTRACT.md` (normative DTOs)
- `STAGING_REVIEW_PUBLISH_AUDIT.md` (workflow)
- Existing: `POST/GET /api/v1/owner/provision`, `auth-probe`

## Next downstream use

Backend implementation; `web-portal/src/shared/lib/api.ts` owner venue client.

---

## Existing (unchanged)

| Method | Path |
|--------|------|
| POST | `/api/v1/owner/provision` |
| GET | `/api/v1/owner/auth-probe` |

## Phase A (implement per contract)

| Method | Path | Summary |
|--------|------|---------|
| GET | `/api/v1/owner/venues` | List manageable venues + onboarding meta |
| GET | `/api/v1/owner/venues/{venue_id}` | Published snapshot + draft/pending + completeness |
| POST | `/api/v1/owner/venues/{venue_id}/proposals` | `section: core_details`, `intent`, `payload` |

**Normative detail:** `OWNER_VENUE_API_CONTRACT.md`

## Reference (frontend picker)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/reference/localities` | Existing; `Cache-Control: public, max-age=300` |

## Phase B (unchanged — not Stage 1)

- Extend proposals for specials/taps/attributes
- `GET` attribute reference for feature step

## Internal (admin only)

| Path | Use |
|------|-----|
| `/api/v1/internal/moderation/*` | Review owner proposals |
| `/api/v1/submissions/corrections` | Pattern reference only |

## Guards

| Guard | Routes |
|-------|--------|
| `require_owner_portal_auth` | All Phase A venue routes |
| Venue scope helper | GET/POST by `venue_id` |

## Tests (when implemented)

- `backend/tests/test_owner_venue_endpoints.py` (new)
- Extend `test_owner_endpoints.py` if shared helpers
- Mirror `test_submission_endpoints.py` — no published mutation on POST
