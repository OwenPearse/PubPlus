# SQL drafting — Wave 8 (structured specials / promotions backbone)

This wave adds the **published-truth** structured specials / promotions model: canonical venue anchor, structured offer kinds, separation from marketing copy, recurring vs one-off subtypes, and **separate** validity/timing vs discovery-tier eligibility. It does **not** introduce workflow/staging tables, commercial overlays, tap lists, redemption, or event campaigns.

> **Planning alignment:** `recommended_migration_schema_build_order.md` lists “Structured Specials / Promotions” as a dedicated build slice; SQL drafting numbers it **Wave 8** (migrations `0021`–`0023`) after the first-tranche verification wave (`WAVE_07_*`).

## What this tranche covers

- **Structured specials backbone** (`0021`): parent table `venue_published_structured_special` keyed by `venue_id`, with `structured_kind` (`meal_special`, `drink_special`, `happy_hour`, `venue_offer`) and `schedule_class` (`recurring` | `one_off`). Adjacent **marketing copy** lives in `venue_published_structured_special_marketing_copy` (display-only narrative).
- **Recurring vs one-off** (`0022`): distinct subtype tables — `venue_published_special_recurring_pattern` (weekly local window + timezone + DOW array + local times) and `venue_published_special_one_off` (absolute `timestamptz` window). No merged “generic promo row” that hides the distinction.
- **Validity vs eligibility** (`0023`): `venue_published_structured_special_validity` holds optional absolute bounds, `validity_bounds_kind`, `timing_signal_strength`, and `suppress_due_to_weak_or_stale_timing` for conservative withholding. `venue_published_structured_special_discovery_eligibility` holds **four independent booleans**: detail, card/badge, filter/search, and active-now/ranking — **not** one omnibus “published” flag.
- **RLS** (`0023`): same posture as migration `0017` — `SELECT` for `anon` and `authenticated` on all new published-special tables; no client write policies (publish path remains service/orchestrated).

## Tables introduced

| Table | Role |
|--------|------|
| `venue_published_structured_special` | Canonical venue–anchored structured special; catalog visibility via `catalog_record_status` (not validity/tiers). |
| `venue_published_structured_special_marketing_copy` | Headline/body/terms; not a discovery driver. |
| `venue_published_special_recurring_pattern` | Recurring/pattern subtype (v1: weekly local window). |
| `venue_published_special_one_off` | One-off subtype with absolute start/end. |
| `venue_published_structured_special_validity` | Timing bounds + strength + explicit weak-timing suppression. |
| `venue_published_structured_special_discovery_eligibility` | Per-surface safety tiers including active-now/ranking. |

## Recurring vs one-off (implementation)

- Parent row carries `schedule_class` so queries and APIs can branch without inspecting nullable FKs alone.
- **Exactly one** subtype row per parent (`recurring` → pattern table, `one_off` → one-off table) is the **intended invariant**; DDL does not enforce mutual exclusivity or completeness (avoid brittle cross-table CHECKs in v1). Publish validation or a later constraint/trigger can harden this.

## Validity vs eligibility vs “published”

- **Catalog presence** is expressed on the parent (`catalog_record_status`, plus existence in published tables).
- **Valid-current** semantics use the validity table (`offer_valid_from` / `offer_valid_to`, `validity_bounds_kind`, `timing_signal_strength`) and may combine with subtype timing in application logic.
- **Discovery tiers** are explicit booleans; **active-now/ranking** is deliberately separate and must not be implied by catalog or validity alone.
- **Weak/vague timing** should set `suppress_due_to_weak_or_stale_timing` and/or downgrade tiers rather than inventing optimistic windows.

## Deliberately deferred

- Workflow proposals, staging payloads, and publish-lineage wiring for specials (reuse patterns from Wave 3 publish tables when implemented).
- Sponsored/boosted placement, subscriptions, campaigns, redemption/coupons, booking integrations.
- Tap-list / beverage product linkage.
- Rich recurrence (nth weekday of month, public-holiday rules, complex exception calendars).
- Automatic derivation of tiers in SQL (materialized views, scheduled jobs) — schema allows conservative app-side rules first.

## Demo seed

`database/sql/seeds/dev_seed_demo_specials.sql` depends on `dev_seed_demo_venues.sql`. It is **not** wired into `database/supabase/seed.sql` by this wave (path allowlist); run it manually after venues or fold it into your local seed composer when convenient.

## See also

- `database/docs/SQL_DRAFTING/SQL_DRAFTING_NOTES.md` — ordering, DOW convention, RLS note.
- Locked planning: `non_negotiable_rules_for_schema_workers.md` rules 17–19; `domain_boundary_map.md` sections 12–14.
