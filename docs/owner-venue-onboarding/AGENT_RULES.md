# Agent rules — Owner venue onboarding workstream

## Purpose

Rules for downstream Cursor agents implementing onboarding/profile builder—after Stage 0 discovery.

## Current stage

Stage 1 complete. Applies to all stages in `docs/owner-venue-onboarding/stages/`. **Normative API:** `OWNER_VENUE_API_CONTRACT.md`.

## Decisions

- **Implementer, not replanner** — follow active `stages/STAGE_*.md` and `PRD.md`.
- **No full owner dashboard** — guided hub + wizard only until product expands scope.
- **Proposal workflow** — no direct published-truth writes from owner UI.
- **No self-approval** — venue claims and relationships remain admin-mediated.

## Assumptions

- Read before coding: `STAGE_0_DISCOVERY.md`, `API_REQUIREMENTS.md`, active stage doc.
- Owner auth from `docs/frontend-owner-signup/` is stable; reuse `OwnerRouteGuard` and `ownerAuthProbe`.

## Open questions

If stage is **BLOCKED** on missing API, stop and report—do not invent endpoints or migrations unless stage explicitly includes them.

## Contract rules (Stage 1+)

- Implement Phase A exactly as `OWNER_VENUE_API_CONTRACT.md` — paths, DTOs, `intent`, field classification.
- Do not add phone/email/website to UI until contact schema migration lands.
- Owner POST must not mutate `venue_published_*` tables.
- Return `proposal_id` from owner POST (unlike consumer ack-only).
- Use `GET /api/v1/reference/localities` for locality — no hardcoded suburb lists.

## Dependencies

- `web-portal/` for UI; `backend/` for owner venue APIs; `database/` only when stage authorizes migrations.

## Next downstream use

Open assigned `stages/STAGE_*.md` before editing code.

---

## Repository scope

| Area | Rule |
|------|------|
| Owner UI | `web-portal/src/owner/**` |
| Shared | `web-portal/src/shared/**` — generic only |
| Admin | `web-portal/src/admin/**` — no regression on founder-venues |
| Backend | `backend/src/api/v1/owner/**`, `apps/owner/`, `apps/submissions/` (if extending intake) |
| Consumer app | Out of scope |
| Docs | `docs/owner-venue-onboarding/**` |

## Auth & permissions

- Reuse `OwnerRouteGuard`, `ownerAuthProbe`, `ownerProvision`.
- New routes: `require_owner_portal_auth` on backend; frontend still calls probe for empty states.
- Check venue scope on every `venue_id` path param.
- Do not bypass admin approval for claims or `business_venue_management_relationship`.

## Data & taxonomy

- Do not duplicate `venue_attribute_definition` or beverage reference data.
- Use `stable_key` from reference API or seed-aligned constants—no hardcoded category lists that contradict DB.
- Do not expose `google_place_id` to owners.

## UX

- Step 1 required; other steps skippable with explicit “Skip for now.”
- Save-as-you-go per step; show pending review state when API provides it.
- Preserve `portalBrand` env branding and placeholder logo path.

## Testing

- Run `pnpm typecheck` and relevant Vitest when touching `web-portal/`.
- Run `pytest` for owner/submission tests when touching `backend/`.
- Cite test files added/updated in stage PR description.

## Prohibited in all stages unless explicitly scoped

- New owner dashboard with dense nav/analytics
- Schema migrations without Data review
- Client-side insert into `owner_account` or approval of own venue relationship
- Force-push or git config changes
