# PubPlus — Consolidated Entity Map

## Purpose

This document identifies the major entity and domain groups PubPlus now clearly requires after consolidation of the locked Stage 1–5 architecture. It is intentionally implementation-facing, but does not define exact tables yet.

## 1. Canonical Public Venue Truth

### Canonical venue identity
- Durable, source-agnostic venue identity
- One canonical published truth per real customer-facing venue at one physical location
- Anchors all venue-linked public, workflow, owner-linked, and private user-linked state

### Published venue profile
- Core public venue identity and presentation
- Public-facing name and canonical display representation
- Core public venue status needed for live discovery surfaces

### Published venue media/contact minimums
- Public-facing image/contact/web presence where approved for live display
- Must remain part of public published truth only when resolved and publishable

## 2. Geography / Location Domain

### Canonical public address
- Structured published address
- Canonical suburb/locality
- Broader geography hierarchy for search, browsing, and future expansion

### Authoritative map point
- Exactly one authoritative published map point for live app use
- Separate from raw source coordinates, proposed corrections, or disputed geodata

### Geographic grouping / hierarchy
- Suburb, locality, region, city grouping structures
- Must support filter/search/grouping without Melbourne-only hardcoding

## 3. Discovery Attribute Domain

### Structured venue attributes
- Discovery-driving structured claims used for filters, badges, search, and grouping
- Examples include amenity/facility/style/category-style families where materially relevant to discovery

### Attribute-family truth sets
- One coherent published truth set per attribute family
- Family-level publishability and confidence rules where required

### Descriptive copy
- Low-risk descriptive/public narrative content if used
- Must remain distinct from structured discovery-driving truth

## 4. Hours and Operational Truth Domain

### Regular hours
- Structured baseline weekly hours

### Exceptions / temporary overrides
- Structured exceptions that override baseline hours for affected periods

### Hours-confidence / uncertainty handling
- Unknown, weak, stale, disputed, pending, and resolved states must remain explicit
- Unknown must not collapse into closed
- Weak/stale must not become open-now

### Derived operational claims
- Derived present-tense claims such as open-now only where supported by sufficiently strong truth
- Must remain separable from the underlying hours truth components

## 5. Moderation / Staging / Publish Workflow Domain

### Raw/source intake
- Imported/source-supplied raw inputs
- External and internal source actor records

### Proposed/staged change objects
- Whole-record proposals
- Field-family proposals
- Consumer submissions
- Owner submissions
- Source/import proposals

### Review / decision objects
- Review actions, review outcomes, reasons, evidence basis, publishability decisions
- Explicit stateful review lifecycle

### Published outcomes / lineage
- Formal publish outcomes
- Version lineage between prior published truth, new published truth, withheld outcomes, and rollback paths

## 6. Provenance / Evidence / Audit Domain

### Source provenance
- Source system, source reference, freshness, capture context

### Evidence records
- Evidence objects attached to proposals, decisions, or published outcomes
- Supports trust and auditability

### Audit / decision rationale
- Internal reasons for meaningful review/publish/rollback decisions
- Must remain durable and queryable

### History / lineage
- History of what changed, why, by whom, and on what evidence basis

## 7. Consumer Account and Private State Domain

### Consumer account domain
- Logical consumer account identity for app users
- Separate logical domain from owner and admin

### Minimal consumer profile
- Minimal app-facing user identity/profile data only

### Consumer private preferences
- Default location as a first-class structured preference
- Notification consent/settings as explicit structured private state

### Consumer submissions
- Venue-linked or discovery-linked submissions from authenticated consumers
- Feeds workflow only; never mutates public truth directly

## 8. Saved Lists and Consumer Personal Organization Domain

### Saved lists
- List-native saved venues model from the start
- User-owned named lists/folders

### Saved list membership
- Venue-to-list linkage using canonical venue identity

### Optional future personal metadata
- Private notes/order/preferences if ever added later
- Must stay clearly private and outside public truth

## 9. Owner / Business / Managed Venue Domain

### Owner account domain
- Logical owner account identity for web portal users
- Mandatory 2FA
- Separate from consumer/admin domains

### Business entity
- First-class operator/business entity
- Primary attachment point for subscriptions and commercial entitlements

### Owner-to-business membership
- Owner-side user membership in a business
- Separate from venue access

### Business-to-venue management relationship
- Explicit approved management relationship
- May be non-exclusive
- Supports multiple businesses per venue and multiple venue relationships per business

### Venue-scoped owner permissions
- Permissions granted through approved business-to-venue relationship
- Distinct from claim status, verification state, or portal membership

### Owner-private operational data
- Owner-visible/private operational data about managed venues
- Must remain outside public truth and separate from business-commercial state

## 10. Authority / Claim / Verification Workflow Domain

### Claim initiation objects
- Claim requests and supporting workflow objects

### Verification state
- Verification outcomes/status distinct from access and permissions

### Management-rights state
- Active or inactive management rights attached to approved business-to-venue relationship

### Permission grants
- Venue-scoped capabilities attached through authority chain
- Distinct from claim initiation and verification history

### Authority workflow history
- History of claims, checks, decisions, grant/revoke actions

## 11. Specials / Promotions Domain

### Structured specials
- Structured discovery-relevant specials/offers
- Separate from descriptive marketing copy

### Recurring offer pattern
- Pattern-based recurring offers such as weekly/nightly structures

### One-off promotion / temporary offer
- Date-bounded or temporary promotional objects

### Timing / validity state
- Published state
- Valid-current state
- Discovery eligibility state
- Active-now state
- Suppression where timing is weak, stale, vague, or ambiguous

### Descriptive promo copy
- Marketing description adjacent to structured offer state, but not a substitute for it

## 12. Tap List Domain

### Beverage product identity
- Product reference/identity layer

### Optional brewery reference
- Brewery/manufacturer reference where used

### Optional style/category reference
- Beverage style/category reference where used

### Venue offering state
- Venue-specific offering on tap
- Distinct from product identity
- Includes offering traits such as guest/rotating/limited

### Offering validity / discovery eligibility
- Published, valid-current, search-safe, and active-now distinctions as required

## 13. Commercial / Subscription Adjacency Domain

### Business subscription / plan state
- Subscription attachment at business level
- Entitlement and plan state

### Venue-scoped overlays
- Venue-level usage/access overlays where needed

### Sponsored/commercial visibility overlays
- Sponsored placements, boosts, campaign state if introduced later
- Must remain separate from truth/confidence/publishability

### Billing/commercial history
- Commercial lifecycle and billing-adjacent records
- Separate from operational and public truth domains

## 14. Admin / Trust Operations Domain

### Admin account domain
- Internal-only admin identity domain
- Separate logical domain

### Review/approval operations
- Admin review, publish, rollback, withholding, and trust operations

### Integrity / trust monitoring
- Operational trust checks, conflict review, audit inspection, and future verification controls

## 15. Cross-Cutting Relationship Anchors

### Canonical venue anchor
- Canonical venue identity is the anchor for:
  - published venue truth
  - location
  - hours
  - discovery attributes
  - specials
  - tap offerings
  - proposals/submissions
  - saved list references
  - managed venue relationships

### Actor domain separation
- Consumer actors
- Owner actors
- Admin actors
- Source/import actors
- Must remain logically distinct even if shared infrastructure exists

## Implementation Notes

- This entity map is intended to guide later schema workers toward clean separation and migration-safe modeling.
- It deliberately avoids exact table lists, field sets, or SQL structures.
- Domains listed here should be treated as first-class planning boundaries rather than optional conveniences.
