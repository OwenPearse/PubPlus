# Worker D — Current-State, Workflow, and History Boundary Blueprint

**Role:** Worker D — Cross-domain boundary and classification for PubPlus  
**Reports to:** Database Manager  
**Status:** Pre-SQL blueprint (no production SQL, no migrations, no Supabase code, no RLS, no triggers, no functions)  
**Inputs read:** Locked planning docs at `database/docs/SCHEMA_PLANNING_DOCS/` (including `decision_log.md`, `non_negotiable_rules_for_schema_workers.md`, `domain_boundary_map.md`, `consolidated_entity_map.md`, `relationship_authority_blueprint.md`, `state_lifecycle_model_summary.md`, `mvp_vs_deferred_scope_map.md`, `recommended_migration_schema_build_order.md`); `database/docs/AGENT_DISCOVERY_SUMMARIES/STAGE_1_SUMMARY.md` through `STAGE_5_SUMMARY.md`; `WORKER_A_FOUNDATIONAL_SCHEMA_BLUEPRINT.md`, `WORKER_B_PRIVATE_STATE_AND_AUTHORITY_BACKBONE.md`, `WORKER_C_REFERENCE_DATA_AND_CONTROLLED_VOCABULARY_BLUEPRINT.md`.

**Note:** The path `database/docs/SCHEMA_PLANNING_DOCS/LOCKED_INPUTS/` was not present in-repo; locked content was taken from the canonical files above.

---

## Confirmed understanding

This document **does not redesign** Workers A–C. It **classifies** their proposed tables (and close table families) into:

- **Current-state** — operational read models: what the live product should treat as “now” for discovery, private UX, or live authority (subject to row-level eligibility rules such as approved-only management links).
- **Workflow** — in-flight intake, proposals, staging payloads, claim initiation, and other objects that exist **before** or **outside** resolved published truth or stable live rights.
- **History / lineage / audit** — append-only or narrative-preserving records of what happened, what was decided, what superseded what; **not** interchangeable with current truth or current permissions.
- **Reference** — stable lookup / vocabulary / registry rows (geography nodes, attribute definitions, external source registry, optional allowed values, coarse capability codes if modeled as tiny tables).
- **Bridge / junction** — relationship rows that connect two or more anchors (list membership, proposal target families, evidence attachment, owner–business membership, capability grant attachment).

**Locked clarifications honored:** specials and tap lists are **out** of wave-one design (named only as deferred); venue-scoped permissions stay **coarse**; minimum evidence metadata stays **minimal but explicit** (actor type, actor identity, source/channel, timestamps, affected object/family, proposal type, reason/evidence basis reference, review/decision timestamps, reviewer/admin identity where applicable).

**Canonical anchor:** **Canonical venue identity** (`venue`) remains the anchor for venue-linked published truth, workflow, saved references, and managed-venue authority (DL-001, DL-002, consolidated entity map).

**Preserved distinctions (non-negotiable):** claim vs verification vs management rights vs capabilities; proposal lifecycle vs Stage-2 review outcome vs publish lineage; Stage-2 moderation vs authority-side decisions.

---

## Cross-domain classification inventory

For each **proposed table or tight table family** from Workers A and B, classification follows. *Why* and *must not* are explicit. Worker C’s **enum/check families** are not separate physical tables; they are summarized under [Reference and bridge map](#reference-and-bridge-map).

| Table / family | Category | Why it belongs there | What it must **not** be used as |
|----------------|----------|----------------------|----------------------------------|
| `venue` | **Current-state** (identity anchor) | Durable, source-agnostic venue root; one row per real venue at one location. | Published field values; workflow payloads; proof of ownership; import identity. |
| `consumer_account`, `owner_account`, `admin_account` | **Current-state** (account anchors) | Logical domain identities for actors; separate domains per locked architecture. | Permission store by themselves; public venue fields; merged “one user table” semantics. |
| `business` | **Current-state** (org anchor) | First-class operator entity; commercial attachment point. | Venue truth; live venue authority without `business_venue_management_relationship` chain. |
| `consumer_profile` | **Current-state** | Minimal private display state for the app. | Discovery filters; public attributes; unstructured dump for prefs that belong elsewhere. |
| `consumer_default_location_preference` | **Current-state** | Structured private default location for UX. | Canonical venue address; authoritative map point; raw location history. |
| `consumer_notification_settings` | **Current-state** | Structured notification/consent domain. | Public venue data; cross-user messaging content. |
| `saved_list` | **Current-state** | User-owned list container; private organization. | Public discovery truth; collaborative semantics (deferred). |
| `saved_list_membership` | **Bridge** (part of **current-state** private behavior) | Links lists to **canonical** `venue`. | Parallel venue identity; source-scoped IDs as keys; duplicate “favorites-only” truth. |
| `venue_published_profile` | **Current-state** | Resolved published public profile for live discovery. | Staged proposals; disputed values; owner-private ops. |
| `venue_published_location` | **Current-state** | Single coherent published address family per venue. | Raw import addresses; multiple competing published addresses; staging candidates. |
| `venue_published_map_point` | **Current-state** | Exactly one authoritative published map point for live app use. | Source scrape coordinates; proposed corrections; multiple live pins. |
| `venue_published_attribute_value` | **Current-state** | Structured published discovery assignments. | Free-text filter drivers; staging-only values; marketing copy as structured claims. |
| `venue_published_descriptive_copy` | **Current-state** | Low-risk narrative/display copy **separate** from structured discovery drivers. | Badge/filter/search drivers without structured rows. |
| `venue_hours_regular`, `venue_hours_exception` | **Current-state** | Baseline and exception hours truth. | Sole storage of “open now” as replacement for truth; conflating unknown with closed. |
| `venue_hours_uncertainty` | **Current-state** | Explicit uncertainty/strength so unknown ≠ closed and weak ≠ open-now. | A substitute for derived present-tense claims. |
| `venue_derived_operational_claim` | **Current-state** (derivative, still operational read) | Present-tense **derived** claims (e.g. open-now eligibility/strength) when underlying truth supports it. | Replacement for baseline/exception/uncertainty tables; raw submission truth. |
| `owner_business_membership` | **Bridge** (membership **current-state**) | Which owner users belong to which business. | Venue access; venue permissions; claim state. |
| `business_venue_management_relationship` | **Current-state** (authority **junction**) + **lifecycle** | Core **business ↔ venue** link; anchor for venue-scoped authority. Rows may be **in-flight** (requested/review) or **approved/active**. | Shortcuts from `business` or `owner_account` to venue without this row; treating non-approved rows as full management authority. |
| `venue_management_rights` | **Current-state** | **Current** management-rights posture on an approved relationship (1:1 with relationship per Worker B). | Historical claim narrative; Stage-2 publish outcomes. |
| `venue_verification_state` | **Current-state** | **Current** verification outcome for management trust (distinct from permissions and from Stage-2). | Stage-2 `proposal_review` semantics; permission grants alone. |
| `venue_capability_grant` | **Current-state** + **bridge-like** | Coarse capability rows for an owner user **through** a management relationship. | Fine-grained ACL matrix; consumer permissions; proof of published field values. |
| `venue_claim_request` | **Workflow** | Claim **initiation** only; intent to manage under a business context. | Live permission grants; verification outcome; published truth. |
| `raw_venue_intake_record` | **Workflow** (intake) | Raw/semi-structured capture and provenance-facing intake. | Canonical venue identity definition; published truth. |
| `venue_change_proposal` | **Workflow** | Header for submissions (whole-record and/or multi-family); actor, channel, lifecycle. | Resolved published values; direct public read model. |
| `venue_proposal_target` | **Bridge** (workflow) | Which truth **families** a proposal touches (hybrid model). | Full field payloads (those live in staging tables or payloads). |
| `venue_proposal_staging_profile`, `venue_proposal_staging_location`, `venue_proposal_staging_attribute`, `venue_proposal_staging_hours` | **Workflow** | Non-published candidate values for review. | Live published rows. |
| `consumer_submission_extension` *(optional)* | **Workflow** (+ **bridge** to proposal) | Thin consumer-only **non-truth** metadata on a proposal. | Duplicate proposal payloads; published values. |
| `proposal_review` | **Workflow** (Stage-2 **decision record**; audit-adjacent) | Outcome of moderation on **public-truth** change packages; ties to reviewer and evidence basis. | Published attribute rows; live permissions; authority verification outcomes. |
| `evidence_item` | **Workflow** / provenance **support** | Durable evidence pointer/taxonomy (not binary store). | Canonical structured discovery values; standalone truth. |
| `evidence_attachment` | **Bridge** (workflow) | Links evidence to proposal and/or review. | Redundant copies of published truth. |
| `venue_publish_event` | **History / lineage / audit** | Publish/withhold/rollback narrative; supersedes links; ties to proposal/review context. | Editable stand-in for `venue_published_*` current rows. |
| `venue_published_row_history` *(optional)* | **History / lineage / audit** | Append-only prior versions or snapshots per publish event. | Mutable current-state; workflow staging. |
| `venue_authority_decision` | **Workflow** (authority **decision record**) + **audit character** | Admin decisions on **authority** matters (claim, verification, rights, capabilities). | Stage-2 field-family publish decisions (`proposal_review`); published venue values. |
| `venue_authority_event` | **History / lineage / audit** | Append-only authority-side transitions. | **Live** permission source of truth; current capability rows. |
| `geographic_region`, `locality` | **Reference** | Geography hierarchy and canonical locality for structured discovery. | Per-venue free-text as sole location truth; venue-specific map coordinates. |
| `external_data_source` | **Reference** | Registered sources for intake and provenance. | Long-term raw blob store (prefer separate intake). |
| `venue_attribute_definition` (+ optional `venue_attribute_allowed_value`) | **Reference** | Controlled keys/families and optional allowed values for structured discovery. | Per-venue truth blobs; unconstrained filter text. |

**Cross-cutting rule:** Any table that **primarily** holds **lifecycle status** for a **submission** or **authority request** is **workflow** until the product semantics place “current rights” or “published truth” in dedicated **current-state** tables (`venue_published_*`, `venue_management_rights`, `venue_capability_grant`, etc.).

---

## Current-state read model map

### Live public discovery (published truth)

**Operational read layer** for Home, Search, Map, Venue Detail (and consistency with Saved list **targets**):

- **`venue`** — identity anchor (join root), not a substitute for published columns.
- **`venue_published_profile`**, **`venue_published_location`**, **`venue_published_map_point`**, **`venue_published_attribute_value`**, **`venue_published_descriptive_copy`** (where used).
- **Hours stack:** `venue_hours_regular`, `venue_hours_exception`, `venue_hours_uncertainty`, **`venue_derived_operational_claim`** (derivative but still a **published operational read**, not a workflow row).
- **Reference joins:** `locality`, `geographic_region`, `venue_attribute_definition` (+ optional allowed values), not raw intake.

**Explicit:**

- **Published truth reads do not come from** `venue_change_proposal`, staging tables, `raw_venue_intake_record`, or `proposal_review`.
- **Public truth does not come from** raw/source rows or unstructured marketing text **for structured discovery claims** (descriptive copy is non-authoritative for filters/badges per Worker A/C).

### Consumer private state

**Operational read layer** for authenticated consumer UX (lists, prefs, notifications):

- `consumer_account`, `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings`, `saved_list`, **`saved_list_membership`** (bridge, current-state behavior).

**Explicit:** Private state **never** defines public venue truth; default location is **not** a venue’s published address.

### Owner / business live authority state

**Operational read layer** for “who may act on which venue under which business context” (coarse v1):

- `business`, `owner_business_membership`, **`business_venue_management_relationship`** (only rows whose **status** semantics allow the operation — SQL workers must enforce **approved/active** vs in-flight consistently).
- **`venue_management_rights`**, **`venue_verification_state`**, **`venue_capability_grant`**.

**Explicit:**

- **Live permissions do not come from** `venue_authority_event`, old `venue_claim_request` rows, or **`proposal_review`**.
- **Live permissions do not come from** `owner_business_membership` alone or `business` alone (DL-021).
- **Stage-2 publish reviews** (`proposal_review`) govern **public-truth** packages, **not** authority verification or management relationship approval (Worker B — different decision taxonomies).

---

## Workflow boundary map

| Workflow object / family | In-flight role | May **eventually affect** (indirectly, via formal workflows — **not** “direct mutation” in schema terms) |
|--------------------------|----------------|----------------------------------------------------------------------------------------------------------|
| `raw_venue_intake_record` | Capture raw/source payloads | Proposals and later **published** truth **only** through Stage-2 → publish pipeline. |
| `venue_change_proposal` (+ `venue_proposal_target`) | Submission header and family targeting | `venue_published_*`, hours tables, lineage via publish — **never** the live read model. |
| `venue_proposal_staging_*` | Candidate non-published field families | Corresponding **published** tables after review + publish. |
| `proposal_review` | Stage-2 decision on public-truth change | **Publish/withhold** outcomes recorded in **`venue_publish_event`** and materialized published rows; not itself “truth.” |
| `consumer_submission_extension` *(optional)* | Ancillary metadata on consumer proposals | Same as proposal — **not** truth. |
| `venue_claim_request` | Claim initiation / intent | **`business_venue_management_relationship`**, **`venue_management_rights`**, **`venue_verification_state`**, **`venue_capability_grant`** — **only** through authority processes and **current-state** tables. |
| `business_venue_management_relationship` *(when status is requested/under review)* | In-flight relationship | When approved/active, becomes the **anchor** for rights; until then, **must not** be treated as full management authority. |

**Explicit:** Wording “may eventually affect” means **product/process**, not a shortcut FK write from workflow rows into `venue_published_*` outside the formal publish path (DL-008).

---

## History / lineage / audit map

| Object | What it preserves | Must **not** be queried as |
|--------|-------------------|----------------------------|
| `venue_publish_event` | Successful publish, withhold, rollback narrative; supersedes chain; links to proposal/review for **lineage**. | Current published field values **by themselves** (those live in `venue_published_*` / hours); proof of “what to show on Search” without joining published tables. |
| `venue_published_row_history` *(optional)* | Append-only prior versions or family snapshots for rollback safety. | Mutable current state; substitute for workflow staging. |
| `venue_authority_event` | Append-only authority transitions (claim filed, relationship approved, rights suspended, etc.). | **Live** permissions; **current** verification or capability state. |
| `venue_authority_decision` | Point-in-time authority decisions with minimum evidence metadata. | Stage-2 publish moderation outcomes; **current** rights (decisions **justify** state changes; **current** state lives in rights/capability/verification tables). |
| `proposal_review` | Stage-2 moderation decisions on public-truth proposals. | Public discovery **current** rows; authority decisions. |
| `evidence_item` / `evidence_attachment` | Evidence pointers and linkage to proposals/reviews (and potentially authority decisions at SQL time). | Structured discovery attribute truth; permission grants. |

**Lineage vs workflow status:** `venue_change_proposal` lifecycle (staged/superseded/etc.) is **workflow**; **`venue_publish_event`** is **publish lineage** — do not collapse the two into one “status.”

---

## Reference and bridge map

### True reference / lookup domains (physical tables or seeded registries)

Per Workers A and C:

- **Geography:** `geographic_region`, `locality` (+ optional level/role on region nodes).
- **Provenance registry:** `external_data_source`.
- **Discovery structure:** `venue_attribute_definition` (+ optional `venue_attribute_allowed_value` or equivalent).
- **Coarse capability codes** may be a **tiny reference table** or constrained enum — either way they are **vocabulary**, not operational venue fact.

### Constrained vocabularies (not necessarily separate tables)

Worker C catalogs enum/check families: actor type, channel, proposal kind, proposal target family, proposal lifecycle, Stage-2 review outcome, publish event kind, evidence kind, hours uncertainty, derived claim strength, saved list lifecycle, owner–business membership status, business–venue relationship status, claim status, verification outcome, management rights posture, authority decision/event types, etc.

These are **reference semantics** embedded on operational tables — they **must not** be mistaken for **mutable operational state** (do not “edit vocabulary” to simulate venue truth changes).

### Bridge / junction tables — role clarity

| Bridge | Primary role in v1 |
|--------|---------------------|
| `venue_proposal_target` | Workflow: links proposal → affected **families**. |
| `evidence_attachment` | Workflow: links evidence → proposal/review. |
| `saved_list_membership` | **Current-state** private: list ↔ `venue`. |
| `owner_business_membership` | **Current-state**: owner ↔ `business`. |
| `venue_capability_grant` | **Current-state** entitlements: owner ↔ **relationship** (bridge-like; carries coarse capability **codes**). |
| `business_venue_management_relationship` | **Current-state authority junction** with **workflow-like** statuses until approved — highest blur risk (see [Risks](#risks)). |

---

## Boundary rules for SQL workers

Short **“never”** rules for draft SQL and app reads:

1. **Never read** `venue_change_proposal` **or** staging tables **as** published discovery truth.
2. **Never read** `proposal_review` **as** current published field values **or** as authority/permission state.
3. **Never read** `raw_venue_intake_record` **as** canonical identity **or** published truth.
4. **Never read** `venue_publish_event` **alone** **as** the full current public picture — always pair with **`venue_published_*`** / hours **current-state** tables when answering “what do we show now?”
5. **Never read** `venue_authority_event` **as** live permissions or live verification state.
6. **Never read** `venue_claim_request` **as** proof of management rights or capabilities.
7. **Never update** `venue_published_*` **directly from** proposals, staging rows, or intake tables **outside** the formal publish workflow (DL-008).
8. **Never update** `venue_capability_grant` / `venue_management_rights` **from** Stage-2 `proposal_review` rows — authority decisions use **`venue_authority_decision`** and **current-state** tables.
9. **Never use** history/lineage tables **as** current rights **or** current public truth.
10. **Never treat** reference vocabulary rows (`venue_attribute_definition`, locality rows, capability code definitions) **as** venue-specific operational truth — they **describe** allowed structure; **values** live in `venue_published_attribute_value` (or workflow staging pre-publish).
11. **Never collapse** unknown hours into closed **or** weak/stale hours into open-now (carry uncertainty + derived claim separation).
12. **Never mix** consumer private tables into public venue read paths for discovery.

---

## Migration grouping implications

Align with `recommended_migration_schema_build_order.md`, but **add category discipline**:

1. **Wave 1 — Anchors + reference spine:** `venue`; account anchors; `geographic_region`, `locality`, `external_data_source`; `venue_attribute_definition` (+ optional allowed values). *Rationale:* stable FK targets before truth rows.
2. **Wave 2 — Published discovery current-state:** all `venue_published_*`, hours + uncertainty + derived claim. *Rationale:* MVP search/read models before broad write paths.
3. **Wave 3 — Workflow + provenance + publish lineage:** intake, proposals, staging, evidence, `proposal_review`, `venue_publish_event`, optional `venue_published_row_history`. *Rationale:* change pipeline **after** published tables exist to avoid empty-publish targets and mixed-tranche shortcuts.
4. **Wave 4 — Consumer private current-state:** profile, prefs, saved lists. *Rationale:* attaches to `consumer_account` + `venue` + geo reference without coupling to workflow internals.
5. **Wave 5 — Authority current-state + authority workflow:** `owner_business_membership`, `business_venue_management_relationship`, `venue_management_rights`, `venue_verification_state`, `venue_claim_request`, `venue_capability_grant`, `venue_authority_decision`, `venue_authority_event`. *Rationale:* business/venue anchors first; **separate** Stage-2 tables from authority decisions in the **same mental migration family** (can be one migration only if boundaries stay explicit in code/comments).

**Grouping rule:** Prefer migrations that **do not** mix **published current-state** DDL with **workflow** DDL in the same changeset unless the team explicitly accepts higher blur risk — optional if process-strong.

**Deferred waves:** specials, tap, commercial detail — **separate** tranches per MVP map; **do not** block wave 1–5 category clarity.

---

## Risks

1. **Using `proposal_review` or `venue_change_proposal` status** as the app’s view of “what’s on the venue page” — violates DL-001 / DL-009.
2. **Using `business_venue_management_relationship` rows without status discipline** — granting access while still “requested/under review.”
3. **Deriving `venue_capability_grant` from `venue_authority_event`** — violates DL-022.
4. **Merging Stage-2 and authority decision tables** because both reference `admin_account` — causes wrong RLS and wrong product semantics (Worker B risk).
5. **Storing discovery filters in `venue_published_descriptive_copy`** — violates structured discovery (DL-005).
6. **Multiple published map points or addresses** — breaks DL-004.
7. **Materializing open-now without uncertainty/baseline separation** — breaks DL-006.
8. **JSON blobs for permissions or discovery attributes** — blurs reference vs operational state and blocks safe queries.
9. **Premature specials/tap tables** — couples migrations before core boundaries are stable (deferred per scope).

---

## Dependencies

- **Upstream:** Auth provider subject identifiers for account anchors; object storage or URL policy for evidence payloads (Worker A).
- **Cross-worker:** Worker D classification assumes Workers A–C table names and responsibilities remain **provisionally** stable; SQL may pluralize/rename with **category** preserved.
- **Deferred:** Specials/tap structured models and rich commercial schema — **depend on** core truth + workflow + authority boundaries remaining clean.

---

## Decisions requiring approval

**None identified.** No blocker contradictions found between locked docs and Workers A–C for this classification layer.

Non-blocking implementation choices (for SQL workers later): history as row-level vs snapshot; single vs split FK strategy for `venue_verification_state` across claim vs relationship; materialized vs computed `venue_derived_operational_claim`; optional `consumer_submission_extension`.

If the Database Manager later mandates **one** physical split for `business_venue_management_relationship` (requested vs approved rows), that is **implementation design**, not an architecture reopen — category rules above still apply.
