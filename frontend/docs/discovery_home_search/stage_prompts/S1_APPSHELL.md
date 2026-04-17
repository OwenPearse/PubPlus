# Stage 1 App Shell

## Role
You are a Cursor worker agent implementing the Discovery / Home / Search app shell foundations for PubPlus.

## Parent manager
Discovery / Home / Search Manager

## Product context
PubPlus is a mobile-first Melbourne pub discovery app. This stage should build the reusable app-shell foundations needed for later Discovery and Search work, without implementing the actual feature logic yet.

## Stage reference
`frontend/docs/discovery-home-search/stages/STAGE_2_APP_SHELL_AND_NAVIGATION.md`

## Objective
Refine the frontend shell so later stages can build Home and Search cleanly. Focus on navigation structure, shared screen scaffolding, and minimal reusable app-shell primitives.

## Security
- Security is highest priority
- Never inspect, open, or depend on `.env`
- Never hardcode secrets or credentials
- Only document config in `.env.example` if required
- Review `.gitignore` if any new tooling or generated files are introduced
- Do not introduce insecure defaults

## Scope included
- Improve the existing navigation shell if needed
- Add a clean screen wrapper/layout pattern for Discovery and Search
- Add minimal shared UI primitives for:
  - screen container
  - section spacing/layout
  - basic loading/empty placeholder support if useful
- Ensure route/screen naming is clear and stable
- Keep the structure ready for later Home/Search implementation
- Add or refine tests for app shell behaviour where meaningful

## Scope excluded
- Real search UX
- Search suggestion logic
- Filters
- Venue cards
- Real result lists
- Backend integration
- Auth flows
- Save/favourite flows
- Map work
- Final visual polish or design system overbuild

## Required files to read first
- `frontend/docs/discovery-home-search/PRD.md`
- `frontend/docs/discovery-home-search/AGENT_RULES.md`
- Existing `/frontend` app shell files

## Files allowed to change
- Files inside `/frontend`
- Do not modify anything outside `/frontend`

## Implementation instructions
1. Keep the navigation simple and stable
2. Ensure Home and Search have a consistent screen-level structure
3. Add only the smallest useful shared app-shell components
4. Prefer feature-grouped structure and small files
5. Avoid creating a broad design system at this stage
6. Avoid speculative abstractions for future features
7. Keep naming clear so later stages can slot in cleanly
8. If the existing shell is already good, make only minimal changes

## Testing requirements
- Update or add tests only where meaningful
- At minimum, verify the shell still renders correctly
- Verify basic navigation/screen structure if practical
- Do not add excessive tests for trivial styling-only changes

## Acceptance criteria
- App shell remains working and minimal
- Home and Search have a consistent reusable screen structure
- Shared shell components are small and useful
- No feature logic is prematurely built
- No backend/API contracts are invented
- Files remain concise and modular
- Required tests pass
- `.gitignore` is reviewed if new generated files/tooling appear

## Deliverables required back
Return:
- short summary of what changed
- files created/changed
- tests added/updated
- acceptance criteria checklist
- whether `.gitignore` needed changes
- any risks or follow-up concerns for Stage 3

## Do not do
- Do not implement Home feature modules
- Do not implement Search UX
- Do not add filters or venue cards
- Do not invent API contracts
- Do not inspect `.env`
- Do not hardcode secrets
- Do not create giant files
- Do not overbuild a design system

## Escalate if
- Stage 1 docs conflict with the current frontend structure
- navigation/tooling choices would materially affect later stages
- safe progress requires guessing backend contracts
- required work would exceed this stage’s scope