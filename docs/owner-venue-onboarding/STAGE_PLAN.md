# Stage plan — Owner venue onboarding

## Purpose

Ordered implementation stages; Stage 1 contract freeze complete.

## Current stage

**Stage 1 complete** → **Backend Phase A** and **Stage 2** can start in parallel after sign-off.

## Decisions

| Stage | Status | Blocker |
|-------|--------|---------|
| 0 Discovery | ✅ Done | — |
| 1 Planning + contract | ✅ Done | — |
| 2 Owner home entry | Ready | `GET /owner/venues` |
| 3 Core pub info | Ready | GET detail + POST proposals |
| 4 Events | Deferred stub | Schema |
| 5–7 Optional sections | Phase B | Staging for specials/taps |
| 8 Photos | Plan only | Schema + storage |
| 9 Review UX | Ready | Partial without publish |
| 10 QA | Ready | After 2–3 |

## Assumptions

- Publish worker not required for Stage 2–3 ship; honest review copy.

## Open questions

- Parallel PR: Backend T1 + Frontend T2 with mocked list

## Dependencies

- `OWNER_VENUE_API_CONTRACT.md`
- `STAGING_REVIEW_PUBLISH_AUDIT.md`

## Next downstream use

Implementation agents use `stages/STAGE_02` onward.

---

## Sequence

```text
Stage 0  ✅ Discovery
Stage 1  ✅ Contract freeze
         ↓
Backend Phase A (T1) ──┬── Stage 2 Frontend hub
                       └── Stage 3 Frontend basics (after T1 read/POST)
Stage 9  Review/checklist polish
Stage 7  Features (Phase B)
Stage 5–6 Specials/taps (Phase B)
Stage 10 QA
Stage 4, 8  When schema exists
```

## Contract artifacts (Stage 1)

| Doc | Role |
|-----|------|
| `OWNER_VENUE_API_CONTRACT.md` | **Normative** DTOs + validation |
| `STAGING_REVIEW_PUBLISH_AUDIT.md` | Workflow + simplification |
| `API_REQUIREMENTS.md` | Endpoint index |
| `DATA_CAPTURE_MODEL.md` | Table mapping + contact plan |
| `UX_FLOW.md` | Stage 2–3 UX |

## Validation gates

1. Implementations must match contract (review PR against `OWNER_VENUE_API_CONTRACT.md`)
2. `pnpm typecheck` + Vitest (frontend); `pytest` (backend)
3. Demo owner: `database/sql/seeds/dev_seed_demo_accounts_and_relationships.sql`
4. No self-approval paths
