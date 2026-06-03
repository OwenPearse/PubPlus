
# PubPlus — Database Architecture Decision Log

## 1. Purpose

This document records approved high-level database decisions so future agents do not re-open settled architectural direction unnecessarily.

## 2. Approved decisions

### Decision 1 — PubPlus will use a staging-and-publish architecture

**Status:** Approved

Live product data should come from a published canonical layer. Incoming edits, source imports, owner updates, and user suggestions must flow through a proposed/staged path before publication.

**Reason**
PubPlus depends on trust, freshness, and mixed-source data early on. Direct-write live editing would create data quality and governance problems.

### Decision 2 — Canonical published data must be separate from proposed changes

**Status:** Approved

Published venue truth and incoming suggestions/edits must not be treated as the same layer.

**Reason**
This protects search quality, moderation, and long-term maintainability.

### Decision 3 — Owner/business schema direction is included from the start

**Status:** Approved

Owner claims, ownership linkage, and business-facing account pathways should be planned now even if business UI is delivered later.

**Reason**
Venue-owner participation is a central future state and should not require database redesign later.

### Decision 4 — Tap list support is included in architecture from the start

**Status:** Approved

Tap list support should be planned now, even if actual data coverage and product use remain limited initially.

**Reason**
Tap lists are a meaningful long-term discovery and venue differentiation feature.

### Decision 5 — Search-first product needs drive MVP database priorities

**Status:** Approved

The earliest priority is supporting strong public search and filtering.

**Reason**
Search accuracy is the most important MVP outcome.

### Decision 6 — Anonymous browsing is allowed; stored actions require accounts

**Status:** Approved

Users should be able to search and browse without authentication. Features that store user-linked data require an account.

**Reason**
This keeps product friction low while preserving account-linked personalisation and saved data.

### Decision 7 — Users may suggest changes, but are not the source of truth

**Status:** Approved

Users may submit changes or corrections, but published truth is controlled by admins and later increasingly by verified venue owners.

**Reason**
This improves data freshness without compromising trust.

### Decision 8 — Venue owners are the intended long-term operational source of truth

**Status:** Approved

In the long term, venue owners should manage their own data. Before that, admin teams manage accuracy and publication.

**Reason**
This is the most scalable operational model.

### Decision 9 — Melbourne-first, expansion-ready location direction

**Status:** Approved

The system should support Melbourne first, but location architecture must be cleanly extensible to wider Victoria later.

**Reason**
Product rollout is staged geographically.

### Decision 10 — Simple coordinate distance is acceptable for MVP

**Status:** Approved

Raw-line coordinate distance can be used initially for nearby discovery and filtering.

**Reason**
This is sufficient for MVP so long as the location model stays clean.

### Decision 11 — Events are not a core MVP data-entry priority

**Status:** Approved

Events may be displayed or referenced later, but they are not a primary initial database focus compared with search filters and specials.

**Reason**
Search and structured venue data matter more at MVP.

### Decision 12 — Specials/promotions must support recurring and one-off patterns

**Status:** Approved

The architecture must be able to support both recurring offers and date-specific promotions.

**Reason**
Venue promotions naturally span both patterns.

### Decision 13 — Only owners should upload venue photos

**Status:** Approved

User-uploaded public venue photos are not part of current direction.

**Reason**
This reduces moderation complexity and improves media trust.

### Decision 14 — Trust/provenance data should be stored now even if not shown yet

**Status:** Approved

Source, freshness, and trust metadata should be captured from the beginning.

**Reason**
This avoids expensive retrofitting later.

## 3. Active assumptions

These are currently treated as working assumptions unless changed later:

* admin review will be required for non-trivial publish actions in early phases
* owner claims will likely require verification before elevated editing rights
* search preference matching will influence home/search experiences once user preference data exists
* owner/business tooling will be introduced after search and auth foundations are stable

## 4. Open future decisions

These are not blockers right now, but will need later approval:

* what trust/freshness signals become public-facing
* how strict owner verification must be
* whether booking integrations become structured data or external-link style features
* how owner subscriptions and premium business capabilities map into account entitlements
* what event data, if any, becomes first-class later

## 5. Instruction to future agents

Do not undo these approved decisions unless explicitly instructed by the Software Executive or a higher-level product authority.
