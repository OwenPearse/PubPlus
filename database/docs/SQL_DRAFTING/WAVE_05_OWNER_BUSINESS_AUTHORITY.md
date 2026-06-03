# SQL drafting — Wave 5 (owner / business authority backbone)

## Scope

Wave 5 adds the **owner → business → managed venue → coarse permissions** chain required by the locked relationship and authority blueprint. Implemented in migrations **0013–0016**.

This tranche does **not** add specials, tap lists, commercial/subscription overlays, rich owner-private operational tables, or RLS policies.

## Tables introduced

| Migration | Tables / DDL changes |
|-----------|----------------------|
| 0013 | `owner_business_membership` |
| 0014 | `business_venue_management_relationship` |
| 0015 | `venue_claim_request`, `venue_verification_state`, `venue_management_rights`, `venue_authority_decision`, `venue_authority_event`; `business_venue_management_relationship.source_venue_claim_request_id` |
| 0016 | `venue_capability_grant` |

## Rules preserved

- **Business is first-class**; venue authority is not embedded on `owner_account` or `venue` rows (domain_boundary_map section 8).
- **No person-to-venue authority shortcut**: grants reference `business_venue_management_relationship`, not `venue` alone (relationship_authority_blueprint section 9).
- **Membership ≠ venue access**: `owner_business_membership` does not reference `venue` (DL-021).
- **Claim, verification, management rights, and permissions stay distinct**: separate tables; no single “claimed venue” status model (DL-009, domain_boundary_map section 9).
- **History is not live authority**: `venue_authority_event` is append-only narrative; current grants live in `venue_capability_grant` plus rights/verification snapshots (DL-022).
- **Non-exclusive management**: multiple businesses may each have a `business_venue_management_relationship` row for the same `venue_id` (v1 DDL uses one row per `(business_id, venue_id)`; see implementation notes below).

## Implementation decisions (SQL-level)

- **One row per `(business_id, venue_id)`** on `business_venue_management_relationship` with a lifecycle column, instead of multiple superseded rows for the same pair—simpler v1 reads; lineage remains in `venue_authority_event` / decisions. This is an **implementation choice for v1**, not a permanent architectural rule locked by planning docs. If lifecycle complexity grows, a later migration may introduce a split or history-heavy relationship model **without** reopening the authority chain (owner → business → managed-venue junction → grants); the junction remains the conceptual anchor either way.
- **Claim ↔ relationship wiring**: optional `venue_claim_request.resulting_business_venue_management_relationship_id` and optional `business_venue_management_relationship.source_venue_claim_request_id` for traceability; authority still flows through the relationship row.
- **Verification and management rights** are **1:1 companions** keyed by `business_venue_management_relationship_id` (Worker B / Worker D) so current-state queries stay obvious.
- **Capability codes** are a small `TEXT` + `CHECK` list (`manage_published_venue_operations`, `submit_restricted_changes_for_review`, `manage_owner_private_venue_operations`, `manage_business_team_settings`)—coarse, not a matrix.
- **`venue_authority_decision`** requires at least one of `venue_claim_request_id` or `business_venue_management_relationship_id` so targets stay explicit without collapsing Stage-2 `proposal_review` into this table.

## Deferred

- Enforcing “owner must be an active member of `business`” for grants/claims in DDL (triggers or composite application checks).
- Subscription/commercial gating on top of authority (mvp_vs_deferred_scope_map).
- Deep team hierarchy beyond coarse `membership_role`.
- Rich owner-private operational tables; portal UX internals.
- RLS and service-role enforcement for these tables.

## Follow-ups

- If relationship lifecycles need full row-level history (superseded approvals, parallel review generations), evolve DDL in a dedicated migration; preserve the managed-venue junction as the authority anchor even if the physical shape becomes multi-table or versioned.
- Optional partial indexes (e.g. approved relationships only) once query patterns are known.
- Align `venue_authority_event.event_kind` vocabulary with product enums if string drift becomes noisy.
- Wave 6+ may tighten admin tooling around `venue_authority_decision` vs `proposal_review` boundaries.
