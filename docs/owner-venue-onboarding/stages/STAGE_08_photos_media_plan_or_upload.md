# Stage 8 — Photos & media (plan only)

## Purpose

Plan upload/gallery UX; **do not implement upload** until `venue_published_media` and storage policies exist.

## Current stage

**Plan only** for MVP — hub shows “Photos — coming soon.”

## Decisions

- No Supabase storage bucket work in this workstream stage without Data approval
- Evidence uploads (`evidence_item`) are workflow-only—not public gallery

## Assumptions

- Future: storage bucket + RLS (INSERT/SELECT/UPDATE for upsert) per Supabase storage rules.

## Open questions

- Hero vs gallery cardinality; moderation queue for images.

## Dependencies

- Schema migration for `venue_published_media`
- Moderation/publish for media

## Next downstream use

Revise to implementation stage when schema lands.

---

## Planning deliverables (this stage)

1. Document intended object key layout and moderation flow
2. UX wireframe: hero + 3 gallery slots max for onboarding
3. Dependency ticket for Data + Backend

## Acceptance

- [ ] Hub deferral copy only OR doc sign-off—no broken upload UI
