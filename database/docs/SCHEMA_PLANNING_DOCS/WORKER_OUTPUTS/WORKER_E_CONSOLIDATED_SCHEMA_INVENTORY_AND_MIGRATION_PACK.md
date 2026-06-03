# Worker E — Consolidated Schema Inventory and Migration Pack

**Role:** Worker E — Consolidated Schema Inventory and Migration Pack for PubPlus  
**Reports to:** Database Manager  
**Status:** Pre-SQL implementation inventory (no production SQL, no migrations, no Supabase code, no RLS, no triggers, no functions)  
**Inputs:** Locked planning docs at `database/docs/SCHEMA_PLANNING_DOCS/` (paths `LOCKED_INPUTS/` were not present in-repo; content taken from canonical files there); `WORKER_A_FOUNDATIONAL_SCHEMA_BLUEPRINT.md`, `WORKER_B_PRIVATE_STATE_AND_AUTHORITY_BACKBONE.md`, `WORKER_C_REFERENCE_DATA_AND_CONTROLLED_VOCABULARY_BLUEPRINT.md`, `WORKER_D_BOUNDARY_AND_CLASSIFICATION_BLUEPRINT.md`; discovery stage summaries STAGE_1–5.

**Locked clarifications (honored):** Specials and tap lists are **out** of the first implementation tranche; venue-scoped permissions stay **coarse** in v1; minimum evidence metadata remains **minimal but explicit** (actor type and identity, source/channel, created/submitted timestamp, affected object/family, proposal type, reason/evidence-basis reference, review/decision timestamps, reviewer/admin identity where applicable).

---

## Confirmed understanding

Architecture and domain boundaries are treated as **locked** per `decision_log.md`, `non_negotiable_rules_for_schema_workers.md`, `domain_boundary_map.md`, `consolidated_entity_map.md`, `relationship_authority_blueprint.md`, `state_lifecycle_model_summary.md`, `mvp_vs_deferred_scope_map.md`, and `recommended_migration_schema_build_order.md`.

This document **synthesizes** Workers A–D into one near-final table inventory. It **does not** explore new architecture, **does not** redesign prior workers, and **does not** collapse public truth, workflow, private consumer state, authority, or deferred commercial/specials/tap domains.

**Canonical anchor:** `venue` (canonical venue identity) remains the anchor for venue-linked published truth, workflow, saved-list references, and business–venue management relationships.

**Preserved authority families (distinct):** claim initiation (`venue_claim_request`), verification (`venue_verification_state`), management rights (`venue_management_rights`), coarse capability grants (`venue_capability_grant`).

**Preserved workflow families (distinct):** proposal lifecycle (`venue_change_proposal` + staging), Stage-2 public-truth review (`proposal_review`), publish lineage (`venue_publish_event`), authority-side decisions and history (`venue_authority_decision`, `venue_authority_event`).

**Read-path rule (unchanged):** live discovery reads **published** current-state tables (+ reference joins), not proposals or staging rows.

---

## Consolidated table inventory

Convention: **FK direction** is stated as **child → parent**. Categories: **current-state**, **workflow**, **history/lineage/audit**, **reference**, **bridge/junction**.  
**Status:** **Build now** = first implementation tranche (waves 1–5 below), excluding explicitly deferred domains. **Plan now / build later** = optional pattern, extension, or deferred wave.

| Proposed name | Domain | Wave | Category | Purpose | Primary anchor / FK direction | Status | Name notes |
|--------------|--------|------|------------|---------|-------------------------------|--------|------------|
| `venue` | Venue / public truth | 1 | current-state | Durable source-agnostic canonical venue identity; one row per real venue at one physical location | Root anchor | Build now | **Strong provisional** |
| `consumer_account` | Consumer private / anchors | 1 | current-state | Logical consumer domain identity; links to auth subject | External auth subject | Build now | **Strong provisional** |
| `owner_account` | Owner / authority | 1 | current-state | Logical owner portal identity | External auth subject | Build now | **Strong provisional** |
| `admin_account` | Admin / trust | 1 | current-state | Internal reviewer/admin identity | External auth subject | Build now | **Strong provisional** |
| `business` | Owner / business | 1 | current-state | First-class operator entity; primary future commercial attachment | Root anchor | Build now | **Strong provisional** |
| `geographic_region` | Geography | 1 | reference | Hierarchy node for geography (country/state/region; self-parent optional) | Optional self-FK `parent_region_id` | Build now | **Strong provisional** |
| `locality` | Geography | 1 | reference | Canonical suburb/locality for search, grouping, display | → `geographic_region` | Build now | **Strong provisional** |
| `external_data_source` | Provenance / reference | 1 | reference | Registry of import/API sources for intake and provenance | Root | Build now | **Strong provisional** |
| `venue_attribute_definition` | Discovery / reference | 1 | reference | Controlled attribute families/keys for structured discovery | Root | Build now | **Strong provisional** |
| `venue_attribute_allowed_value` | Discovery / reference | 1 | reference | Optional normalized allowed values for discrete attributes | → `venue_attribute_definition` | Plan now / build later | **Flexible** — optional split per Worker A/C |
| `venue_published_profile` | Venue / public truth | 2 | current-state | Published public profile: name, slug/display ids, high-level discovery/operational status | → `venue` | Build now | **Strong provisional** |
| `venue_published_location` | Geography | 2 | current-state | Single coherent published structured address | → `venue`; → `locality` | Build now | **Strong provisional** |
| `venue_published_map_point` | Geography | 2 | current-state | Exactly one authoritative published map point per venue | → `venue` (1:1) | Build now | **Strong provisional** |
| `venue_published_attribute_value` | Discovery | 2 | current-state | Published structured attribute assignments | → `venue`; → `venue_attribute_definition` | Build now | **Strong provisional** |
| `venue_published_descriptive_copy` | Venue / public truth | 2 | current-state | Low-risk narrative/marketing copy separate from structured discovery drivers | → `venue` | Build now | **Flexible** — optional if product folds into profile with clear non-discovery rules |
| `venue_hours_regular` | Hours | 2 | current-state | Baseline weekly hours pattern | → `venue` | Build now | **Strong provisional** |
| `venue_hours_exception` | Hours | 2 | current-state | Date-bounded overrides superseding baseline | → `venue` | Build now | **Strong provisional** |
| `venue_hours_uncertainty` | Hours | 2 | current-state | Explicit uncertainty/strength; unknown ≠ closed; weak ≠ open-now | → `venue` | Build now | **Strong provisional** |
| `venue_derived_operational_claim` | Hours / operational | 2 | current-state | Derived present-tense claims (e.g. open-now eligibility/strength) | → `venue` | Build now | **Strong provisional** (implementation: materialized vs computed — see choices) |
| `raw_venue_intake_record` | Workflow / intake | 3 | workflow | Raw or semi-structured source payloads and capture metadata | → `external_data_source`; optional → `venue` | Build now | **Strong provisional** |
| `venue_change_proposal` | Workflow | 3 | workflow | Submission header: hybrid whole-record / field-family; actor, channel, lifecycle | → `venue`; nullable actor FKs per rules | Build now | **Strong provisional** |
| `venue_proposal_target` | Workflow | 3 | bridge/junction | Which truth families this proposal touches | → `venue_change_proposal` | Build now | **Strong provisional** |
| `venue_proposal_staging_profile` | Workflow | 3 | workflow | Staged non-published profile candidates | → `venue_change_proposal`; → `venue` | Build now | **Strong provisional** |
| `venue_proposal_staging_location` | Workflow | 3 | workflow | Staged geo candidates | → `venue_change_proposal`; → `venue` | Build now | **Strong provisional** |
| `venue_proposal_staging_attribute` | Workflow | 3 | workflow | Staged attribute assignments | → `venue_change_proposal`; → `venue` | Build now | **Strong provisional** |
| `venue_proposal_staging_hours` | Workflow | 3 | workflow | Staged hours packages | → `venue_change_proposal`; → `venue` | Build now | **Strong provisional** |
| `proposal_review` | Workflow / moderation | 3 | workflow | Stage-2 decision on public-truth package; reviewer, timestamps, reason/evidence basis | → `venue_change_proposal`; → `admin_account` | Build now | **Strong provisional** |
| `evidence_item` | Provenance | 3 | workflow | Durable evidence pointer (kind, external ref); not blob store | Optional standalone | Build now | **Strong provisional** |
| `evidence_attachment` | Provenance | 3 | bridge/junction | Links evidence to proposal and/or review | → `evidence_item`; → proposal/review targets | Build now | **Strong provisional** |
| `venue_publish_event` | Publish lineage | 3 | history/lineage/audit | Publish/withhold/rollback narrative; supersedes chain | → `venue`; optional → proposal/review; self-FK supersedes | Build now | **Strong provisional** |
| `venue_published_row_history` | Publish lineage | 3 | history/lineage/audit | Optional append-only prior versions or per-family snapshots | → `venue`; → `venue_publish_event` | Plan now / build later | **Flexible** — pattern choice |
| `consumer_profile` | Consumer private | 4 | current-state | Minimal display identity for app | → `consumer_account` | Build now | **Strong provisional** |
| `consumer_default_location_preference` | Consumer private | 4 | current-state | Structured default location for UX | → `consumer_account`; → `locality` and/or `geographic_region` | Build now | **Strong provisional** |
| `consumer_notification_settings` | Consumer private | 4 | current-state | Structured notification and consent (explicit columns or narrow rows) | → `consumer_account` (1:1) | Build now | **Strong provisional** |
| `saved_list` | Saved lists | 4 | current-state | User-owned named list/folder | → `consumer_account` | Build now | **Strong provisional** |
| `saved_list_membership` | Saved lists | 4 | bridge/junction | List ↔ canonical venue | → `saved_list`; → `venue` | Build now | **Strong provisional** |
| `consumer_submission_extension` | Consumer / workflow | 4 | workflow (+ bridge) | Optional thin 1:1 extension on proposal for consumer-only non-truth metadata | → `venue_change_proposal`; → `consumer_account` | Plan now / build later | **Flexible** — omit if unused |
| `owner_business_membership` | Owner / business | 5 | bridge/junction | Owner user ↔ business membership lifecycle | → `owner_account`; → `business` | Build now | **Strong provisional** |
| `business_venue_management_relationship` | Authority | 5 | current-state (+ lifecycle) | Core business ↔ venue management link; may be in-flight or approved/active | → `business`; → `venue` | Build now | **Strong provisional** |
| `venue_management_rights` | Authority | 5 | current-state | Current management-rights posture on relationship | → `business_venue_management_relationship` (1:1) | Build now | **Strong provisional** |
| `venue_claim_request` | Authority | 5 | workflow | Claim initiation only | → `venue`; → `business` and/or initiator per rules | Build now | **Strong provisional** |
| `venue_verification_state` | Authority | 5 | current-state | Current verification outcome (distinct from Stage-2 review) | → relationship and/or claim per SQL choice | Build now | **Strong provisional** |
| `venue_capability_grant` | Authority | 5 | current-state + bridge/junction | Coarse capabilities for owner user through management relationship | → `business_venue_management_relationship`; → `owner_account` | Build now | **Strong provisional** |
| `venue_authority_decision` | Authority / audit | 5 | workflow (+ audit character) | Admin decisions on authority matters; minimum evidence metadata | → `admin_account`; → claim/relationship/verification targets | Build now | **Strong provisional** |
| `venue_authority_event` | Authority / audit | 5 | history/lineage/audit | Append-only authority transitions | → anchors as needed (`venue`, `business`, relationship, claim, etc.) | Build now | **Strong provisional** |

**Enum / check families (Worker C):** Not separate physical tables in this inventory; they are **reference semantics** embedded on the tables above (actor type, channel, proposal lifecycle, review outcome, publish event kind, hours uncertainty, relationship statuses, capability codes, etc.). SQL workers attach them via CHECK/enum or tiny lookup tables per [Remaining implementation choices](#remaining-implementation-choices).

---

## Migration wave table map

Waves align with `recommended_migration_schema_build_order.md` and Worker D’s category discipline. **Do not** place specials or tap-list tables in these waves for the first tranche.

### Wave 1 — Anchors and reference spine

**Purpose:** Stable FK targets before truth rows and write paths.

- `venue`
- `consumer_account`, `owner_account`, `admin_account`, `business`
- `geographic_region`, `locality`
- `external_data_source`
- `venue_attribute_definition`
- Optional: `venue_attribute_allowed_value`

### Wave 2 — Published current-state truth

**Purpose:** MVP search-first read models for public discovery.

- `venue_published_profile`
- `venue_published_location`, `venue_published_map_point`
- `venue_published_attribute_value`, `venue_published_descriptive_copy` (if used)
- `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty`, `venue_derived_operational_claim`

### Wave 3 — Workflow, provenance, publish lineage

**Purpose:** Safe change pipeline after published targets exist; evidence and lineage explicit.

- `raw_venue_intake_record`
- `venue_change_proposal`, `venue_proposal_target`
- `venue_proposal_staging_profile`, `venue_proposal_staging_location`, `venue_proposal_staging_attribute`, `venue_proposal_staging_hours`
- `evidence_item`, `evidence_attachment`
- `proposal_review`
- `venue_publish_event`
- Optional: `venue_published_row_history`

### Wave 4 — Consumer private state

**Purpose:** Private UX and list-native saved state; depends on `consumer_account`, `venue`, geography reference.

- `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings`
- `saved_list`, `saved_list_membership`
- Optional: `consumer_submission_extension` (after `venue_change_proposal` exists)

**Note:** Consumer and owner **submissions** to public truth remain **`venue_change_proposal`** (Wave 3); Wave 4 does not introduce a parallel truth submission table.

### Wave 5 — Authority backbone

**Purpose:** Owner–business–venue chain, current rights, coarse grants, authority decisions/history — separate from Stage-2 publish reviews.

- `owner_business_membership`
- `business_venue_management_relationship`, `venue_management_rights`
- `venue_claim_request`, `venue_verification_state`
- `venue_capability_grant`
- `venue_authority_decision`, `venue_authority_event`

### Deferred waves (planned, not first tranche)

| Deferred wave (conceptual) | Content |
|----------------------------|---------|
| Structured specials / promotions | Recurring vs one-off, timing/eligibility layers — per Stage 5 / MVP deferral |
| Tap list | Product/brewery/style references; venue offering state — per Stage 5 / MVP deferral |
| Commercial / subscription adjacency | Business-level subscription attachment, venue overlays, sponsorship adjacency — shallow planning only until needed |
| Advanced trust / fraud | Rich verification cycles, scoring — explicitly deferred |

---

## Domain-by-domain inventory

### Venue / public truth

| Table | Wave | Category |
|-------|------|----------|
| `venue` | 1 | current-state |
| `venue_published_profile` | 2 | current-state |
| `venue_published_descriptive_copy` | 2 | current-state |

### Geography

| Table | Wave | Category |
|-------|------|----------|
| `geographic_region`, `locality` | 1 | reference |
| `venue_published_location`, `venue_published_map_point` | 2 | current-state |
| Staging: `venue_proposal_staging_location` | 3 | workflow |

### Discovery attributes

| Table | Wave | Category |
|-------|------|----------|
| `venue_attribute_definition` (+ optional `venue_attribute_allowed_value`) | 1 | reference |
| `venue_published_attribute_value` | 2 | current-state |
| `venue_proposal_staging_attribute` | 3 | workflow |

### Hours

| Table | Wave | Category |
|-------|------|----------|
| `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty` | 2 | current-state |
| `venue_derived_operational_claim` | 2 | current-state |
| `venue_proposal_staging_hours` | 3 | workflow |

### Workflow / moderation

| Table | Wave | Category |
|-------|------|----------|
| `raw_venue_intake_record` | 3 | workflow |
| `venue_change_proposal`, `venue_proposal_target`, staging `_*` | 3 | workflow / bridge |
| `proposal_review` | 3 | workflow |
| `venue_claim_request` | 5 | workflow |
| `consumer_submission_extension` (optional) | 4 | workflow |

### Provenance / evidence / audit

| Table | Wave | Category |
|-------|------|----------|
| `external_data_source` | 1 | reference |
| `evidence_item`, `evidence_attachment` | 3 | workflow / bridge |
| `venue_publish_event` | 3 | history/lineage/audit |
| `venue_published_row_history` (optional) | 3 | history/lineage/audit |
| `venue_authority_decision` | 5 | workflow (+ audit) |
| `venue_authority_event` | 5 | history/lineage/audit |

### Consumer private state

| Table | Wave | Category |
|-------|------|----------|
| `consumer_account` | 1 | current-state |
| `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings` | 4 | current-state |

### Saved lists

| Table | Wave | Category |
|-------|------|----------|
| `saved_list` | 4 | current-state |
| `saved_list_membership` | 4 | bridge/junction |

### Owner / business / authority

| Table | Wave | Category |
|-------|------|----------|
| `owner_account`, `business` | 1 | current-state |
| `owner_business_membership` | 5 | bridge/junction |
| `business_venue_management_relationship` | 5 | current-state (+ lifecycle) |
| `venue_management_rights`, `venue_verification_state` | 5 | current-state |
| `venue_capability_grant` | 5 | current-state + bridge/junction |
| `admin_account` | 1 | current-state |

### Reference data (physical tables)

| Table | Wave | Category |
|-------|------|----------|
| `geographic_region`, `locality`, `external_data_source`, `venue_attribute_definition` (+ optional allowed values) | 1 | reference |

### Bridges

| Table | Wave | Category |
|-------|------|----------|
| `venue_proposal_target` | 3 | bridge/junction |
| `evidence_attachment` | 3 | bridge/junction |
| `saved_list_membership` | 4 | bridge/junction |
| `owner_business_membership` | 5 | bridge/junction |
| `venue_capability_grant` | 5 | bridge/junction (current-state entitlements) |

---

## Category map

### current-state

`venue`; `consumer_account`, `owner_account`, `admin_account`, `business`; `venue_published_profile`, `venue_published_location`, `venue_published_map_point`, `venue_published_attribute_value`, `venue_published_descriptive_copy`; `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty`, `venue_derived_operational_claim`; `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings`, `saved_list`; `business_venue_management_relationship`; `venue_management_rights`, `venue_verification_state`, `venue_capability_grant`.

### workflow

`raw_venue_intake_record`; `venue_change_proposal`; `venue_proposal_staging_profile`, `venue_proposal_staging_location`, `venue_proposal_staging_attribute`, `venue_proposal_staging_hours`; `proposal_review`; `venue_claim_request`; `venue_authority_decision` (decision record); optional `consumer_submission_extension`.

### history/lineage/audit

`venue_publish_event`; optional `venue_published_row_history`; `venue_authority_event`.

### reference

`geographic_region`, `locality`, `external_data_source`, `venue_attribute_definition`, optional `venue_attribute_allowed_value`; plus **constrained vocabularies** on operational tables per Worker C (not separate rows in this map unless promoted to lookup tables).

### bridge/junction

`venue_proposal_target`; `evidence_attachment`; `saved_list_membership`; `owner_business_membership`; `venue_capability_grant` (bridge-like current-state).

---

## Strong provisional names vs flexible names

### Strong provisional names (treat as stable for SQL drafting unless project convention forces plural/prefix)

- Identity and anchors: `venue`, `consumer_account`, `owner_account`, `admin_account`, `business`
- Geography reference: `geographic_region`, `locality`
- Published venue/geo/discovery: `venue_published_profile`, `venue_published_location`, `venue_published_map_point`, `venue_published_attribute_value`
- Hours stack: `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty`, `venue_derived_operational_claim`
- Workflow core: `venue_change_proposal`, `venue_proposal_target`, `proposal_review`, `venue_publish_event`
- Staging family: `venue_proposal_staging_profile`, `venue_proposal_staging_location`, `venue_proposal_staging_attribute`, `venue_proposal_staging_hours`
- Evidence: `evidence_item`, `evidence_attachment`
- Intake: `raw_venue_intake_record`, `external_data_source`
- Discovery reference: `venue_attribute_definition`
- Consumer private: `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings`, `saved_list`, `saved_list_membership`
- Authority: `owner_business_membership`, `business_venue_management_relationship`, `venue_management_rights`, `venue_claim_request`, `venue_verification_state`, `venue_capability_grant`, `venue_authority_decision`, `venue_authority_event`

### Flexible names (SQL workers may rename without changing architecture if semantics preserved)

- `venue_published_descriptive_copy` — could merge with profile table if non-discovery rules stay strict
- `venue_published_row_history` — optional; alternative snapshot table naming
- `consumer_submission_extension` — optional; may be omitted entirely
- `venue_attribute_allowed_value` — optional companion to attribute definitions
- Pluralization / schema prefixes (`pub_`, `core_`) — cosmetic per repo standards

---

## Remaining implementation choices

Open **only** at SQL/detail level; architecture remains closed.

1. **Row-level history vs snapshot history** for published truth: `venue_published_row_history` vs family snapshots keyed by `venue_publish_event` — both preserve lineage (DL-011, DL-012).
2. **Materialized vs computed** `venue_derived_operational_claim`: conceptual separation from baseline/exception/uncertainty is mandatory; storage strategy is optional.
3. **Fold vs split** `venue_hours_uncertainty`: may be columns on regular/exception tables if uncertainty remains explicit and separable from derived claims.
4. **Enum/CHECK vs tiny lookup table** for: coarse `venue_capability_grant` codes, proposal lifecycle, publish event kind, relationship statuses — promote to lookup when admin-editable taxonomies are required.
5. **Optional** `venue_attribute_allowed_value` table vs enum-per-definition — choose based on MVP filter set and migration ergonomics.
6. **`venue_verification_state` FK strategy**: attach primarily to `business_venue_management_relationship` vs `venue_claim_request` during overlapping lifecycles — must yield **one clear current-state read path** (Worker B).
7. **Nullable FK matrix** on `venue_change_proposal` for multi-type actors (`consumer_account`, `owner_account`, `admin_account`, source linkage) — must satisfy minimum evidence metadata and one resolved actor per submission.
8. **`consumer_notification_settings`**: single wide row vs narrow per-channel rows — must stay structured, not an opaque JSON blob (DL-017).
9. **`business_venue_management_relationship`**: single table with status column vs split requested/approved — implementation convenience only; status discipline remains mandatory (Worker D).
10. **Evidence attachment to authority decisions**: whether `evidence_attachment` also links to `venue_authority_decision` at SQL time — optional extension of the same evidence pattern.

---

## Deferred inventory

**Intentionally deferred from first implementation tranche** (planning hooks only; do not build detailed tables in waves 1–5):

| Domain | Plan-but-defer |
|--------|----------------|
| Structured specials / promotions | Recurring vs one-off structures; eligibility tiers; descriptive vs structured copy — DL-025–DL-028 |
| Tap list | Product identity vs venue offering state; brewery/style references — DL-029 |
| Commercial / subscription | Business-level plans, venue overlays, sponsorship/boost adjacency — DL-024, DL-030; MVP map defers detail |
| Advanced verification / trust | Fraud scoring, rich re-verification — MVP map |
| Rich consumer profile / social lists | Per MVP map “extension-ready only” |
| Deep owner-private operational data | Broad portal internals — deferred |
| Deep permission matrix | Coarse capabilities only in v1 — MVP map |
| Rich geo internationalization | Sub-locality / address formats beyond MVP geography |

---

## Risks

1. **Direct writes to `venue_published_*` or hours tables** bypassing formal publish workflow — violates DL-008.
2. **Reading proposals or staging as live discovery truth** — violates DL-001, DL-009.
3. **Multiple published map points or competing addresses** — violates DL-004.
4. **Collapsing unknown hours into closed or weak hours into open-now** — violates DL-006.
5. **Reusing Stage-2 `proposal_review` vocabulary for authority verification** — blurs Worker B/C boundaries; permission and audit bugs.
6. **Deriving live `venue_capability_grant` or rights from `venue_authority_event` or old `venue_claim_request`** — violates DL-022.
7. **Treating `business_venue_management_relationship` as authority without status discipline** — access while still “under review.”
8. **JSON blobs for discovery attributes or permissions** — undermines structured discovery (DL-005) and coarse capability clarity.
9. **Premature specials/tap migrations** — couples schema before core boundaries stable; out of first tranche per scope.
10. **Flattening saved venues to a favorites flag** — violates DL-016.

---

## Dependencies

- **Auth provider:** stable subject identifiers for `consumer_account`, `owner_account`, `admin_account`.
- **Worker A workflow stack:** Waves 4–5 consumer and authority tables assume `venue`, geography reference, and `venue_change_proposal` / review / publish / evidence patterns exist or ship in dependency order.
- **Object storage or URL policy:** for `evidence_item` payloads (pointer-only in DB).
- **Seeding:** `geographic_region`, `locality`, `venue_attribute_definition`, `external_data_source` require initial data strategy.
- **Deferred domains:** specials, tap, commercial detail depend on stable published truth + workflow + authority boundaries from waves 1–5.

---

## Decisions requiring approval

**None identified.** No blocker contradictions found between locked planning docs and Workers A–D syntheses.

There are **no approval items** pending from this pack. Optional implementation choices listed above are for SQL workers and the Database Manager only when choosing storage patterns, not when revisiting architecture.
