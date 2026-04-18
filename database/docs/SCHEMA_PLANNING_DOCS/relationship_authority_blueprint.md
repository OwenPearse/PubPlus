# PubPlus — Relationship and Authority Blueprint

## Purpose

This document maps the most important relationship chains and authority paths that later schema workers must preserve.

## 1. Canonical Venue Relationship Spine

### Canonical venue as primary anchor
Canonical venue identity is the anchor point for:
- published venue profile
- published location/geography
- published discovery attributes
- published hours and operational truth
- specials/promotions
- tap offerings
- workflow proposals and reviews
- consumer saved-list references
- owner/business managed-venue relationships

### Design consequence
Venue-linked state should attach to canonical venue identity, not to source IDs, screen-specific models, or ad hoc duplicated venue references.

## 2. Venue to Location / Geography Relationships

### Core relationship
- One canonical venue
- One authoritative published public address family
- One authoritative published map point
- One canonical locality/suburb placement
- One broader geography hierarchy placement

### Design consequence
Live discovery reads should resolve against one authoritative published geography set per venue.

## 3. Venue to Discovery Attribute Relationships

### Core relationship
- One canonical venue
- One coherent truth set per structured attribute family

### Design consequence
Schema should support attribute-family-level clarity and publishability rather than fragmented contradictory truth.

## 4. Venue to Hours / Operational Truth Relationships

### Core relationship
- One canonical venue
- Structured regular hours
- Structured temporary exceptions
- Explicit uncertainty/strength handling
- Derived open-now claim only when justified

### Design consequence
Hours-related reads must be able to distinguish baseline truth, overrides, uncertainty, and derived operational status.

## 5. Venue to Workflow / Publish Relationships

### Core relationship
A canonical venue may link to:
- raw/source intake records
- whole-record proposals
- field-family proposals
- review/decision records
- publish outcomes
- rollback lineage/history

### Authority chain
No actor writes directly into published venue truth except the formal publish workflow.

### Design consequence
Workflow data should point at the affected canonical venue when known, or at proposed candidate identity resolution when not yet resolved.

## 6. Proposal / Review / Publish Chain

### Core chain
- Actor submits or system imports proposal
- Proposal enters staged state
- Review actor evaluates evidence and publishability
- Review outcome records reason/evidence basis
- Publish workflow writes resolved truth or withholds safely
- Prior truth lineage remains inspectable for rollback and audit

### Actor families
- source/import actor
- consumer actor
- owner actor
- admin/reviewer actor

## 7. Consumer Account Relationships

### Core relationships
A consumer account may link to:
- private profile/minimal user state
- default location preference
- notification settings
- saved lists
- saved list membership entries
- consumer-authenticated submissions

### Venue linkage
Saved-list items and submissions should reference canonical venue identity where venue-linked.

### Design consequence
Consumer-private data remains separate from public venue truth and separate from owner/business structures.

## 8. Saved Lists Relationships

### Core relationships
- Consumer account owns many saved lists
- Saved list contains many canonical venues
- Canonical venue may appear in many user lists

### Design consequence
Saved state must be list-native from the start, not a flat favorites-only shortcut.

## 9. Owner / Business / Venue Authority Chain

### Core chain
- Owner user belongs to a business
- Business may have one or more owner users
- Business may have one or more managed-venue relationships
- A managed-venue relationship links one business to one canonical venue
- Venue-scoped permissions attach through that managed-venue relationship
- One venue may have multiple concurrent approved managing businesses

### Non-allowed shortcuts
- direct person-to-venue authority
- business membership alone as venue authority
- portal login alone as venue authority

### Design consequence
The business-to-venue management relationship is the core authority junction.

## 10. Claim / Verification / Access Relationship Chain

### Core chain
- Claim initiation object proposes or requests management authority
- Verification process evaluates supporting evidence/authority
- Managed-venue relationship may be approved, denied, inactive, revoked, or otherwise lifecycle-controlled
- Venue-scoped permission grants are attached through approved relationship state

### Design consequence
Claim history, verification status, active management rights, and permissions must be modeled as distinct linked concepts.

## 11. Owner Submission to Stage 2 Workflow

### Core relationship
Owner-side changes to discovery-relevant content must flow into Stage 2 workflow unless within a narrow approved fast-path.

### Design consequence
Even when owner-linked, submissions are workflow objects first and not automatic public truth writes.

## 12. Business to Commercial State Relationships

### Core relationship
- Business entity is the primary attachment point for subscription/commercial entitlements
- Venue-scoped overlays may attach where needed

### Design consequence
Commercial attachment should not be anchored primarily on individual owner users or directly on public venue truth.

## 13. Venue to Specials / Promotions Relationships

### Core relationship
- Canonical venue may have many structured specials/promotions
- Specials may be recurring-pattern or one-off promotion type
- Timing/validity/discovery-eligibility state belongs to the special/promotion object or its state layer

### Design consequence
Discovery tiers for specials must be derived from structured timing/confidence, not from descriptive text alone.

## 14. Venue to Tap Offering Relationships

### Core relationship
- Canonical venue may have many tap offerings
- Tap offering references beverage product identity
- Beverage product may optionally reference brewery
- Beverage product may optionally reference style/category
- Offering traits belong to offering state, not product identity

### Design consequence
Schema should preserve the split between product reference and venue-specific offering state.

## 15. Admin / Trust Operations Relationships

### Core relationships
Admin actors may link to:
- reviews and decisions
- publish outcomes
- rollback actions
- verification decisions
- integrity/trust checks

### Design consequence
Admin activity should be traceable without collapsing it into public truth or user-facing account models.

## 16. Evidence / Provenance Relationships

### Core relationships
Evidence and provenance may attach to:
- raw/source records
- proposals
- reviews/decisions
- publish outcomes
- verification actions

### Design consequence
Trust, moderation, and auditability require durable attachment between claims and evidence basis.

## Summary Rule

The most important relationship anchors are:
- canonical venue identity for venue-linked truth and workflow
- business-to-venue management relationship for owner-side authority
- structured workflow lineage for any change to published truth
