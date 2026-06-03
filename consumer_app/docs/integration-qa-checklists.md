# Integration QA Checklists (Reference)

Historical manual verification checklists from MVP integration stages. **Not required for onboarding** — see [README.local-run.md](../README.local-run.md) for day-to-day local run.

OpenAPI source for contract checks: `lib/api-spec/openapi.yaml`.

## OpenAPI codegen workflow

Orval generates TypeScript types and React Query hooks from the spec. **Committed** outputs (do not hand-edit):

- `lib/api-client-react/src/generated/` — schema types + React Query client
- `lib/api-zod/src/generated/` — Zod schemas

From `consumer_app/`:

```bash
corepack pnpm run openapi:lint
corepack pnpm run openapi:generate
corepack pnpm run typecheck
```

Workflow:

1. Update `lib/api-spec/openapi.yaml` when the backend contract changes.
2. Run `openapi:lint`, then `openapi:generate`.
3. Import types from `@workspace/api-client-react` in mobile mappers/hooks (keep `publicApiRequest` / `privateApiRequest` unless migrating to generated hooks intentionally).
4. Never edit files under `*/generated/` manually.

Home, Search, Map, saved-list, and shared venue card inputs use generated OpenAPI schema types; runtime still uses hand fetch helpers. Profile types may remain hand-written where optional-field normalization is undefined.

## Stage 2 — Search filters and radius

1. Re-apply database seeds (`database/supabase/seed.sql` or `supabase db reset`) so `dev_seed_mvp_feature_attribute_values.sql` is loaded.
2. Open Search → Filters → pick **Brunswick** suburb, then **Beer garden** → expect at least one venue (e.g. Penny Black / Grand View).
3. With **no suburb** selected, distance chips disabled; request must **not** include `radius_m`.
4. Select **Melbourne** suburb, choose **5 km** → request includes `lat`, `lng`, and `radius_m`.
5. `GET /api/v1/search/venues?radius_m=5000` alone → `400` with `location_incomplete`.

## Stage 3 — Search `q`

1. Re-run dev DB seed.
2. Search for venue name (e.g. `Penny`) — request includes `q=Penny`.
3. Search for suburb (e.g. `Brunswick`).
4. Combine `q` with **Beer garden** — both params sent.
5. Clear search input — `q` not sent.
6. Whitespace-only input — `q` not sent.
7. Event filters remain hidden.

## Stage 4 — Events honesty

1. Search — no event filter chips.
2. Search with `q` — copy does not promise event discovery.
3. Home — no **Events tonight** section.
4. Venue detail with empty `events.items` — no fake event rows.
5. Map popup — no event line unless API returns non-empty event data.

## Stage 5 — Profile locality

1. Log in → Profile.
2. Drink, venue feature, event interest, distance, personalization sections not shown.
3. Change default suburb — persists after reload.
4. `PATCH /api/v1/profile/` sends only supported fields.
5. Notification toggles persist.
6. Clear default suburb — locality IDs clear when backend allows.

## Stage 6 — Locality reference + device location

**Reference endpoint**

1. Re-run dev DB seed.
2. Profile default suburb picker loads from `GET /api/v1/reference/localities`.
3. Select suburb — PATCH sends `default_locality_id` and `default_geographic_region_id`.
4. Backend stopped briefly — Profile renders; picker shows unavailable/retry.

**Device location (search origin)**

1. Foreground location prompt uses PubPlus copy (or browser prompt on web).
2. Allow location — distance chips enabled without suburb; search sends device `lat`/`lng`/`radius_m`.
3. Profile PATCH does not send GPS.
4. Deny location — Home/Search/Map still load.
5. Location denied + profile suburb — distance search uses profile/reference coordinates.
6. Location denied + no profile suburb — distance chips disabled until Search suburb selected.

## Stage 7 — Search locality alignment

1. Search suburb options match `GET /api/v1/reference/localities`.
2. Select Brunswick — `suburb=Brunswick` in request.
3. Distance + suburb — `lat`, `lng`, `radius_m` from locality (device location takes priority when granted).
4. Backend stopped briefly — Search does not crash.

## Stage 8 — Contract verification

1. `GET /api/v1/search/filters` — `event_filters` is `[]`.
2. `GET /api/v1/reference/localities` — pickers match.
3. Search with `q`, `suburb`, and `lat`/`lng`/`radius_m` as applicable.
4. Event filter chips hidden.
5. Home/Map use device origin when allowed; profile locality fallback when denied.

## Stage 9 — Venue detail contract

1. `GET /api/v1/venues/{venue_id}` matches OpenAPI `VenueDetail*` schemas.
2. `events.items` is `[]`, `events.not_implemented` is `true` when applicable.
3. Consumer detail screen loads without errors.
4. Authenticated save toggle reflects `authenticated_actions.is_saved`.

## Stage 12 — Attribute correction UX

1. Log in → venue detail → correction flow.
2. **Features & amenities** available; loads from `GET /api/v1/search/filters`.
3. Tri-state feature correction (e.g. Beer garden **Present**).
4. Submit — `domain=attributes`, `proposed_values.items[]` with `attribute_definition_id` / `value_boolean`.
5. Backend returns `201` / `status: received`.
6. Profile/location/hours corrections still work; event correction not shown.

## Known deferred product areas

- Event discovery when API has no published event catalog.
- Profile taste preferences beyond default suburb and notifications.
- Google, Facebook, Apple SSO — external provider setup required.
