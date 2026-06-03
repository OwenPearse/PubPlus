# PubPlus Consumer App Local Run

## Prerequisites

- Node with Corepack enabled for pnpm.
- Python/Django backend configured from `backend/.env.example`.
- A Supabase project with email/password auth enabled.
- Optional social auth providers configured in Supabase and their external dashboards.

## Environment

Copy `consumer_app/artifacts/mobile/.env.example` to a local `.env.local` or `.env` file for Expo. Use only frontend-safe `EXPO_PUBLIC_` variables in the mobile app.

Required values:

- `EXPO_PUBLIC_API_BASE_URL` - Django API origin, for example `http://localhost:8000`.
- `EXPO_PUBLIC_SUPABASE_URL` - Supabase project URL.
- `EXPO_PUBLIC_SUPABASE_ANON_KEY` - Supabase anon/publishable key. Do not use a service role key.
- `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` - Expo native deep link scheme, currently `pubplus`.

Keep populated env files ignored and local. Do not commit credentials, passwords, Supabase service role keys, or demo user secrets.

## Run Backend

From `backend/`:

```bash
python manage.py runserver 8000
```

The backend uses explicit CORS and CSRF trusted-origin settings from its environment. Include `http://localhost:8081` and `http://127.0.0.1:8081` when running Expo web on port 8081.

## Run Expo Web

From `consumer_app/`:

```bash
corepack pnpm install
corepack pnpm --filter @workspace/mobile exec expo start --web --localhost --port 8081 --clear
```

Use mobile device emulation in the browser for layout checks. Port `8081` is the default QA port; stop stale Expo processes before changing ports.

## Run Expo Go

From `consumer_app/`:

```bash
corepack pnpm --filter @workspace/mobile exec expo start --localhost --port 8081
```

Open the QR code with Expo Go. For a physical device, set `EXPO_PUBLIC_API_BASE_URL` to a backend origin reachable from that device rather than `localhost`.

## Validation

Frontend:

```bash
cd consumer_app
corepack pnpm run typecheck
```

Backend integration tests:

```bash
cd backend
python manage.py test --keepdb --noinput tests.test_auth_boundary tests.test_saved_venues_endpoints tests.test_profile_endpoints tests.test_reference_localities tests.test_submission_endpoints tests.test_discovery_public_endpoints tests.test_home_and_venue_detail_endpoints
```

## Stage 6 device location (current search origin) manual verification

1. Open the app on a device or simulator with location services available.
2. On first visit to the main tabs, confirm a foreground location permission prompt uses the PubPlus nearby-pubs copy (or browser location prompt on web).
3. **Allow** location — open Search → Filters → confirm distance chips are enabled without selecting a suburb.
4. Select a distance (e.g. 5 km) — confirm the search request includes `lat`, `lng`, and `radius_m` from device coordinates (not profile PATCH).
5. Confirm Profile default suburb still saves via `PATCH /api/v1/profile/` only (GPS is not sent to profile).
6. **Deny** location (or disable location services) — confirm the app still loads Home/Search/Map.
7. With location denied, set a Profile default suburb and reload — confirm distance search works using profile/reference coordinates when no suburb is selected in Search.
8. With location denied and no profile suburb, confirm distance chips stay disabled until a Search suburb is selected (Stage 2 rule: no `radius_m` without `lat`/`lng`).

## Stage 6 Locality reference endpoint manual verification

1. Re-run dev DB seed (Melbourne localities + published venues).
2. Start backend and consumer app.
3. Log in to the consumer app.
4. Open Profile.
5. Open default suburb picker — confirm options load from `GET /api/v1/reference/localities` (not hardcoded UUIDs).
6. Select Brunswick (or another listed suburb).
7. Confirm `PATCH /api/v1/profile/` sends `default_locality_id` and `default_geographic_region_id` from the endpoint row.
8. Reload Profile — confirm selection persists.
9. Clear suburb (X on chip) — confirm PATCH sends both locality fields as `null`.
10. Stop backend briefly — confirm Profile still renders; suburb picker shows unavailable/retry, not a crash.

## Stage 5 Profile locality + preference cleanup manual verification

1. Log in to the consumer app.
2. Open Profile.
3. Confirm drink, venue feature, event interest, distance, and personalization chip sections are not shown.
4. Change default suburb (e.g. Brunswick) using the suburb picker.
5. Confirm saving shows a loading state and completes without error.
6. Reload Profile — confirm the selected default suburb persists.
7. In network tools, confirm `PATCH /api/v1/profile/` sends only supported fields (`default_locality_id`, `default_geographic_region_id`, notification toggles, etc.).
8. Confirm unsupported fields such as `favourite_venue_features` are not sent.
9. Toggle push, marketing email, and SMS marketing — confirm each persists after reload.
10. Clear default suburb (X on chip) — confirm both locality IDs clear if backend allows `null`.

Requires published venues in seeded localities (see Stage 6 reference endpoint).

## Stage 4 Events honesty manual verification

1. Re-run backend and consumer app.
2. Open Search — confirm no event filter chips appear.
3. Search for a venue using `q` — confirm copy does not promise event discovery.
4. Open Home — confirm no **Events tonight** section; banner does not show event counts.
5. Open a venue card/detail with empty `events_summary` / `events.items` — confirm no event rows or “0 events”.
6. Open Map popup — confirm no event line unless real non-empty event data exists (MVP should show none).

## Stage 3 Search `q` manual verification

1. Re-run dev DB seed.
2. Open consumer Search.
3. Search for a known venue name, e.g. `Penny` — confirm the request includes `q=Penny` and matching venues appear.
4. Search for a suburb/locality, e.g. `Brunswick` — confirm matching venues appear.
5. Combine `q` with **Beer garden** — confirm `q` and `venue_features=beer_garden` are both sent.
6. Clear the search input — confirm `q` is no longer sent.
7. Enter whitespace-only input — confirm `q` is not sent.
8. Confirm event filters remain hidden.

## Stage 2 Search manual verification

1. Re-apply database seeds (`database/supabase/seed.sql` or `supabase db reset`) so `dev_seed_mvp_feature_attribute_values.sql` is loaded.
2. Open Search → Filters → pick **Brunswick** suburb, then **Beer garden** under Venue features → expect at least one venue (e.g. Penny Black / Grand View).
3. With **no suburb** selected, distance chips should appear disabled and the network request must **not** include `radius_m` (only `suburb`, feature, drink, meal, or open-now params).
4. Select **CBD** suburb, choose **5 km** distance → request must include `lat`, `lng`, and `radius_m` together.
5. `GET /api/v1/search/venues?radius_m=5000` alone should return `400` with `location_incomplete`.

## Known Deferred UI

- Event discovery is deferred: Search `event_filters` stays empty, Home has no `events_tonight` section, and venue event UI only renders when the API returns non-empty published event data.
- Correction submission supports basic profile, location, and hours payloads; attribute-domain lookup UX is deferred.
- Profile taste preferences (drinks, venue features, events, distance, personalization) are deferred; only default suburb and supported notification settings are editable.
- Google, Facebook, and Apple sign-in require Supabase provider configuration plus external provider dashboard setup.
- React Native Web browser automation is useful for smoke checks, but some native controls still require Expo Go or simulator verification.
# PubPlus Mobile - Local Cursor Run Guide

This workspace is a pnpm monorepo. The Expo Router app lives at `artifacts/mobile`.

## Prerequisites

- Node.js 22+ (Node 24 is preferred by the workspace docs)
- Corepack enabled (for pnpm): `corepack enable`

## Install dependencies

Run from `consumer_app/`:

```bash
corepack pnpm install
```

## Start Expo dev server

Run from `consumer_app/` (recommended):

```bash
corepack pnpm run mobile:start
```

Equivalent direct command from `consumer_app/artifacts/mobile/`:

```bash
corepack pnpm run start
```

## Web preview

Run from `consumer_app/`:

```bash
corepack pnpm run mobile:web
```

For accurate UI validation, open the web preview in Chrome and enable DevTools mobile device emulation (responsive/mobile viewport).
This app is mobile-first; full desktop browser width is not the target layout at this stage.

## Physical phone (Expo Go)

1. Start the dev server (`mobile:start`).
2. Scan the QR code shown in the terminal with Expo Go.
3. If LAN discovery is blocked, use tunnel mode:

```bash
corepack pnpm --filter @workspace/mobile exec expo start --tunnel
```

Expo Go on a physical phone is the preferred mobile-device check.

## Android/iOS simulator

From `consumer_app/`:

```bash
corepack pnpm run mobile:android
corepack pnpm run mobile:ios
```

Notes:
- Android requires Android Studio + emulator set up.
- iOS simulator requires macOS + Xcode, so it is not available on Windows.

## Environment variables

Create `artifacts/mobile/.env` from `artifacts/mobile/.env.example`.

Required for Stage 2 API/Auth foundation:

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
EXPO_PUBLIC_SUPABASE_URL=https://<your-project-ref>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<your-public-anon-key>
EXPO_PUBLIC_AUTH_REDIRECT_SCHEME=pubplus
```

Notes:
- `EXPO_PUBLIC_API_BASE_URL` points to the Django backend base origin.
- Frontend must only use Supabase anon/public key (never service role key).
- Keep provider client secrets (Google/Facebook/Apple) only in provider dashboards/Supabase, never in frontend env.
- `EXPO_PUBLIC_DOMAIN` remains optional for Replit-oriented flows.

## Supabase auth provider setup (required externally)

Enable providers in Supabase Auth and configure redirect URLs:

- **Google**
  - Enable Google provider in Supabase.
  - Configure Google OAuth client in Google Cloud.
  - Add Supabase callback URL from provider settings in Google Cloud allow-list.
- **Facebook**
  - Enable Facebook provider in Supabase.
  - Configure Facebook app + OAuth redirect URL shown by Supabase provider settings.
  - Ensure app mode/settings allow the test users you need.
- **Apple (iOS launch requirement)**
  - Enable Apple provider in Supabase.
  - Configure Apple Services ID / key / team details in Apple Developer + Supabase.
  - Apple sign-in helper is intentionally iOS-only in the app.

## Deep-link redirect setup

- Expo app scheme is set to `pubplus` in `artifacts/mobile/app.json`.
- OAuth redirect path used by the app is `auth/callback`.
- Native redirect URL shape:

```text
pubplus://auth/callback
```

- Expo web returns to the current app origin, for example:

```text
http://localhost:8081/auth/callback
```

- Add the native redirect URL, the web callback origin/path you actually use in development, and any Supabase callback URLs shown in dashboard to:
  - Supabase Auth URL allow-list
  - Provider dashboards (Google/Facebook/Apple)
- Some provider flows and OAuth redirects are more reliable in a development build than Expo Go; if Expo Go flow is limited, use a dev build for end-to-end SSO validation.

## Stage 2 smoke check utility

The mobile app now includes a lightweight API helper at `artifacts/mobile/lib/api.ts` with:
- `healthCheck()` -> calls `GET /api/v1/health`
- `publicApiRequest()` for unauthenticated calls
- `privateApiRequest()` for calls that require JWT

These are foundation utilities only; screens remain mock-data driven in Stage 2.

## Current known issues

- The existing `dev` script in `artifacts/mobile/package.json` is Replit-specific and depends on Replit env vars.
- Use the local scripts (`start`, `web`, `android`, `ios`) for Cursor/local development.
- If web shows a blank page, first ensure Metro output says `Web Bundled ...` (not `Web Bundling failed`).
- If Expo reports port conflicts in non-interactive mode, rerun with an explicit free port:

```bash
corepack pnpm --filter @workspace/mobile exec expo start --web --localhost --port 8082 --clear
```
