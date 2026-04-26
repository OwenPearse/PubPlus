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
- Expected redirect URL shape:

```text
pubplus://auth/callback
```

- Add this redirect URL (and any Supabase callback URLs shown in dashboard) to:
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
