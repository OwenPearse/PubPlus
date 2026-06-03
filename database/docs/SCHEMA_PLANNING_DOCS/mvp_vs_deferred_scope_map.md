# PubPlus — MVP vs Deferred Scope Map

## Purpose

This document separates what must be first-class in the first schema wave from what should be planned but deferred, so later workers do not overbuild.

---

## A. Must Be First-Class in the First Schema Wave

### 1. Canonical public venue truth
Required now because the product is search-first and trust-first.

Includes:
- canonical venue identity
- published venue profile core
- published location/geography core
- structured discovery attributes that drive search and filters
- structured hours and exceptions
- support for coherent truth across Home/Search/Map/Saved/Venue Detail

### 2. Moderation / staging / publish workflow backbone
Required now because live truth cannot be written directly from raw inputs or submissions.

Includes:
- raw/source intake layer
- proposed/staged change layer
- review/decision layer
- published outcome lineage
- reason/evidence basis attachment at meaningful decision points

### 3. Provenance / audit minimums
Required now for moderation safety and later trust debugging.

Includes:
- source provenance
- evidence attachment capability
- decision rationale
- basic lineage/history

### 4. Consumer account and private-state minimums
Required now because authenticated consumer features already exist in scope.

Includes:
- separate consumer account domain
- default location preference
- notification settings
- authenticated consumer submissions into workflow

### 5. Saved lists
Required now because saved venues are list-native by locked decision.

Includes:
- saved lists
- saved list membership tied to canonical venue identity

### 6. Owner / business authority backbone
Required now at least at core structure level so later owner portal work does not force a redesign.

Includes:
- separate owner account domain
- business entity
- owner-to-business membership
- business-to-venue managed relationship
- distinct claim / verification / access / permissions concepts

### 7. Admin/trust operations minimums
Required now so review and publish workflows have a clean authority layer.

Includes:
- separate admin logical domain
- review/publish/rollback authority hooks

### 8. Non-negotiable separation of public, workflow, private, owner, and commercial domains
Required now as an architectural property of the schema.

---

## B. Planned but Deferred from the First Detailed Schema Wave

These should be deliberately planned for, but not fully expanded unless needed immediately.

### 1. Richer consumer profile and personalization
Plan for:
- more profile fields
- personal notes/tags
- richer personalization logic

Defer:
- broad profile expansion beyond minimal MVP needs

### 2. Advanced owner portal operational data
Plan for:
- owner-private operational metadata
- richer venue-management tooling
- more internal owner workflows

Defer:
- broad owner-portal internal tooling that is not needed to establish authority and workflow backbone

### 3. Detailed permission granularity
Plan for:
- venue-scoped capabilities
- role variation within owner-side teams

Defer:
- overly elaborate permission matrices before core authority chain is proven

### 4. Rich specials/promotion extensions
Plan for:
- structured specials model
- recurring vs one-off separation
- eligibility tiers

Defer:
- event-linked promos
- redemption mechanics
- booking logic
- campaign automation
unless directly needed in the next implementation wave

### 5. Rich tap-list ecosystem modeling
Plan for:
- product identity
- brewery/style references
- venue offering state

Defer:
- overly deep catalog/brand taxonomy complexity unless immediate product work requires it

### 6. Commercial overlays beyond core attachment direction
Plan for:
- business-level subscriptions
- venue overlays
- sponsored placement adjacency

Defer:
- complex billing/reporting/campaign systems in the schema pack unless immediate delivery requires them

### 7. Advanced verification / trust operations
Plan for:
- richer fraud/risk workflows
- re-verification cycles
- trust scoring or integrity tooling

Defer:
- advanced operational trust machinery not needed for the first schema foundation

---

## C. Extension-Ready Only

These should be kept architecturally possible, but not materially built in the first schema design unless a later approved stage requires them.

### Consumer-side extensions
- social features
- collaborative lists
- personal recommendations/history systems

### Owner-side extensions
- multi-step internal venue workflows
- deep team-role hierarchies
- owner analytics and CRM-style data

### Specials / commerce extensions
- coupon/redemption systems
- booking integrations
- campaign targeting
- paid boosts logic
- event-promo bundles

### Tap-list extensions
- inventory-level operational tie-ins
- live availability telemetry
- supplier/invoice integrations

### Expansion extensions
- non-Melbourne regional scaling structures beyond what is needed for clean geography design
- more venue-category verticals beyond current pubs/restaurants scope

---

## Practical Rule for Later Workers

If a domain is required to preserve trust, authority, workflow safety, or a locked MVP behavior, it is first-class now.

If a domain is only useful for richer tooling, monetization sophistication, or future product breadth, it should be modeled for extension but not overbuilt into the first schema wave.
