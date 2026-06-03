# SQL drafting — Wave 2 (published public discovery truth)

## Scope

Wave 2 is the **published current-state** read model for search-first discovery: profile, structured geography pins, structured attributes, hours baseline/exceptions/uncertainty, and derived operational claims. Implemented in migrations **0003–0006** (split across files per tranche layout).

## Tables introduced

| Migration | Tables |
|-----------|--------|
| 0003 | `venue_published_location`, `venue_published_map_point` |
| 0004 | `venue_published_profile`, `venue_published_descriptive_copy` |
| 0005 | `venue_published_attribute_value` |
| 0006 | `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty`, `venue_derived_operational_claim` |

## Rules preserved

- **No direct-write shortcut**: schema cannot enforce the publish pipeline in DDL alone; **RLS and service-layer discipline** must block casual updates to these tables (see `0009` comments).
- **One authoritative map point**: `venue_published_map_point.venue_id` is the primary key (1:1 with `venue`).
- **Structured discovery**: attribute values are normalized rows referencing `venue_attribute_definition` / optional `venue_attribute_allowed_value`, not opaque JSON for filter drivers.
- **Hours safety**: `venue_hours_uncertainty` is separate from `venue_derived_operational_claim`; unknown/stale enumerations are explicit.
- **Descriptive copy** is isolated from structured discovery (`venue_published_descriptive_copy`).

## Implementation decisions (locked architecture, SQL-level only)

- **Day-of-week encoding** for `venue_hours_regular.day_of_week`: `0 = Sunday` through `6 = Saturday` (document for app; change only with coordinated migration).
- **Staging hours** use JSON packages on `venue_proposal_staging_hours` while published hours stay normalized; publish jobs materialize into `venue_hours_*` tables.
- **`venue_derived_operational_claim`** is materialized with timestamps; recomputation strategy (cron vs app) is deferred.

## Deferred

- Search indexes (`pg_trgm`, full-text), PostGIS upgrades, rich international address formats.
- `venue_published_row_history` optional snapshots are defined in Wave 3 migration `0008` (lineage), not Wave 2.

## Follow-ups

- Partial unique indexes per attribute definition for single-cardinality enforcement if needed without triggers.
- Generated columns for display-only derived fields only after product locks semantics.
