Stage 1 — Core Venue & Discovery Data

Purpose
Define the clean public discovery model that powers Home, Search, Map, Saved, and Venue Detail.

Locked outcomes

PubPlus runs on one canonical published truth per venue.
A venue is one real customer-facing trading venue at one physical location.
Canonical identity must be durable and source-agnostic.
Source IDs never define canonical identity.
Same-address ambiguity defaults conservatively toward one venue unless separation is positively proven.
Public surfaces may differ in depth, but not in truth.
Geography is structured: public address, canonical suburb/locality, broader geography hierarchy, and exactly one authoritative published map point.
Discovery attributes must be structured where they materially drive filters, badges, counts, grouping, or search.
One venue should have one coherent truth set per attribute family.
Hours are structured operational truth, with regular hours, exceptions, and uncertainty kept separate.
Unknown hours must not become closed.
Weak or stale hours must not become open-now.
Valid exceptions override baseline hours.

Manager refinements / approvals

The published layer contains only resolved public truth.
Weak, ambiguous, stale, disputed, or pending values stay outside published truth.
Search trust is the highest MVP priority.
Structured claims need freshness/confidence guardrails.
Venue-open truth must not imply food/event/special/access availability.

Main guardrails

No duplicate truth systems per screen.
No raw free-text discovery model.
No Melbourne-specific hardcoding that blocks later expansion.
No weak location or hours truth leaking into live discovery.