# PubPlus Frontend PRD

## 1. Product overview

PubPlus is a cross-platform mobile app that helps users discover pubs and bars in Melbourne using structured, trustworthy venue data.

The product is built to answer practical nightlife questions such as:

* where should I go tonight
* which venues nearby have trivia or live music
* which pub has a certain beer on tap
* where can I find a meal special in a specific suburb
* which venue has enough useful info for me to trust going there

The frontend must present this information in a clean, fast, minimal, and premium-feeling mobile experience.

## 2. Frontend objective

The frontend exists to help users quickly discover relevant venues and confidently decide where to go.

It must:

* feel polished and modern
* work well on both iOS and Android
* prioritise simple navigation
* surface structured data clearly
* handle incomplete venue data gracefully
* support future growth without major redesign

## 3. Platform and scope

### Platform

* Cross-platform mobile app
* iOS and Android
* Single shared frontend codebase

### Recommended stack

* React Native
* Expo

### Out of scope for frontend MVP

* venue-owner dashboards
* public reviews
* social posting/community feeds
* booking flows
* loyalty programs
* advanced AI chat UI
* pub crawl generation UI

## 4. Product principles

The frontend must be:

* mobile-first
* minimalistic
* visually polished
* fast to browse
* easy to understand
* structured rather than cluttered
* resilient to partial or stale data
* built with reusable design patterns

The design should avoid:

* overly dense screens
* giant nested flows
* unnecessary animations
* excessive modal usage
* large, confusing component files

## 5. Primary users

### Main users

* people deciding where to go tonight
* pub-goers and bar-goers in Melbourne
* users looking for drinks, specials, or events
* users comparing multiple nearby venues

### User needs

Users need to:

* open the app and see useful options quickly
* browse by suburb, map area, or relevant suggestions
* filter venues by what matters to them
* inspect venue details with enough confidence to act
* save venues for later

## 6. Core frontend promise

The frontend should make PubPlus feel like a premium hospitality discovery app, not a generic venue directory.

## 7. Information architecture

The app should use five primary tabs:

1. Home
2. Search
3. Map
4. Saved
5. Profile

## 8. Screen overview

### Home

Purpose:

* default entry point
* personalised and contextual suggestions
* highlight nearby venues, events, specials, and timely recommendations

Key content:

* nearby suggestions
* suburb-based suggestions
* day/time-aware cards
* featured categories like trivia tonight, parma night, live music, Guinness nearby

### Search

Purpose:

* structured venue discovery through filters and list browsing

Key content:

* suburb selector
* filter controls
* result list
* sort options
* quick filter chips

### Map

Purpose:

* visual discovery by location and area

Key content:

* venue pins
* map clusters
* preview cards
* map-area refresh behaviour
* quick open to venue details

### Saved

Purpose:

* view favourited venues
* future home for pub crawl planning

Key content:

* saved venue list
* grouped or sortable saved items later

### Profile

Purpose:

* account and preference management

Key content:

* profile basics
* saved preferences
* preferred suburbs
* drink interests
* event interests
* account actions

## 9. Core user flows

### Flow 1: Discover from home

* user opens app
* sees timely suggestions
* taps a venue or category
* views venue details
* decides whether to save or visit

### Flow 2: Search with filters

* user opens Search
* selects suburb and filters
* browses venue list
* opens a venue
* compares results and decides

### Flow 3: Explore by map

* user opens Map
* browses visible area
* taps a pin or preview card
* opens venue detail page

### Flow 4: Save venues

* user opens a venue
* taps save
* venue appears in Saved tab

### Flow 5: Submit correction or new venue

* user opens submission flow
* submits correction or new venue suggestion
* frontend confirms that review is required before publication

## 10. Core frontend features

The frontend must support:

* authentication entry points
* home feed
* structured search and filtering
* map browsing
* venue detail pages
* saving/favouriting
* profile/preferences
* correction/new venue submission forms
* light and dark mode
* clear loading, empty, and error states

## 11. Venue detail page requirements

Each venue page should support display of:

* venue name
* venue type
* address
* suburb
* map location
* opening hours
* photos
* tap list
* drinks highlights
* meal specials
* recurring special nights
* events
* venue features
* save action
* data trust/freshness messaging where appropriate

The page should prioritise readability and scanning over density.

## 12. Search and filter requirements

MVP search is structured, not natural-language based.

Users should be able to filter by:

* suburb
* open now
* venue type
* drink brand/type
* meal special type
* day-based specials
* event type
* venue features

The frontend must present filters in a way that feels powerful without feeling complex.

## 13. UX requirements

The frontend must:

* load quickly
* keep navigation obvious
* minimise taps to useful results
* support one-handed mobile use where practical
* degrade gracefully when data is incomplete
* keep lists and cards visually clean
* avoid overwhelming the user with too much text

## 14. Design system direction

The frontend should use:

* a small, consistent colour system
* a small set of typography styles
* reusable spacing rules
* reusable card patterns
* reusable chips/tags/badges
* consistent icon usage
* consistent light and dark themes

Visual direction:

* premium
* minimal
* sleek
* hospitality-focused
* not generic
* not crowded

## 15. State handling requirements

The frontend must define clear behaviour for:

* loading states
* empty states
* error states
* partial data states
* unauthenticated states
* offline/poor connection states where relevant

It must never assume all venue records are fully complete.

## 16. Data trust presentation

Because data quality is central to PubPlus, the frontend should be designed to present trust clearly.

This includes support for:

* last updated or last checked messaging where appropriate
* confidence/completeness cues if approved later
* safe fallback UI when venue data is partial
* clear review messaging for user submissions

The frontend must not imply certainty where the product does not have it.

## 17. Performance and maintainability requirements

The frontend architecture should:

* support reusable components
* avoid giant files and giant screens
* keep feature boundaries clear
* remain easy for worker agents to extend
* support staged feature additions later
* minimise refactor risk through clean structure

## 18. Accessibility and usability

The frontend should aim for:

* readable font sizing
* strong contrast in both themes
* tap targets suitable for mobile
* clear labels and predictable navigation
* low-friction interaction patterns

## 19. Success criteria

The frontend is successful if users can:

* open the app and quickly understand what to do
* find relevant venues efficiently
* trust venue pages enough to make decisions
* save venues easily
* return to the product regularly without confusion

## 20. Stage 1 frontend deliverables

The frontend manager should produce:

* navigation definition
* screen inventory
* component system overview
* design rules
* state handling rules
* frontend file/folder philosophy
* dependencies on backend contracts

## 21. Final product standard

The PubPlus frontend should feel intentionally designed, minimal, and trustworthy.

It should help users move from:
**“I want to go out”**
to
**“I know where I’m going”**
as quickly and confidently as possible.
