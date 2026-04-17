# PubPlus — Decision Log

Status: Locked / Approved
Purpose: Canonical guardrail reference for later schema, SQL, migration, RLS, and verification workers.

This file captures the architectural decisions from Stages 1–5 that materially affect implementation planning. It is not a transcript. It is the durable record of decisions that later workers must treat as settled.

---

## DL-001 — One canonical published truth per venue

**Status:** Locked / Approved  
**Stage source:** Stage 1  
**Decision statement:** PubPlus operates on one canonical published truth per venue, and live app surfaces read from that published canonical layer only.  
**Why it matters:** Search trust and cross-surface consistency depend on one authoritative public truth model.  
**Implementation consequence:** Later schema work must anchor public venue-linked truth to a single canonical venue identity and prevent parallel live truth systems by screen, source, or feature.  
**What must not happen:** No duplicate public truth models for Home, Search, Map, Saved, or Venue Detail. No source-specific “live truth” alongside canonical truth.

## DL-002 — Canonical venue identity is durable and source-agnostic

**Status:** Locked / Approved  
**Stage source:** Stage 1  
**Decision statement:** Canonical venue identity must be durable and source-agnostic; source IDs do not define canonical identity.  
**Why it matters:** Venue truth, private state, workflow records, and future owner/business relationships must attach to a stable identity.  
**Implementation consequence:** Schema planning must center venue-linked relationships on canonical venue identity, not importer IDs or scraped identifiers.  
**What must not happen:** No source ID as the primary identity anchor. No fragmentation of venue-linked state by provider.

## DL-003 — Published truth contains only resolved public truth

**Status:** Locked / Approved  
**Stage source:** Stage 1  
**Decision statement:** Weak, ambiguous, stale, disputed, unresolved, or pending values stay outside the published layer.  
**Why it matters:** PubPlus’s public discovery model must remain trustworthy and moderation-safe.  
**Implementation consequence:** Schema workers must preserve separation between published truth and non-published states such as staged, disputed, stale, weak, or under-review data.  
**What must not happen:** No leaking unresolved data into public truth. No publishing because a value exists somewhere in workflow history.

## DL-004 — Geography is structured and authoritative

**Status:** Locked / Approved  
**Stage source:** Stage 1  
**Decision statement:** Geography is a structured domain with public address, canonical suburb/locality, broader geography hierarchy, and exactly one authoritative published map point.  
**Why it matters:** Search, map, locality grouping, and filter trust depend on consistent location truth.  
**Implementation consequence:** Location-related public truth must be explicitly modeled and kept coherent at the venue level.  
**What must not happen:** No multiple competing published map points. No loose free-text geography standing in for structured location truth.

## DL-005 — Discovery attributes must be structured when discovery-relevant

**Status:** Locked / Approved  
**Stage source:** Stage 1  
**Decision statement:** Discovery-driving claims must be structured where they materially affect filters, badges, counts, grouping, or search.  
**Why it matters:** Search-first discovery requires reliable, queryable, auditable attribute families.  
**Implementation consequence:** Later schema must prefer structured attribute domains over free-text blobs for public discovery claims.  
**What must not happen:** No raw free-text discovery model for important filters or badges.

## DL-006 — Hours are structured operational truth with conservative uncertainty handling

**Status:** Locked / Approved  
**Stage source:** Stage 1  
**Decision statement:** Regular hours, exceptions, and uncertainty are distinct. Unknown hours must not become closed. Weak or stale hours must not become open-now. Valid exceptions override baseline hours.  
**Why it matters:** Hours are high-risk public truth and one of the easiest ways to lose user trust.  
**Implementation consequence:** Schema must support separate regular hours, exception periods, and uncertainty-aware derivation boundaries.  
**What must not happen:** No silent collapse of unknown into closed. No promotion of weak hours into open-now. No ignoring valid exceptions.

## DL-007 — Four-layer truth workflow is mandatory

**Status:** Locked / Approved  
**Stage source:** Stage 2  
**Decision statement:** PubPlus uses a four-layer model: Raw/source, Proposed/staged, Reviewed/decisioned, Published.  
**Why it matters:** This is the core moderation-safe pipeline from messy inputs to trustworthy public truth.  
**Implementation consequence:** Schema planning must preserve distinct lifecycle layers and lineage across them.  
**What must not happen:** No collapsing raw, staged, review, and published into one generic record state.

## DL-008 — No direct write path into published truth

**Status:** Locked / Approved  
**Stage source:** Stage 2  
**Decision statement:** No actor writes directly into the published layer except through the formal publish workflow.  
**Why it matters:** Protects public truth from shortcut mutations and preserves auditability.  
**Implementation consequence:** Later schema, SQL, and RLS must enforce formal publish boundaries.  
**What must not happen:** No direct app, portal, importer, user, or owner write path into published truth tables/domains.

## DL-009 — Submission is not truth

**Status:** Locked / Approved  
**Stage source:** Stage 2 / Stage 3  
**Decision statement:** User submissions and owner submissions are workflow objects, not published truth.  
**Why it matters:** Inputs must be reviewable, evidence-aware, and auditable before public publication.  
**Implementation consequence:** Submission records must remain distinct from published objects and must feed the workflow/review system.  
**What must not happen:** No submission record doubling as live public truth.

## DL-010 — Hybrid proposal model is required

**Status:** Locked / Approved  
**Stage source:** Stage 2  
**Decision statement:** The proposal model supports both whole-record proposals and field-family proposals.  
**Why it matters:** Different venue maturity states and correction types need different proposal granularity.  
**Implementation consequence:** Schema planning must allow both broad onboarding/repair proposals and targeted family-level updates.  
**What must not happen:** No forcing every change into only whole-record or only field-level flows.

## DL-011 — Provenance, evidence, freshness, and auditability are first-class

**Status:** Locked / Approved  
**Stage source:** Stage 2  
**Decision statement:** Meaningful workflow decisions require provenance/evidence basis, freshness awareness, and audit retention.  
**Why it matters:** Review safety and rollback quality depend on traceable decision history.  
**Implementation consequence:** Schema must leave room for evidence references, actor separation, reasons, timestamps, and lineage-preserving review outcomes.  
**What must not happen:** No opaque review actions with no basis recorded.

## DL-012 — Rollback must preserve lineage and withhold weak replacements

**Status:** Locked / Approved  
**Stage source:** Stage 2  
**Decision statement:** Rollback restores prior truth where defensible, otherwise withholds safely; history must remain intact.  
**Why it matters:** Corrections and reversals must not destroy audit trails or accidentally republish weak truth.  
**Implementation consequence:** Later workers must design history-aware rollback-capable state handling rather than destructive overwrite models.  
**What must not happen:** No delete-and-replace rollback pattern that loses history. No rollback that republishes unsupported values.

## DL-013 — Consumer, owner, and admin are separate logical account domains

**Status:** Locked / Approved  
**Stage source:** Stage 3  
**Decision statement:** Consumer, owner, and admin are separate logical account domains even if shared auth infrastructure is used underneath.  
**Why it matters:** Permission clarity, security posture, and future RLS all depend on non-blurred account domains.  
**Implementation consequence:** Schema and policy design must not assume one flexible multi-role account model.  
**What must not happen:** No generic user role bag that blends consumer, owner, and admin authority.

## DL-014 — Owner accounts are not upgrades from consumer accounts

**Status:** Locked / Approved  
**Stage source:** Stage 3  
**Decision statement:** Owner accounts are separate from consumer accounts; same human or same email does not imply shared authority.  
**Why it matters:** Prevents accidental privilege inheritance and domain confusion.  
**Implementation consequence:** Permission and identity models must avoid shortcutting across account domains.  
**What must not happen:** No automatic consumer-to-owner upgrade path. No inferred shared authority from email reuse.

## DL-015 — Anonymous browsing is allowed; consumer private state is separate

**Status:** Locked / Approved  
**Stage source:** Stage 3  
**Decision statement:** Anonymous users can browse and search; consumer accounts primarily add private state such as saved lists and preferences.  
**Why it matters:** Search-first product behavior should not depend on authentication, while private personalization remains isolated.  
**Implementation consequence:** Public discovery models must remain independent of private consumer data structures.  
**What must not happen:** No requirement that public venue truth depends on login-only data. No mixing saved state into public truth.

## DL-016 — Saved venues are list-native

**Status:** Locked / Approved  
**Stage source:** Stage 3  
**Decision statement:** Saved venues must be modeled as lists/folders from the start, not as a flat favorites-only concept.  
**Why it matters:** This avoids schema rework later and matches the product direction for consumer organization.  
**Implementation consequence:** Private saved-state planning must treat lists as first-class, with venue links attached to canonical venue identity.  
**What must not happen:** No flat single-bucket favorites model that blocks later list behavior.

## DL-017 — Default location and notification settings are first-class private domains

**Status:** Locked / Approved  
**Stage source:** Stage 3  
**Decision statement:** Default location preference and notification settings/consent are explicit structured private domains.  
**Why it matters:** Preferences need clean evolution and must not be buried inside vague profile blobs.  
**Implementation consequence:** Later schema workers must keep these as structured private account-linked state.  
**What must not happen:** No dumping them into a generic profile JSON field with unclear semantics.

## DL-018 — Business entity is first-class and separate from owner users and venues

**Status:** Locked / Approved  
**Stage source:** Stage 4  
**Decision statement:** Business/operator group is a first-class domain, separate from individual owner users and separate from venues.  
**Why it matters:** Commercial state, portal growth, multi-user ownership, and multi-venue management require a proper business layer.  
**Implementation consequence:** Owner-side architecture must model businesses explicitly rather than treating a person or a venue as the business.  
**What must not happen:** No direct collapse of owner user into business, or business into venue.

## DL-019 — One business may manage multiple venues; multiple owner-side users may exist

**Status:** Locked / Approved  
**Stage source:** Stage 4  
**Decision statement:** A business may manage multiple venues, and multiple owner-side users may exist per business and per venue context.  
**Why it matters:** Avoids single-login-per-venue assumptions and supports realistic operator structures.  
**Implementation consequence:** Relationship planning must support business memberships and managed-venue relationships without one-to-one assumptions.  
**What must not happen:** No architecture built around one login per venue.

## DL-020 — Management rights flow through explicit business-to-venue relationships

**Status:** Locked / Approved  
**Stage source:** Stage 4  
**Decision statement:** Venue access comes through an explicit approved business-to-venue management relationship.  
**Why it matters:** This is the core authority bridge between owner-side domains and venue-scoped capabilities.  
**Implementation consequence:** Permissions must derive from explicit approved relationships, not vague owner flags.  
**What must not happen:** No direct person-to-venue authority. No loose owner flag standing in for management rights.

## DL-021 — Claim, verification, active management rights, and permissions are distinct

**Status:** Locked / Approved  
**Stage source:** Stage 4  
**Decision statement:** Claim initiation, verification status, active management rights, and venue-scoped permissions are separate concepts.  
**Why it matters:** Authority chain integrity depends on not collapsing workflow, trust, and live access into one state.  
**Implementation consequence:** Schema planning must support layered authority rather than a single “claimed venue” switch.  
**What must not happen:** No claim-to-access shortcut. No verification-to-access shortcut. No business-membership-to-access shortcut.

## DL-022 — Workflow history is not live authority

**Status:** Locked / Approved  
**Stage source:** Stage 4  
**Decision statement:** Authority workflow records and history are distinct from current live management authority state.  
**Why it matters:** Historical records must not accidentally grant present access.  
**Implementation consequence:** Current-state authority domains must remain separate from claim/verification/workflow history domains.  
**What must not happen:** No deriving live permissions from old workflow events alone.

## DL-023 — Public truth, owner-private data, business-private data, user-private data, workflow data, and commercial state are distinct domains

**Status:** Locked / Approved  
**Stage source:** Stage 4  
**Decision statement:** Public truth, owner-private operational data, business-private data, user-private data, workflow/history, authority workflow, and commercial/subscription state must remain distinct.  
**Why it matters:** Clean separation is essential for trust, privacy, RLS, and future maintainability.  
**Implementation consequence:** Later schema workers must preserve physical/logical separation between these domain families.  
**What must not happen:** No generic metadata blob that mixes public, private, workflow, and commercial concerns.

## DL-024 — Commercial/subscription state attaches primarily to business

**Status:** Locked / Approved  
**Stage source:** Stage 4  
**Decision statement:** Core commercial entitlements and subscriptions attach primarily to the business entity, with venue-scoped overlays where needed.  
**Why it matters:** Billing and portal entitlements are operator-level concerns, not person-level or public venue-truth concerns.  
**Implementation consequence:** Commercial schema planning should center business-linked commercial state.  
**What must not happen:** No primary attachment of subscription state to individual owner logins or public venue truth records.

## DL-025 — Structured specials are distinct from descriptive marketing copy

**Status:** Locked / Approved  
**Stage source:** Stage 5  
**Decision statement:** Discovery-relevant specials must be structured; descriptive free text is a separate content type.  
**Why it matters:** Search/filter-safe discovery claims require queryable structure.  
**Implementation consequence:** Later schema should separate structured special/offer truth from descriptive promotional copy.  
**What must not happen:** No vague promo blob driving public filters or badges.

## DL-026 — Recurring offers and one-off promotions are distinct patterns

**Status:** Locked / Approved  
**Stage source:** Stage 5  
**Decision statement:** Recurring offers and one-off promotions are distinct lifecycle patterns and must not be collapsed.  
**Why it matters:** Timing logic, validity, and discovery eligibility differ materially across these content types.  
**Implementation consequence:** Schema planning must preserve distinct content/lifecycle semantics for recurring vs one-off promotional content.  
**What must not happen:** No single generic promo model that hides recurrence differences.

## DL-027 — Published, valid-current, discovery-eligible, and active-now are distinct states

**Status:** Locked / Approved  
**Stage source:** Stage 5  
**Decision statement:** For dynamic discovery content, publication status, current validity, search/card eligibility, and active-now/ranking claims are separate concepts.  
**Why it matters:** Dynamic content can be visible without being currently active-now or search-safe at all levels.  
**Implementation consequence:** Schema and logic planning must leave room for multiple eligibility/state layers rather than one boolean active flag.  
**What must not happen:** No shortcut where published automatically means active-now, searchable, or ranking-safe.

## DL-028 — Weak, vague, stale, or text-dependent timing must be suppressed rather than guessed

**Status:** Locked / Approved  
**Stage source:** Stage 5  
**Decision statement:** Dynamic discovery claims with weak or ambiguous timing should be suppressed, not inferred optimistically.  
**Why it matters:** Discovery trust is damaged when promotional timing is guessed from poor evidence.  
**Implementation consequence:** Later workers must treat timing confidence as a gating concern for discovery-facing eligibility.  
**What must not happen:** No best-guess active-now or current-valid claims from vague copy alone.

## DL-029 — Tap offering state is distinct from beverage product identity

**Status:** Locked / Approved  
**Stage source:** Stage 5  
**Decision statement:** Tap-list architecture must separate venue offering state from beverage product identity, with light normalization.  
**Why it matters:** A product can exist independently of whether a venue currently pours it, and venue offerings change frequently.  
**Implementation consequence:** Schema planning should separate offering-state records from product/reference identities and optional brewery/style references.  
**What must not happen:** No raw tap-text-only model as strong discovery truth. No collapsing product identity with current offering state.

## DL-030 — Sponsored/commercial state is separate from discovery truth

**Status:** Locked / Approved  
**Stage source:** Stage 5 / Stage 4  
**Decision statement:** Sponsored placement, billing/commercial state, boosts, redemption, and campaign logic are adjacent layers, not public discovery truth.  
**Why it matters:** Trustworthy discovery requires that money and truth remain separate.  
**Implementation consequence:** Commercial overlays must not change the meaning of venue/public truth fields.  
**What must not happen:** No sponsored state treated as proof, confidence, freshness, or canonical venue truth.

---

## Implementation use note

Later schema, SQL, migration, RLS, and verification workers should use this file as a guardrail reference during implementation planning. Where a later convenience decision conflicts with this log, this log wins unless the Database Manager explicitly reopens and changes the decision.
