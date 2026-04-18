# SQL drafting notes — Tranche 1 (Waves 1–3)

This file records **implementation-level** choices made while staying within locked architecture. It does not reopen planning decisions.

## Migration ordering

Migrations `0001`–`0009` apply in lexical order. Dependencies:

- Published tables reference `venue` and geography/attribute reference rows created earlier.
- Workflow tables reference account anchors from `0002`.
- `0008` depends on proposals from `0007`; `0009` depends on `proposal_review` from `0008`.

## Enum / CHECK vs lookup tables

- **Stable, small vocabularies** (actor type, channel, proposal lifecycle, publish event kind, evidence kind, hours uncertainty) use `TEXT` + `CHECK` lists in v1.
- **Evolving or admin-editable** vocabularies use tables: `venue_attribute_allowed_value`, `external_data_source`, geography nodes.

## Publish boundary

- DDL cannot enforce “no direct writes” to published tables; **RLS + service role** must implement DL-008. Migration `0009` documents the intended posture.

## Staging hours JSON

- `venue_proposal_staging_hours.regular_hours_json` / `exceptions_json` store proposal packages before normalization. Publish workflows must validate shape and write to `venue_hours_regular` / `venue_hours_exception` / `venue_hours_uncertainty`.

## Attribute value integrity

- `venue_published_attribute_value.allowed_value_id` references `venue_attribute_allowed_value.id` only; ensuring the value belongs to the same `attribute_definition_id` as the row is left to **publish validation** (composite FK possible in a follow-up migration).

## Supabase / auth

- Account tables reference `auth.users(id)`. Migrations assume Supabase Auth is present.

## Seed scaffolding (later)

Recommended seed data (not shipped in this tranche):

- At least one `geographic_region` + `locality` for dev.
- Core `venue_attribute_definition` rows matching MVP filters.
- One `external_data_source` row for imports.

## Non-blocking review items

- Whether `day_of_week` should follow ISO-8601 Monday-first instead of US Sunday-first.
- Whether `audit_event` should be partitioned or replaced with product analytics pipeline for high volume.
