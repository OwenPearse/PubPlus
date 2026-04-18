# PubPlus — Domain Boundary Map

## Purpose

This document defines the separations that later schema workers must preserve. It is a guardrail pack designed to prevent domain collapse, trust leakage, and authority confusion.

## 1. Published Truth vs Staged / Workflow Truth

### Must remain separate
- Live published venue truth
- Proposed/staged changes
- Review objects
- Decision history
- Rollback history

### Why
The live app must read from resolved published truth only. Workflow state, pending submissions, rejected changes, ambiguous proposals, and review history must never be treated as live discovery truth.

### Guardrail
Submission is not truth. Workflow history is not published truth.

## 2. Published Truth vs Raw / Source Data

### Must remain separate
- Canonical published venue truth
- Raw imported/source-provided inputs
- Source references and capture metadata

### Why
Raw data can be weak, stale, partial, duplicated, or disputed. Canonical truth must be resolved independently of raw intake shape.

### Guardrail
Source IDs and source payloads do not define canonical identity or live truth.

## 3. Public Truth vs Consumer Private Data

### Must remain separate
- Public venue truth used by Home/Search/Map/Saved/Venue Detail
- Consumer account data
- Consumer preferences
- Consumer notification settings
- Saved lists
- Optional future personal notes

### Why
Consumer-private state is user-specific and must not pollute shared discovery truth.

### Guardrail
Private user state is never a public venue attribute.

## 4. Public Truth vs Owner-Private Operational Data

### Must remain separate
- Public discovery truth
- Owner-private operational records
- Owner portal metadata
- Internal owner-side management data

### Why
Owner operational data may inform workflow, but is not automatically publishable truth.

### Guardrail
Portal access or owner-supplied state does not equal published truth.

## 5. Public Truth vs Commercial / Sponsored State

### Must remain separate
- Canonical venue truth and trust/confidence
- Sponsored placement state
- Subscription status
- Commercial entitlements
- Boost/campaign logic

### Why
Commercial state must never alter what is treated as true, current, trustworthy, or discoverable on a truth basis.

### Guardrail
Sponsored/commercial state is not truth, confidence, or moderation approval.

## 6. Consumer Domain vs Owner Domain vs Admin Domain

### Must remain separate
- Consumer accounts
- Owner accounts
- Admin accounts

### Why
They represent different authority models, different risk levels, and different access needs.

### Guardrail
No generic multi-role account model that collapses consumer, owner, and admin into one logical account domain.

## 7. Auth Identity vs Permission / Authority Model

### Must remain separate
- Login identity
- Business membership
- Venue management rights
- Venue-scoped permissions
- Claim/verification state

### Why
Identity alone does not define authority. Authority must flow through explicit layered relationships.

### Guardrail
No person-to-venue authority shortcut. No portal-login shortcut. No business-membership shortcut.

## 8. Business Entity vs Owner User vs Venue

### Must remain separate
- Business/operator entity
- Owner-side user identity
- Venue/canonical venue truth

### Why
Businesses may manage multiple venues, multiple owner users may belong to one business, and one venue may have multiple concurrent managing businesses.

### Guardrail
Do not model venue authority as a property of a single person or a property directly embedded on the venue.

## 9. Claim vs Verification vs Management Rights vs Permissions

### Must remain separate
- Claim initiation
- Verification state
- Management relationship activation
- Venue-scoped permission grants

### Why
These are different state families with different meanings and lifecycles.

### Guardrail
No claim-to-access shortcut. No verification-to-access shortcut.

## 10. Current-State Domains vs Workflow / History Domains

### Must remain separate
- Current authority state
- Current published truth
- Current valid dynamic content state
- Historical submissions, reviews, claims, and prior states

### Why
Current truth and current rights need clean operational reads, while history must stay auditable and lineage-preserving.

### Guardrail
History objects must not be used as if they were the current state record.

## 11. Structured Discovery Claims vs Descriptive Copy

### Must remain separate
- Structured discovery-driving data
- Descriptive or marketing copy

### Why
Filters, badges, search, and ranking require structured trustworthy claims. Free text may be useful for display but cannot substitute for structured truth.

### Guardrail
No raw free-text discovery model.

## 12. Structured Specials vs Descriptive Marketing Copy

### Must remain separate
- Structured specials/promotions used for discovery logic
- Descriptive promo/marketing text

### Why
Discovery claims about specials require structured timing and offer logic.

### Guardrail
Free text alone is not enough for strong discovery-facing claims.

## 13. Recurring Offers vs One-Off Promotions

### Must remain separate
- Pattern-based recurring offer logic
- Date-bounded one-off promotion logic

### Why
They have different timing models, validation rules, and lifecycle behavior.

### Guardrail
Do not collapse weekly recurring specials and temporary promotions into one vague promo object.

## 14. Published vs Valid-Current vs Discovery-Eligible vs Active-Now

### Must remain separate
- Published existence
- Currently valid timing window
- Safe-for-search/filter/badge eligibility
- Strong active-now claim

### Why
A thing can be published but not currently valid, valid but not safe for a specific discovery tier, or valid but insufficiently strong for active-now.

### Guardrail
Published does not imply active-now. Valid does not imply ranking-safe.

## 15. Hours Truth vs Derived Open-Now Claim

### Must remain separate
- Structured regular hours
- Exceptions
- Uncertainty state
- Derived open-now claim

### Why
Open-now is a higher-strength derivative claim and must only exist when underlying truth is sufficiently reliable.

### Guardrail
Unknown is not closed. Weak/stale is not open-now.

## 16. Tap Offering State vs Beverage Product Identity

### Must remain separate
- Product identity/reference
- Brewery reference
- Style/category reference
- Venue-specific on-tap offering state

### Why
A product may exist independently of whether a venue currently offers it, and a venue offer may have temporary traits independent of product identity.

### Guardrail
Rotating/guest/limited are offering traits, not proof of specific current-product availability.

## 17. Submission Objects vs Published Objects

### Must remain separate
- User submissions
- Owner submissions
- Source/import submissions
- Published venue/special/tap truth

### Why
Submissions are inputs to workflow, not live truth objects.

### Guardrail
No direct submission write path into published truth.

## 18. Operational Venue Truth vs Feature-Specific Availability Truth

### Must remain separate
- Venue open/closed truth
- Food availability
- Event availability
- Special availability
- Access/entry-specific conditions

### Why
A venue being open does not automatically prove other present-tense availability claims.

### Guardrail
Venue-open truth must not imply food/event/special/access availability.

## 19. Public Venue Identity vs Source-System Identity

### Must remain separate
- Canonical venue identity
- External/import source IDs

### Why
Canonical identity must survive source changes and source disagreement.

### Guardrail
Source IDs never define canonical identity.

## 20. Geographic Published Truth vs Proposed / Disputed Geo Corrections

### Must remain separate
- Authoritative published address/map point
- Proposed location corrections
- Raw source coordinates

### Why
Geography is high-risk for trust and search quality.

### Guardrail
No weak or disputed location truth leaking into live discovery.

## Implementation Consequence

Any later schema, SQL, migration, or RLS design that weakens these boundaries should be treated as non-compliant with the locked architecture.
