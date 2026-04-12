# Stage 1 Flows

## Role
You are a Cursor worker agent defining the Discovery / Home / Search feature foundation docs for PubPlus.

## Parent manager
Discovery / Home / Search Manager

## Product context
PubPlus is a mobile-first app for discovering pubs and bars in Melbourne. Discovery should be locality-first, guided, structured, and minimal. Search must resolve user intent into structured entities, tags, suburbs, and filters rather than open-ended semantic search.

## Stage reference
Create the manager docs and stage docs for Discovery / Home / Search inside `/frontend/docs/discovery-home-search/`.

## Objective
Create the concise product and delivery documentation needed to guide staged Cursor implementation for Discovery / Home / Search.

## Security
- Security is highest priority
- Never inspect, read, or depend on `.env`
- Never hardcode secrets or credentials
- If env variables need documentation, add them to `.env.example` only
- Review `.gitignore` and update it for frontend-generated files, caches, logs, local env files, build outputs, and other noise
- Do not introduce insecure defaults

## Scope included
- Create `PRD.md`
- Create `AGENT_RULES.md`
- Create stage docs for Discovery / Home / Search
- Define Home MVP purpose and modules
- Define Search structured-resolution UX
- Define result presentation expectations
- Define state and interaction boundaries
- Define implementation slices for later workers
- Define testing expectations for later stages
- Tighten `.gitignore` if needed
- Add `.env.example` only if truly needed at this stage

## Scope excluded
- Building feature UI beyond trivial doc-supporting changes
- Real backend integration
- Auth implementation
- Map implementation
- Saved/favourites implementation
- Contribution/reporting implementation
- Final design system work
- Large architecture redesign outside this feature area

## Required files to read first
- `S0_Foundation.md`
- Existing files inside `/frontend`
- Any existing docs already present under `/frontend/docs` if they exist

## Files allowed to change
- `/frontend/docs/discovery-home-search/**`
- `/frontend/.gitignore`
- `/frontend/.env.example` only if needed
- Minimal supporting doc files inside `/frontend` if required
- Do not modify anything outside `/frontend`

## Required files to create
- `frontend/docs/discovery-home-search/PRD.md`
- `frontend/docs/discovery-home-search/AGENT_RULES.md`

Create stage docs under:
- `frontend/docs/discovery-home-search/stages/STAGE_0_FOUNDATION_AND_BOOTSTRAP.md`
- `frontend/docs/discovery-home-search/stages/STAGE_1_SCOPE_AND_USER_FLOWS.md`
- `frontend/docs/discovery-home-search/stages/STAGE_2_APP_SHELL_AND_NAVIGATION.md`
- `frontend/docs/discovery-home-search/stages/STAGE_3_HOME_DISCOVERY_SHELL.md`
- `frontend/docs/discovery-home-search/stages/STAGE_4_STRUCTURED_SEARCH_UX.md`
- `frontend/docs/discovery-home-search/stages/STAGE_5_DISCOVERY_RESULTS_AND_VENUE_CARDS.md`
- `frontend/docs/discovery-home-search/stages/STAGE_6_FILTERS_LOCALITY_AND_QUERY_STATE.md`
- `frontend/docs/discovery-home-search/stages/STAGE_7_AUTH_GATES_DISCLAIMERS_AND_EDGE_STATES.md`
- `frontend/docs/discovery-home-search/stages/STAGE_8_TESTING_VALIDATION_AND_POLISH.md`

You may slightly rename stages only if the result is clearer and still concise.

## File requirements
Every markdown file must include:
- Purpose
- Current stage
- Decisions
- Assumptions
- Open questions
- Dependencies
- Next downstream use

Every stage doc must also include:
- Stage goal
- Scope included
- Scope excluded
- Files expected to be created or changed
- Acceptance criteria
- Test requirements
- Deliverables required back
- Do not do

## Implementation instructions
1. Keep docs concise, practical, and Cursor-friendly
2. Do not write bloated strategy documents
3. Clearly define the MVP role of:
   - Home
   - Search
   - discovery result lists
   - venue cards in discovery contexts
   - locality defaulting
   - guest browsing
   - auth-gated interruption points
   - subtle disclaimer handling
4. Search must be structured and guided
5. Make it clear that suburb, tag, feature, event, and similar inputs should resolve into structured matches
6. Define no-match, empty, loading, and error states
7. Define what later implementation stages should test
8. Make stages small enough for narrow Cursor worker execution
9. Call out dependencies on backend/data, moderation, map, saved/lists, and QA
10. Update `.gitignore` if frontend ignores are incomplete

## Testing requirements
This stage is documentation-first. No heavy UI tests required.
Required checks:
- docs are complete and internally consistent
- stage boundaries are non-overlapping
- acceptance criteria exist for every stage
- testing expectations exist for every stage
- `.gitignore` changes are sensible if made

## Acceptance criteria
- `PRD.md` exists and is concise but clear
- `AGENT_RULES.md` exists and is concise but clear
- stage docs exist for the Discovery / Home / Search workstream
- Stage 0 is documented, even though it has already been executed
- each stage is small enough for a worker agent
- each stage has explicit acceptance criteria
- each stage has explicit testing requirements
- dependencies and assumptions are clearly labeled
- docs do not invent backend contracts
- `.gitignore` is reviewed and improved if needed
- no content is added outside allowed scope

## Deliverables required back
Return:
- short summary of what changed
- files created/changed
- whether `.gitignore` was updated and why
- whether `.env.example` was added/updated and why
- acceptance criteria checklist
- any risks, gaps, or clarification needs for Stage 2+

## Do not do
- Do not build the feature UI in this stage
- Do not invent API schemas or payloads
- Do not inspect `.env`
- Do not hardcode secrets
- Do not create giant docs
- Do not add unrelated app architecture
- Do not modify anything outside `/frontend`

## Escalate if
- existing frontend structure conflicts with the planned stage sequence
- there is a real ambiguity about product behaviour that blocks stage design
- a later stage cannot be cleanly separated without a manager decision