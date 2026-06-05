# PRD — Owner venue onboarding / profile builder (MVP)

## Purpose

Define MVP scope for guided owner listing capture after portal access—complementing `docs/frontend-owner-signup/` (identity/access only).

## Current stage

**Stage 4 — policy reframe.** Product direction updated: verified owners **direct-edit** operational listing fields; only identity/location changes require admin review. See `OWNER_EDIT_POLICY.md`.

Stages 2–3 and Backend Phase A shipped an interim “review everything” path; Stages 4.1–4.2 will migrate Step 1 to the new model.

## Decisions

- **In scope:** Guided onboarding hub + step pages for approved venue owners; Step 1 (pub details) required; optional skippable sections; save-as-you-go.
- **Direct edit:** Verified owners update descriptions, hours, features, specials, taps (and contact when schema exists) **without per-field admin review**.
- **Restricted edit:** Trading name, address, locality, map coordinates go through **restricted change requests** → admin moderation → publish.
- **Claim / ownership:** Admin verifies venue management relationship; owners cannot self-approve claims.
- **Out of scope:** Full venue management dashboard; analytics; billing; consumer app changes; self-service claim approval.
- **Success:** Owner with approved venue can keep listing operational details current immediately; restricted identity changes have clear pending state; admin workload focuses on verification and sensitive edits.

### Superseded (pre–Stage 4)

> ~~Success: changes enter review workflow for every field~~ — replaced by direct-edit policy above.

## Assumptions

- Owner already has `portal_home` (`venue_count > 0`) or sees honest wait/claim states.
- Backend enforces `manage_published_venue_operations` for direct writes and `submit_restricted_changes_for_review` for restricted requests.
- Publish worker for **restricted** approvals remains a follow-on; direct edits are live on PATCH success.
- Product copy uses `portalBrand` placeholders until final branding.

## Open questions

- SLA for admin review of **restricted** change requests (not operational edits).
- Photo/media moderation workflow (deferred).
- Whether empty published records on first login need a one-time admin seed vs owner direct-fill (default: owner direct-fill).

## Dependencies

- `OWNER_EDIT_POLICY.md` (normative edit model)
- `STAGE_0_DISCOVERY.md`, `API_REQUIREMENTS.md`, owner auth-probe (done)
- Backend Phase A list/detail (done); direct-edit endpoints (Stage 4.1)

## Next downstream use

Stage 4.1 backend implementation; Stage 4.2 Step 1 UI split; Stages 5–7 direct-edit section pages.

---

## User stories (MVP)

1. As an owner with approved venue access, I see a simple “complete your listing” entry—not an empty dashboard.
2. As an owner, I can update descriptions and opening hours and see them reflected on my public listing without waiting for review.
3. As an owner, I must **request approval** to change my venue name or address.
4. As an owner, I must confirm name, address/locality, hours, and description for “basics done” completeness (read from published truth).
5. As an owner, I can skip events, specials, taps, features, and photos and return later.
6. As an owner, I see when a **restricted** change is pending review vs when operational saves are already live.
7. As an owner without venue access, I see wait/claim guidance and cannot edit listing data.

## Non-goals

- Replacing admin founder-venue CRM (`/internal/founder-venues`)
- Multi-user business team management UI
- Menu PDF upload, photo gallery, calendar events (v1)
- Google Place ID editing or display
- Owner self-approval of venue claims or management relationships

## UX principles

> Complete the basics now. Add extra details whenever you can.

- One primary CTA path; progress checklist, not dense nav.
- **Save changes** for operational fields; **Request change** for name/address.
- Preserve admin operator experience; no feature regression on `/internal/*`.
