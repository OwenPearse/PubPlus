# Wave 12 — Final cross-wave readiness review (SQL drafting)

## Purpose

This wave is **verification, documentation, and light seed composition only**. It does not add product-domain schema. It consolidates handoff signals so app/backend integration workers can proceed without mistaking omissions for mistakes, and so later SQL workers do not casually reopen locked separations.

## Locked constraints (do not reinterpret)

Implementation must remain consistent with:

- `database/docs/SCHEMA_PLANNING_DOCS/decision_log.md`
- `database/docs/SCHEMA_PLANNING_DOCS/non_negotiable_rules_for_schema_workers.md`
- `database/docs/SCHEMA_PLANNING_DOCS/domain_boundary_map.md`
- `database/docs/SCHEMA_PLANNING_DOCS/relationship_authority_blueprint.md`
- `database/docs/SCHEMA_PLANNING_DOCS/state_lifecycle_model_summary.md`
- `database/docs/SCHEMA_PLANNING_DOCS/mvp_vs_deferred_scope_map.md`
- `database/docs/SCHEMA_PLANNING_DOCS/recommended_migration_schema_build_order.md`

## What the drafted package now covers

| Area | Scope |
|------|--------|
| **Migrations** | `0001`–`0032` under `database/supabase/migrations/` — foundations through commercial adjacency (see `MIGRATION_RUN_ORDER.md`). |
| **Public discovery truth** | Published venue profile, geography, attributes, hours families, structured specials, tap offerings + beverage reference. |
| **Workflow / provenance** | Intake, proposals, staging, reviews, publish events, evidence, audit. |
| **Consumer private** | Profile split tables, saved lists, workflow submissions. |
| **Authority** | Owner↔business, business↔venue management, claims, verification, rights, grants — distinct tables. |
| **RLS** | Published truth broadly readable (including `anon` where `0017` applies); consumer self-scope; owner scoped via membership + BVM; admin read on workflow/audit; Wave 11 commercial tables **not** exposed like public truth (`subscription_plan_reference` is `authenticated` only). |
| **Commercial adjacency** | Business subscription, entitlements, venue overlays via BVM, overlay attachments — **not** merged into published truth. |

## Verification artifacts

| File | Role |
|------|------|
| `database/sql/checks/check_wave_01_foundations.sql` … `check_wave_06_rls_and_permission_guardrails.sql` | Domain checks for Waves 1–6. |
| `database/sql/checks/check_wave_08_specials_promotions.sql` | Specials stack (`0021`–`0023`). |
| `database/sql/checks/check_wave_09_tap_list_backbone.sql` | Tap stack (`0024`–`0026`). |
| `database/sql/checks/check_wave_10_post_wave_cleanup_and_hardening.sql` | Indexes + optional CHECKs (`0027`–`0029`). |
| `database/sql/checks/check_wave_11_commercial_subscription_adjacency.sql` | Commercial adjacency (`0030`–`0032`). |
| `database/sql/checks/check_first_tranche_end_to_end.sql` | Cross-cutting checklist; includes optional blocks when Waves 8–9 and 11 migrations are present. |
| `database/sql/checks/check_full_schema_readiness.sql` | **Single pass** after full `0001`–`0032` apply: all drafted tables present, sample separations, RLS posture samples. |

**Overlap is intentional:** per-wave checks stay the first line of defense when editing a domain; aggregate checks catch wiring mistakes after a full reset.

## Seeds

**Recommended order** (dependency chain):

1. `dev_seed_reference_minimum.sql` — geography, attribute defs, external source.
2. `dev_seed_demo_venues.sql` — canonical venues + published-truth rows (dev-only direct inserts).
3. `dev_seed_demo_accounts_and_relationships.sql` — auth users, accounts, businesses, BVM, authority satellites, light consumer private rows.
4. `dev_seed_demo_specials.sql` — structured specials (requires venues; migrations through `0023`).
5. `dev_seed_demo_taps.sql` — beverage reference + tap lines (requires venues; migrations through `0026`).
6. `dev_seed_demo_commercial.sql` — minimal subscription/entitlement/overlay rows (requires accounts + BVM; migrations through `0032`).

**Composer:** `database/supabase/seed.sql` includes steps 1–3 and, for a fuller local demo, steps 4–6 in that order. Comment out later `\ir` lines if you need a smaller seed or have not applied extended migrations.

Requirements: Supabase-style `auth` schema and `pgcrypto` for password hashing when running account seed.

## What app/backend workers should assume

- **Published truth** is read-safe for discovery; **writes** to published tables for end users are **not** modeled as normal client `INSERT`/`UPDATE` — RLS denies by default; orchestration uses `service_role` or trusted backends.
- **Commercial state** does not grant venue permissions; grants remain on `venue_capability_grant` through `business_venue_management_relationship`.
- **JWT + account tables** drive RLS; policies do not rely on rich `user_metadata` for authorization.
- **Seeded published rows** are for local validation, not proof of production publish lineage.

## What later SQL workers should not reopen casually

- Collapsing **public truth**, **workflow**, **private**, **authority**, and **commercial** into fewer tables or shared “status” blobs.
- Direct client write paths into **published truth** (DL-008 posture).
- **Subscription or billing events** as schema in this tranche — only adjacency and current-row subscription state are drafted; event streams remain a later phase.

## What remains intentionally deferred

See `mvp_vs_deferred_scope_map.md` and per-wave “deferred” sections. Examples: full billing webhooks, CRM/analytics engines, deep admin write policies for every workflow table, historical subscription timelines, automated RLS integration tests (recommended as app-layer follow-up).

## Related docs

- `FIRST_TRANCHE_OVERVIEW.md` — tranche summary.
- `SQL_DRAFTING_NOTES.md` — implementation notes and dependency detail.
- `MIGRATION_RUN_ORDER.md` — ordered migration file list.
