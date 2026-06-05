# PRD — Owner venue onboarding / profile builder (MVP)

## Purpose

Define MVP scope for guided owner listing capture after portal access—complementing `docs/frontend-owner-signup/` (identity/access only).

## Current stage

Planning reference for Stages 1–10. Not approved for implementation until Stage 1 planning sign-off.

## Decisions

- **In scope:** Guided onboarding wizard/shell for approved venue owners; Step 1 (core pub details) required; optional skippable sections; save-as-you-go.
- **Out of scope:** Full venue management dashboard; analytics; billing; consumer app changes; schema migrations (unless unblocker ticket); self-service venue claim approval.
- **Success:** Owner with approved venue can confirm/improve listing basics and optionally add specials/features; changes enter review workflow; owner sees clear status.

## Assumptions

- Owner already has `portal_home` (`venue_count > 0`) or sees honest wait/claim states.
- Backend will add owner-scoped read + proposal submit APIs before UI stages that edit data.
- Product copy uses `portalBrand` placeholders until final branding.

## Open questions

- SLA for admin review of owner submissions.
- Whether Step 1 fields publish automatically for “verified” venues in v1.

## Dependencies

- `STAGE_0_DISCOVERY.md`, `API_REQUIREMENTS.md`, owner auth-probe (done).

## Next downstream use

Stage 1 planning and `stages/STAGE_*.md` acceptance criteria.

---

## User stories (MVP)

1. As an owner with approved venue access, I see a simple “complete your listing” entry—not an empty dashboard.
2. As an owner, I must confirm name, address/locality, hours, and description before the listing is considered “basics done.”
3. As an owner, I can skip events, specials, taps, features, and photos and return later.
4. As an owner, I see when my changes are pending review vs live (once publish pipeline connected).
5. As an owner without venue access, I see wait/claim guidance and cannot edit listing data.

## Non-goals

- Replacing admin founder-venue CRM (`/internal/founder-venues`)
- Multi-user business team management UI
- Menu PDF upload, photo gallery, calendar events (v1)
- Google Place ID editing or display

## UX principles

> Complete the basics now. Add extra details whenever you can.

- One primary CTA path; progress checklist, not dense nav.
- Preserve admin operator experience; no feature regression on `/internal/*`.
