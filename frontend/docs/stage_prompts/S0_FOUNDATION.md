# Stage 0 Foundation

## Role
You are a Cursor worker agent building the initial frontend foundation for PubPlus.

## Parent manager
Discovery / Home / Search Manager

## Product context
PubPlus is a mobile-first pub discovery app for Melbourne. This slice only sets up the minimum frontend foundation needed for later Discovery / Home / Search work. The codebase is currently empty. All work must be inside `/frontend`.

## Stage reference
`frontend/docs/discovery-home-search/stages/STAGE_0_FOUNDATION_AND_BOOTSTRAP.md`

## Objective
Create the minimum Expo + React Native frontend foundation needed to begin staged Discovery / Home / Search implementation.

## Scope included
- Bootstrap the app inside `/frontend`
- Set up a clean, minimal folder structure
- Add app entry and basic navigation shell
- Add placeholder Home and Search screens
- Add minimal shared UI/theme foundations only if needed
- Add test setup suitable for later stages
- Add concise setup/run notes if missing

## Scope excluded
- Real backend integration
- Final UI polish
- Search logic
- Filters
- Venue cards
- Auth flows
- Map work
- Saved/favourites flows
- Overbuilt architecture

## Required files to read first
- `frontend/docs/discovery-home-search/PRD.md`
- `frontend/docs/discovery-home-search/AGENT_RULES.md`
- `frontend/docs/discovery-home-search/stages/STAGE_0_FOUNDATION_AND_BOOTSTRAP.md`

## Files allowed to change
- Anything inside `/frontend`
- Do not modify anything outside `/frontend`

## Implementation instructions
1. Initialize a minimal Expo React Native app in `/frontend`
2. Use a small, feature-grouped structure suitable for Discovery / Home / Search
3. Add a basic navigation/screen shell with:
   - Home screen
   - Search screen
4. Keep screens very small and composed simply
5. Add minimal shared folders only where useful, for example:
   - `src/app`
   - `src/features/discovery`
   - `src/features/search`
   - `src/components`
   - `src/test`
6. Add a lightweight testing setup
7. Use typed placeholders only where necessary
8. Keep files small and avoid premature abstraction
9. Add a concise README or setup note only if required for running/tests

## Testing requirements
- Confirm the app boots successfully
- Add at least one basic render test for the app shell or a placeholder screen
- Add any essential test config needed for future stages
- Do not add excessive tests for trivial styling

## Acceptance criteria
- `/frontend` contains a working minimal Expo app
- The app has a basic shell with Home and Search placeholders
- The structure is clean and suitable for staged feature growth
- Test setup exists and at least one meaningful test passes
- No backend contracts are invented
- No unrelated features are built
- Files remain concise and modular

## Deliverables required back
Return:
- short summary of what changed
- list of files created/changed
- tests added/updated
- acceptance criteria checklist
- any risks or follow-up concerns

## Do not do
- Do not build the full feature
- Do not add fake complex architecture
- Do not invent API contracts
- Do not add map, auth, favourites, or submission flows
- Do not create giant files
- Do not modify anything outside `/frontend`

## Escalate if
- A required dependency is missing for Expo setup
- The stage docs conflict with implementation reality
- A decision is needed on navigation/tooling that materially affects later stages