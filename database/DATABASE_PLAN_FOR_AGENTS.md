# PubPlus — Database Stage Plan for Manager Agents

## 1. Purpose

This document defines the recommended stage-manager structure for database planning and later implementation delegation.

The goal is to keep work focused, reduce cross-domain confusion, and protect clean architecture decisions.

## 2. Stage structure overview

### Stage Manager 1 — Core Venue & Discovery Data

**Purpose**
Own the architecture direction for public venue discovery data.

**Scope**

* canonical venue direction
* venue identity rules
* location and suburb support
* coordinates and map support
* search-driving attributes
* opening hours direction
* open-now support direction
* venue features and drink type support
* MVP search/filter readiness

**Outputs**

* high-level domain breakdown for public venue data
* discovery data architecture notes
* risks around duplicate venues and identity handling
* decisions needed for search correctness

### Stage Manager 2 — Moderation, Staging & Provenance

**Purpose**
Own the architecture direction for all proposed, staged, reviewed, and published data flows.

**Scope**

* staging model direction
* proposal/change flow direction
* publish workflow direction
* provenance tracking direction
* trust and freshness state direction
* admin review flow direction
* rejection/approval/audit direction

**Outputs**

* publish workflow outline
* proposal lifecycle definition
* provenance and freshness requirements
* moderation risk analysis

### Stage Manager 3 — Auth, User Data & Permissions

**Purpose**
Own the architecture direction for authenticated user-linked data and role boundaries.

**Scope**

* user-linked records
* saved venues
* preferences
* account-required product actions
* role boundaries between anonymous users, signed-in users, owners, and admins
* data access implications for Supabase/auth integration

**Outputs**

* user data domain outline
* permission boundary recommendations
* authenticated feature storage plan
* risks around mixing public and private data

### Stage Manager 4 — Owner & Business Data

**Purpose**
Own the architecture direction for venue ownership, claims, and future business tooling.

**Scope**

* business account direction
* owner-to-venue relationships
* claim flows
* owner verification pathway direction
* future business-facing account linkage
* future monetisation support readiness

**Outputs**

* owner domain plan
* claims workflow outline
* business-account relationship notes
* future SaaS-readiness considerations

### Stage Manager 5 — Specials, Tap Lists & Future Commerce Extensions

**Purpose**
Own the architecture direction for richer venue-managed dynamic content.

**Scope**

* meal deals and happy hour support
* recurring vs one-off offer direction
* future promo/event-adjacent display readiness
* tap list support direction
* optional future booking/integration adjacency awareness

**Outputs**

* specials domain direction
* recurring/one-off modelling guidance
* tap list architecture notes
* future extension risk notes

## 3. Recommended execution order

### Order 1

Core Venue & Discovery Data

This must happen first because the product is search-first.

### Order 2

Moderation, Staging & Provenance

This must be defined early because the product uses mixed data sources and needs controlled publishing.

### Order 3

Auth, User Data & Permissions

This should follow once search-facing structure is clear.

### Order 4

Owner & Business Data

This should be planned early but implemented after core user/auth/search direction is stable.

### Order 5

Specials, Tap Lists & Future Commerce Extensions

This should be planned in parallel or shortly after core data, because the architecture matters early even if full implementation comes later.

## 4. Working rules for all stage managers

Each stage manager must:

* remain architecture-first unless explicitly instructed otherwise
* avoid direct table design unless the Database Manager requests it
* separate confirmed facts from assumptions
* identify cross-domain dependencies clearly
* flag risks before proposing added complexity
* protect search performance, trust, and maintainability
* keep public truth separate from proposed/staged data

## 5. Escalation expectations

Stage managers must escalate when:

* domain boundaries become unclear
* MVP and future-state needs conflict
* workflow complexity threatens simplicity
* permission boundaries affect multiple domains
* moderation logic changes what should be canonical
