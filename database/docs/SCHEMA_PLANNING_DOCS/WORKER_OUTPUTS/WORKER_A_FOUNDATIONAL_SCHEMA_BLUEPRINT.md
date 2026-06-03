**Worker A — Foundational Schema Blueprint (Waves 1–3)**

**Role:** Worker A — Foundational Schema Blueprint for PubPlus  
**Reports to:** Database Manager  
**Status:** Pre-SQL blueprint (no migrations, no SQL, no RLS, no triggers)  
**Inputs locked:** `database/docs/SCHEMA_PLANNING_DOC/` decision and planning set (see Confirmed understanding). Workspace paths `database/docs/SCHEMA_PLANNING_DOCS/LOCKED_INPUTS/` and `Pasted text.txt` were not present; this output is based on the locked docs that exist in-repo plus the Database Manager’s implementation clarifications below.

---

# Confirmed understanding

**Architecture:** Treated as locked per `decision_log.md`, `non_negotiable_rules_for_schema_workers.md`, `domain_boundary_map.md`, `consolidated_entity_map.md`, `relationship_authority_blueprint.md`, `state_lifecycle_model_summary.md`, `mvp_vs_deferred_scope_map.md`, and `recommended_migration_schema_build_order.md`.

**Implementation clarifications (locked for this blueprint):**

- **Specials and tap lists** are **out** of the first schema wave; they follow after core public truth, workflow/moderation, consumer-private minimums, and owner/business authority backbone. This blueprint **does not** table-design those domains.
- **Venue-scoped permissions** stay **coarse** in v1: a small capability set aligned to domains (e.g. manage approved venue operational data, submit restricted changes for review, manage owner-private operational data later, manage owner-side team/business settings later). **No** deep permission matrix.
- **Minimum evidence metadata** must be explicit and minimal: actor type; actor identity; source/channel; created/submitted timestamp; affected object/family; proposal type; reason/evidence-basis reference; review/decision timestamps; reviewer/admin identity where applicable.

**In-scope waves for this document:**

| Wave | Focus |
|------|--------|
| **1** | Foundational identity and domain anchors |
| **2** | Core public discovery truth (published layer) |
| **3** | Workflow / moderation / provenance backbone |

**Explicitly out of scope for detailed table design here (dependencies only):** consumer-private feature tables (saved lists, preferences beyond anchors), full owner/business authority chain (beyond anchors needed for actors/FKs), specials, tap lists, commercial/subscription schema, advanced trust tooling.

**Principles applied:** Canonical venue identity anchors venue-linked published truth and workflow; submission is workflow input, not truth; no direct write path to published truth except formal publish; geography clean and authoritative in published truth; hours baseline, exceptions, uncertainty, and derived claims kept conceptually separable; history/lineage preserved, not destructive overwrite.

---

# Proposed table blueprint

## Per-table inventory (Waves 1–3)

Naming is migration-ready in spirit; final names may be pluralized or prefixed per project conventions.

### Wave 1 — Foundational identity and anchors

| Proposed table name | Domain | Purpose | Category | Key parent / anchor | Do **not** store here |
|---------------------|--------|---------|----------|---------------------|------------------------|
| `venue` | Canonical venue identity | Durable, source-agnostic venue anchor; single row per real customer-facing venue at one physical location | Current-state | *(root anchor)* | Published profile/geo/hours/attributes (belongs in published-truth tables); workflow payloads; owner/commercial state |
| `consumer_account` | Account anchor | Logical consumer domain identity; links to auth identity for app users | Current-state | Auth subject (external) | Public venue truth; workflow internals beyond actor reference |
| `owner_account` | Account anchor | Logical owner domain identity for portal | Current-state | Auth subject (external) | Venue published truth; coarse permissions beyond future owner-scope tables |
| `admin_account` | Account anchor | Logical admin/reviewer identity | Current-state | Auth subject (external) | Published venue fields; non-audit operational data |
| `business` | Account / org anchor | First-class operator entity; future commercial and team structure attach here | Current-state | *(root anchor)* | Venue truth; claim/verification/workflow history as live authority |
| `geographic_region` | Geography (reference) | Region/state/country (or equivalent) hierarchy node for non–hardcoded geography | Reference | Optional self-FK `parent_region_id` | Venue-specific address lines; map coordinates |
| `locality` | Geography (reference) | Canonical suburb/locality (and similar) for search, grouping, display | Reference | FK → `geographic_region` (or hierarchy pattern) | Free-text-only location truth; per-venue map points |
| `external_data_source` | Provenance (reference) | Registered import/API/source systems for intake and provenance | Reference | *(root)* | Raw payload blobs long-term (optional); prefer separate intake |

### Wave 2 — Core public discovery truth (published layer only)

| Proposed table name | Domain | Purpose | Category | Key parent / anchor | Do **not** store here |
|---------------------|--------|---------|----------|---------------------|------------------------|
| `venue_published_profile` | Published venue truth | Public-facing name, slug/display identifiers, high-level venue status for discovery (e.g. operational/discovery eligibility), presentation minimums approved for live display | Current-state | FK → `venue` | Staged proposals; raw imports; disputed/unresolved values; owner-private ops |
| `venue_published_location` | Published geography | Structured published address; FK to `locality`; single coherent published address family per venue | Current-state | FK → `venue` | Raw source addresses; proposed corrections; multiple competing addresses |
| `venue_published_map_point` | Published geography | Exactly **one** authoritative published map point per venue for live app use | Current-state | FK → `venue` (1:1) | Alternative/coordinates under review; source scrape points |
| `venue_attribute_definition` | Structured discovery (reference) | Controlled attribute keys/families used for filters, badges, grouping (e.g. amenity, style family) | Reference | *(root)* | Per-venue values |
| `venue_published_attribute_value` | Structured discovery | Resolved published attribute assignments (normalized rows: venue + definition + allowed value/enum) | Current-state | FK → `venue`, FK → `venue_attribute_definition` | Free-text discovery filters; marketing copy; workflow staging |
| `venue_published_descriptive_copy` | Published venue truth | Optional low-risk public narrative/marketing copy **separate** from structured discovery drivers | Current-state | FK → `venue` | Structured filter/badge claims; workflow proposals |
| `venue_hours_regular` | Hours | Baseline weekly hours pattern (normalized rows) | Current-state | FK → `venue` | Exceptions; uncertainty handling alone; open-now derivation |
| `venue_hours_exception` | Hours | Date-bounded overrides that supersede baseline for affected periods | Current-state | FK → `venue` | Baseline hours; permanent closure semantics without exception modeling |
| `venue_hours_uncertainty` | Hours | Explicit uncertainty/strength/partiality for hours truth (unknown ≠ closed; weak ≠ open-now) | Current-state | FK → `venue` (1:1 or 1:1 per scope if split later) | Derived “open now” boolean as sole storage of truth |
| `venue_derived_operational_claim` | Hours / operational | Narrow store for **derived** present-tense claims (e.g. open-now **eligibility** / strength), only when underlying truth supports it | Current-state | FK → `venue` | Replacement for baseline/exception tables; raw submissions |

**Note:** If product prefers fewer physical tables, `venue_hours_uncertainty` may be folded into `venue_hours_regular` / `venue_hours_exception` as explicit columns **without** collapsing uncertainty into derived claims—SQL workers must preserve conceptual separation.

### Wave 3 — Workflow, moderation, provenance

| Proposed table name | Domain | Purpose | Category | Key parent / anchor | Do **not** store here |
|---------------------|--------|---------|----------|---------------------|------------------------|
| `raw_venue_intake_record` | Raw / source | Captured raw or semi-structured source payloads and capture metadata | Workflow-adjacent (intake) | FK → `external_data_source`; optional FK → `venue` | Canonical identity definition; published truth |
| `venue_change_proposal` | Workflow | Header for a submission: whole-record and/or one or more field-family targets; carries minimum lifecycle + actor + channel + timestamps | Workflow | FK → `venue` | Resolved published values; silent truth updates |
| `venue_proposal_target` | Workflow | Bridge: which **families** (profile, geo, attributes, hours, descriptive copy, etc.) this proposal touches; supports hybrid model | Bridge | FK → `venue_change_proposal` | Full payload (use family staging tables or payload table) |
| `venue_proposal_staging_profile` | Workflow | Staged **non-published** profile fields for review | Workflow | FK → `venue_change_proposal`; FK → `venue` | Live published profile |
| `venue_proposal_staging_location` | Workflow | Staged address/locality/map **candidates** | Workflow | FK → `venue_change_proposal`; FK → `venue` | `venue_published_*` |
| `venue_proposal_staging_attribute` | Workflow | Staged attribute assignments | Workflow | FK → `venue_change_proposal`; FK → `venue` | Published attribute rows |
| `venue_proposal_staging_hours` | Workflow | Staged baseline/exception/uncertainty packages | Workflow | FK → `venue_change_proposal`; FK → `venue` | Published hours tables |
| `proposal_review` | Review / decision | Review outcome: decision, reviewer identity, decision timestamps, reason/evidence basis reference; links to proposal | Workflow / audit | FK → `venue_change_proposal`; FK → `admin_account` (reviewer) | Published truth rows |
| `evidence_item` | Provenance | Minimal durable evidence reference (pointer, kind, optional external ref) | Workflow / audit | Optional linkage via junction | Full binary storage (use object storage + pointer) |
| `evidence_attachment` | Provenance | Attach evidence to proposal and/or review decision | Bridge | FK → `evidence_item`; FK → `venue_change_proposal` and/or `proposal_review` | Redundant copies of published truth |
| `venue_publish_event` | Publish lineage | Each successful publish (or explicit withhold/rollback event): what was published, supersedes which event, ties to proposal/review context | History / lineage | FK → `venue` | Editable “current” truth by itself (current-state lives in published tables) |
| `venue_published_row_history` *(optional pattern)* | History / audit | Append-only prior versions for selected published tables **or** snapshot JSON per family per publish—pattern choice for SQL workers | History / audit | FK → `venue`; FK → `venue_publish_event` | Workflow staging |

**Actor resolution:** `venue_change_proposal` holds **actor_type** and nullable FKs to `consumer_account`, `owner_account`, `admin_account`, and/or linkage to `external_data_source` (and source record) per your actor model—exact nullable-FK pattern is for SQL workers; rule is **one** resolved actor identity per submission consistent with minimum evidence metadata.

**Specials / tap lists:** **No** tables in this wave (per locked clarification).

---

## Table grouping by domain

### Canonical venue identity

- `venue`

### Published venue truth

- `venue_published_profile`
- `venue_published_descriptive_copy` (optional but recommended separation from structured attrs)

### Geography / location

- `geographic_region`, `locality` (reference)
- `venue_published_location`
- `venue_published_map_point`
- Staging: `venue_proposal_staging_location`

### Structured discovery attributes

- `venue_attribute_definition`
- `venue_published_attribute_value`
- Staging: `venue_proposal_staging_attribute`

### Hours and exceptions

- `venue_hours_regular`
- `venue_hours_exception`
- `venue_hours_uncertainty`
- `venue_derived_operational_claim`
- Staging: `venue_proposal_staging_hours`

### Workflow / proposals

- `raw_venue_intake_record`
- `venue_change_proposal`
- `venue_proposal_target`
- `venue_proposal_staging_profile`
- Family staging tables as above

### Reviews / decisions / publish lineage

- `proposal_review`
- `venue_publish_event`
- `venue_published_row_history` (optional pattern)

### Provenance / evidence / audit

- `external_data_source`
- `evidence_item`
- `evidence_attachment`
- (Audit fields on `proposal_review` and `venue_publish_event` are mandatory minimums; optional generic `audit_event` is **not** required if decision records stay explicit.)

### Account-domain anchors needed now

- `consumer_account`, `owner_account`, `admin_account`, `business`

---

# Relationship spine

**Convention:** Arrows read as **child → parent** (FK direction SQL workers should preserve).

## Canonical venue anchor

- `venue_published_profile` → `venue`
- `venue_published_location` → `venue`
- `venue_published_map_point` → `venue`
- `venue_published_attribute_value` → `venue`
- `venue_published_descriptive_copy` → `venue`
- `venue_hours_regular` → `venue`
- `venue_hours_exception` → `venue`
- `venue_hours_uncertainty` → `venue`
- `venue_derived_operational_claim` → `venue`

## Published truth family relationships

- `venue_published_location` → `locality`
- `venue_published_attribute_value` → `venue_attribute_definition`
- `locality` → `geographic_region` (or equivalent hierarchy)

## Workflow lineage relationships

- `raw_venue_intake_record` → `external_data_source`; optional → `venue`
- `venue_change_proposal` → `venue`
- `venue_proposal_target` → `venue_change_proposal`
- `venue_proposal_staging_*` → `venue_change_proposal` and → `venue`
- `proposal_review` → `venue_change_proposal`; `proposal_review` → `admin_account` (reviewer)
- `venue_publish_event` → `venue`; optional → `venue_change_proposal` / `proposal_review` for traceability; **self-FK** `supersedes_publish_event_id` for ordering/rollback narrative
- `venue_published_row_history` (if used) → `venue`, → `venue_publish_event`

## Evidence / provenance attachment

- `evidence_attachment` → `evidence_item`
- `evidence_attachment` → `venue_change_proposal` and/or `proposal_review`

## Account anchor relationships (minimal, now)

- `venue_change_proposal` → nullable `consumer_account` / `owner_account` / `admin_account` (per actor_type rules)
- `proposal_review` → `admin_account`

**Downstream (not designed here):** `business` ↔ `owner_account` membership; `business` ↔ `venue` managed relationship; coarse `venue_management_capability_grant`—only alluded for future FK targets.

---

# Current-state vs workflow split

| Category | Tables |
|----------|--------|
| **Current-state operational read (published)** | `venue_published_profile`, `venue_published_location`, `venue_published_map_point`, `venue_published_attribute_value`, `venue_published_descriptive_copy`, `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty`, `venue_derived_operational_claim` |
| **Current-state identity / anchors** | `venue`, `consumer_account`, `owner_account`, `admin_account`, `business` |
| **Workflow (staging, intake, review)** | `raw_venue_intake_record`, `venue_change_proposal`, `venue_proposal_target`, `venue_proposal_staging_profile`, `venue_proposal_staging_location`, `venue_proposal_staging_attribute`, `venue_proposal_staging_hours`, `proposal_review` |
| **History / lineage / audit** | `venue_publish_event`, `venue_published_row_history` (optional), evidence records as audit-support |
| **Reference** | `geographic_region`, `locality`, `venue_attribute_definition`, `external_data_source` |
| **Bridge** | `venue_proposal_target`, `evidence_attachment` |

**Read path for live app:** discovery surfaces read **published** tables (+ reference joins), not proposal or staging tables.

---

# Minimal reference-data pack

Controlled vocabularies and reference rows recommended **from the start** (Waves 1–3):

1. **Geography:** `geographic_region`, `locality` (seeded; supports expansion beyond a single metro without schema churn).
2. **Discovery attribute definitions:** `venue_attribute_definition` — keys, data types, allowed value enums or join to `venue_attribute_allowed_value` if SQL workers split normalization.
3. **External data sources:** `external_data_source` — registry for provenance and intake.
4. **Enumerations (CHECK or small reference tables):** proposal status (staged, in_review, approved, rejected, superseded, withdrawn); review decision type; actor_type (consumer, owner, admin, system, source); proposal_scope / **field family** (profile, geo, attributes, hours, descriptive_copy, whole_venue); hours uncertainty level; channel (app_consumer, app_owner, portal, import_batch, admin_tool).
5. **Evidence item kind** (document, url, source_record_ref, note) — minimal.

Avoid stuffing these enums undocumented in app-only constants if DB workers need queryable integrity.

---

# Migration-tranche recommendation

Staying at planning level—**suggested chunk order** within the first implementation tranche:

1. **Identity anchors:** `venue`; account anchors `consumer_account`, `owner_account`, `admin_account`, `business`; geography reference `geographic_region`, `locality`; `external_data_source`; `venue_attribute_definition` (+ allowed values if split).
2. **Published discovery truth:** `venue_published_profile`, `venue_published_location`, `venue_published_map_point`, `venue_published_attribute_value`, optional `venue_published_descriptive_copy`, hours stack + uncertainty + derived claim table.
3. **Workflow and provenance:** `raw_venue_intake_record`, `venue_change_proposal`, `venue_proposal_target`, staging tables, `evidence_item`, `evidence_attachment`, `proposal_review`, `venue_publish_event`, optional `venue_published_row_history`.

Rationale: stable anchors and reference data first; published truth second (queryable MVP); workflow third so publish path can target real tables without mixing layers in one migration.

---

# Risks

1. **Direct writes to published tables** from app/import bypassing `venue_publish_event` and review—violates DL-008; RLS later must enforce, but schema should make the wrong path obvious.
2. **Merging staging into published** or using proposal rows as read models—violates “submission is not truth.”
3. **Multiple published map points** or competing addresses—violates DL-004; enforce 1:1 `venue_published_map_point` to `venue`.
4. **Collapsing uncertainty into closed or open-now**—violates hours rules; keep `venue_hours_uncertainty` (or equivalent columns) and derived claim separate.
5. **JSON blobs for published structured attributes**—convenient but undermines structured discovery and audit; prefer normalized `venue_published_attribute_value` with definitions.
6. **Omitting `venue_publish_event` / history**—rollback and lineage suffer (DL-011, DL-012).
7. **Deriving live permissions from workflow history**—violates DL-022; keep authority tables for later waves separate from `proposal_review`.
8. **Premature permission matrix**—contradicts coarse v1; use enums/capability rows later, not in this wave’s core.
9. **Introducing specials/tap tables early**—out of scope for this wave; risks coupling migrations.

---

# Dependencies

**Depends on (external to blueprint):** auth provider user IDs for account tables; object storage or URL policy for `evidence_item` payloads.

**Downstream waves (not table-designed here):**

- **Consumer-private minimums:** saved lists, default location, notification settings, consumer submissions—require `consumer_account`, `venue`, and workflow tables from this blueprint.
- **Owner/business authority backbone:** business↔owner membership, business↔venue management relationship, claim/verification/management rights/coarse capabilities—require `business`, `owner_account`, `venue`; separate from workflow history.
- **Specials / tap lists / commercial:** per locked ordering, after foundational truth and workflow patterns exist.

---

# Decisions requiring approval

**Open questions (true blockers):** None.

**None identified** as approval items. Open choices left to SQL workers (non-blocking): whether history is **row-level** (`venue_published_row_history`) vs **publish snapshot** blobs per event; exact nullable-FK matrix for multi-type actors on `venue_change_proposal`; whether `venue_derived_operational_claim` is materialized in DB vs computed in application layer (architecture requires **conceptual** separation in all cases).

If the Database Manager wants a strict rule on **materialized vs computed** derived operational claims, that can be decided at SQL design time without blocking this blueprint.
