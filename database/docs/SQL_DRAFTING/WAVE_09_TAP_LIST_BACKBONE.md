# SQL drafting — Wave 9 (tap list backbone)

This wave adds the **published-truth** tap list model: lightweight **beverage product reference** (with optional brewery and style anchors), **venue-scoped tap offering state** separated from product identity, **offering traits** (guest / rotating / limited) on the venue side only, and **split** freshness/validity vs discovery-tier eligibility. It does **not** add workflow/staging objects, inventory, pricing, supplier links, specials coupling, or commercial overlays.

> **Planning alignment:** `recommended_migration_schema_build_order.md` lists “Tap List Backbone” after structured specials; in this repo **SQL drafting Wave 8** is structured specials (`0021`–`0023`), so **tap list is Wave 9** (`0024`–`0026`).

## What this tranche covers

- **Beverage reference (`0024`):** `beverage_brewery`, `beverage_style`, `beverage_product` — global reference rows only; **no `venue_id`** on product identity (DL-029).
- **Venue tap offering (`0025`):** `venue_published_tap_offering` keyed by **`venue_id`**, optional `beverage_product_id`, **trait booleans** (`is_rotating`, `is_guest_tap`, `is_limited_run`), optional **`unstructured_line_label`** for chalkboard-style copy that is **not** structured discovery truth.
- **Freshness + tiers (`0026`):** `venue_published_tap_offering_validity` (assertion time, `freshness_signal_strength`, `availability_truth_state`, `suppress_strong_current_tap_claim`) and `venue_published_tap_offering_discovery_eligibility` (**four independent booleans** plus notes). **RLS** on all Wave 9 tables: `SELECT` for `anon` and `authenticated` only (parity with `0023`).

## Tables introduced

| Table | Role |
|--------|------|
| `beverage_brewery` | Optional producer anchor for `beverage_product`. |
| `beverage_style` | Optional style/category anchor for `beverage_product`. |
| `beverage_product` | Product identity; may reference brewery + style; **not** venue availability. |
| `venue_published_tap_offering` | Canonical venue–anchored tap line; traits + optional product link + optional unstructured label. |
| `venue_published_tap_offering_validity` | Freshness / assertion strength / suppression — **not** a single “active” bit. |
| `venue_published_tap_offering_discovery_eligibility` | Detail vs list row vs filter/search vs **strong current-tap claim** tiers. |

## Product identity vs venue offering state

- **Identity** lives in `beverage_product` (+ optional `beverage_brewery` / `beverage_style`).
- **What the venue lists as a tap line** lives in `venue_published_tap_offering`, with an **optional** FK to `beverage_product` when structured linkage exists.
- **Rotating / guest / limited** are **columns on the venue offering row** — they are not columns on `beverage_product` (non_negotiable rules 20–21).

## Validity / freshness / eligibility vs “published”

- **Catalog presence** for the line uses `catalog_record_status` on the parent (same *kind* of separation as structured specials — catalog ≠ validity ≠ tiers).
- **Freshness and conservative “current pour” posture** use `venue_published_tap_offering_validity` (including explicit **`suppress_strong_current_tap_claim`**).
- **Where the row may appear in discovery** uses `venue_published_tap_offering_discovery_eligibility`; **`safe_for_strong_current_tap_claim`** is the strongest tier and is **not** implied by row existence or by `catalog_record_status = 'active'` alone.

## Deliberately deferred

- Workflow proposals, staging payloads, and publish-lineage wiring for tap lines (reuse Wave 3 patterns when implemented).
- Deep beverage catalog (SKU matrices, batch/lot, ABV/IBU standardization, cross-source dedup engines).
- Inventory, keg-level stock, supplier/distributor, pricing, pours/redemption.
- Sponsored tap placement, boosts, subscription-gated tap features.
- Automatic derivation of eligibility tiers in SQL (materialized views, jobs) — schema supports conservative app-side rules first.

## Demo seed

`database/sql/seeds/dev_seed_demo_taps.sql` depends on `dev_seed_demo_venues.sql`. It is **not** wired into `database/supabase/seed.sql` by this wave; include it in your local composer when you want tap rows loaded.

## See also

- `database/docs/SQL_DRAFTING/SQL_DRAFTING_NOTES.md` — ordering and RLS note.
- Locked planning: `non_negotiable_rules_for_schema_workers.md` rules 19–21; `decision_log.md` DL-029.
