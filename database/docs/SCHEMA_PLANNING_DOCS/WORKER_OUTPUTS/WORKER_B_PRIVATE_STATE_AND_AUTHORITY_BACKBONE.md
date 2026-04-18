# Worker B — Private State and Authority Backbone Blueprint

**Role:** Worker B — Private State and Authority Backbone for PubPlus  
**Reports to:** Database Manager  
**Status:** Pre-SQL blueprint (no migrations, no SQL, no RLS, no triggers, no functions)  
**Inputs locked:** `database/docs/SCHEMA_PLANNING_DOC/` decision and planning set. `SCHEMA_PLANNING_DOCS/LOCKED_INPUTS/` was not present in-repo; alignment is to the locked docs above plus Worker A (`WORKER_A_FOUNDATIONAL_SCHEMA_BLUEPRINT.md`).

---

## Confirmed understanding

**Architecture:** Treated as locked per `decision_log.md`, `non_negotiable_rules_for_schema_workers.md`, `domain_boundary_map.md`, `consolidated_entity_map.md`, `relationship_authority_blueprint.md`, `state_lifecycle_model_summary.md`, `mvp_vs_deferred_scope_map.md`, and `recommended_migration_schema_build_order.md`.

**Implementation clarifications (fixed for this blueprint):**

- **Specials and tap lists** are **out** of this design; no tables for them here.
- **Venue-scoped permissions** stay **coarse** in v1: a small capability set aligned to domains (e.g. manage approved venue operational data; submit restricted changes for review; manage owner-private operational data later; manage owner-side team/business settings later). No deep permission matrix.
- **Minimum evidence metadata** remains minimal but explicit wherever decisions attach: actor type; actor identity; source/channel; created/submitted timestamp; affected object/family; proposal type; reason/evidence basis reference; review/decision timestamps; reviewer/admin identity where applicable. (Consumer and owner **workflow** inputs to public truth continue to use Worker A’s `venue_change_proposal` / `proposal_review` / evidence pattern; **authority** workflows add parallel decision records where those decisions are not the same as Stage-2 publish reviews.)

**Dependency on Worker A (Waves 1–3):** This blueprint **does not** redesign canonical venue identity, published public truth, or the core proposal/review/publish/evidence spine. It adds **consumer private state**, **saved lists**, **owner–business–venue authority chain**, **claim / verification / management-rights / coarse permissions**, and **admin anchor usage** for authority-side decisions.

**Non-negotiable separations for this worker:**

- Private consumer state is **not** public truth. Saved venues are **list-native** (lists own memberships; no flat single-bucket favorites model).
- Default location preference and notification/consent settings are **first-class structured** private domains, not a generic profile JSON blob.
- Consumer, owner, and admin remain **separate logical account domains**; auth identity is **not** the permission model.
- Owner user, **business** entity, and **venue** remain distinct; **business membership alone is not venue authority**.
- **Claim is not access**; **verification is not access**; **workflow history is not live authority**; consumer/owner **submissions are not public truth** (they feed workflow via Worker A objects).

---

## Proposed table blueprint

Naming is migration-ready in spirit; final pluralization/prefixes follow project conventions.

### A. Consumer private state (extends Wave 4)

| Proposed table name | Domain | Purpose | Category | Key parent / anchor | Do **not** store here |
|---------------------|--------|---------|----------|----------------------|------------------------|
| `consumer_account` | Consumer / account anchor | Logical consumer identity; link to auth subject | Current-state | Auth provider subject (external) | Published venue truth; owner/admin authority |
| `consumer_profile` | Consumer private | Minimal display identity (e.g. display name, avatar ref); app-facing only | Current-state | FK → `consumer_account` | Discovery truth; marketing segments; unstructured catch-all prefs |
| `consumer_default_location_preference` | Consumer private | Structured default location for discovery UX (e.g. pinned locality/region references or approved lightweight geo preference rows) | Current-state | FK → `consumer_account`; FK → `locality` and/or `geographic_region` (Worker A reference) as product requires | Published venue address; multiple authoritative map points; raw GPS history |
| `consumer_notification_settings` | Consumer private | Structured notification channels, categories, quiet hours, **and** consent flags as explicit columns (not an opaque blob) | Current-state | FK → `consumer_account` (1:1) | Email/SMS content bodies; cross-user messaging; public venue fields |
| `saved_list` | Consumer private | User-owned named list/folder for organizing saved venues | Current-state | FK → `consumer_account` | Venue truth; shared collaborative semantics (defer) |
| `saved_list_membership` | Consumer private | List ↔ canonical venue membership | Bridge | FK → `saved_list`; FK → `venue` | Duplicate “favorite” parallel to lists; source-defined venue identity |

**Consumer submissions (workflow input):** Authenticated consumer submissions that affect venue truth are **workflow objects**, not truth. **Canonical pattern:** use Worker A’s `venue_change_proposal` (and children) with `actor_type = consumer` and `consumer_account_id` set, plus existing `proposal_review` / `evidence_*` / `venue_publish_event` for publish lineage. **Do not** add a second parallel “source of truth” submission table for the same proposal payload.

| Proposed table name | Domain | Purpose | Category | Key parent / anchor | Do **not** store here |
|---------------------|--------|---------|----------|----------------------|------------------------|
| `consumer_submission_extension` *(optional)* | Consumer / workflow | Thin 1:1 extension keyed by `venue_change_proposal_id` for consumer-only **non-truth** metadata (e.g. app surface, campaign attribution) if strictly needed and not folded into proposal header | Workflow / bridge | FK → `venue_change_proposal`; FK → `consumer_account` | Staged field payloads (belong in staging tables); published values |

If product needs no extra columns beyond `venue_change_proposal`, **omit** `consumer_submission_extension`.

### B. Owner / business / managed venue / authority (Wave 5)

| Proposed table name | Domain | Purpose | Category | Key parent / anchor | Do **not** store here |
|---------------------|--------|---------|----------|----------------------|------------------------|
| `owner_account` | Owner / account anchor | Logical owner portal identity; mandatory 2FA at product layer | Current-state | Auth provider subject (external) | Consumer private data; live venue permissions without relationship chain |
| `business` | Owner / org | First-class operator entity; primary future commercial attachment | Current-state | *(root anchor)* | Canonical venue published truth; claim history as authority |
| `owner_business_membership` | Owner / business | Owner user ↔ business membership lifecycle (invited, active, removed) | Bridge / current-state | FK → `owner_account`; FK → `business` | Venue-scoped permissions; claim/verification state |
| `business_venue_management_relationship` | Authority | Approved (or in-flight) **business ↔ canonical venue** management link; core junction for venue-scoped authority | Current-state / workflow *(lifecycle)* | FK → `business`; FK → `venue` | Published operational field values; person-to-venue shortcut |
| `venue_management_rights` | Authority | **Current** management-rights posture for an approved relationship (e.g. not granted / active / suspended / revoked) | Current-state | FK → `business_venue_management_relationship` (1:1) | Historical claim events; Stage-2 publish rows |
| `venue_claim_request` | Authority workflow | Claim **initiation** object: requests/asserts intent to manage a venue under a business context | Workflow | FK → `venue`; FK → `business` (and/or `owner_account` as initiator per product rules) | Permission grants; verification outcome as final authority |
| `venue_verification_state` | Authority | **Current** verification outcome/state for a management relationship and/or active claim case (distinct from permissions) | Current-state | FK → `business_venue_management_relationship` and/or FK → `venue_claim_request` *(design-time choice: at minimum one stable anchor)* | Workflow history rows; proof document storage |
| `venue_capability_grant` | Authority | Coarse venue-scoped **capability** rows for an owner user **through** an approved management relationship | Current-state / bridge | FK → `business_venue_management_relationship`; FK → `owner_account`; optional FK → `business` for redundancy checks | Fine-grained ACL matrix; consumer permissions |
| `venue_authority_decision` | Authority / audit | Admin/reviewer decisions on **authority** matters (approve/deny claim, verification pass/fail, rights suspend/revoke) with **minimum evidence metadata** | Workflow / history | FK → `admin_account` (decider); FK targets as needed (`venue_claim_request`, `business_venue_management_relationship`, `venue_verification_state`) | Published venue attribute values; Stage-2 field-family publish decisions *(those stay on `proposal_review` / publish events)* |
| `venue_authority_event` | Authority / audit | Append-only **history** of authority-side transitions (claim filed, verification requested, relationship approved, rights suspended, grant added/revoked) | History / audit | FK → relevant anchor IDs (`venue`, `business`, `business_venue_management_relationship`, etc.) | **Do not** use as live permission source of truth |

**Owner submissions (workflow input):** Same rule as consumers: **owner-originated changes to public discovery truth** flow through Worker A’s `venue_change_proposal` with `actor_type = owner` and `owner_account_id` (and business context on the proposal header if needed). **Do not** store proposed public field values in `venue_capability_grant` or `venue_claim_request`.

### C. Admin anchor (cross-cutting)

| Proposed table name | Domain | Purpose | Category | Key parent / anchor | Do **not** store here |
|---------------------|--------|---------|----------|----------------------|------------------------|
| `admin_account` | Admin / account anchor | Internal reviewer/admin identity | Current-state | Auth provider subject (external) | Consumer PII by default; published truth fields |

`proposal_review` (Worker A) and `venue_authority_decision` (this blueprint) both reference `admin_account` where a human admin acts.

---

## Consumer-private domain blueprint

**Intent:** Everything here is **private to the consumer account** or **workflow input**, never live public discovery truth.

1. **`consumer_account`** — Anchor already assumed from Worker A; consumer features hang here.
2. **`consumer_profile`** — Minimal structured profile; **not** a generic JSON blob for all preferences.
3. **`consumer_default_location_preference`** — First-class structured default location (FK into `locality` / `geographic_region` per product). Distinct from any single venue’s published address.
4. **`consumer_notification_settings`** — First-class structured notification and **consent** state (explicit columns or normalized rows, but not an unstructured profile blob).
5. **Consumer submissions** — Represented by **`venue_change_proposal`** (+ staging/review/publish) for authenticated users; **optional** `consumer_submission_extension` only for non-truth metadata. Submissions **feed** moderation; they **do not** mutate published truth directly (DL-009).
6. **`saved_list` / `saved_list_membership`** — **List-native** saved venues: many lists per user; memberships reference **`venue`** (canonical identity) only. **Saved venues are list-native**, not a parallel favorites table (DL-016).

**Explicit:** Private state is **not** public truth. Preferences are **not** embedded as opaque profile JSON.

---

## Owner/business/authority blueprint

**Intent:** Preserve **layered** authority without shortcuts (DL-020, DL-021).

1. **`owner_account`** — Portal identity; **not** a consumer account and not a venue.
2. **`business`** — Operator entity; future commercial state attaches primarily here (DL-024); **not** a venue.
3. **`owner_business_membership`** — Which owner users belong to which business. **Does not** grant venue access by itself (DL-021).
4. **`business_venue_management_relationship`** — The **approved (or requested) business ↔ venue** management link; central junction for venue-scoped authority (DL-020). Multiple businesses per venue and multiple venues per business are allowed at the data model level (DL-019).
5. **`venue_claim_request`** — **Claim initiation** only: requests/asserts management intent. **Not** permission grants.
6. **`venue_verification_state`** — **Verification** outcome/state, distinct from access and from published truth.
7. **`venue_management_rights`** — **Current** management-rights state on the relationship (distinct from claim and verification narratives).
8. **`venue_capability_grant`** — **Coarse** venue-scoped capabilities for a specific owner user **through** `business_venue_management_relationship`. Distinct from verification and from claim objects.
9. **`venue_authority_decision` / `venue_authority_event`** — Human/admin **decisions** and **append-only history** on the authority side. **Workflow/history is not live authority** (DL-022): live grants live in `venue_capability_grant` / `venue_management_rights`; history lives in `venue_authority_event`.

**Explicit:** Owner, business, and venue remain **distinct**. Claim ≠ access; verification ≠ access; history ≠ current rights.

---

## Relationship spine

**Convention:** Arrows read as **child → parent** (FK direction to preserve).

### Consumer domain

- `consumer_profile` → `consumer_account`
- `consumer_default_location_preference` → `consumer_account`
- `consumer_default_location_preference` → `locality` and/or `geographic_region` (Worker A reference tables)
- `consumer_notification_settings` → `consumer_account`
- `saved_list` → `consumer_account`
- `saved_list_membership` → `saved_list`
- `saved_list_membership` → **`venue`** (canonical venue identity only)
- `venue_change_proposal` → `consumer_account` *(nullable, when actor is consumer)*
- `consumer_submission_extension` → `venue_change_proposal`; → `consumer_account` *(if used)*

### Owner → business → managed venue → permissions

- `owner_business_membership` → `owner_account`
- `owner_business_membership` → `business`
- `business_venue_management_relationship` → `business`
- `business_venue_management_relationship` → **`venue`**
- `venue_management_rights` → `business_venue_management_relationship`
- `venue_capability_grant` → `business_venue_management_relationship`
- `venue_capability_grant` → `owner_account`

### Claim / verification / management-rights chain

- `venue_claim_request` → `venue`
- `venue_claim_request` → `business` *(and/or initiating `owner_account` per rules)*
- `venue_verification_state` → `business_venue_management_relationship` *(post-approval)* and/or → `venue_claim_request` *(in-flight)* — SQL workers pick a **single clear** FK strategy; must not mix “current rights” queries with historical claim rows.
- `venue_authority_decision` → `admin_account`
- `venue_authority_decision` → one or more of: `venue_claim_request`, `business_venue_management_relationship`, `venue_verification_state`
- `venue_authority_event` → anchors as needed for audit (always includes context pointers to `venue`, `business`, relationship/claim IDs)

### Admin / reviewer attachments

- `proposal_review` (Worker A) → `admin_account`
- `venue_authority_decision` → `admin_account`
- Optional future: admin tooling tables **must not** collapse into `consumer_account` or `owner_account`.

### Authority shortcuts that must **not** be encoded as FK “shortcuts”

- **No** `owner_account` → `venue` direct edge for permissions.
- **No** `business` → `venue_capability_grant` without `business_venue_management_relationship`.
- **No** `venue_claim_request` → `venue_capability_grant` without relationship approval pattern.
- **No** using `venue_authority_event` as the runtime permission read model.

---

## Current-state vs workflow split

| Category | Tables / objects |
|----------|------------------|
| **Live private state (consumer)** | `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings`, `saved_list`, `saved_list_membership` |
| **Live authority state (owner/business)** | `business`, `owner_business_membership`, `business_venue_management_relationship`, `venue_management_rights`, `venue_verification_state` *(current snapshot)*, `venue_capability_grant` |
| **Workflow objects** | `venue_change_proposal` (+ Worker A staging) for **all** consumer/owner submissions to public truth; `venue_claim_request`; `consumer_submission_extension` *(optional)* |
| **History / audit** | `venue_authority_event`; `venue_authority_decision`; Worker A `venue_publish_event`, `proposal_review`, optional `venue_published_row_history` |
| **Bridges** | `saved_list_membership`; `owner_business_membership`; `venue_capability_grant` (bridge-like attachment of user to relationship) |
| **Reference / anchors** | `consumer_account`, `owner_account`, `admin_account`, `venue` (Worker A), geography reference tables |

**Rule:** Current **rights** and **permissions** are read from **`venue_management_rights`**, **`venue_verification_state`** (as designed), and **`venue_capability_grant`** — **not** from `venue_authority_event` alone.

---

## Minimal coarse permission pack

**v1 recommendation:** encode capabilities as a **small enum** (check constraint or reference table) on `venue_capability_grant.capability_code` / `kind`. Example **coarse** set (names illustrative):

| Code | Meaning (domain-aligned) |
|------|----------------------------|
| `MANAGE_PUBLISHED_VENUE_OPERATIONS` | Manage **approved** venue operational data that maps to published/truth workflows per product policy (still via Stage-2 publish for discovery truth — grant does not bypass publish) |
| `SUBMIT_RESTRICTED_CHANGES_FOR_REVIEW` | Submit proposals that may require review before publish |
| `MANAGE_OWNER_PRIVATE_VENUE_OPERATIONS` | Manage owner-private operational data **not** in public truth *(future columns/tables; not public fields)* |
| `MANAGE_BUSINESS_TEAM_SETTINGS` | Invite/remove owner users within business / business settings *(later-heavy; may exist as stub)* |

**Rules:**

- Permissions are **always** scoped through **`business_venue_management_relationship`** (and `owner_account`), never global per user.
- **No** per-field ACL matrix in v1.
- **Do not** conflate verification state or active management rights with capability rows; grants may be **invalidated** when `venue_management_rights` or `venue_verification_state` says so (product/RLS later).

---

## Migration-tranche recommendation

Planning-level order for **this worker’s** domain, assuming Worker A Waves 1–3 exist or ship alongside:

1. **Account anchors** (if not already deployed): `consumer_account`, `owner_account`, `admin_account`, `business`, `venue`.
2. **Consumer structured private state:** `consumer_profile`, `consumer_default_location_preference`, `consumer_notification_settings` (depends on geography reference for location preference).
3. **Saved lists:** `saved_list`, `saved_list_membership` (depends on `consumer_account`, `venue`).
4. **Consumer submission extension (optional)** after `venue_change_proposal` exists.
5. **Owner–business structure:** `owner_business_membership`.
6. **Managed venue + current rights:** `business_venue_management_relationship`, `venue_management_rights`, `venue_verification_state`.
7. **Claim workflow:** `venue_claim_request` before or with relationship request states (SQL workers align lifecycles).
8. **Coarse permissions:** `venue_capability_grant`.
9. **Authority audit/decision:** `venue_authority_decision`, `venue_authority_event`.

Rationale: anchors and **consumer private** data can ship after canonical `venue` exists; **authority chain** requires `business`, `owner_account`, `venue`, and should precede or co-ship with coarse grants; audit tables last among authority objects to have stable FK targets.

---

## Risks

1. **Deriving live `venue_capability_grant` from `venue_authority_event` or old `venue_claim_request` rows** — violates DL-022; live reads must use current-state tables.
2. **Adding `owner_account_id` directly on `venue` for “ownership”** — violates person-to-venue shortcut ban; use `business_venue_management_relationship`.
3. **Treating `owner_business_membership` as venue access** — violates DL-021.
4. **Storing default location or notification prefs inside `consumer_profile` as JSON** — violates DL-017; keep dedicated tables.
5. **Flat `saved_venue` without lists** — violates DL-016.
6. **Duplicate submission payloads** in consumer-specific tables that mirror `venue_change_proposal`** — violates single workflow spine; use extension only for ancillary metadata.
7. **Mixing Stage-2 `proposal_review` with authority decisions** for the same semantic decision — confuses publish moderation vs business/venue authority; use `venue_authority_decision` for authority outcomes unless Database Manager explicitly unifies terminology at SQL time.
8. **Overloading `venue_verification_state` with Stage-2 review state** — verification of **management** is not the same as publish review of **field families**.

---

## Dependencies

**Upstream (required):**

- Worker A: `venue`, `consumer_account`, `owner_account`, `admin_account`, `business`, geography references (`locality`, `geographic_region`), `venue_change_proposal` (+ staging/review/publish/evidence stack).
- Auth provider identifiers for account anchors.

**Downstream (explicitly not designed here):**

- Rich owner-private operational tables; deep team hierarchies; commercial/subscription detail; specials/tap; advanced fraud/trust scoring.

---

## Decisions requiring approval

**None identified as blockers.** Open non-blocking choices for SQL workers: (1) whether `consumer_notification_settings` is one row per account vs normalized channel rows; (2) whether `venue_verification_state` attaches primarily to `venue_claim_request` vs `business_venue_management_relationship` during overlapping lifecycles — model must stay **one clear current-state read path**; (3) optional presence of `consumer_submission_extension`.

No approval items pending from this blueprint.
