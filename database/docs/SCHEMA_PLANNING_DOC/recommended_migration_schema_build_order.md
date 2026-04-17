# PubPlus — Recommended Migration / Schema Build Order

## Purpose

This document recommends a high-level build order for later schema and migration workers. It is not the final migration file list, but a planning sequence that reduces redesign risk.

## Wave 1 — Foundational Identity and Domain Anchors

### Build first
1. Canonical venue identity backbone
2. Core published venue truth anchor structures
3. Core geography/location structures
4. Consumer / owner / admin logical account-domain anchors
5. Business entity backbone

### Why first
These are the stable anchors that most later domains attach to. Getting them clean early reduces migration churn.

## Wave 2 — Core Public Discovery Truth

### Build second
1. Published venue profile structures
2. Published structured discovery attribute families
3. Published hours / exceptions / operational-truth structures
4. Live discovery-read-safe truth boundaries

### Why second
The MVP is search-first. Core public discovery truth must be queryable and trustworthy early.

## Wave 3 — Workflow / Moderation / Provenance Backbone

### Build third
1. Raw/source intake structures
2. Proposed/staged change structures
3. Review / decision structures
4. Publish lineage / rollback-safe outcome structures
5. Source provenance / evidence / audit minimums

### Why third
Once the public truth anchors exist, the safe change path into them must be established before broader ingestion or owner-edit flows expand.

## Wave 4 — Consumer Private State

### Build fourth
1. Consumer private preferences
2. Default location preference
3. Notification settings
4. Saved lists
5. Saved-list membership
6. Consumer-authenticated submission objects

### Why fourth
These are important MVP/private features, but they should attach to already-stable consumer and venue anchors.

## Wave 5 — Owner / Business Authority Chain

### Build fifth
1. Owner-to-business membership
2. Business-to-venue managed relationship
3. Claim initiation workflow structures
4. Verification state structures
5. Venue-scoped management-rights / permission attachment structures

### Why fifth
Authority modeling depends on having stable business, owner, admin, and canonical venue anchors already in place.

## Wave 6 — Admin / Trust Operations Tightening

### Build sixth
1. Review authority support
2. Verification decision support
3. Rollback/trust operation support
4. Integrity-check and audit-friendly adjunct structures where needed

### Why sixth
This wave strengthens operational safety once the core workflow and authority chain exist.

## Wave 7 — Structured Specials / Promotions

### Build seventh
1. Structured specials backbone
2. Recurring-offer structures
3. One-off promotion structures
4. Timing / validity / eligibility-state support

### Why seventh
This is important, but it should be added after core venue truth and workflow machinery are stable.

## Wave 8 — Tap List Backbone

### Build eighth
1. Beverage product identity/reference
2. Optional brewery/style references
3. Venue-specific tap offering state
4. Offering validity/eligibility support

### Why eighth
This benefits from already having stable venue anchors and workflow/publish patterns.

## Wave 9 — Commercial / Subscription Adjacency

### Build ninth
1. Business-level commercial/subscription attachment structures
2. Venue-scoped overlays where needed
3. Sponsored/commercial adjacency structures kept separate from truth

### Why ninth
Commercial state should attach to the stable business/venue foundation without distorting earlier truth/workflow design.

## Ordering Rules

### Rule 1
Build stable identity anchors before feature domains.

### Rule 2
Build published truth before convenience features that reference it.

### Rule 3
Build safe moderation/workflow before broad write-capable surfaces.

### Rule 4
Build authority chain after the account/business/venue anchors exist.

### Rule 5
Build dynamic discovery extensions after the core truth and moderation model is stable.

### Rule 6
Build commercial adjacency after business structures are stable and clearly separate from truth.

## Practical Warning

Later migration workers should avoid mixing unrelated waves into one convenience migration. The main implementation risk is not lack of features — it is premature coupling across truth, workflow, authority, and commercial domains.
