# Discovery / Home / Search PRD

## Purpose
Define the MVP product behaviour, scope, and delivery direction for the PubPlus Discovery / Home / Search frontend workstream.

## Current stage
Manager foundation document for Stage 1 planning and downstream staged implementation.

## Decisions
- PubPlus is a mobile-first pub discovery app for Melbourne
- Discovery is the primary browsing experience
- Home is locality-first by default
- Users can browse without signing in
- Auth is required for gated actions such as contributions, feedback, favourites, and similar protected actions
- Search is guided and structured, not unrestricted semantic search
- User input should resolve into structured concepts such as suburb, venue, event type, feature, tap item, or special tag where supported
- Map is a secondary companion, not the main discovery surface
- Venue cards are DB-backed and should be consistent across discovery surfaces
- Data trust should be handled with subtle disclaimers, not freshness badges
- MVP should stay minimal, fast, and suburb-density aware

## Assumptions
- Frontend stack is React Native + Expo
- Backend/data contracts will be provided or confirmed by adjacent managers
- Discovery will initially focus on Melbourne and nearby relevant locality flows
- Locality may come from device permission, user profile preference, or a fallback default
- Search suggestions may be powered by backend-assisted structured lookup, but this workstream should not invent the contract
- Guest users can browse Home, Search, and results without sign-in

## Open questions
- What is the exact fallback locality when device permission is unavailable?
- Will search suggestions be one combined endpoint or multiple structured sources?
- Which result filters are guaranteed in MVP versus desirable but optional?
- What save/favourite affordances must appear on venue cards during MVP?
- What exact disclaimer copy is approved by moderation/content stakeholders?

## Dependencies
- Backend / Data Systems Manager for locality, search resolution, result payloads, and filter contracts
- Content Moderation / Data Operations Manager for trust wording and report/data submission gating touchpoints
- Saved / Lists Manager for any save/favourite integration points
- Map / Venue Browsing Manager for shared venue card and result presentation consistency
- QA / Release Manager for coverage expectations on guest flows, gated prompts, and core discovery states

## Next downstream use
Used by Cursor agents to implement Discovery / Home / Search in small stages without inventing product behaviour.

---

## Product summary
PubPlus helps users decide where to go by surfacing structured, relevant venue information in a simple discovery flow. The app should feel fast, useful, and trustworthy without becoming cluttered or over-personalised.

## MVP goals
- Help users quickly find a good venue nearby or in a chosen suburb
- Make common intents easy to express through structured search and filters
- Surface useful venue summaries without overwhelming detail
- Support guest browsing while gently gating protected actions
- Keep discovery polished but lightweight

## Out of scope for this workstream
- Full map-first browsing
- Profile/account settings implementation
- Saved lists as a primary owned feature
- Contribution/report flows as a primary owned feature
- Backend schema design
- Owner tools
- Deep personalisation

## Home screen definition
Home is the default discovery entry point.

Its role in MVP is to:
- show locality-first suggestions
- provide a quick path into structured search
- surface a small number of useful discovery modules
- help undecided users browse quickly

Likely Home modules:
- nearby or local picks
- popular in your area
- tonight / current useful highlights if supported
- quick search or structured prompt entry
- quick chips for common intents such as trivia, parma night, beer garden, live music

Home should not become a crowded dashboard.

## Search definition
Search must guide users into structured matches.

Supported intent types may include:
- suburb
- venue name
- event type
- special type
- feature
- drink/tap category if supported
- open-now or similar structured availability concept if supported by backend

Search behaviour:
- user types text
- UI suggests structured matches
- user selects a match or token
- results update from structured state, not vague free text alone

Search should support:
- autocomplete or suggestion rows
- selected chips/tokens
- clear empty and no-match states
- clean handoff into filtered result lists

Search should not behave like an unrestricted chatbot or fuzzy semantic search bar.

## Discovery results definition
Discovery results should be list-first and easy to scan.

Results should include:
- clear venue name
- suburb / locality context
- selected relevant highlights
- key tags or metadata if supported
- tap target into venue detail or adjacent browsing flow
- optional save/report entry points if owned elsewhere and available

Result states required:
- loading
- empty
- no structured match
- no results for selected combination
- recoverable error

## Venue card expectations
Venue cards used in discovery should be:
- compact
- consistent
- modular
- reusable across Home and Search results

Cards should prioritise:
- recognisable venue identity
- locality relevance
- a few useful structured highlights
- clear interaction affordances

Cards should not attempt to show every known venue detail.

## Locality behaviour
Locality-first behaviour should prefer:
1. explicit user-selected suburb or area
2. profile preference if available
3. device-derived nearby locality if permitted
4. sensible Melbourne fallback

The UI should make locality understandable and adjustable without friction.

## Guest and auth-gated behaviour
Guests can:
- browse Home
- search
- view results
- open venue details if available within adjacent flows

Guests should be prompted to sign in when attempting protected actions.

Auth-gated interruptions should be:
- clear
- lightweight
- non-destructive
- easy to dismiss or continue browsing from

## Trust and disclaimer behaviour
The app should not show freshness scores or technical trust metrics.

A subtle disclaimer may appear in discovery contexts to communicate that:
- data is maintained carefully
- users should verify details where needed

This should not dominate the interface.

## State boundaries
This workstream should clearly separate:
- local UI state
- remote query/result state
- search token/filter state
- locality context
- auth-gate UI interruption state

Do not overcomplicate state early. Prefer small, testable patterns.

## UX principles
- fast to scan
- guided, not vague
- structured over clever
- minimal but polished
- locality-aware
- easy for guests
- safe for future extension