# PubPlus — First SQL implementation tranche (Waves 1–11 + Wave 12 readiness)

This document summarizes what the **first tranche** of SQL migrations (`database/supabase/migrations/0001`–`0032`) delivers, how **Wave 7** (verification/seeds) and **Wave 12** (final readiness) support integration, and what remains **deferred by design**. It helps **future workers** continue without re-deriving architecture.

## What Waves 1–11 cover (migrations)

| Wave | Migrations (files) | What it establishes |
|------|--------------------|----------------------|
| **1** | `0001`–`0003` | Extensions placeholder; canonical `venue`; separate `consumer_account` / `owner_account` / `admin_account`; `business`; geography (`geographic_region`, `locality`) |
| **2** | `0004`–`0006` | Published profile + descriptive copy; attribute definitions + published values; published location + single map point; hours regular/exception/uncertainty + derived operational claim |
| **3** | `0007`–`0009` | `external_data_source`; raw intake; proposals + staging packages; reviews; publish events + optional row history; evidence + audit |
| **4** | `0010`–`0012` | Consumer profile + default location + notification settings (split tables); saved lists + membership; consumer submission extensions + workflow submissions |
| **5** | `0013`–`0016` | Owner↔business membership; business↔venue managed relationship; claims, verification, management rights, authority decisions/events; venue capability grants |
| **6** | `0017`–`0020` | RLS: public read for published truth; consumer self-scope; owner relationship-scope; admin read for workflow/audit; minimal `SECURITY INVOKER` helpers |
| **8** | `0021`–`0023` | Structured specials backbone; recurring vs one-off; validity vs discovery eligibility; SELECT RLS on published specials |
| **9** | `0024`–`0026` | Beverage reference; venue tap offerings; validity/freshness vs discovery tiers; SELECT RLS on tap + beverage tables |
| **10** | `0027`–`0029` | Post-wave indexes; optional CHECK hardening; comment/cleanup consistency (no new product tables) |
| **11** | `0030`–`0032` | Business subscription backbone; entitlements; venue commercial overlays; sponsored overlay adjacency + RLS for commercial domain |

**Ordering:** migrations apply in lexical order (`0001` … `0032`). Dependencies are documented in `SQL_DRAFTING_NOTES.md` and `MIGRATION_RUN_ORDER.md`.

**Naming note:** SQL drafting uses **Wave 8/9** for specials/tap migration slices; planning doc `recommended_migration_schema_build_order.md` uses different wave numbers for the same domains — follow the **file list**, not the label alone.

## Wave 7 (SQL drafting) — verification + seeds

Wave 7 is **verification + seeds + documentation**, not new domains:

- **Checks** under `database/sql/checks/` to validate structure, separation, and coarse RLS posture (extended by later waves).
- **Seeds** under `database/sql/seeds/` plus `database/supabase/seed.sql` as the composed entry point.
- **Docs:** `WAVE_07_VERIFICATION_AND_SEEDS.md`, cross-linked from Wave 12.

## Wave 12 (SQL drafting) — final readiness

Wave 12 is **cross-wave verification and handoff only** (see `WAVE_12_FINAL_READINESS_REVIEW.md`):

- **`check_full_schema_readiness.sql`** — single pass after full `0001`–`0032` apply.
- **`check_first_tranche_end_to_end.sql`** — updated with optional Wave 11 table block.
- **Docs:** this file, `MIGRATION_RUN_ORDER.md`, `SQL_DRAFTING_NOTES.md` alignment.
- **Seeds:** `seed.sql` composes the full minimal demo chain (reference → venues → accounts → specials → taps → commercial) when all migrations are present.

## What is still deferred (by design)

Aligned with locked planning docs and MVP scope:

- **Billing webhooks, invoice lines, dunning** — not in v1 tables beyond opaque external IDs on subscription rows.
- **Rich CRM / analytics** — not modeled here.
- **Deep admin write policies** for every workflow mutator — many flows still expected via **service_role** / trusted backends.
- **Automated RLS integration tests** — optional follow-up (app-level tests with real JWT roles).
- **Historical subscription / commercial event timelines** — v1 uses a single current subscription row per business.

## How a future worker should continue

1. **Do not reinterpret** locked planning docs; treat them as constraints (`decision_log.md`, `non_negotiable_rules_for_schema_workers.md`, `domain_boundary_map.md`, `relationship_authority_blueprint.md`, `state_lifecycle_model_summary.md`, `mvp_vs_deferred_scope_map.md`, `recommended_migration_schema_build_order.md`).
2. **After migrations:** run relevant `check_wave_*.sql` files for touched domains, then `check_first_tranche_end_to_end.sql`; on a full fresh apply use `check_full_schema_readiness.sql`.
3. **For local UX:** extend **seeds** sparingly; keep them small and labeled as dev/demo.
4. **Next product schema work:** follow `recommended_migration_schema_build_order.md` *after* this tranche — do not collapse tables that were split intentionally (claims vs verification vs grants, etc.).

## File map (quick)

- **Migrations:** `database/supabase/migrations/`
- **Checks:** `database/sql/checks/`
- **Seeds:** `database/sql/seeds/`
- **Seed entry:** `database/supabase/seed.sql`
- **Readiness:** `WAVE_12_FINAL_READINESS_REVIEW.md`, `MIGRATION_RUN_ORDER.md`
- **Implementation notes:** `SQL_DRAFTING_NOTES.md`
