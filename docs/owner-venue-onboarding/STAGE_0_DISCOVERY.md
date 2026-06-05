# Stage 0 — Owner venue onboarding / profile builder discovery

## Purpose

Inspect repo, database, backend, and existing owner/admin patterns; document confirmed findings and recommend a staged implementation plan for guided owner venue listing capture—**no implementation in this stage**.

## Current stage

**Stage 0 — complete.** Stage 1 contract freeze complete — see `OWNER_VENUE_API_CONTRACT.md` and `STAGING_REVIEW_PUBLISH_AUDIT.md` for normative Phase A detail.

## Decisions

| Topic | Confirmed finding | Recommendation |
|-------|-------------------|----------------|
| Owner portal shell | `/owner` → `OwnerHomePlaceholder` inside `OwnerRouteGuard` + `PortalShell` | Extend home into onboarding entry; do not build full dashboard |
| Auth | Supabase JWT + `GET /api/v1/owner/auth-probe` + `POST /provision` | Reuse; add venue APIs behind `require_owner_portal_auth` |
| Venue access gate | `next_step`: membership → venue → `portal_home`; counts only | Block onboarding until `venue_count > 0`; show claim/wait states before |
| Published truth | No client writes to `venue_published_*` (RLS read-only) | Owner changes via **proposals + admin publish** (or new owner intake mirroring consumer) |
| Core pub fields | Profile, location, hours, descriptive copy exist; **phone/website/email absent** | MVP Step 1: name, address/locality, hours, descriptions; defer contact until schema |
| Google Place ID | Not on published venue; only founder-lead source enum | **Internal-only**; never show in owner UI |
| Multi-venue | Schema supports many venues per owner; probe returns count only | MVP: single venue or simple picker when count > 1 |
| Owner venue APIs | **None** beyond provision/auth-probe | New `GET /owner/venues`, proposal intake, optional read of published snapshot |
| Claim workflow | `venue_claim_request` + `business_venue_management_relationship` in DB; **no backend API** | Admin-mediated claim; owner UI = request/wait, not self-approve |
| Consumer submissions | `POST /submissions/corrections` → staging proposals | Reuse pattern for owner with `actor_type=owner`, `channel=owner_portal` |
| Moderation | Internal queue closes proposal lifecycle; **does not publish** to live tables yet | Owner edits → review → separate publish pipeline (dependency) |
| Specials / taps | Published tables exist; no owner staging RLS | Phase 2+ after core profile; happy hour = `structured_kind: happy_hour` |
| Photos / menus | No `venue_published_media` or menu tables | Defer upload to post-MVP stage |
| Completeness | No backend completeness score | MVP: client-side checklist from probe + section save flags |
| Branding | `portalBrand` env-driven name/tagline; placeholder logo | Preserve `VITE_PORTAL_*` and `/brand/placeholder-mark.svg` |

## Assumptions

- Owner signup/access workstream (`docs/frontend-owner-signup/`) is largely complete; this workstream starts after `portal_home` or waiting states.
- Same Supabase project and Django API as consumer app.
- Admins assign `owner_business_membership` and approve `business_venue_management_relationship`; owners do not self-approve.
- Publish pipeline (proposal approved → `venue_published_*`) may lag moderation; document as dependency.

## Open questions

1. **Publish automation:** When moderation approves, who writes `venue_publish_event` and published rows—batch job, manual admin tool, or new endpoint?
2. **Owner direct publish:** Will any fields (e.g. `short_description`) ever skip review for verified owners?
3. **Contact fields:** Target table and proposal target family for phone/website/email?
4. **Claim intake:** Owner-initiated `venue_claim_request` via Django API or admin-only today?
5. **Tap list MVP:** Structured `venue_published_tap_offering` rows vs free-text staging field?

## Dependencies

| Dependency | Status |
|------------|--------|
| Owner auth-probe / provision | **Done** — `backend/docs/OWNER_PORTAL_AUTH.md` |
| Owner account + membership + approved venue relationship | **Schema + RLS** — `0013`–`0019` |
| Owner venue list / read / write APIs | **Missing** |
| Owner proposal intake service | **Missing** (consumer intake exists) |
| Publish after approval | **Partial** (moderation updates lifecycle only) |
| Contact + media schema | **Missing** |
| Claim request API | **Missing** |

## Next downstream use

- `PRD.md`, `DATA_CAPTURE_MODEL.md`, `API_REQUIREMENTS.md`, `UX_FLOW.md`, `STAGE_PLAN.md`, `AGENT_RULES.md`, `stages/*.md`

---

## 1. Owner portal / frontend (confirmed)

### 1.1 What `/owner` renders

- **Routes:** `web-portal/src/App.tsx` — `/owner/*` under `OwnerRouteGuard`; index → `OwnerHomePlaceholder`; other paths redirect to `/owner`.
- **Home:** `web-portal/src/owner/pages/OwnerHomePlaceholder.tsx` branches on `ownerAuthProbe().body.next_step`:
  - `complete_owner_provisioning` — provision CTA
  - `owner_waiting_for_membership` — `NoVenueAccessState` (membership)
  - `owner_waiting_for_venue_access` — `NoVenueAccessState` (venue)
  - `portal_home` — placeholder welcome + `business_count` / `venue_count`

### 1.2 Owner auth guarding

- **`OwnerRouteGuard`** (`web-portal/src/owner/components/OwnerRouteGuard.tsx`): Supabase session → `ownerAuthProbe()` → 403/unprovisioned → `/access`; success → `PortalShell`.
- MFA is **optional** for `/owner` (`OWNER_MFA_REQUIRED = false`; `portalRole.ts`).
- Entry/auth: `PortalEntryPage` at `/access` with sign-in/up, password reset, optional MFA, `resolvePortalRole()`.

### 1.3 Auth/probe data on frontend

Types in `web-portal/src/shared/lib/api.ts` — `OwnerAuthProbeBody`:

- Identity: `owner_account_exists`, `owner_account_id`, `owner_account_active`
- Access: `business_count`, `venue_count`, `has_active_business_membership`, `has_approved_managed_venue_relationship`
- MFA: `aal`, `mfa_required`, `mfa_enabled`
- Routing: `next_step`

**No venue IDs, names, or listing payload.**

### 1.4 Assigned venues visible?

**No.** Only aggregate counts. No `GET /owner/venues` client.

### 1.5 Owner home / dashboard

Single placeholder page—no nav, venue cards, or sub-routes. Explicit copy: *"venue management features will appear here in a future release."*

### 1.6 Reusable shared assets

| Asset | Path |
|-------|------|
| API client | `web-portal/src/shared/lib/api.ts` |
| Supabase auth/MFA | `web-portal/src/shared/lib/supabase.ts` |
| Portal shell | `web-portal/src/shared/components/PortalShell.tsx` |
| Errors | `web-portal/src/shared/components/ErrorBanner.tsx` |
| Brand | `web-portal/src/shared/lib/portalBrand.ts` |
| Role/routing | `web-portal/src/shared/lib/portalRole.ts`, `portalRedirect.ts` |

### 1.7 Admin patterns to adapt

- **List:** `FounderVenuesListPage` — filters in URL, loading/error, `ErrorBanner`
- **Detail/edit:** `FounderVenueDetailPage` — load → form state → diff-only PATCH
- **Not reusable as-is:** founder-lead fields/outreach; owner needs venue published/proposal fields

### 1.8 Multi-venue selection

**Not implemented.** Schema allows multiple approved relationships; MVP should add picker when `venue_count > 1`.

### 1.9 Branding placeholders

- `VITE_PORTAL_PRODUCT_NAME`, `VITE_PORTAL_PRODUCT_TAGLINE` (default `"Venue Portal"`)
- Logo: `/brand/placeholder-mark.svg` (not env-driven)
- See `docs/frontend-owner-signup/branding-placeholder-strategy.md`

### 1.10 Frontend tests (cited)

- `web-portal/src/owner/components/OwnerRouteGuard.test.tsx`
- `web-portal/src/owner/pages/OwnerHomePlaceholder.test.tsx`
- `web-portal/src/owner/pages/PortalEntryPage.test.tsx`
- `web-portal/src/shared/lib/api.owner.test.ts`, `portalRole.test.ts`

---

## 2. Backend / API (confirmed)

### 2.1 Owner portal routes (today)

| Method | Path | File |
|--------|------|------|
| POST | `/api/v1/owner/provision` | `backend/src/api/v1/owner/views.py` |
| GET | `/api/v1/owner/auth-probe` | same |

Wiring: `backend/src/api/v1/owner/urls.py`. Guards defined in `backend/src/common/auth/guards.py` (`require_owner_portal_auth`, `require_owner_portal_auth_aal2`) — **not used on routes yet**.

### 2.2 Auth-probe behaviour by state

| State | HTTP | `next_step` |
|-------|------|-------------|
| No token | 401 | — |
| No `owner_account` | 403 | `complete_owner_provisioning` |
| No active membership | 200 | `owner_waiting_for_membership` |
| Membership, no approved venue | 200 | `owner_waiting_for_venue_access` |
| Approved venue(s) | 200 | `portal_home` |

Implementation: `backend/src/apps/owner/services/owner_access_service.py`. Docs: `backend/docs/OWNER_PORTAL_AUTH.md`.

Admin/founder accounts: provisioning blocked if `admin_account` exists for same auth user.

### 2.3 Backend venue knowledge

`load_owner_access_counts()` counts distinct `venue_id` via `owner_business_membership` (active) → `business_venue_management_relationship` (approved). **No list, no per-venue authorization API.**

### 2.4 Read/write conventions

- Bearer JWT, JSON errors `{ error: { code, message } }`
- Consumer submissions: `201` ack, no workflow ID in response
- Venue public read: `GET /api/v1/venues/{venue_id}` — optional auth, published snapshot

### 2.5 Owner venue writes

**Do not exist.**

### 2.6 Direct writes vs submissions

- **Published truth:** not mutated by intake APIs
- **Consumer:** `backend/src/apps/submissions/services/submission_intake_service.py` writes `venue_change_proposal` + staging (`profile`, `geo`, `attributes`, `hours`)
- **Owner:** no intake; RLS allows owner CRUD on proposals when `actor_type = 'owner'` (Supabase direct path exists but portal uses Django)

### 2.7 Admin review

- `GET/POST /api/v1/internal/moderation/*` — approve/reject updates `lifecycle_status` + `proposal_review`
- **Does not** write `venue_published_*` (documented in `backend/docs/API_ENDPOINT_OVERVIEW.md`)
- No owner-specific moderation path

### 2.8 Audit logging

- `audit_event` on moderation decisions/notes (`moderation_write_service.py`)
- Consumer submission intake: **no** audit row
- Owner edits: N/A until APIs exist

### 2.9 Backend tests (cited)

- `backend/tests/test_owner_endpoints.py`
- `backend/tests/test_submission_endpoints.py`
- `backend/tests/test_internal_moderation_endpoints.py`

---

## 3. Database / schema (confirmed)

### 3.1 Venue core storage

| Concern | Table(s) | Migration |
|---------|----------|-----------|
| Identity | `venue` | `0002_canonical_venue_backbone.sql` |
| Name, slug, status | `venue_published_profile` | `0004_published_venue_profile_core.sql` |
| Descriptions | `venue_published_descriptive_copy` | `0004` |
| Address, locality | `venue_published_location`, `locality`, `geographic_region` | `0003_published_geography_core.sql` |
| Map point | `venue_published_map_point` | `0003` |
| Hours | `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty` | `0006_hours_and_exceptions_foundations.sql` |
| Phone, website, email | **Not in schema** | — |
| Google Place ID | **Not on published venue**; `google_places` in founder leads only | `0033_founder_venue_leads.sql` |

### 3.2 Owner / venue relationships

```
owner_account → owner_business_membership → business
  → business_venue_management_relationship (lifecycle: requested … approved)
  → venue_capability_grant
```

Claim: `venue_claim_request` (`0015_claims_verification_and_management_rights.sql`). Verification: `venue_verification_state`; rights: `venue_management_rights`.

### 3.3 RLS (owner)

- **Migration `0019_rls_owner_business_authority.sql`:** owner SELECT on authority chain; INSERT/UPDATE on `venue_claim_request`, `venue_change_proposal` (+ staging) for owner actor
- **Migration `0017_rls_public_truth_reads.sql`:** published tables SELECT-only for clients
- **Docs:** `database/docs/SQL_DRAFTING/WAVE_06_RLS_AND_PERMISSION_GUARDRAILS.md`
- **Checks:** `database/sql/checks/check_wave_05_owner_business_authority.sql`, `check_wave_06_rls_and_permission_guardrails.sql`

### 3.4 Corrections / submissions model

- `venue_change_proposal` + `venue_proposal_target` + `venue_proposal_staging_*` (`0007_raw_intake_and_proposals.sql`)
- Review: `proposal_review` (`0008_reviews_publish_lineage.sql`)
- Publish lineage: `venue_publish_event`, `venue_published_row_history`
- Consumer extension: `consumer_submission_extension` (`0012`) — no owner extension table

### 3.5 Related content tables

| Domain | Published table(s) | Owner staging RLS |
|--------|-------------------|-------------------|
| Structured specials | `venue_published_structured_special` (+ recurring/one-off, validity) | No |
| Tap list | `venue_published_tap_offering` | No |
| Beverage ref | `beverage_product`, `beverage_brewery`, `beverage_style` | N/A |
| Attributes | `venue_attribute_definition`, `venue_published_attribute_value` | Yes (`venue_proposal_staging_attribute`) |
| Events (calendar) | **None** | — |
| Menus | **None** | — |
| Photos/media | **None** (`venue_published_media` planned in backend comments only) | — |

### 3.6 Taxonomy

- Attributes: `stable_key` + UUID `id`, `value_shape` (`boolean`, `single_select`, …)
- Seeded booleans: `database/sql/seeds/dev_seed_mvp_filter_taxonomy.sql` — `beer_garden`, `rooftop`, `live_music`, `dog_friendly`, `sports_screens`, `pool_table`, `late_night`, `vegan_options`
- Special kinds: CHECK enum on `structured_kind` — `meal_special`, `drink_special`, `happy_hour`, `venue_offer`
- No TAB/pokies/gambling keys in MVP seed

### 3.7 Attribute modelling

- Boolean: row present + `value_boolean`; absent = unknown (no tri-state column)
- Select: `allowed_value_id` FK
- Definitions use **stable_key** for filters; assignments use **UUID** `attribute_definition_id`

### 3.8 Media / menus

- `evidence_item.storage_url` for workflow evidence (`0009`) — not public gallery
- No storage bucket DDL in migrations
- Menu upload: **not supported**

### 3.9 Audit

- `audit_event` (`0009_provenance_evidence_audit_minimums.sql`)
- Domain: `venue_authority_event`, `venue_authority_decision`, `proposal_review`, `venue_publish_event`

---

## 4. Product discovery — proposed onboarding structure

Evaluated flow (Step 1 required; rest optional/skippable):

| Step | Section | Schema readiness | MVP? |
|------|---------|------------------|------|
| 1 | Confirm pub details (name, address/locality, hours, description) | High (gaps: phone/web/email) | **Yes — required** |
| 2 | Live events / recurring activities | No events table | Defer or stub “coming soon” |
| 3 | Meal specials + menu | Specials yes; menu no | Specials optional; menu defer |
| 4 | Tap list / drinks | Published taps yes; no owner intake | Optional; simple rows later |
| 5 | Venue features | Boolean attributes seeded | Optional — subset of taxonomy |
| 6 | Photos / media | No table | Defer |
| 7 | Review and publish | Depends on publish pipeline | Show checklist + submission status |

Principle: **Save-as-you-go. Skip for now. Come back later.** Not a giant dashboard.

---

## 5. Approval / permission states (must distinguish)

| State | Owner experience | Self-approve? |
|-------|------------------|---------------|
| No `owner_account` | Provision CTA | N/A |
| No business membership | `NoVenueAccessState` membership variant | **No** — admin adds membership |
| Membership, no approved venue | `NoVenueAccessState` venue variant; optional claim request UI (API TBD) | **No** — admin approves relationship |
| Approved venue access | Onboarding + listing edits (when built) | N/A |

`venue_claim_request` lifecycles: `draft` → `submitted` → `under_review` → … — admin decisions via `venue_authority_decision`.

---

## 6. Specific product questions — answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Owner edits live immediately or admin review? | **Review first** for published-truth fields; matches proposal + moderation model. Direct publish not implemented. |
| 2 | Reuse consumer correction flow? | **Yes — recommended.** Extend `submission_intake_service` (or parallel owner service) with `actor_type=owner`, `channel=owner_portal`, same staging families. |
| 3 | Safe direct owner edits? | **None to published tables** via client. Low-risk staging drafts OK before submit. |
| 4 | Reviewable submissions? | Profile, geo, hours, attributes, descriptive copy (via profile staging). Location changes especially sensitive. |
| 5 | Address owner-editable? | **Proposed-change** via `venue_proposal_staging_location`; treat as reviewable, not silent live edit. |
| 6 | Google Place ID visible to owners? | **No** — internal/import only. |
| 7 | Multiple venues MVP? | **Single-venue default;** if `venue_count > 1`, simple venue picker before onboarding. No multi-dashboard. |
| 8 | Menu/photo upload MVP? | **Later** — schema and storage absent. |
| 9 | Tap list MVP format? | Prefer **structured rows** (`venue_published_tap_offering` + `beverage_product`) when built; interim optional free-text in staging only if product insists. |
| 10 | Happy hour modelling? | Use **`happy_hour`** `structured_kind` on `venue_published_structured_special` with `schedule_class` recurring/one_off — not a separate entity. |
| 11 | Features to expose first? | MVP seed booleans: beer garden, rooftop, live music, dog friendly, sports screens, pool table, late night, vegan options — **≤8 toggles**. |
| 12 | TAB/pokies/gambling? | **Defer** — not in MVP taxonomy; if added later, treat as boolean attributes with `publishability_risk_hint` review, not filters until policy set. |
| 13 | Listing completeness feasible? | **Client-side checklist** only: required step 1 fields + optional section “started/complete” flags; no server score until publish read API aggregates published rows. |

---

## 7. Inspected paths (inventory)

**Frontend:** `web-portal/src/App.tsx`, `web-portal/src/owner/**`, `web-portal/src/shared/**`, `web-portal/src/admin/pages/FounderVenueDetailPage.tsx`, `web-portal/src/admin/pages/FounderVenuesListPage.tsx`

**Backend:** `backend/src/api/v1/owner/**`, `backend/src/api/v1/submissions/**`, `backend/src/api/v1/venues/**`, `backend/src/api/v1/internal/**`, `backend/src/apps/owner/**`, `backend/src/apps/submissions/**`, `backend/docs/OWNER_PORTAL_AUTH.md`

**Database:** `database/supabase/migrations/0002`–`0026`, `0019`, `0020`, `database/sql/seeds/dev_seed_mvp_filter_taxonomy.sql`, `database/docs/SQL_DRAFTING/WAVE_06_RLS_AND_PERMISSION_GUARDRAILS.md`

**Related docs:** `docs/frontend-owner-signup/STAGE_0_DISCOVERY.md`, `docs/frontend-owner-signup/DATABASE_REPORT.md`

---

## 8. Testing / validation (this stage)

Discovery-only: **no frontend/backend tests run or required.** Tests cited above for future stages.
