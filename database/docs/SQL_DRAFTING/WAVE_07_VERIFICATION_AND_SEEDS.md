# SQL drafting — Wave 7 (verification, seeds, first-tranche handoff)

This wave is **not** new schema architecture. It finalizes the **first implementation tranche** (migrations `0001`–`0020`) by adding **verification SQL**, **minimal dev/demo seeds**, and **handoff documentation** so later workers can verify integrity and continue without duplicating work.

> **Naming note:** Planning docs refer to a future product “Wave 7 — Structured Specials / Promotions” in `recommended_migration_schema_build_order.md`. This SQL drafting wave is **only** about verification/seeds/cleanup for the completed Waves 1–6 tranche.

## What was added

### Verification scripts (`database/sql/checks/`)

| File | Purpose |
|------|---------|
| `check_wave_01_foundations.sql` | Anchors: `venue`, separate account-domain tables, `business`, geography FK sanity |
| `check_wave_02_public_truth.sql` | Published vs workflow separation; 1:1 map point; structured attributes; hours families distinct |
| `check_wave_03_workflow_provenance.sql` | Intake, proposals, staging, reviews, lineage history, evidence, audit present and distinct |
| `check_wave_04_consumer_private_state.sql` | Split prefs tables; list-native saves; venue FK; submissions not “published truth” by naming |
| `check_wave_05_owner_business_authority.sql` | No membership→venue shortcut; grants via managed-venue junction; distinct authority tables |
| `check_wave_06_rls_and_permission_guardrails.sql` | RLS on key classes; helpers `SECURITY INVOKER`; published truth without client write policies (samples) |
| `check_first_tranche_end_to_end.sql` | Small cross-cutting checklist (table presence, separation, helper posture, sample RLS/write posture; optional blocks when later waves applied) |
| `check_full_schema_readiness.sql` | Added in Wave 12 — single pass after migrations `0001`–`0032` (see `WAVE_12_FINAL_READINESS_REVIEW.md`) |

Run these **after** migrations apply. Each file returns result sets with `check_name` and `ok` (boolean) or explicit `pg_catalog` rows — **inspect for `ok = false` / `relrowsecurity = false`**.

These checks are **practical guardrails**, not formal proofs. They catch obvious domain-collapse mistakes (wrong FK targets, missing tables, accidental write policies on published truth) early.

### Seed scripts (`database/sql/seeds/`)

| File | Purpose |
|------|---------|
| `dev_seed_reference_minimum.sql` | AU → NSW → Sydney geography; two attribute definitions + allowed values; one `external_data_source` |
| `dev_seed_demo_venues.sql` | Two canonical venues with published profile/location/map, structured attributes, hours/exception/uncertainty/derived rows |
| `dev_seed_demo_accounts_and_relationships.sql` | Supabase `auth.users` + `auth.identities` (email), consumer/owner/admin logical accounts, two businesses, memberships, two managed-venue links, verification/rights snapshots, two capability grants, light consumer private rows |

### Supabase entry point

| File | Purpose |
|------|---------|
| `database/supabase/seed.sql` | Composes reference → venues → accounts → (optional) specials, taps, commercial via `\ir` — see `WAVE_12_FINAL_READINESS_REVIEW.md` |

## How to run safely

1. **Migrations first:** apply `0001`–`0032` in order for the full drafted package (or stop earlier and omit optional seed includes). Database must include Supabase Auth (`auth` schema) for account seeding. Plain Postgres without Auth will fail on account seeding.
2. **Checks:** run each `check_wave_*.sql` and `check_first_tranche_end_to_end.sql` as a privileged user (same as migrations). No writes required.
3. **Seeds:**
   - **Reference + venues only:** run `dev_seed_reference_minimum.sql` then `dev_seed_demo_venues.sql` if you want published data **without** auth.
   - **Full demo:** run `database/supabase/seed.sql` (or the same files in dependency order). Requires `pgcrypto` (`extensions.crypt` / `gen_salt`) for password hashing. Tail files need matching migrations (specials/taps/commercial).
4. **Trust / workflow posture:** seeding **published-truth tables directly** is intentional for **local/dev** to exercise reads and joins. It does **not** replace publish pipelines, evidence, or reviews in production. Document this clearly to anyone interpreting demo data as “real” provenance.

## Small cleanup decisions (implementation-level)

- **End-to-end check** uses a bounded list of expected table names; if you rename tables in a later tranche, update the list — it is a **maintenance join**, not a dynamic invariant.
- **Auth seed** uses fixed UUIDs so re-runs and cross-table references stay stable; guards use `WHERE NOT EXISTS` on `auth.users` / `auth.identities` to reduce duplicate errors.
- **BVM relationship IDs** use a distinct prefix pattern (`rm…`) so they are not confused with `business.id` UUIDs in demos.

## What was intentionally not added

- No specials / tap-list / commercial / analytics schema (later workers).
- No new migrations or RLS policy changes in this wave.
- No exhaustive policy matrix testing (would require role sessions and integration tests beyond SQL scripts).

## See also

- `database/docs/SQL_DRAFTING/FIRST_TRANCHE_OVERVIEW.md` — tranche summary and continuation guidance
- `database/docs/SQL_DRAFTING/SQL_DRAFTING_NOTES.md` — implementation notes for SQL workers
