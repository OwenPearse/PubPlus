# SQL drafting notes — Tranche 1 (Waves 1–4)

This file records **implementation-level** choices made while staying within locked architecture. It does not reopen planning decisions.

## Migration ordering

Migrations `0001`–`0012` apply in lexical order. Dependencies:

- Published tables reference `venue` and geography/attribute reference rows created earlier.
- Workflow tables reference account anchors from `0002`.
- `0008` depends on proposals from `0007`; `0009` depends on `proposal_review` from `0008`.
- `0010`–`0012` (Wave 4) depend on `consumer_account`, `venue`, `locality`, `geographic_region`, and `venue_change_proposal`.

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

## Wave 4 — Consumer private state (0010–0012)

- **`consumer_profile` scope**: minimal display/support fields only; do not treat this table as the future container for personalization, history, or social features (deferred per MVP guidance — add separate tables later if product requires them).
- **Split tables vs one blob**: `consumer_profile`, `consumer_default_location_preference`, and `consumer_notification_settings` are separate 1:1 tables keyed by `consumer_account_id` to keep domains explicit (Worker B / DL-023).
- **Default location nullability**: both `default_locality_id` and `default_geographic_region_id` may be null to represent “cleared”; the app decides whether one or both are required for a valid preference.
- **Quiet hours**: stored as local `time without time zone` pairs; timezone for interpretation is not in-schema in v1.
- **Push toggle**: `push_notifications_opt_in` names product push channel consent distinctly from email/SMS columns.
- **Saved lists**: list-native model only — `saved_list` + `saved_list_membership` to `venue`; optional `position` on membership for ordering; `is_archived` on lists without a separate archive table.
- **Submissions**: `venue_change_proposal` remains the spine for truth-impacting packages. `consumer_submission_extension` is optional 1:1 metadata; `consumer_workflow_submission` covers non-proposal authenticated intake. Actor alignment between extension and `actor_consumer_account_id` is enforced in application code.

## Seed scaffolding (later)

Recommended seed data (not shipped in this tranche):

- At least one `geographic_region` + `locality` for dev.
- Core `venue_attribute_definition` rows matching MVP filters.
- One `external_data_source` row for imports.

## Non-blocking review items

- Whether `day_of_week` should follow ISO-8601 Monday-first instead of US Sunday-first.
- Whether `audit_event` should be partitioned or replaced with product analytics pipeline for high volume.
- Whether `consumer_notification_settings` should add a stored IANA timezone name once quiet hours need DB-level comparisons.
