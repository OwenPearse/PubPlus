# Wave 10 — Post-wave cleanup and hardening (SQL drafting)

This wave tightens the **already drafted** first-tranche SQL (Waves 1–9) without new product domains or architecture changes. It ships as migrations `0027`–`0029`.

## Objectives

- Add **purposeful** indexes (FK joins, workflow lookups, common catalog reads).
- Apply **low-risk CHECK** hardening where v1 docs previously left validation to apps.
- Align **table comments** on companion 1:1 patterns and beverage reference vs venue state.

## Migrations

| File | Role |
|------|------|
| `0027_post_wave_constraints_and_indexes.sql` | Performance-oriented indexes (partial where helpful). |
| `0028_optional_invariant_hardening.sql` | Safe CHECK constraints on recurring DOW values and specials validity naming. |
| `0029_schema_cleanup_and_consistency.sql` | Comment/documentation consistency; no DDL shape changes. |

## What was hardened

### Indexes (`0027`)

- **Published attributes:** partial index on `venue_published_attribute_value(allowed_value_id)` for catalog→venue joins.
- **Staging attributes:** `attribute_definition_id` index; partial on `allowed_value_id`.
- **Proposals / publish lineage:** partial indexes on `venue_change_proposal.superseded_by_proposal_id`, `venue_publish_event.venue_change_proposal_id`, `venue_publish_event.proposal_review_id`.
- **Verification:** partial index on `venue_verification_state.context_venue_claim_request_id`.
- **Authority events:** partial indexes on optional entity FK columns (`business_id`, `owner_account_id`, `venue_claim_request_id`, `business_venue_management_relationship_id`).
- **Audit:** partial indexes on actor account columns for support-style lookups.
- **Catalog reads:** partial indexes on `venue_published_structured_special` and `venue_published_tap_offering` for `(venue_id)` where `catalog_record_status = 'active'`.

### Optional CHECK constraints (`0028`)

- **Recurring specials:** `recurring_days_of_week` elements must be within `0`–`6` (documented convention).
- **Specials validity:** when `validity_bounds_kind = 'fully_bounded'`, both `offer_valid_from` and `offer_valid_to` must be non-null.

## What stayed soft / app-enforced (intentionally)

- **Subtype completeness** for `schedule_class` vs recurring/one-off child tables — still validated in publish pipelines (no cross-table DDL trigger).
- **Discovery tier implication rules** (specials and taps) — still explicit in application logic; no CHECK chains between tier booleans.
- **Composite attribute value integrity** (`allowed_value_id` vs `attribute_definition_id`) — still publish validation (possible future composite FK).
- **Consumer extension vs proposal actor alignment** — still application/service checks.
- **`open_started` / `open_ended` semantics** for `validity_bounds_kind` — partial interpretation remains app-led; only `fully_bounded` was tightened.

## What was deferred

- Additional indexes on every nullable FK (e.g. `raw_venue_intake_record_id` on proposals) until concrete query paths justify them.
- Stronger `validity_bounds_kind` rules for non–`fully_bounded` kinds.
- Cross-table exclusion between recurring and one-off subtype rows.
- Automated RLS integration tests (still optional / app-level).

## Verification

- `database/sql/checks/check_wave_10_post_wave_cleanup_and_hardening.sql` — index + constraint spot checks.
- `database/sql/checks/check_first_tranche_end_to_end.sql` — extended section when the full migration stack through Wave 9+ is applied.

## Ordering

Apply after `0026` (lexical order: `0027` → `0028` → `0029`).
