# PubPlus — State / Lifecycle Model Summary

## Purpose

This document summarizes the major lifecycle and state families the schema must support. It defines the kinds of states later workers must preserve, without prescribing exact table structures.

## 1. Proposal / Review / Publish Lifecycle

### Scope
Applies to venue truth changes, discovery attributes, geography, hours, specials, tap-list changes, and other moderated public-facing changes.

### Core lifecycle
- raw/source captured
- proposed/staged
- under review
- decisioned
- published
- withheld
- rejected
- superseded
- rolled back/corrected where needed

### Notes
- Whole-record and field-family proposals both exist
- No direct write path into published truth outside formal publish workflow
- Meaningful decisions retain reason/evidence basis

## 2. Published Truth Lineage Lifecycle

### Scope
Applies to canonical public truth domains.

### Core lifecycle concepts
- no published truth yet
- published current truth
- superseded prior truth
- withheld due to insufficient confidence
- restored prior truth after rollback where defensible
- removed/retired where appropriate without history destruction

### Notes
Rollback is lineage-preserving, not destructive.

## 3. Hours / Open-Now State Family

### Scope
Operational venue hours and derived present-tense operational claims.

### Core state concepts
- regular hours known
- exception known
- hours unknown
- hours partial
- hours weak/stale
- hours disputed/pending
- strong enough for open-now derivation
- not strong enough for open-now derivation

### Rules
- Unknown must not become closed
- Weak/stale must not become open-now
- Exceptions override regular hours for affected periods

## 4. Geography / Location Truth State Family

### Core state concepts
- published authoritative location
- proposed correction
- disputed/weak geo claim
- withheld pending confirmation
- superseded prior location truth

### Notes
Geography is a high-risk family and should preserve stronger publishability controls.

## 5. Discovery Attribute Truth State Family

### Core state concepts
- structured attribute proposed
- reviewed
- published
- withheld
- corrected/replaced
- retired if no longer true

### Notes
Attribute-family-level publishability may be stricter for search-driving claims.

## 6. Consumer Private State Family

### Scope
Consumer preferences and personal organization.

### Core state concepts
- consumer account exists or not
- default location set / not set
- notification settings set / not set
- saved list created / edited / archived/deleted
- venue saved into list / removed from list

### Notes
These are user-private lifecycle states, not public-truth states.

## 7. Owner / Business Relationship State Family

### Scope
Owner-side access and business structures.

### Core state concepts
#### Owner account
- created
- active
- secured with required 2FA
- suspended/deactivated if needed later

#### Business membership
- invited/proposed
- active
- removed/revoked

#### Managed-venue relationship
- requested
- under review
- approved
- active
- inactive
- revoked/ended
- denied

### Notes
Management state is distinct from verification and permissions.

## 8. Claim / Verification / Access Lifecycle

### Scope
Authority workflow for owner-side access.

### Core state concepts
#### Claim
- initiated
- pending review
- supported/unsupported
- approved/denied/withdrawn

#### Verification
- not started
- pending
- verified
- failed/denied
- expired/recheck-needed if introduced later

#### Management rights
- not granted
- granted active
- inactive
- revoked

#### Venue permissions
- not granted
- granted
- modified
- revoked

### Notes
These are linked but distinct lifecycle families.

## 9. Dynamic Content Lifecycle for Specials / Promotions

### Scope
Structured specials and promotions.

### Core lifecycle
- draft/proposed
- under review
- published
- valid current
- scheduled upcoming
- paused
- expired
- retired/removed
- corrected/replaced

### Discovery eligibility layer
A special may independently be:
- detail-display safe
- card/badge safe
- filter/search safe
- active-now/ranking safe
- suppressed for weak/vague timing

### Notes
Published does not imply valid-current.
Valid-current does not imply active-now.

## 10. Tap Offering Lifecycle

### Scope
Venue tap-list state and related discovery claims.

### Core lifecycle
- proposed/drafted
- published
- valid current
- uncertain/stale
- suppressed
- removed/replaced

### Discovery eligibility concepts
- detail-display safe
- filter/search safe if sufficiently structured/current
- active-now/currently-on-tap safe only where strong enough

### Notes
Venue offering state must remain separate from beverage product identity lifecycle.

## 11. Commercial / Subscription Lifecycle

### Scope
Business-level subscription and commercial overlays.

### Core lifecycle concepts
- no subscription
- trial/provisional if used
- active
- paused
- cancelled/ended
- venue-scoped overlay active/inactive as needed
- sponsored campaign active/inactive/scheduled if used later

### Notes
Commercial lifecycle must not alter truth lifecycle or moderation status.

## 12. Review / Admin Trust Operations Lifecycle

### Scope
Admin review, moderation, verification, rollback, and trust operations.

### Core lifecycle concepts
- review opened
- evidence gathered
- decision recorded
- publish/withhold/reject action taken
- follow-up/correction action taken
- audit trail retained

## Cross-Cutting Rule

Later schema workers should model current-state needs and history/audit needs as distinct concerns. Current truth, current rights, and current validity must be easy to query without destroying lineage and review history.
