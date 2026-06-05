# Stage plan — Owner venue onboarding

## Purpose

Ordered implementation stages. **Stage 4 policy reframe** updates sequencing so future pages use direct-edit, not review-all proposals.

## Current stage

**Stage 4.2 complete (frontend split + restricted requests).** Next: **Stage 4.3** hardening or **Stage 7** features page.

## Decisions

| Stage | Status | Notes |
|-------|--------|-------|
| 0 Discovery | ✅ Done | |
| 1 Planning + contract | ✅ Done | Phase A contract (superseded for edit policy by Stage 4) |
| Backend Phase A | ✅ Done | List, detail, proposal intake |
| 2 Owner home entry | ✅ Done | Hub + picker |
| 3 Core pub info | ✅ Done | Interim all-proposal form |
| 3.5 Proposal hardening | ✅ Done | Draft hydration + in_review guard |
| **4 Edit policy reframe** | ✅ Done | Docs only — `OWNER_EDIT_POLICY.md` |
| **4.1 Direct-edit backend** | ✅ Done | PATCH operational-profile + hours + audit |
| **4.2 Step 1 UI split** | ✅ Done | Save vs Request change + restricted POST |
| **4.3 Hardening** | Planned | Row history, contact schema, deprecate proposal shim |
| 5 Meal specials | Ready after 4.1 | Direct-edit page |
| 6 Tap list | Ready after 4.1 | Direct-edit page |
| 7 Features | Ready after 4.1 | Direct-edit page |
| Admin restricted publish | Parallel | Publish worker for approved restricted proposals |
| 8 Photos | Plan only | Schema + moderation |
| 9 Review UX polish | Updated scope | Restricted pending states only |
| 10 QA | After 4.2+ | |

### Superseded numbering

> Old “Stage 4 Events” deferred stub — events remain schema-deferred; Stage 4 is now edit policy.

## Assumptions

- Direct edits go live on PATCH; restricted still needs publish worker for approved proposals
- No broad schema changes in Stage 4 (planning only); contact migration in 4.3

## Open questions

- Parallel PR: 4.1 backend + 4.2 frontend with mocked PATCH

## Dependencies

- `OWNER_EDIT_POLICY.md`
- `OWNER_VENUE_API_CONTRACT.md` (Stage 4.1 additions)
- Existing Phase A code in `owner_venue_service.py`

## Next downstream use

Open Stage 4.1 implementation ticket.

---

## Recommended sequence (post–Stage 4)

```text
Stage 4   ✅ Edit policy docs
Stage 4.1     Backend PATCH operational-profile + hours + audit + grant enforce
Stage 4.2     Frontend Step 1 split (Save / Request change)
Stage 4.3     Row history snapshots, contact migration, remove proposal shim
Stage 7       Features direct-edit page
Stage 5       Meal specials direct-edit page
Stage 6       Tap list direct-edit page
Admin         Restricted-change review + publish worker
Later         Contact UI, photos/media, events
Stage 10      QA across direct + restricted paths
```

## Contract artifacts

| Doc | Role |
|-----|------|
| `OWNER_EDIT_POLICY.md` | **Normative** edit classification (Stage 4+) |
| `OWNER_VENUE_API_CONTRACT.md` | DTOs + validation (Phase A legacy + 4.1 additions) |
| `API_REQUIREMENTS.md` | Endpoint index |
| `DATA_CAPTURE_MODEL.md` | Table mapping |
| `UX_FLOW.md` | Screen contracts |
| `STAGING_REVIEW_PUBLISH_AUDIT.md` | Restricted proposal workflow |

## Validation gates

1. Stage 4.1+: implementations match `OWNER_EDIT_POLICY.md` + contract additions
2. Direct PATCH must write published tables + `audit_event`; must not create `venue_change_proposal` for operational-only edits
3. Restricted POST must not write published tables
4. `pnpm typecheck` + Vitest (frontend); `pytest` (backend)
5. No self-approval paths
