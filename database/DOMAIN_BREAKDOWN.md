
# PubPlus — Domain Breakdown by Data Area

## 1. Purpose

This document defines the major data domains PubPlus must support and the role of each domain in the system.

It is intentionally high-level and does not define exact tables.

## 2. Domain overview

### 2.1 Venue identity domain

This is the core public entity layer.

It covers the stable identity of a venue, including the idea that one real-world venue should resolve to one canonical published listing.

This domain exists to prevent duplicates, support search consistency, and act as the root for most other public-facing data.

Includes concepts such as:

* venue identity
* venue naming
* venue type/category
* location attachment
* status/visibility state
* published canonical record ownership

### 2.2 Location and geography domain

This domain supports place-based discovery.

Includes concepts such as:

* suburb
* city/region hierarchy
* coordinates
* display locality
* map placement
* simple distance support

This domain must support Melbourne-first usage without blocking expansion.

### 2.3 Discovery attributes domain

This domain holds structured attributes used for searching, filtering, and matching.

Includes concepts such as:

* venue features
* drink categories
* service style tags
* cuisine or food style support if introduced
* relevant discovery metadata used on home/search/map views

This domain should stay highly structured.

### 2.4 Opening hours and availability domain

This domain supports open-now style logic and display.

Includes concepts such as:

* standard opening hours
* special opening exceptions later
* display status
* freshness of operating hours

This is operationally important because stale hours damage trust quickly.

### 2.5 Specials, promotions, and recurring offer domain

This domain supports meal deals, happy hours, and other promotional patterns.

It must support both recurring and one-off records.

Includes concepts such as:

* recurring weekly specials
* date-based one-off promotions
* limited promotions
* meal deals
* happy hour style offers
* future event-adjacent promo display

This is one of the most important future-proofing domains.

### 2.6 Tap list domain

This domain supports future beer and drink tap data.

Includes concepts such as:

* products on tap
* brewery/brand linkage where known
* style/category linkage
* availability state
* optional richer owner-supplied detail later

This should be architecture-ready early, even if data coverage is thin initially.

### 2.7 Media domain

This domain supports venue photos and related display media.

For current direction, only owner-provided media should be supported, not user-uploaded photos.

Includes concepts such as:

* hero images
* gallery images
* display ordering
* moderation/approval state if needed
* owner association

### 2.8 User account and profile domain

This domain supports authenticated user-linked product features.

Includes concepts such as:

* user identity linkage
* saved venues
* preferences
* account settings
* future personalised feed support

Anonymous browsing should remain supported outside this domain.

### 2.9 User preferences domain

This domain powers better search and home recommendations.

Includes concepts such as:

* suburb preferences
* drink preferences
* venue feature preferences
* possibly behavioural preference signals later

This domain should be clearly separate from public venue data.

### 2.10 Saved and user-linked action domain

This domain supports user actions tied to venue records.

Includes concepts such as:

* favourites/saved venues
* future check-ins later if ever added
* future user interaction history if needed

### 2.11 Submission and correction domain

This domain supports user-submitted or owner-submitted changes.

Includes concepts such as:

* proposed changes
* suggested corrections
* supporting notes
* actor identity
* review state
* publish outcome

This domain is critical because user reports are part of the path to fresher live data.

### 2.12 Moderation and publishing domain

This domain governs how data changes move into live truth.

Includes concepts such as:

* review queues
* approval/rejection states
* publish actions
* comparison between proposed and current data
* actor history
* decision audit trail

### 2.13 Provenance and trust domain

This domain records where data came from and how trustworthy it is.

Includes concepts such as:

* source type
* source reference
* import/admin/owner/user origin
* verification state
* freshness state
* auditability

### 2.14 Owner and business domain

This domain supports venue owner participation and future business tooling.

Includes concepts such as:

* business accounts
* ownership relationships
* claims
* claim review
* owner permissions
* future subscription linkage
* future business profile controls

### 2.15 Admin and operational domain

This domain supports internal management.

Includes concepts such as:

* admin roles
* review permissions
* publish permissions
* moderation workflow support
* future data operations tooling

### 2.16 Analytics-supporting domain

This is not a priority modelling area for MVP, but the architecture should not block it.

Includes concepts such as:

* owner-facing insights later
* listing performance tracking later
* future monetisation support
* internal operational reporting later

## 3. Highest priority domains for MVP

The highest priority domains are:

* venue identity
* location and geography
* discovery attributes
* opening hours
* specials/promotions
* user account linkage
* saved venues
* user preferences
* submissions/corrections
* moderation/publishing
* provenance/trust

## 4. Important but secondary early domains

Secondary-but-planned domains are:

* owner/business
* media
* tap lists
* admin operations
* analytics support

## 5. Domain interaction principle

Public discovery should read from clean published domains.

Change-driving workflows should operate through submission, provenance, moderation, and publishing domains.

Owner and user-linked data should remain associated but clearly separated from public venue truth.

