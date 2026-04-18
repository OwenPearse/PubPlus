# SQL drafting — Wave 6 (RLS and permission guardrails)

## Scope

Wave 6 adds **Row Level Security policies** and minimal **SECURITY INVOKER** helper functions so the Supabase Data API respects locked domain boundaries. Implemented in migrations **0017–0020**.

This tranche is **guardrails only**: it does not introduce new product tables, specials/tap-list logic, subscriptions, or a fine-grained ACL matrix.

### Helper functions (discipline for later workers)

Wave 6 keeps the helper layer **small**: account-resolution helpers (`current_*_account_id`, `is_admin_session`) plus **`owner_is_member_of_business(uuid)`** for repeated membership predicates. That posture is intentional.

**Later workers should not grow a sprawling helper-function system** around RLS unless it becomes **clearly necessary** (for example, duplicated predicates across many migrations that are hard to audit, or a single well-bounded primitive that reduces policy bugs). Prefer **readable inline policy conditions** or **small, explicit additions** over a parallel policy DSL built from many SQL functions.

## Migrations

| Migration | Focus |
|-----------|--------|
| `0017_rls_public_truth_reads.sql` | Published discovery truth + geography reference + `external_data_source` catalog: **public `SELECT`** for `anon` + `authenticated`; **no client `INSERT`/`UPDATE`/`DELETE`** (deny by default). |
| `0018_rls_consumer_private_state.sql` | Consumer account + profile + prefs + saved lists + consumer submissions + **consumer-actor** proposals and staging: **self-scoped** reads/writes; `authenticated` only (not `anon`). |
| `0019_rls_owner_business_authority.sql` | Owner account + business/membership + managed-venue chain + claim/verification/rights/grants + authority snapshots: **relationship-scoped** reads; **owner-actor** proposals and staging; optional **minimal** `venue_claim_request` insert/update for initiator + member business. |
| `0020_rls_workflow_audit_admin_boundaries.sql` | Raw intake, Stage-2 review, publish lineage, evidence, audit, and **admin `SELECT`** over proposals/staging/authority/business rows; consumer-private tables stay **without** admin read policies in v1. |

## Policy groups (by table)

### Public published truth (`0017`)

RLS enabled with a single **public read** policy per table for `anon` and `authenticated`:

- `venue`, `geographic_region`, `locality`
- `venue_published_location`, `venue_published_map_point`
- `venue_published_profile`, `venue_published_descriptive_copy`
- `venue_attribute_definition`, `venue_attribute_allowed_value`, `venue_published_attribute_value`
- `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty`, `venue_derived_operational_claim`
- `external_data_source`

**Writes:** no policies for `INSERT`/`UPDATE`/`DELETE` → clients cannot mutate published truth through normal roles; **publish** remains **service_role / backend** only.

### Consumer private + consumer workflow inputs (`0018`)

- **Helpers:** `current_consumer_account_id()`
- **Self-scoped:** `consumer_account` (select own row), `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings`, `saved_list`, `saved_list_membership`, `consumer_submission_extension`, `consumer_workflow_submission`
- **Consumer proposals:** `venue_change_proposal` where `actor_consumer_account_id` matches; `venue_proposal_target` and all `venue_proposal_staging_*` tables tied to those proposals
- **Deletes** on proposals limited to `lifecycle_status in ('staged','withdrawn')` for the consumer actor policy

### Owner / business authority (`0019`)

- **Helpers:** `current_owner_account_id()`, `owner_is_member_of_business(uuid)`
- **Self / membership:** `owner_account` (select self), `owner_business_membership` (select; update own row only)
- **Business + chain:** `business` (select where non-removed membership), `business_venue_management_relationship`, `venue_claim_request`, `venue_verification_state`, `venue_management_rights`, `venue_capability_grant` (grantee + relationship visibility), `venue_authority_decision`, `venue_authority_event`
- **Owner proposals:** `venue_change_proposal` and staging tables for `actor_owner_account_id` matches; delete limited same as consumer policy

### Workflow, audit, admin reads (`0020`)

- **Helpers:** `current_admin_account_id()`, `is_admin_session()`
- **Deny-by-default with admin read:** `raw_venue_intake_record`, `proposal_review`, `venue_publish_event`, `venue_published_row_history`, `evidence_item`, `evidence_attachment`, `audit_event`
- **Admin visibility:** `venue_change_proposal`, `venue_proposal_target`, all `venue_proposal_staging_*` (select only — admin writes still expected via **service_role** / trusted backend)
- **Admin read on authority/org rows:** `business`, `owner_business_membership`, `business_venue_management_relationship`, `venue_claim_request`, `venue_verification_state`, `venue_management_rights`, `venue_capability_grant`, `venue_authority_decision`, `venue_authority_event`, `owner_account`
- **`admin_account`:** select own row

## Intentionally denied by default

- **Published truth:** any direct client write to published-truth tables.
- **Raw intake, evidence, audit, publish lineage:** no `anon` access; `authenticated` only via **admin** policies where provided — otherwise **deny**.
- **Consumer private:** no `anon` access; no cross-user access; **no admin read policies** in v1 (support flows use **service_role** or a later dedicated tranche).
- **Cross-domain shortcuts:** no policy grants venue access from login alone; owner visibility flows through **membership → business → managed-venue** predicates (plus grant visibility rules on `venue_capability_grant`).

## Backend / service_role expectations

- **Supabase `service_role`** bypasses RLS — use for publish workflows, raw ingestion, evidence/audit append, and any automation that must not be expressible as client-safe policies.
- **Stage-2 reviews, publish events, authority decisions that change system state:** client-side admin UIs should either use **service_role** only on the server or call Edge Functions — **no** broad admin `UPDATE`/`INSERT` policies were added in Wave 6.

## Deliberately deferred

- **Specials / tap lists / commercial overlays:** tables not in schema v1 — **no** RLS here (TODO when those waves land).
- **Per-capability write matrix** (e.g. mapping `venue_capability_grant` to proposal edits): still **application/service**; RLS stays coarse.
- **Admin read paths to consumer private data** (GDPR/support): policy design deferred — use **service_role** with audited app logic until requirements are explicit.
- **RLS on views / `security_invoker` views:** not introduced in this tranche.
- **Consumer `INSERT` into `consumer_account`:** still expected from **service_role** / signup path — no client insert policy.

## Rules preserved (non-negotiables)

- **No direct write path into published truth** from normal client contexts.
- **Submission / workflow / history are not live authority** — policies allow consumer/owner **staging** only where modeled; published tables remain read-only for clients.
- **Separate account domains** — consumer, owner, and admin policies do not merge into one generic role.
- **No claim / verification / membership shortcut to venue power** — `venue_capability_grant` remains relationship-scoped; membership alone does not unlock venue rows without the predicate patterns above.
