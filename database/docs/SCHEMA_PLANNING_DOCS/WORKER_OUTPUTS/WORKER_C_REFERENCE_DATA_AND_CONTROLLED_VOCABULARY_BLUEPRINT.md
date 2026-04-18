# Worker C — Reference Data and Controlled Vocabulary Blueprint

**Role:** Worker C — Reference Data and Controlled Vocabulary for PubPlus  
**Reports to:** Database Manager  
**Status:** Pre-SQL blueprint (no production SQL, no migrations, no Supabase code, no RLS, no triggers, no functions)  
**Inputs:** Locked docs under `database/docs/SCHEMA_PLANNING_DOC/` (paths `SCHEMA_PLANNING_DOCS/LOCKED_INPUTS/` were not present in-repo); `WORKER_A_FOUNDATIONAL_SCHEMA_BLUEPRINT.md`; `WORKER_B_PRIVATE_STATE_AND_AUTHORITY_BACKBONE.md`; discovery stage summaries.

---

# Confirmed understanding

**Architecture** is treated as locked per `decision_log.md`, `non_negotiable_rules_for_schema_workers.md`, `domain_boundary_map.md`, `consolidated_entity_map.md`, `relationship_authority_blueprint.md`, `state_lifecycle_model_summary.md`, `mvp_vs_deferred_scope_map.md`, and `recommended_migration_schema_build_order.md`.

**Fixed implementation clarifications (honored here):**

- **Specials and tap lists** are out of the first schema wave; this blueprint may name deferred vocabulary *areas* but does **not** design those domains in detail for wave 1.
- **Venue-scoped permissions** stay **coarse**: a small domain-aligned capability set only; **no** deep permission matrix or large role taxonomy.
- **Minimum evidence metadata** stays minimal but explicit everywhere decisions attach: **actor type**; **actor identity**; **source/channel**; **created/submitted timestamp**; **affected object/family**; **proposal type**; **reason/evidence-basis reference**; **review/decision timestamps**; **reviewer/admin identity** where applicable.

**Scope:** This document defines **reference data, lookup, enum-style constraints, and controlled vocabularies** that sit *under* Worker A (public/workflow) and Worker B (private state / authority). It does **not** redesign their core tables or relationship graphs.

**Consistency:** Naming aligns with Worker A/B **provisional** names (`venue_change_proposal`, `proposal_review`, `venue_publish_event`, `business_venue_management_relationship`, `venue_management_rights`, `venue_verification_state`, `venue_claim_request`, `venue_capability_grant`, `venue_authority_decision`, `venue_authority_event`, `geographic_region`, `locality`, `venue_attribute_definition`, etc.). Where a **shared vocabulary name** improves cross-worker clarity, it is called out explicitly without altering their table designs.

---

# Reference data inventory

Each row describes a **reference/lookup domain**, not a full table DDL.

| Proposed name | What it governs | Recommended form | Why that form | Expected dependents (tables/domains) |
|---------------|-----------------|------------------|---------------|-------------------------------------|
| **Geography region node** (`geographic_region` per Worker A) | Non–hardcoded geography hierarchy (country/state/region/larger groupings as product defines) | **Dedicated reference table** + self-parent pattern | Expansion beyond one metro without schema churn; clean FKs for locality and consumer default location | `locality`, `venue_published_location`, `consumer_default_location_preference` |
| **Locality** (`locality` per Worker A) | Canonical suburb/locality (and similar) for search, grouping, display | **Dedicated reference table** | Published discovery geography must be structured, not free-text place names as truth | `venue_published_location`, filters/grouping, consumer default location |
| **Geography node role / level** *(optional column on `geographic_region` or parallel small lookup)* | Distinguishes hierarchy levels (e.g. country vs state vs macro-region) when a single table holds mixed levels | **Lightweight lookup** *or* **small constrained enum/check family** | Avoids inventing multiple parallel region tables too early; still prevents ambiguous hierarchy joins | Region browsing/filter UX; admin seeding tools |
| **External data source** (`external_data_source`) | Registered import/API/source systems for intake and provenance | **Dedicated reference table** | Source IDs do not define venue identity, but **provenance** must be durable and queryable | `raw_venue_intake_record`, proposal/source linkage, audit |
| **Venue attribute definition** (`venue_attribute_definition`) | Discovery-driving structured attribute **families** (keys, semantics, cardinality expectations) | **Dedicated reference table** | DL-005: discovery-driving claims must be structured; one coherent truth set per family | `venue_published_attribute_value`, staging attributes, proposals targeting attribute family |
| **Venue attribute allowed value** *(optional companion)* | Normalized allowed values for discrete attributes | **Lightweight lookup table** *(optional split from Worker A text)* | Keeps filter/badge values DB-enforced without a heavy ontology | `venue_published_attribute_value`, staging |
| **Actor type** | Which logical domain initiated an action (`consumer`, `owner`, `admin`, `system`, `source` / `import` as needed) | **Constrained enum/check family** *(small, stable)* | Tiny, rarely extended; used everywhere for audit and RLS posture | `venue_change_proposal`, authority-side records, some events |
| **Submission / actor channel** | Surface/path for intake (e.g. app consumer, app owner, portal, import batch, admin tool) | **Constrained enum/check family** *or* **lightweight lookup** if product needs runtime add | Distinguishes operational telemetry from identity; minimum evidence metadata | `venue_change_proposal`, raw intake metadata |
| **Proposal kind / proposal type** | Whole-record vs field-family proposal; optional intent flags (e.g. onboarding vs correction) | **Constrained enum/check family** + optional small extension | DL-010 hybrid model; must not collapse granularity | `venue_change_proposal`, reporting |
| **Proposal target family** | Which **truth family** is touched (profile, geo, attributes, hours, descriptive copy, whole venue package, etc.) | **Constrained enum/check family** | Bridges hybrid proposals (`venue_proposal_target`); must stay stable for migration and audit | `venue_proposal_target`, evidence attachment scope |
| **Proposal lifecycle status** | Staged workflow state for venue truth change proposals (e.g. staged, in review, withdrawn, superseded) | **Constrained enum/check family** | Distinct from **publish lineage** and distinct from **authority** states | `venue_change_proposal` |
| **Stage-2 review outcome / decision type** | Moderator decision on **public-truth** proposal (`proposal_review`) | **Constrained enum/check family** + **decision reason code** (see below) | Must not reuse authority verification vocabulary | `proposal_review`, downstream publish |
| **Publish event kind / publish outcome family** | What happened in formal publish workflow (`venue_publish_event`): success publish, withhold, rollback narrative, etc. | **Constrained enum/check family** | DL-007/008: publish layer is separate from proposal status; lineage is explicit | `venue_publish_event`, rollback/audit |
| **Published truth lineage disposition** *(if encoded as sub-kind)* | Supersedes prior, restored, retired, withheld | **Constrained enum/check family** | Keeps lineage queries honest without overbuilding | Publish history patterns |
| **Evidence item kind** | Minimal taxonomy for evidence pointers (`document`, `url`, `source_record_ref`, `note`, etc.) | **Constrained enum/check family** | Small, audit-stable | `evidence_item`, attachments |
| **Stage-2 decision reason family** *(optional)* | Normalized reasons for approve/reject/withhold on **public truth** reviews | **Lightweight lookup** *or* **enum** for core + `other` | Reduces “mystery meat” free text in compliance queries; still allow detail text | `proposal_review` |
| **Venue published profile status / discovery eligibility** *(high-level)* | Operational/discovery-facing venue status fields that are **not** workflow state | **Constrained enum/check family** | Must not be confused with proposal or authority states | `venue_published_profile` |
| **Hours uncertainty / strength family** | Unknown vs partial vs weak/stale vs disputed/pending; rules for derivation boundaries | **Constrained enum/check family** | DL-006: distinct from **closed** and from **open-now**; prevents silent collapse | `venue_hours_uncertainty`, staging hours |
| **Derived operational claim strength / eligibility** | Whether **open-now** (or similar) is supportable | **Constrained enum/check family** | “Weak/stale is not open-now” must be data-backed | `venue_derived_operational_claim` |
| **Geography truth workflow state** *(if separated)* | Proposed correction vs published authoritative vs withheld pending | **Constrained enum/check family** | High-risk domain; must not leak weak geo into published truth | Staging location, publish |
| **Saved list lifecycle status** | User list active/archived/deleted | **Constrained enum/check family** | Private organization domain; simple lifecycle | `saved_list` |
| **Saved list membership** | Presence in list (optional soft-remove) | **Usually boolean/timestamp only** | Avoid inventing parallel “truth” states | `saved_list_membership` |
| **Notification channel / category / consent axes** | Structured notification settings (DL-017) | **Constrained enum/check families** *and/or* **narrow normalized rows** | Must not become opaque JSON blob | `consumer_notification_settings` |
| **Default location preference mode** | How consumer default location resolves (pinned locality vs region vs “system”) | **Constrained enum/check family** | Keeps preference reads deterministic | `consumer_default_location_preference` |
| **Owner–business membership status** | Invited / active / removed | **Constrained enum/check family** | Distinct from venue relationship states | `owner_business_membership` |
| **Business–venue management relationship status** | Requested / under review / approved / active / inactive / denied / revoked | **Constrained enum/check family** | Core authority junction; must be queryable | `business_venue_management_relationship` |
| **Claim request status** | Initiated / pending / approved / denied / withdrawn (+ optional unsupported) | **Constrained enum/check family** | **Claim ≠ access** | `venue_claim_request` |
| **Verification state outcome** | Not started / pending / verified / failed / expired / recheck-needed | **Constrained enum/check family** | **Verification ≠ permission**; do not reuse Stage-2 review outcomes | `venue_verification_state` |
| **Management rights posture** | Not granted / active / suspended / inactive / revoked | **Constrained enum/check family** | **Current** rights snapshot | `venue_management_rights` |
| **Venue capability code** | Coarse capability tokens (Worker B examples: `MANAGE_PUBLISHED_VENUE_OPERATIONS`, `SUBMIT_RESTRICTED_CHANGES_FOR_REVIEW`, `MANAGE_OWNER_PRIVATE_VENUE_OPERATIONS`, `MANAGE_BUSINESS_TEAM_SETTINGS`) | **Constrained enum/check family** *or* **tiny dedicated reference table** | Coarse v1; avoids matrix explosion while keeping integrity | `venue_capability_grant` |
| **Authority decision type** | Approve/deny claim, pass/fail verification, suspend/revoke rights, grant/revoke capability | **Constrained enum/check family** | Must not be confused with `proposal_review` outcomes | `venue_authority_decision` |
| **Authority event type** | Append-only taxonomy for transitions (claim filed, verification requested, relationship approved, etc.) | **Constrained enum/check family** | History is not authority, but taxonomy must be stable | `venue_authority_event` |
| **Authority decision reason family** *(optional)* | Normalized admin reasons for authority actions | **Lightweight lookup** *or* **enum** | Supports operational reporting without mixing Stage-2 reasons | `venue_authority_decision` |
| **Commercial lifecycle** *(deferred detail)* | Business subscription states | **Planned enum/ref later** | Out of first-wave depth per MVP map | Future commercial tables |

---

# Must-be-structured vs lightweight

## Vocabularies that should definitely be modeled as first-class reference data (from the start)

- **Geography references:** `geographic_region`, `locality` (Worker A) — published and consumer default location depend on them.
- **External data source registry** — provenance and intake without conflating identity.
- **Venue attribute definitions** — DL-005 / structured discovery; anchors filters and publish rules.
- **Optional `venue_attribute_allowed_value` (or equivalent)** — if multiple attributes share discrete value sets and SQL workers want FK integrity (still MVP-safe if kept narrow).

## Vocabularies that can stay lightweight in v1

- **Most lifecycle/status families** listed above — implement as **CHECK/enum-style constraints** *unless* the product needs runtime-added values without migrations (then promote selectively to lookup tables).
- **Actor type, channel, proposal/proposal-target families, evidence kinds** — small **enum/check** families; document the canonical list alongside migrations.
- **Coarse capability codes** — either **enum/check** or a **tiny seeded reference table** (two valid patterns); avoid adding columns per capability.
- **Stage-2 vs authority “reason” vocabularies** — start with **short code lists**; expand to lookup tables only if operators need editable taxonomies early.

## Vocabularies that should be planned for later but not built now (beyond naming)

- **Specials / tap lists:** recurring vs one-off, eligibility tiers, product/style catalogs — **defer detailed reference packs** (per MVP map); do not import Stage-5 complexity into wave 1.
- **Rich commercial/billing/sponsorship** — only architectural separation, not catalog design.
- **Deep verification/trust scoring** — not MVP reference layer.

---

# Cross-domain shared vocabularies

These should be **standardized once** and reused across Worker A and Worker B contexts (same semantic codes), even when different tables carry them:

| Shared vocabulary | Canonical use | Must not collide with |
|-------------------|----------------|------------------------|
| **Actor type** | Who acted: consumer / owner / admin / system / source | Not the same as **account domain** alone; actor type is the workflow evidence dimension |
| **Actor channel** | Where the action entered | Distinct from actor type |
| **Proposal kind + proposal target family** | Hybrid proposals | Not authority lifecycle |
| **Stage-2 review outcome** | `proposal_review` on public-truth proposals | **Verification outcome** or **management relationship status** |
| **Publish event / lineage outcome** | `venue_publish_event` | Not the same as proposal row status |
| **Evidence item kind** | Evidence pointers | Not a substitute for structured discovery values |
| **Geography references** | `locality` / `geographic_region` | Raw source labels |
| **Attribute definition + allowed values** | Discovery claims | Descriptive copy |
| **Hours uncertainty + derived claim strength** | Operational safety | Stage-2 moderation states |
| **Business–venue relationship status** | Approved/in-flight junction | Claim status |
| **Claim / verification / management rights / capability code** | Owner authority chain | Stage-2 publish permissions |

**Naming consistency note:** If SQL workers prefer a single prefix for all authority enums (e.g. `authority_*` vs `venue_*`), either is fine — **semantic separation** matters more than string prefixes.

---

# Discovery attribute reference strategy

**Goal:** DL-005 — discovery-driving claims remain structured; **no raw free-text discovery model** for filter/badge/search drivers.

**What belongs in `venue_attribute_definition` (conceptual minimum):**

- **Stable family key** (internal identifier) and **display label**.
- **Value shape:** boolean, single-select, multi-select, numeric band, etc. (product-dependent).
- **Cardinality rules** (e.g. single primary style vs many amenities).
- **Discovery-driving flag** — if true, values must be constrained and queryable.
- **Publishability tier / risk hint** — aligns with Stage-2 “high-risk family” thinking without encoding policy in the DB.

**Allowed values strategy for v1:**

- **Normalize discrete values now** when they drive MVP filters/badges (FK to allowed-value rows or enum constrained by definition).
- **Defer exhaustive ontologies** — do not build a universal taxonomy system; add rows as the product proves need.

**Avoiding a free-text discovery model:**

- Keep **marketing/descriptive copy** in `venue_published_descriptive_copy` (or equivalent), explicitly **non-authoritative for filters**.
- For “other / not listed” cases, prefer **explicit sentinel allowed values** (e.g. `OTHER`) plus optional **non-discovery** text, rather than unconstrained text driving search.

---

# State vocabulary strategy

**Rule:** **Do not collapse distinct state families** because labels sound similar. Below, each **family** keeps its own vocabulary and storage locus (enum/check or dedicated columns), even if both contain a word like “pending.”

## Workflow / proposals / Stage-2 review / publish (Worker A)

- **Proposal lifecycle** (`venue_change_proposal`): staged → in review → closed outcomes (withdrawn/superseded/etc.).
- **Stage-2 review outcome** (`proposal_review`): decision on **public-truth** change packages.
- **Publish lineage** (`venue_publish_event`): what landed in published truth, withheld, superseded, rollback-related events.

**Distinct from:** authority states, commercial states, consumer private states.

## Hours / operational truth

- **Hours uncertainty / strength** (`venue_hours_uncertainty`): unknown/partial/weak/stale/disputed/etc.
- **Derived operational claim** (`venue_derived_operational_claim`): whether present-tense claims are **eligible** and at what strength.

**Distinct from:** Stage-2 workflow state (you can have a staged hours proposal while published hours still show prior strength).

## Geography

- **Published authoritative location** vs **staging/proposed** vs **withheld** — workflow/geo families intersect Worker A staging tables, not owner authority.

## Authority / claim / verification / management rights / coarse capabilities (Worker B)

- **Claim request status** (`venue_claim_request`): initiation workflow only.
- **Verification state** (`venue_verification_state`): trust/verification outcome; **not** publish review.
- **Management rights posture** (`venue_management_rights`): whether the relationship currently grants operational authority posture.
- **Capability grants** (`venue_capability_grant`): coarse entitlements **through** the relationship.
- **Authority decisions/events** (`venue_authority_decision`, `venue_authority_event`): audit/history; **not** live permission reads.

**Explicit:** `proposal_review` (Stage 2) and `venue_authority_decision` (authority) both involve admin actors but **different decision taxonomies**.

## Consumer private state

- **Saved list lifecycle**, **notification settings**, **default location preference** — user-private; **never** mixed into public truth enums.

## Deferred (named only)

- **Specials / tap** state stacks — follow Stage 5 semantics **later**; do not import into wave-1 enums.

---

# Minimal first-tranche reference pack

Minimum controlled-vocabulary and reference **set** that should exist early enough for clean migrations aligned with Workers A and B:

1. **Geography:** `geographic_region`, `locality` (+ optional level/role on region nodes).
2. **Provenance:** `external_data_source`.
3. **Discovery structure:** `venue_attribute_definition` (+ optional allowed-value companion for discrete MVP attributes).
4. **Workflow evidence dimensions:** actor type, actor channel, proposal kind, proposal target family, proposal lifecycle status.
5. **Stage-2 review + publish:** review outcome type; publish event kind; evidence item kind; optional compact reason codes.
6. **Hours safety:** hours uncertainty/strength family; derived operational claim strength/eligibility family.
7. **Consumer private (light):** saved list lifecycle; default location preference mode; notification enums/axes as structured columns imply.
8. **Authority chain:** owner–business membership status; business–venue relationship status; claim status; verification outcome; management rights posture; coarse capability codes; authority decision/event types.

**Principle:** Seed **only** what MVP flows require; keep extension points as **additive** rows or **new enum values** with explicit migration notes — not premature generic taxonomy engines.

---

# Deferred reference areas

Anticipate but **do not materially build** in wave 1:

- **Specials:** recurring vs one-off pattern vocabularies; eligibility tiers; offer-type taxonomies.
- **Tap lists:** product/brewery/style reference depth; offering-trait vocabularies beyond light planning.
- **Commercial plans:** plan catalogs, billing reason codes, sponsorship/boost vocabularies.
- **Advanced trust:** fraud labels, risk scores, integrity-case taxonomies.
- **Deep team/role models** beyond coarse capabilities.
- **Rich geo:** international address formats, sub-locality precision — extend reference geography only when product leaves Melbourne assumptions.

---

# Risks

1. **Reusing the same enum for Stage-2 review vs authority verification** — causes permission bugs and audit confusion (Worker B risk #7/#8).
2. **Storing discovery-driving filters in free text** “for speed” — breaks DL-005 and poisons search trust.
3. **Promoting every status to a heavy reference table** — migration churn without operational need; start with enums, promote surgically.
4. **Collapsing unknown hours into closed** or weak hours into open-now — semantic failure, not just bad data.
5. **Multiple competing “pending” states** across families without documentation — operators and SQL writers will pick the wrong column.
6. **Encoding permissions as JSON blobs** — breaks coarse capability clarity and RLS readiness.
7. **Using `venue_authority_event` as a live permission source** — violates DL-022; taxonomy must not replace current-state tables.
8. **Letting source/import actor identifiers substitute for structured channel/type** — undermines minimum evidence metadata.
9. **Premature normalization of optional reason taxonomies** — can block shipping; keep reasons **minimal codes** first.

---

# Dependencies

- **Worker A** reference anchors: geography, attribute definitions, external sources; workflow enums on proposals/reviews/publish/evidence.
- **Worker B** authority enums: membership, relationship, claim, verification, rights, capabilities, authority decisions/events.
- **Auth provider identifiers** — out of scope here but required for actor identity linkage on anchors.

---

# Decisions requiring approval

**None identified.** No open blockers found in locked docs versus Workers A/B; remaining choices (enum vs tiny ref table for capabilities; optional `venue_attribute_allowed_value` split; optional reason-code lookups) are **implementation-level** and can be decided by SQL workers without reopening architecture.

If the Database Manager later mandates **editable taxonomies** (admin UI) for a specific vocabulary, promote **only** that vocabulary from enum/check to a lookup table — without expanding scope to specials/tap in wave 1.
