# Discovery / Home / Search Agent Rules

## Purpose
Define how Cursor worker agents must execute Discovery / Home / Search stages safely, consistently, and with minimal ambiguity.

## Current stage
Manager rules document used across all downstream Cursor tasks in this workstream.

## Decisions
- Work must be completed in small stages
- Worker agents must stay tightly within scope
- Security has highest priority
- Testing is mandatory where meaningful
- Documentation must stay concise and practical
- Workers must not invent backend contracts
- Workers must prefer modular, small files over broad abstractions

## Assumptions
- All code for this workstream lives inside `/frontend`
- The app is React Native + Expo
- Adjacent managers own backend contracts, auth implementation, map ownership, and other non-owned surfaces
- Some stages may require temporary typed placeholders, but they must be clearly labeled as assumptions

## Open questions
- Exact search/result contracts may still be pending from backend/data ownership
- Final disclaimer copy may still need moderation review
- Save/favourite integration points may depend on adjacent feature work

## Dependencies
- `PRD.md` for product truth and scope
- Stage docs under `frontend/docs/discovery-home-search/stages/`
- Existing `/frontend` codebase state
- Adjacent manager decisions where called out in stage docs

## Next downstream use
Used by every Cursor worker before coding and by the manager when reviewing worker outputs.

---

## Core execution rules
- Read the assigned stage doc before changing code
- Stay within the stage scope
- Keep files small and focused
- Prefer composition over large multi-purpose components
- Avoid speculative architecture
- Do not solve future stages early
- If a decision materially affects later stages, escalate rather than guessing

## Security rules
- Security is highest priority
- Never inspect, open, parse, or depend on `.env`
- Never hardcode secrets, tokens, or credentials
- Never commit secret-bearing files
- If configuration variables must be documented, add them to `.env.example` only
- Prefer safe defaults and explicit documentation over hidden assumptions

## Repository hygiene rules
- Review `.gitignore` when introducing new tooling or generated files
- Ensure noisy files are not committed
- Ignore local env files, caches, logs, build outputs, dependency folders, temporary artifacts, and similar generated files as appropriate
- Do not add unnecessary scaffolding or throwaway files to the repo

## Backend contract rules
- Do not invent API schemas, payloads, endpoints, or database shapes
- If a typed placeholder is needed, mark it clearly as temporary and assumption-based
- Keep integration surfaces narrow and easy to replace later
- Escalate contract ambiguity rather than silently deciding it

## Testing rules
- Add tests for meaningful logic, hooks, state transforms, and important component states
- Do not add theatrical tests for trivial styling-only work
- Keep tests targeted and maintainable
- If no test is added, state why
- A stage is not complete unless required tests pass

## Documentation rules
- Keep docs concise and useful
- Avoid repeating product context unnecessarily
- Keep stage docs implementation-oriented
- Clearly label assumptions, dependencies, and exclusions
- Update docs when a stage materially changes implementation direction

## Code quality rules
- Prefer feature-grouped structure
- Prefer explicit names
- Keep components and hooks single-purpose where possible
- Avoid giant files
- Avoid premature abstraction
- Avoid hidden shared state
- Make loading, empty, error, and edge states explicit where relevant

## UX rules
- Discovery should feel guided, not vague
- Search should resolve into structured matches
- Home should stay locality-first
- Guests should browse freely within allowed areas
- Auth-gated actions should interrupt lightly and clearly
- Trust messaging should be subtle

## Worker deliverable rules
Every worker response must include:
- short summary of changes
- files created or changed
- tests added or updated
- acceptance criteria checklist
- risks or follow-up concerns

## Escalation rules
Escalate if:
- stage scope conflicts with the current codebase
- backend or data contract uncertainty blocks safe progress
- a security concern appears
- required work would exceed the allowed stage scope
- adjacent manager decisions are needed
- an implementation would require reading `.env` or guessing secrets

## Review expectations
Your output will be reviewed for:
- scope discipline
- security compliance
- `.gitignore` hygiene
- modularity
- test coverage
- acceptance criteria completion
- avoidance of backend invention
- clarity for future stages

## Definition of done
A stage is only done when:
- scope is met
- exclusions were respected
- required tests pass
- docs are updated if needed
- no security rules were broken
- no unrelated work was added
- deliverables are clearly reported