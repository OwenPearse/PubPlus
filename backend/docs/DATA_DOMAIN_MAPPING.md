
---

## File: `backend/docs/DATA_DOMAIN_MAPPING.md`

```md
# PubPlus Backend Data Domain Mapping

## Purpose

Translate the completed database architecture into backend-facing domain ownership so stage managers and worker agents know which data domains the backend reads from, writes to, and must keep separated.

## Current stage

Planning-to-implementation bridge document created before stage-manager execution.

## Summary

The PubPlus database architecture is already complete and migrated in the development Supabase environment.

The backend must therefore align to the existing data architecture rather than invent a new one.

This document maps database domain concepts into backend usage rules across:

- public read paths
- consumer-private writes
- moderation/workflow writes
- internal/admin reads/actions
- future owner/business/commercial compatibility

The backend should understand data domains as product and trust boundaries, not just storage areas.

---

## Core mapping principles

### 1. Data domains are not interchangeable

The backend must not collapse these domains:

- published public truth
- workflow/staging/proposed changes
- moderation/audit history
- consumer-private state
- owner/business authority state
- commercial/subscription state

These are distinct for product trust, access control, and future scalability reasons.

### 2. Backend reads and writes are domain-specific

Each endpoint and service should know which domain it is allowed to interact with.

For example:

- Search should read published truth only
- save/unsave should write consumer-private state only
- consumer submissions should write workflow/moderation-bound records only
- internal moderation may read workflow state and trigger formal publish paths

### 3. The database architecture is authoritative

If there is tension between implementation convenience and database domain separation, the backend should preserve the database boundary.

The backend is an application layer on top of the schema foundation, not a schema redesign layer.

---

## Domain 1 — Published public truth

## Purpose

This is the canonical public venue data used to power the consumer discovery product.

## Typical content

This domain includes published/publicly consumable truth such as:

- venue identity
- venue type
- address and suburb
- coordinates/geography
- published hours
- published exceptions
- published features
- published meal specials
- published events
- published tap/drink highlights
- public contact links
- public venue photos/media references
- derived public operational claims where supported from published truth

## Backend read usage

Public consumer endpoints may read this domain for:

- Home
- Search
- Map
- Venue Detail
- Saved list venue rendering

Internal/admin endpoints may also read it when reviewing or operating.

## Backend write usage

Public consumer endpoints must not write directly to this domain.

Changes to this domain should happen only through approved workflow/publish paths.

## Examples of backend services that depend on this domain

- discovery query services
- venue detail aggregation
- open-now computation
- card/detail serializer logic

---

## Domain 2 — Workflow / staging / proposed changes

## Purpose

This domain holds proposed changes and submissions that have not yet become published truth.

## Typical content

Examples include:

- correction proposals
- new venue suggestions
- staged candidate changes
- moderation-bound structured submission data
- pre-publication review data

## Backend read usage

Internal/admin moderation tools may read this domain.

Public consumer endpoints should not expose raw workflow state.

## Backend write usage

Consumer submission endpoints may write into this domain through structured, moderation-safe intake logic.

Internal moderation actions may update status/decision state in this domain or trigger formal publish operations depending on the architecture.

## Important rule

Workflow/staging data is not public truth and must not be treated as such in Search, Map, Home, or Venue Detail.

---

## Domain 3 — Moderation / audit / decision history

## Purpose

This domain preserves operational trust, reviewability, and internal accountability.

## Typical content

Examples include:

- moderation status
- decision records
- operator attribution
- audit notes
- review timestamps
- action history

## Backend read usage

Internal/admin endpoints may read this domain for:

- queue triage
- moderation detail
- review history context
- issue handling

Public consumer endpoints must not expose internal moderation history.

## Backend write usage

Internal/admin moderation endpoints may write to this domain when:

- recording decisions
- adding notes
- attributing operator actions

Consumer endpoints must not write decision history or operator actions.

---

## Domain 4 — Consumer-private state

## Purpose

This domain stores user-specific private data for the consumer app experience.

## Typical content

Examples include:

- saved venues
- profile basics
- preferences
- account-linked personal settings
- future notification settings/placeholders

## Backend read usage

Authenticated consumer endpoints may read this domain for:

- Saved
- Profile
- preferences
- authenticated enrichment such as `is_saved`

Internal/admin access should be limited and justified where needed.

## Backend write usage

Authenticated consumer endpoints may write this domain for:

- save/unsave actions
- profile updates
- preference updates

These writes do not require moderation.

## Important rule

Consumer-private state must remain separate from public truth and separate from future owner/business state.

---

## Domain 5 — Public read-model enrichment data

## Purpose

This is not necessarily a separate schema domain, but a backend usage concept describing data used to enrich public responses without changing public truth semantics.

## Examples

- authenticated `is_saved`
- computed distance
- backend-computed `open_now`
- light preference-aware ordering

## Backend usage

This enrichment may be added by backend read services when safe and appropriate.

## Important rule

Enrichment must not:

- leak internal workflow state
- change the meaning of public truth
- make public endpoints unusable when unauthenticated

---

## Domain 6 — Owner / business authority state

## Purpose

This domain supports future owner and operator systems and must remain structurally separate even if not used by the MVP consumer app.

## Typical content

Examples include:

- business/operator entities
- business-to-venue management relationships
- claims and verification states
- owner-side user relationships
- access rights for owner systems

## Backend read usage in MVP

Generally deferred for public consumer APIs.

Internal tooling may later reference some of this domain, but MVP consumer backend work should not depend on it.

## Backend write usage in MVP

Deferred.

## Important rule

Consumer identity must not be blurred into owner/business authority models.

Public consumer APIs should be designed so future owner APIs can coexist cleanly later.

---

## Domain 7 — Commercial / subscription / entitlement state

## Purpose

This domain supports future SaaS and business model systems.

## Typical content

Examples include:

- business subscriptions
- entitlements
- billing adjacency
- plan state
- commercial usage overlays

## Backend read usage in MVP

Not part of the consumer MVP backend read path.

## Backend write usage in MVP

Deferred.

## Important rule

Commercial state must not pollute public venue truth or consumer-private state semantics.

---

## Domain 8 — Provenance / evidence / source confidence

## Purpose

Support trust, reviewability, and future operational confidence.

## Typical content

Examples include:

- source metadata
- evidence references
- provenance indicators
- freshness/confidence-supporting records

## Backend read usage

Mostly internal in MVP.

Certain light freshness messaging may later be surfaced publicly where useful.

## Backend write usage

May be involved in workflow/moderation or future ingestion systems.

## Important rule

Do not dump provenance internals directly into public payloads in MVP.

---

## Domain 9 — Dynamic public subdomains

## Purpose

Support dynamic venue content that affects discovery and venue detail while remaining lifecycle-aware.

## Typical content

Examples include:

- specials
- events
- tap-list or drink highlights
- hours exceptions

## Backend read usage

Public read services may use published/currently eligible records from these domains.

Examples:

- Search filter matches
- Home sections like specials tonight or events tonight
- Venue Detail dynamic sections
- open-now logic through hours and exceptions

## Backend write usage

Consumer corrections about these areas should go to workflow/moderation, not directly to published truth.

## Important rule

Dynamic domains still follow the same truth/workflow separation as static venue data.

---

## Backend endpoint-to-domain mapping

## Public endpoints

### Home
Reads:
- published public truth
- dynamic public subdomains
- optional enrichment data
Writes:
- none

### Search
Reads:
- published public truth
- dynamic public subdomains
- optional enrichment data
Writes:
- none

### Map
Reads:
- published public truth
- dynamic public subdomains where relevant
- optional enrichment data
Writes:
- none

### Venue Detail
Reads:
- published public truth
- dynamic public subdomains
- optional enrichment data
Writes:
- none

---

## Consumer-authenticated endpoints

### Saved
Reads:
- consumer-private state
- published public truth for rendering saved venue cards
Writes:
- consumer-private state

### Profile
Reads:
- consumer-private state
Writes:
- consumer-private state

### Submissions
Reads:
- published public truth where target validation is needed
Writes:
- workflow/staging/proposed changes
- submission attribution context linked to consumer identity

Must not write:
- published public truth
- moderation decision history

---

## Internal/admin endpoints

### Moderation queue/detail
Reads:
- workflow/staging/proposed changes
- moderation/audit history
- selected published public truth context
- possibly provenance/supporting context where available

Writes:
- none for pure reads

### Moderation decisions/notes
Reads:
- workflow/staging/proposed changes
- published public truth where needed
Writes:
- moderation/audit history
- workflow state changes
- formal publish flow triggers where approval requires it

Must not operate as:
- ad hoc raw overwrite of published truth

### Internal venue lookup
Reads:
- published public truth
- selected internal workflow/moderation context where justified

---

## Backend service-to-domain mapping

## Discovery services

May read:
- published public truth
- dynamic public subdomains
- enrichment inputs

Must not read as public truth:
- workflow proposals
- moderation state
- commercial state

---

## Venue detail services

May read:
- published public truth
- dynamic public subdomains
- storage/media references
- authenticated enrichment inputs

Must not expose:
- moderation internals
- workflow records
- internal notes

---

## Saved/profile services

May read/write:
- consumer-private state

May read:
- published truth as supporting context for rendering

Must not write:
- workflow or public truth domains

---

## Submission services

May read:
- published truth for validation/context
- consumer identity context

May write:
- workflow/staging/proposed changes
- submission intake records

Must not write:
- published public truth
- moderation decisions

---

## Moderation services

May read:
- workflow/staging/proposed changes
- moderation history
- published truth context
- provenance/support context if available

May write:
- moderation history
- workflow decisions
- publish triggers through proper path

Must not behave as:
- direct unaudited table patching

---

## Practical backend rules

### Rule 1

If a feature is consumer-visible discovery, start by asking whether it is reading published truth only.

### Rule 2

If a feature captures a user suggestion about public data, it belongs in workflow/moderation-bound writes, not direct truth mutation.

### Rule 3

If a feature stores something personal to the user, it belongs in consumer-private state, not public truth.

### Rule 4

If a feature concerns internal review, it may read workflow/audit context, but it must remain internal-only.

### Rule 5

If a future owner/business or subscription concept is involved, do not hack it into consumer state or public truth.

---

## Things workers must not do

- use workflow proposals in public Search results as if they are published
- expose moderation notes in public venue detail
- write public truth from consumer submission endpoints
- store consumer saves inside public venue records
- use commercial/subscription state to shape public venue truth semantics in MVP
- conflate owner authority state with consumer auth state

---

## Key decisions

- backend domain usage must follow the completed database architecture
- published truth, workflow, moderation, consumer-private, owner/business, and commercial state remain separate
- public consumer endpoints read published truth only
- consumer submissions write to workflow/proposed-change domains only
- internal moderation endpoints may read workflow and audit domains and apply formal decisions
- consumer-private state is the only domain written directly by consumer account actions outside submissions

---

## Assumptions

- the database migrations in development correctly reflect these domain boundaries
- exact table names may differ, but the domain separation is already architecturally locked
- backend workers will need this document to interpret the DB safely

---

## Open questions

- exact table-to-domain inventory for implementation
- exact publish-path mechanics after moderation approval
- exact provenance/freshness domain exposure inside internal tools

These are implementation mapping details, not blockers for this domain document.

---

## Dependencies

- `backend/docs/BACKEND_ARCHITECTURE_OVERVIEW.md`
- `backend/docs/WRITE_PATHS_AND_MODERATION.md`
- completed database architecture and migrated schema
- database manager handoff materials

---

## Downstream use

This document should guide:

- backend stage managers
- workers building Django data access layers
- internal moderation implementation
- API review for domain safety
- coordination between backend and database management