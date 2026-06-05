# Agent rules — Owner venue onboarding workstream

## Purpose

Rules for downstream Cursor agents implementing onboarding/profile builder.

## Current stage

**Stage 4+.** Normative edit policy: `OWNER_EDIT_POLICY.md`. Normative API DTOs: `OWNER_VENUE_API_CONTRACT.md`.

## Decisions

- **Implementer, not replanner** — follow active stage docs and `OWNER_EDIT_POLICY.md`.
- **No full owner dashboard** — guided hub + step pages only.
- **Direct operational edits** — verified owners PATCH published operational tables via backend (service role); **no per-field admin review**.
- **Restricted proposals** — identity/location only; existing staging tables; admin moderation + publish worker.
- **No self-approval** — venue claims and relationships remain admin-mediated.

### Superseded (pre–Stage 4)

> ~~Proposal workflow — no direct published-truth writes from owner UI~~ — operational fields use direct PATCH after capability check.

## Assumptions

- Read before coding: `OWNER_EDIT_POLICY.md`, `API_REQUIREMENTS.md`, active stage doc.
- Owner auth from `docs/frontend-owner-signup/` is stable; reuse `OwnerRouteGuard` and `ownerAuthProbe`.
- Phase A proposal code exists; migrate rather than delete until Stage 4.3.

## Open questions

If stage is **BLOCKED** on missing API, stop and report—do not invent endpoints or migrations unless stage explicitly includes them.

## Contract rules (Stage 4+)

- Classify every field per `OWNER_EDIT_POLICY.md` before wiring UI or API.
- Direct writes: require `manage_published_venue_operations`; write published tables; append `audit_event`.
- Restricted writes: require `submit_restricted_changes_for_review`; use proposal/staging only; never mutate published on POST.
- Do not route descriptions/hours/specials/taps/features through `POST .../proposals` in new code.
- Do not add phone/email/website to UI until contact schema migration lands (unless stage includes migration).
- Use `GET /api/v1/reference/localities` for locality — no hardcoded suburb lists.
- Return structured errors via `validation_error` + `details`.

## Dependencies

- `web-portal/` for UI; `backend/` for owner venue APIs; `database/` only when stage authorizes migrations.

## Next downstream use

Stage 4.1: extend `owner_venue_service.py` with direct-write functions; add PATCH routes in `api/v1/owner/`.

---

## Repository scope

| Area | Rule |
|------|------|
| Owner UI | `web-portal/src/owner/**` |
| Shared | `web-portal/src/shared/**` — generic only |
| Admin | `web-portal/src/admin/**` — no regression on founder-venues |
| Backend | `backend/src/api/v1/owner/**`, `apps/owner/` |
| Consumer app | Out of scope |
| Docs | `docs/owner-venue-onboarding/**` |

## Auth & permissions

- Reuse `OwnerRouteGuard`, `ownerAuthProbe`, `ownerProvision`.
- `require_owner_portal_auth` on backend; venue scope on every `venue_id`.
- Enforce capability grants on writes (not just warnings) from Stage 4.1 onward.
- Do not bypass admin approval for claims or `business_venue_management_relationship`.

## Data & taxonomy

- Do not duplicate `venue_attribute_definition` or beverage reference data.
- Use `stable_key` from reference API — no hardcoded category lists.
- Do not expose `google_place_id` to owners.
- Do not delete proposal/staging tables.

## UX

- Step 1 required; other steps skippable with “Skip for now.”
- **Save changes** for operational; **Request change** for restricted.
- Show restricted pending state separately from operational saves.
- Preserve `portalBrand` env branding.

## Testing

- `pnpm typecheck` + Vitest when touching `web-portal/`.
- `pytest` when touching `backend/` — include tests that PATCH mutates published rows and POST restricted does not.
- Cite test files in PR description.

## Prohibited unless explicitly scoped

- New owner dashboard with dense nav/analytics
- Schema migrations without stage authorization
- Client-side approval of own venue relationship
- Direct owner edit of `display_name`, address, locality, coordinates
- Force-push or git config changes
