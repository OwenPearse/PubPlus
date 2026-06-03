# SQL drafting — Wave 4 (consumer private state and saved lists)

## Scope

Wave 4 adds **consumer-private** structures that attach to existing `consumer_account`, `venue`, and geography reference rows from earlier waves. Implemented in migrations **0010–0012**.

This tranche does **not** model owner/business authority, claims, permissions, specials, tap lists, or commercial overlays.

## Tables introduced

| Migration | Tables |
|-----------|--------|
| 0010 | `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings` |
| 0011 | `saved_list`, `saved_list_membership` |
| 0012 | `consumer_submission_extension`, `consumer_workflow_submission` |

## Rules preserved

- **Separate account domains**: consumer tables reference `consumer_account` only, not owner/admin role collapse (DL-007).
- **Saved venues are list-native**: memberships live under `saved_list`; no flat favorites table (DL-016).
- **Canonical venue identity**: `saved_list_membership.venue_id` and optional `consumer_workflow_submission.venue_id` reference `venue` only (DL-003).
- **Default location and notifications are first-class**: dedicated tables with explicit columns, not a generic profile JSON blob (DL-023).
- **Submissions are not truth**: truth-impacting payloads remain on `venue_change_proposal` and staging tables; Wave 4 adds optional proposal metadata and non-proposal intake rows (DL-005, Worker B).

## Implementation decisions (SQL-level)

- **`consumer_profile`**: intentionally minimal display/support identity (`display_name`, `avatar_storage_ref`). It is **not** the long-term home for broad personalization, behavioral history, or social graph data — those remain deferred per MVP-vs-deferred guidance and should land in future dedicated tables if needed.
- **Profile and preferences**: split into `consumer_profile`, `consumer_default_location_preference`, and `consumer_notification_settings` with `consumer_account_id` as primary key for 1:1 shapes.
- **Default location**: nullable `default_locality_id` and `default_geographic_region_id`; all-null means “no default” — product may set one or both.
- **Quiet hours**: `quiet_hours_start_local` / `quiet_hours_end_local` must be both set or both null; timezone interpretation is app-layer.
- **Saved lists**: `saved_list` carries `sort_order` and `is_archived`; `saved_list_membership` uses composite PK `(saved_list_id, venue_id)` and optional `position` for intra-list ordering.
- **Authenticated submissions**:
  - **`consumer_submission_extension`**: optional 1:1 with `venue_change_proposal` for consumer-only non-truth metadata; DDL does not enforce equality with `actor_consumer_account_id` (validate in app).
  - **`consumer_workflow_submission`**: standalone workflow intake (e.g. issue reports, feedback) without duplicating proposal staging payloads.

## Deferred

- Shared/collaborative lists, notes, social graph, recommendation history.
- Rich personalization, segments, marketing analytics stores, and **expanded consumer profile** beyond the minimal `consumer_profile` columns (explicitly not grown into a mega-profile on this table).
- Per-channel notification category matrices (beyond the explicit toggles here).
- RLS and Edge policies for consumer tables (explicitly deferred).
- Linking `consumer_workflow_submission` to `venue_change_proposal` when a report escalates to a formal proposal (optional FK or join table in a later migration).

## Follow-ups

- Optional composite FK from `consumer_submission_extension` to proposals where `actor_type = 'consumer'` if the team wants database-level coupling.
- Consider `timezone` column on `consumer_notification_settings` if quiet hours need unambiguous interpretation in SQL.
