# PubPlus — First SQL implementation tranche (Waves 1–6 + verification)

This document summarizes what the **first tranche** of SQL migrations (`database/supabase/migrations/0001`–`0020`) delivers, what **Wave 7 (SQL drafting)** adds on top, and how a **future worker** should continue without re-deriving architecture.

## What Waves 1–6 cover (migrations)

| Wave | Migrations (files) | What it establishes |
|------|--------------------|----------------------|
| **1** | `0001`–`0003` | Extensions placeholder; canonical `venue`; separate `consumer_account` / `owner_account` / `admin_account`; `business`; geography (`geographic_region`, `locality`) |
| **2** | `0004`–`0006` | Published profile + descriptive copy; attribute definitions + published values; published location + single map point; hours regular/exception/uncertainty + derived operational claim |
| **3** | `0007`–`0009` | `external_data_source`; raw intake; proposals + staging packages; reviews; publish events + optional row history; evidence + audit |
| **4** | `0010`–`0012` | Consumer profile + default location + notification settings (split tables); saved lists + membership; consumer submission extensions + workflow submissions |
| **5** | `0013`–`0016` | Owner↔business membership; business↔venue managed relationship; claims, verification, management rights, authority decisions/events; venue capability grants |
| **6** | `0017`–`0020` | RLS: public read for published truth; consumer self-scope; owner relationship-scope; admin read for workflow/audit; minimal `SECURITY INVOKER` helpers |

**Ordering:** migrations apply in lexical order (`0001` … `0020`). Dependencies are documented in `SQL_DRAFTING_NOTES.md`.

## What Wave 7 adds (this tranche)

Wave 7 (SQL drafting) is **verification + seeds + documentation**, not new domains:

- **Checks** under `database/sql/checks/` to validate structure, separation, and coarse RLS posture.
- **Seeds** under `database/sql/seeds/` plus `database/supabase/seed.sql` as a composed entry point.
- **Docs:** `WAVE_07_VERIFICATION_AND_SEEDS.md` (this folder), updates to `SQL_DRAFTING_NOTES.md` where needed.

## What is still deferred (by design)

Aligned with locked planning docs and MVP scope:

- **Specials / promotions / tap lists** — future schema tranche (see planning “Wave 7” product wave; do not confuse with SQL drafting Wave 7 doc title).
- **Commercial / subscriptions / billing** — not in v1 tables.
- **Rich CRM / analytics** — not modeled here.
- **Deep admin write policies** — Stage-2 / authority state changes still expected via **service_role** / trusted backends for most mutators.
- **Automated RLS integration tests** — optional follow-up (app-level tests with real JWT roles).

## How a future worker should continue

1. **Do not reinterpret** locked planning docs; treat them as constraints (`decision_log.md`, `non_negotiable_rules_for_schema_workers.md`, `domain_boundary_map.md`, `relationship_authority_blueprint.md`, `state_lifecycle_model_summary.md`, `mvp_vs_deferred_scope_map.md`, `recommended_migration_schema_build_order.md`).
2. **Before new migrations:** run the wave checks relevant to touched domains + `check_first_tranche_end_to_end.sql` on a fresh migration apply.
3. **For local UX:** prefer extending **seeds** over ad hoc manual inserts; keep seeds small and labeled as dev/demo.
4. **Next product schema waves** (when prioritized): follow `recommended_migration_schema_build_order.md` *after* this tranche — do not collapse tables that were split intentionally (claims vs verification vs grants, etc.).

## File map (quick)

- **Migrations:** `database/supabase/migrations/`
- **Checks:** `database/sql/checks/`
- **Seeds:** `database/sql/seeds/`
- **Seed entry:** `database/supabase/seed.sql`
- **Implementation notes:** `database/docs/SQL_DRAFTING/SQL_DRAFTING_NOTES.md`
