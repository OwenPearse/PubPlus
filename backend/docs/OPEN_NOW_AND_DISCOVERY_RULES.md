# PubPlus Open-Now and Discovery Rules

## Purpose

Lock the trust-sensitive backend rules for open-now behaviour, discovery filtering, and MVP discovery ranking so Home, Search, Map, and Venue Detail behave consistently and safely.

## Current stage

Pre-implementation rule document created before discovery-oriented stage-manager prompts.

## Summary

PubPlus is a discovery-first venue app. This means the quality and trustworthiness of discovery behaviour matters more than raw feature count.

Among all discovery behaviours, `open_now` is one of the most trust-sensitive.

It must be computed in backend only, using published hours and valid published exceptions, and it must behave consistently across:

- Home
- Search
- Map
- Venue Detail

Discovery more broadly must use explicit MVP ranking and filtering rules that are understandable, conservative where trust matters, and consistent across surfaces.

This document defines those rules.

---

## Part 1 — Open-now rules

## Rule 1: Open-now is backend computed only

The frontend must not compute or override open-now state.

All public surfaces that show `open_now` must use backend-computed truth.

### Applies to

- Home cards/sections
- Search results
- Map results/popups
- Venue Detail

---

## Rule 2: Open-now must use published truth only

`open_now` must be derived from published public hours truth and published valid temporary exceptions.

It must not use:

- workflow/staged proposals
- unreviewed consumer suggestions
- internal moderation guesses
- future owner-side draft edits
- weak non-published signals

---

## Rule 3: Unknown must not silently become closed

If the system does not have sufficiently reliable hours truth to determine whether a venue is open, the backend must not silently convert uncertainty into a false closed claim.

This is a critical trust rule.

### Meaning

Missing, stale, partial, or unresolved hours data is not proof of closure.

### Practical implication

The backend may internally preserve richer operational state than a simple public boolean.

If the public API presents a simplified field, the simplification should still be driven by conservative backend rules rather than by pretending uncertainty equals closed.

---

## Rule 4: Weak hours truth must not be promoted into open-now

The backend must not produce a confident open-now claim from weak or insufficient hours data.

Examples of weak inputs include:

- vague “open late” style information
- incomplete schedules
- stale operational data
- ambiguous or unresolved exception periods
- missing day coverage needed for a reliable decision

### Meaning

Open-now must be conservative in the positive direction.

Do not tell the user a venue is open unless published truth is strong enough to support that claim.

---

## Rule 5: Valid exceptions override regular hours

If a valid published temporary exception applies to the relevant date or time, it must override normal weekly hours for that period.

Examples include:

- one-off closures
- temporary holiday trading changes
- special event opening variations
- reduced hours on a specific date

This rule must apply consistently everywhere open-now is computed.

---

## Rule 6: One open-now logic source across all surfaces

Home, Search, Map, and Venue Detail must all use the same underlying open-now computation logic.

Do not implement separate versions in different endpoint paths.

### Reason

Different open-now answers across surfaces will destroy product trust.

---

## Rule 7: Open-now should influence filtering and ranking, but not distort truth

`open_now` may be used for:

- explicit open-now filters
- Home section generation
- discovery ranking boosts where appropriate

But it must remain a truth-derived state, not a ranking invention.

Do not set or infer `open_now` merely because ranking wants more attractive results.

---

## Rule 8: Time handling must be explicit and consistent

Open-now logic is time-sensitive and must use a clearly defined timezone strategy.

The implementation must not allow different services to make conflicting assumptions about local time when evaluating venue status.

This is especially important for:

- daily transitions
- late-night trading
- exception windows
- section generation such as “tonight”

---

## Rule 9: Late-night logic must be handled intentionally

Venues that trade past midnight must not be misclassified due to simplistic day-boundary logic.

The implementation must account for operational periods that span calendar-day boundaries where the published truth supports it.

---

## Rule 10: Open-now output should be simple publicly, richer internally if needed

For MVP product use, a simple public `open_now` field may be sufficient.

Internally, the backend may preserve richer reasoning states if useful, such as:

- determinable open
- determinable closed
- indeterminate due to insufficient truth

This richer internal state can help preserve the trust rules above without overcomplicating the initial public contract.

---

## Part 2 — Discovery filtering rules

## Rule 11: Search and Map share one discovery core

Search and Map must use one shared backend discovery query core.

They may differ in payload shape and presentation mode, but not in the core interpretation of filters and public truth eligibility.

---

## Rule 12: Public discovery uses published truth only

Discovery filtering and surfacing must use published public truth only.

Do not include workflow proposals or pending edits in public discovery outputs.

---

## Rule 13: Mandatory MVP discovery filters

The backend discovery core must support these MVP filter families:

- suburb
- distance or location radius
- viewport bounds for map mode
- open now
- meal specials
- drink type
- venue features
- events

These should be implemented as structured backend filters, not informal text hacks.

---

## Rule 14: Filters must have clear semantics

Each discovery filter must have a stable meaning.

Examples:

- `open_now` means backend-computed current operational availability from published truth
- `meal_specials` means venues with eligible published specials matching the requested filter semantics
- `events` means venues with eligible published event content matching the requested filter semantics

Do not let filter meaning drift per endpoint.

---

## Rule 15: Unsupported or unknown filters should fail clearly

If a request includes unsupported filter keys or invalid values, the backend should reject them clearly rather than inventing fallback behaviour.

This improves trust and implementation clarity.

---

## Rule 16: Map mode is viewport-first

Map discovery must support viewport-based querying from day one.

Viewport filtering is a primary query mode for the map experience, not a later enhancement.

Map mode may also combine viewport constraints with other filters where appropriate.

---

## Rule 17: Distance-aware discovery should be backend computed

Distance values used for filtering, sorting, or display should be computed in backend logic.

The frontend should not be responsible for reproducing ranking-grade distance logic.

---

## Rule 18: Dynamic discovery domains must be lifecycle-aware

Filters and surfacing around:

- specials
- events
- drink/tap highlights
- hours exceptions

must respect lifecycle-aware published truth, not just raw record presence.

For example, an expired or inapplicable dynamic item should not make a venue match a live filter.

---

## Part 3 — Discovery ranking rules

## Rule 19: MVP ranking should be explicit, simple, and explainable

The first ranking system should not depend on ML-heavy personalization or opaque behavioural scoring.

It should be a clearly defined rule-based system that can be reasoned about and tuned.

---

## Rule 20: Search ranking and Home ranking are related but not identical

Search is a structured discovery surface.

Home is an orchestrated surface blending multiple intents.

They may share ranking ingredients, but Home should not just be “Search with defaults.”

---

## Rule 21: Base ranking inputs for MVP discovery

The backend may use a combination of these inputs in discovery ranking where relevant:

- geographic relevance
- viewport relevance for map
- open-now relevance
- eligible specials/events relevance
- structured feature/drink match strength
- light preference alignment
- venue completeness or quality signals if safely available

These inputs should remain rule-based and understandable.

---

## Rule 22: Open-now may boost relevant surfaces, but must not dominate all discovery

`open_now` is very important in certain contexts, but the product should still support useful discovery beyond immediate operational state.

Examples:

- Home “open now” section should strongly use it
- Search with no open-now filter may still include currently closed venues if they are otherwise relevant
- Venue Detail should present truth, not ranking logic

---

## Rule 23: Home should be sectioned by intent

The Home feed should be intentionally sectioned around discovery intents such as:

- nearby
- open now
- specials tonight
- events tonight
- light preference-aware recommendations

This is better than one undifferentiated ranked feed for MVP.

---

## Rule 24: Search should prioritize relevance to active filters and context

Search ranking should respect the user’s active discovery constraints first.

For example:

- if location context exists, geographic relevance matters
- if a user applies specials or events filters, matching those filters matters
- if open-now is requested, venues should satisfy that truth-derived state

Search should not behave like a generic popularity list.

---

## Rule 25: Map should prioritize correctness and performance over rich ranking complexity

For map results, the primary job is to return correct, relevant venues in the viewport and support responsive interaction.

Map mode should not become ranking-heavy at the expense of speed or consistency.

---

## Rule 26: Light personalization only in MVP

Personalization in MVP should stay light and explicit, based on known structured context such as:

- suburb preference
- distance preference
- favourite drink types
- favourite venue features
- event interests

Do not depend on heavy behavioural learning for launch.

---

## Rule 27: Saved-state is enrichment, not a ranking truth signal by default

The fact that a user has saved a venue may be useful in certain experiences later, but it should not automatically become a major discovery ranking factor in MVP unless intentionally defined.

Keep save-state primarily as per-user enrichment and private-state functionality.

---

## Part 4 — Surface-specific rules

## Home rules

### Rule 28

Home must return a sectioned response, not a single flat venue list.

### Rule 29

Home should remain useful when unauthenticated.

### Rule 30

Home may use light preference-aware ordering when authenticated, but should not require heavy personalization data.

---

## Search rules

### Rule 31

Search returns compact list/card results, not full detail payloads.

### Rule 32

Search must support structured filters consistently.

### Rule 33

Search must use the same open-now truth source as all other discovery surfaces.

---

## Map rules

### Rule 34

Map must support viewport-based querying from launch.

### Rule 35

Map payloads should be lighter than Search payloads where practical.

### Rule 36

Map and Search share core discovery logic but may have different response densities.

---

## Venue Detail rules

### Rule 37

Venue Detail must show backend-computed open-now where the product includes that state.

### Rule 38

Venue Detail uses published truth and eligible dynamic published content only.

### Rule 39

Venue Detail should not expose internal workflow or moderation context in MVP.

---

## Part 5 — Safety and consistency rules

## Rule 40: No surface-specific truth forks

Do not allow Home, Search, Map, and Venue Detail to drift into separate interpretations of:

- open_now
- hours eligibility
- specials/event eligibility
- venue matching semantics

Shared truth logic must stay centralized.

---

## Rule 41: Public discovery must not leak internal confidence mechanics directly

Internal provenance, evidence, and confidence-supporting signals may help backend decisions, but MVP public APIs should expose only simple user-appropriate outputs unless a specific lightweight freshness message is intentionally designed.

---

## Rule 42: Discovery logic changes are product changes

Changes to open-now, discovery filter semantics, or ranking logic are not trivial refactors.

They affect product trust and should be treated as intentional product/backend decisions.

---

## Rule 43: When in doubt, preserve trust over surface attractiveness

If there is tension between:

- making results look more attractive
- preserving conservative truthful behaviour

the backend should prefer truthful conservative behaviour.

This is especially important for open-now and time-sensitive discovery claims.

---

## Key decisions

- open-now is backend computed only
- open-now uses published hours and valid published exceptions only
- unknown must not silently become closed
- weak hours truth must not be promoted into confident open-now
- Search and Map share one discovery core
- MVP filters are structured and consistent
- Home is sectioned and orchestrated, not just generic search
- discovery ranking is explicit, simple, and light-personalization only
- public discovery prioritizes trust and consistency over cleverness

---

## Assumptions

- the completed database architecture supports published hours, exceptions, and dynamic public subdomains in a way the backend can consume
- frontend screens can adapt to these backend truth rules with only small payload-driven adjustments
- richer internal operational states may exist in implementation even if the public API remains simpler

---

## Open questions

- exact public representation of indeterminate operational state behind a simplified `open_now` field
- exact ranking weight tuning for MVP discovery
- exact dynamic eligibility rules for specials/events/tap highlights by time window

These are implementation and tuning questions, not blockers for the rules in this document.

---

## Dependencies

- `backend/docs/READ_MODEL_STRATEGY.md`
- `backend/docs/DATA_DOMAIN_MAPPING.md`
- completed database architecture and hours/exceptions design
- frontend discovery surface requirements

---

## Downstream use

This document should guide:

- discovery stage managers
- workers implementing Search, Map, Home, and Venue Detail
- open-now computation workers
- QA review of discovery correctness
- product/backend review of ranking and filter behaviour