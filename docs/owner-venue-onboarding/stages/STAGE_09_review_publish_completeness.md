# Stage 9 — Review, completeness & hub polish

## Purpose

Polish the owner venue hub into a guided onboarding review page with server-derived completeness, section statuses, and recommended next actions.

## Current stage

**Stage 9 complete.** Hub shows weighted completion percent, checklist rows for all implemented sections, deferred events/menus, and restricted pending banner.

## Decisions

- **Completeness is server-derived** from published truth (not client-only scoring).
- **No separate review route** — review stays inside the venue hub (`/owner/venues/:venueId`).
- **No public preview** — deferred until a stable consumer listing URL exists.
- **Events and menus** remain `deferred` with “Coming later — you can skip this for now.”

## Completeness weights

| Section | Weight | Required? |
|---------|-------:|-----------|
| Pub details / hours | 30 | Yes |
| Features | 15 | Recommended |
| Meal specials | 15 | Recommended |
| Tap list / drinks | 15 | Recommended |
| Photos | 20 | Recommended |
| Restricted identity settled (no open `in_review` request) | 5 | Conditional |

Total caps at **100**.

Partial pub-details credit: up to 30 points proportional to identity + description + hours sub-checks.

## Section status rules

| Status | Meaning |
|--------|---------|
| `missing` | No published content for section |
| `partial` | Pub details started but required basics incomplete |
| `complete` | Section meets completion rule |
| `pending_review` | Reserved; restricted pending shown via hub banner + `restricted_pending_review` flag |
| `deferred` | Not implemented (events, menus) |

### Pub details

Complete when published has:

- `display_name` + `address_line_1` + `locality_id`
- `short_description`
- hours: regular row OR non-confident uncertainty OR hours notes (≥10 chars)

Restricted name/address `in_review` does **not** mark pub details incomplete if operational fields are saved.

### Features

Complete when at least one MVP boolean feature is `true` in `venue_published_attribute_value`.

### Meal specials

Complete when at least one active `venue_published_structured_special` (`meal_special` kind).

### Tap list

Complete when at least one active `venue_published_tap_offering`.

### Photos

Complete when at least one active `venue_published_media` (profile or gallery). Retired rows do not count.

### Events / menus

Always `deferred`, `available: false`.

## Recommended next action (frontend)

Pick the first implemented section that is not `complete` or `deferred`:

1. Pub details
2. Features
3. Meal specials
4. Tap list
5. Photos

If all implemented sections are `complete`:

```text
Your listing is looking good.
You can keep updating it anytime.
```

## API additions

`GET /api/v1/owner/venues` and `GET /api/v1/owner/venues/{venue_id}`:

- `completeness.percent` — weighted 0–100
- `completeness.sections[]` — ordered checklist with `status`, `available`
- `completeness.restricted_pending_review` — boolean (detail only)
- `sections_available.menus` — `false`

## Frontend scope

- `OwnerVenueHub.tsx` — progress card, next action card, status badges, checklist copy
- `ownerVenueUi.ts` — `recommendedNextAction`, `sectionStatusLabel`, hub copy constants

## Tests

- `backend/tests/test_owner_venue_endpoints.py` — completeness sections, weights, inactive rows, restricted pending, sparse venue
- `web-portal/src/owner/pages/OwnerVenueHub.test.tsx` — hub rendering
- `web-portal/src/shared/lib/api.owner-venues.test.ts` — DTO parsing

## Acceptance

- [x] Hub shows meaningful completion percentage
- [x] Active rows: Pub details, Features, Meal specials, Tap list, Photos
- [x] Events/menus deferred
- [x] Recommended next action
- [x] Restricted pending banner
- [x] Inactive/retired records excluded
- [x] Sparse approve-new venues tolerated

## Out of scope

Events, menus, contact schema, billing, analytics, public preview, image moderation.
