# PubPlus — Database Architecture Direction

## 1. Purpose

This document defines the high-level database architecture direction for PubPlus.

PubPlus is a mobile app for discovering pubs and bars, initially in Melbourne, with future expansion into wider Victoria and beyond. The database must support a search-first MVP while also laying foundations for trusted venue data, owner-managed updates, moderation workflows, user-linked data, and future B2B monetisation.

The database is a core product asset. PubPlus depends on data quality, trust, freshness, and structure more than on raw application complexity.

## 2. Core architecture principle

PubPlus should use a **staging-and-publish architecture**.

Live app experiences must read from a clean, canonical, published layer. Incoming changes from imports, admins, owners, or users must pass through separate proposed or staged layers before becoming published truth.

This protects trust, prevents accidental corruption of live data, and allows the product to scale from mixed-source bootstrapping into owner-managed data over time.

## 3. Architectural goals

The database direction must:

* support fast, accurate venue discovery
* keep published data clean and stable
* preserve provenance and freshness metadata
* allow mixed-source ingestion in early phases
* support review, moderation, and publishing workflows
* enable future owner-managed listings without redesigning core data
* support account-linked user data without forcing login for browsing
* remain simple in MVP while avoiding short-sighted shortcuts
* fit naturally within Supabase/Postgres

## 4. Primary data layers

### 4.1 Published canonical layer

This is the live, trusted layer used by the app for:

* search
* map
* venue detail
* saved venues
* home recommendations
* preference matching

This layer should contain the single published truth used by the product.

### 4.2 Proposed and staged layer

This layer holds incoming changes before publication, including:

* imported source data
* owner-submitted edits
* user-submitted corrections
* admin-created updates
* future structured refresh workflows

This layer exists so changes can be reviewed, compared, approved, rejected, merged, or published.

### 4.3 Ownership and business layer

This layer handles:

* venue claims
* owner accounts
* venue-to-owner relationships
* permissions boundaries
* future business tooling
* future monetised owner features

This must remain clearly separated from public venue discovery data.

### 4.4 User-linked product layer

This layer handles:

* saved venues
* user preferences
* account-linked settings
* change submissions
* future review/check-in style data if introduced later

Browsing and searching should remain available without an account, but stored user actions require authentication.

## 5. Core design principles

### 5.1 Single published truth

There should be one published venue truth for the product at any point in time. The app should not read directly from mixed raw source data.

### 5.2 Separation of truth and suggestion

Canonical published records must remain separate from suggestions, edits, imports, and owner proposals.

### 5.3 Provenance is first-class

Important records should preserve where data came from, how it entered the system, and who changed it.

### 5.4 Freshness is first-class

Important records should carry freshness and update context so the system can reason about stale data later.

### 5.5 Structure over free text

Search-driving information should be stored as structured data wherever possible. Free text may exist as supporting detail, but not as the main search/filter substrate.

### 5.6 MVP simplicity without future damage

The MVP should stay focused on core discovery, but not at the cost of creating flat, hard-to-govern records that break once owners and moderation workflows arrive.

## 6. MVP product support requirements

The architecture must support these product needs at launch or near-launch:

* suburb-based discovery
* coordinate-based simple distance filtering
* open now logic
* meal specials
* drink categories
* venue features
* map presence
* favourites/saved venues
* account-linked user preferences
* user-submitted changes
* admin-managed review and publishing

Events are not a primary MVP data-entry focus, but the architecture should not block future event or promotional display.

## 7. Future-ready requirements

The architecture should also be ready for:

* owner-managed listing updates
* recurring and one-off promotions
* tap lists
* owner-uploaded photos
* venue claims
* admin moderation tooling
* venue-level trust indicators
* analytics and monetisation support
* eventual expansion beyond Melbourne

## 8. Location direction

PubPlus is Melbourne-first, but the location model should be expansion-ready.

The architecture should not assume only one city forever. It should allow clean support for:

* Melbourne suburbs now
* regional Victoria later
* additional cities/states later

Distance can initially be raw-line coordinate distance. This is acceptable for MVP, provided the location model remains clean and queryable.

## 9. Trust model direction

Trust should be recorded internally from the start, even if not fully surfaced in the UI yet.

The database direction should support:

* source type
* verification state
* review state
* publish state
* last updated timing
* actor type responsible for change

## 10. Architectural boundaries

The database architecture should not:

* write every incoming change directly into live records
* merge owner, admin, and user edits into one uncontrolled flow
* rely on loose free text for key searchable fields
* overbuild rarely used domains before core search works
* mix business operations data into public browsing structures

## 11. Outcome

PubPlus should have a clean, trust-aware, extensible database foundation that supports a strong search-first MVP and evolves naturally into a moderated, owner-managed venue platform.

---
