# SQL drafting — Wave 3 (workflow, moderation, provenance, publish lineage)

## Scope

Wave 3 models **raw intake**, **proposals and staging**, **Stage-2 review**, **publish lineage**, **evidence**, and a **minimal audit log**. Implemented in migrations **0007–0009**.

## Tables introduced

| Migration | Tables |
|-----------|--------|
| 0007 | `raw_venue_intake_record`, `venue_change_proposal`, `venue_proposal_target`, `venue_proposal_staging_profile`, `venue_proposal_staging_location`, `venue_proposal_staging_attribute`, `venue_proposal_staging_hours` |
| 0008 | `proposal_review`, `venue_publish_event`, `venue_published_row_history` |
| 0009 | `evidence_item`, `evidence_attachment`, `audit_event` |

## Rules preserved

- **Submission is not truth**: proposals and staging tables are workflow, not live discovery reads.
- **Stage-2 review ≠ authority verification**: `proposal_review` uses a distinct outcome vocabulary from future `venue_authority_decision` (Worker B), not included here.
- **Publish lineage ≠ proposal status**: `venue_publish_event` records formal publish/withhold/rollback narrative; current published fields still live in Wave 2 tables.
- **Evidence** stores pointers, not binary payloads.

## Implementation decisions (SQL-level)

- **`venue_change_proposal` actor resolution** (exactly one logical actor per rules) is enforced in application code; DDL includes nullable FKs plus a consistency check for `actor_type = source`.
- **`proposal_review`**: multiple rows per proposal allowed via `review_sequence` for re-review flows.
- **`audit_event`**: generic append-only log; domain-specific tables (`proposal_review`, `venue_publish_event`) remain authoritative for their domains.

## Deferred

- `venue_authority_decision`, `venue_authority_event`, claim/verification/management tables (Wave 5 tranche).
- Linking `evidence_attachment` to authority decisions (optional extension in Worker E).
- RLS policies and Edge Function publish orchestration (explicitly deferred).

## Follow-ups

- Tighten CHECK constraints once actor matrix is fully enumerated in code.
- Optional compaction job for old `raw_venue_intake_record.payload_jsonb` per retention policy.
