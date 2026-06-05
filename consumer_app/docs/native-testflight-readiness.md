# Native, EAS, and TestFlight Readiness — Consumer Mobile App

Source of truth for moving from **Expo Go** smoke success to **EAS native builds**, **iOS dev builds**, and **TestFlight** (production-like).

Related docs:

- [environment-strategy.md](./environment-strategy.md) — env vars, dev/prod Supabase, backend alignment
- [auth-sso-runbook.md](./auth-sso-runbook.md) — OAuth providers, redirect URLs, Apple validation
- [README.local-run.md](../README.local-run.md) — Expo Go local run

---

## Stage 6B — Brand-neutral pause (current status)

**Owner decision:** The final public app name will **not** be PubPlus. A new product name/brand is in development. **Native release work is paused** until permanent app identifiers are chosen.

### Provisional identifiers (do not treat as final)

All of the following were added in Stage 6 for config scaffolding only. **Revisit every item before EAS linking, App Store Connect, or TestFlight:**

| Identifier | Current provisional value | Where it appears |
| ---------- | ------------------------- | ---------------- |
| **App display name** | `PubPlus` | `app.json` `expo.name` |
| **iOS bundle identifier** | `com.pubplus.mobile` | `app.json` `expo.ios.bundleIdentifier` |
| **Android package name** | `com.pubplus.mobile` | `app.json` `expo.android.package` |
| **URL scheme / deep link** | `pubplus` | `app.json` `expo.scheme`, `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME`, OAuth redirects (`pubplus://auth/callback`) |
| **Railway backend domain** | `pubplus-production.up.railway.app` | `eas.json` `EXPO_PUBLIC_API_BASE_URL`, backend docs |

The Railway URL remains useful as a **temporary development/test backend**; it is not a permanent product domain.

### Release pause — do not proceed until brand is final

**Do not run** any of the following until the final brand, app name, and native identifiers are chosen:

- `eas init` (EAS project linking)
- `eas build` (any profile — development, preview, or production)
- App Store Connect app record creation
- Google Play Console app record creation
- Final Apple Sign In **production** setup (Services ID tied to final bundle ID)
- Final Google / Facebook **production** OAuth app branding and consent screens
- TestFlight build upload or internal/external tester invites
- Final splash screen, app icon, and store marketing assets

Stage 6 config files (`eas.json`, `app.json` bundle IDs) remain in the repo as **scaffolding** — they are not approval to ship under the PubPlus name.

### Rename checklist (when new brand is chosen)

Complete this checklist before resuming Stage 7+ native release work:

- [ ] **App display name** — `expo.name` in `app.json` and store listing title
- [ ] **Expo slug / EAS project name** — `expo.slug` and Expo dashboard project name
- [ ] **iOS bundle identifier** — `expo.ios.bundleIdentifier`, Apple Developer App ID, App Store Connect
- [ ] **Android package name** — `expo.android.package`, Play Console application ID
- [ ] **URL scheme** — `expo.scheme`, `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME`, Supabase redirect allow-list, provider OAuth redirect URIs
- [ ] **Railway service / domain naming** — Railway project/service display name; optional custom domain; `DJANGO_ALLOWED_HOSTS`; mobile `EXPO_PUBLIC_API_BASE_URL` in EAS profiles
- [ ] **Supabase project display names** — dashboard labels (e.g. “PubPlus Dev” → new brand); project refs/URLs unchanged unless projects are recreated
- [ ] **OAuth redirect URLs** — Supabase Auth allow-list per Dev/Prod project; `https://<ref>.supabase.co/auth/v1/callback` in Google/Facebook/Apple dashboards
- [ ] **Google / Facebook / Apple app names** — OAuth consent screens, Meta app display name, Apple Services ID labels
- [ ] **Privacy policy URL** — store listings and OAuth consent (Google, Facebook, Apple, App Store)
- [ ] **Support URL** — store listings and OAuth consent
- [ ] **App Store / Play Store metadata** — descriptions, keywords, screenshots, categories, age rating

After the checklist, update [auth-sso-runbook.md](./auth-sso-runbook.md) redirect allow-lists and [environment-strategy.md](./environment-strategy.md) env examples.

### Safe to continue (no brand lock-in)

- Backend performance optimisation (Railway deploy, home/search tuning)
- Database migrations, schema work, and data/import pipelines
- Supabase Dev/Prod split **planning** (project creation can use generic display names)
- Generic API testing against Railway or local Django
- UI/UX work in Expo Go / web that does not depend on final brand (screens, navigation, API integration)
- Documentation updates

### Blocked until brand decision

- EAS project linking (`eas init`)
- Native builds intended for TestFlight or App Store submission
- App Store Connect / Play Console app creation
- Apple Sign In production setup (requires final bundle ID)
- Google / Facebook production OAuth branding and Live-mode apps
- Final splash screen, app icon, and store marketing creative

---

## 1. Current native readiness summary

| Area | State |
| ---- | ----- |
| **Expo Go** | Suitable for smoke testing; previously passed for core flows |
| **Email/password auth** | Works when Supabase env is configured |
| **EAS config** | **`eas.json` added** (Stage 6) — profiles: `development`, `preview`, `production` |
| **Native identifiers** | **`com.pubplus.mobile`** — iOS bundle ID + Android package in `app.json` (**confirm before public launch**) |
| **`expo-dev-client`** | **Installed** — required for EAS `development` profile builds |
| **EAS project link** | **Paused (Stage 6B)** — do not run `eas init` until brand/identifiers final |
| **TestFlight** | **Paused (Stage 6B)** — config scaffolding only; blocked on final brand + identifiers |
| **Production API** | **`https://pubplus-production.up.railway.app`** — baked into EAS `preview`/`production` profiles |
| **SSO (Google/Facebook/Apple)** | Code exists; provider dashboards incomplete; **native validation required** |
| **Typecheck / OpenAPI lint** | Pass from `consumer_app/` |

**Bottom line:** Stage 6 adds EAS/native **config scaffolding** with **provisional PubPlus identifiers**. Stage 6B **pauses** `eas init`, `eas build`, and TestFlight until the final brand is chosen. See [Stage 6B](#stage-6b--brand-neutral-pause-current-status).

---

## 2. Target release path

Primary path is **iOS first** (TestFlight). Android internal testing is follow-up unless Owen prioritises it sooner.

```text
Expo Go smoke (done / ongoing for JS-level QA)
  -> EAS project setup (eas init) + eas.json  [config done Stage 6]
  -> iOS development build (expo-dev-client)
  -> native iPhone smoke (API, auth, SSO, core tabs)
  -> configure EAS Supabase secrets (Dev for dev build; Prod before external TestFlight)
  -> TestFlight build (production profile)
  -> TestFlight auth/SSO validation (Google, Facebook, Apple)
  -> App Store metadata / privacy / review readiness
```

**Android** (Play internal testing, package name, signing): defer until iOS TestFlight path is underway unless explicitly requested.

---

## 3. Required external accounts

| Account / resource | Purpose | Status |
| ------------------ | ------- | ------ |
| **Expo account** | EAS builds, credentials | Owner has account; EAS linkage **unknown** |
| **EAS** | iOS builds, env secrets, signing | **Not set up in repo** |
| **Apple Developer Program** | Bundle ID, Sign in with Apple, TestFlight, App Store | **Not confirmed** in docs/repo |
| **Supabase — PubPlus Dev** | Local / Expo Go / dev native smoke | Intended; may not exist yet |
| **Supabase — PubPlus Prod** | TestFlight + launch | Intended; may not exist yet |
| **Google Cloud** | OAuth clients (Dev + Prod recommended) | Setup deferred — [auth-sso-runbook.md](./auth-sso-runbook.md) |
| **Meta / Facebook Developer** | Facebook Login apps | Setup deferred |
| **Production backend hosting** | Django API for TestFlight | **Does not exist yet**; URL **unknown** |
| **Domain / privacy / support hosting** | Store listings, OAuth consent | **Unknown** — defer until app name final |

No third **staging** Supabase project for now (owner direction).

---

| Item | Value | Notes |
| ---- | ----- | ----- |
| **App display name** | `PubPlus` in `app.json` `expo.name` | Final public name may change |
| **Expo slug** | `mobile` | EAS project slug reference |
| **iOS bundle ID** | **`com.pubplus.mobile`** | Confirm before App Store Connect |
| **Android package** | **`com.pubplus.mobile`** | Android follow-up; not immediate priority |
| **URL scheme / deep link** | `pubplus` | OAuth: `pubplus://auth/callback` |
| **Production API URL** | **`https://pubplus-production.up.railway.app`** | In EAS `preview`/`production` `env` |
| **Privacy policy / support URLs** | **Unknown** | Required for store + OAuth consent |

### Identifier policy

- **All PubPlus identifiers are provisional (Stage 6B)** — `PubPlus`, `com.pubplus.mobile`, `pubplus`, and `pubplus-production.up.railway.app` must be revisited before any release setup. See [rename checklist](#rename-checklist-when-new-brand-is-chosen).
- **Do not run `eas init`, `eas build`, or create store records** until the final brand is chosen.
- EAS Supabase values use **secrets**, not git.
- Do not commit populated `.env` or anon keys.

---

## 5. EAS setup (Stage 6 — implemented)

### Files

| File | Purpose |
| ---- | ------- |
| `artifacts/mobile/eas.json` | Build profiles |
| `artifacts/mobile/app.json` | Bundle ID, package, scheme, plugins |
| `artifacts/mobile/.env.example` | Local env template + EAS secret notes |

### Build profiles (`eas.json`)

| Profile | Purpose | Key settings |
| ------- | ------- | -------------- |
| **development** | iOS dev client, internal device testing | `developmentClient: true`, `distribution: internal` |
| **preview** | Internal production-like build before TestFlight | Production API URL in `env`; Supabase via **EAS secrets** |
| **production** | TestFlight / App Store archive | Production API URL; `autoIncrement: true`; Supabase via **EAS secrets** |

Public env in `eas.json` (not secrets):

- `EXPO_PUBLIC_API_BASE_URL=https://pubplus-production.up.railway.app` (`preview`, `production`)
- `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME=pubplus` (all profiles)

### EAS secrets (Owen — Dashboard or CLI)

Set per project/environment; **never commit**:

```bash
cd consumer_app/artifacts/mobile
npx eas secret:create --name EXPO_PUBLIC_SUPABASE_URL --value "https://<project-ref>.supabase.co" --scope project
npx eas secret:create --name EXPO_PUBLIC_SUPABASE_ANON_KEY --value "<anon-key>" --scope project
```

| Build | Supabase target | Notes |
| ----- | --------------- | ----- |
| **development** (first native smoke) | Current single project or **PubPlus Dev** | Must match backend JWT config |
| **preview / production** | **PubPlus Prod** preferred before external TestFlight | Internal smoke may use current project temporarily |

**Never** put `SUPABASE_SERVICE_ROLE_KEY` in mobile/EAS env.

### Link EAS project (manual — **paused Stage 6B**)

```bash
cd consumer_app/artifacts/mobile
npx eas login
npx eas init
```

Adds `expo.extra.eas.projectId` to `app.json`. Required before first cloud build — **do not run until final brand and bundle ID are chosen**.

### Useful workspace scripts (from `consumer_app/`)

```bash
corepack pnpm run mobile:eas:build:ios:dev
corepack pnpm run mobile:eas:build:ios:preview
corepack pnpm run mobile:eas:build:ios:production
corepack pnpm run mobile:expo:config
```

**Do not run `eas build` (Stage 6B pause)** — wait until final brand and native identifiers are chosen.

### iOS credentials (manual)

- Apple Developer Program membership
- Team ID configured in EAS (`eas credentials`)
- App Store Connect app record — **after** bundle ID confirmed

### `expo-dev-client`

**Added in Stage 6.** Required for EAS `development` profile. Local Expo Go still works via `pnpm run mobile:start`; use `start:dev-client` (or `expo start --dev-client`) after installing a dev build on device.

---

## 6. Current Expo config audit

From `consumer_app/artifacts/mobile/app.json` (exact values as of repo inspection):

| Field | Value | Release note |
| ----- | ----- | -------------- |
| `expo.name` | `PubPlus` | Store display name may diverge later |
| `expo.slug` | `mobile` | EAS project slug reference |
| `expo.version` | `1.0.0` | Bump for each store submission |
| `expo.scheme` | `pubplus` | OAuth deep links; align with `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` |
| `expo.orientation` | `portrait` | OK for MVP |
| `expo.icon` | `./assets/images/icon.png` | Single asset — may need 1024×1024 store icon set |
| `expo.splash.image` | Same as icon | Basic; may need dedicated splash creative |
| `expo.newArchEnabled` | `true` | New Architecture on — validate on first native build |
| `expo.ios.supportsTablet` | `false` | iPhone-focused |
| `expo.ios.bundleIdentifier` | **`com.pubplus.mobile`** | Confirm before App Store |
| `expo.android.package` | **`com.pubplus.mobile`** | Android follow-up |
| `expo.android.adaptiveIcon` | **Not set** | Android store gap |
| `expo.web.favicon` | `./assets/images/icon.png` | Web only |

### Plugins (`expo.plugins`)

- `expo-dev-client` (Stage 6 — EAS development builds)
- `expo-router`
- `expo-font`
- `expo-web-browser` (OAuth)
- `expo-location` with `locationWhenInUsePermission`: *"PubPlus uses your location to show nearby pubs and distance-based search results."*

### Experiments

- `typedRoutes: true`
- `reactCompiler: true`

### Assets on disk

- `assets/images/icon.png` only (no separate adaptive icon, splash art, or iOS App Store marketing set in repo).

### `package.json` notes

- **`expo-dev-client`** installed (~6.0.21)
- **`eas.json`** at `artifacts/mobile/eas.json`
- EAS invoked via `npx eas` / workspace scripts (`mobile:eas:build:ios:*`)
- Replit `dev` / `build` / `serve` scripts — **legacy**, not TestFlight path

### Remaining release gaps

- EAS project not linked (`eas init` pending)
- Apple Developer / App Store Connect not configured
- EAS Supabase secrets not set
- SSO provider dashboards incomplete
- Minimal icon/splash (store marketing TBD)
- No `runtimeVersion` / EAS Update policy documented

---

## 7. TestFlight environment requirements

TestFlight builds should be **production-like**:

| Layer | Requirement |
| ----- | ------------- |
| **API** | Deployed **production** Django backend (`EXPO_PUBLIC_API_BASE_URL` = production URL — **TBD**) |
| **Auth** | **PubPlus Prod** Supabase |
| **Database** | Production-like DB behind prod backend (not Dev seed data) |
| **OAuth** | Google, Facebook, Apple configured on **Prod** Supabase + prod provider apps |
| **Redirects** | `pubplus://auth/callback` + Supabase prod allow-list — [auth-sso-runbook.md](./auth-sso-runbook.md) |

### Mobile env vars (EAS production profile)

| Variable | TestFlight expectation |
| -------- | ---------------------- |
| `EXPO_PUBLIC_API_BASE_URL` | **`https://pubplus-production.up.railway.app`** (EAS preview/production) |
| `EXPO_PUBLIC_SUPABASE_URL` | `https://<pubplus-prod-project-ref>.supabase.co` |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Prod anon key (EAS secret) |
| `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` | `pubplus` (unless scheme changes) |

Inject via **EAS secrets / environment** for the production build profile — do not commit prod values to git.

Backend deployment must use matching **Prod** `SUPABASE_URL`, JWT issuer, and JWKS (see [environment-strategy.md](./environment-strategy.md)).

---

## 8. iOS development build checklist

- [x] Add **`eas.json`** with development profile (Stage 6)
- [x] Set **`expo.ios.bundleIdentifier`** → `com.pubplus.mobile`
- [x] Add **`expo-dev-client`**
- [ ] Run **`eas init`** + **`eas login`** (Owen)
- [ ] Configure **EAS Supabase secrets** for dev smoke
- [ ] Configure **Apple Developer team** in EAS
- [ ] Run **`pnpm run mobile:eas:build:ios:dev`** (Owen — when ready)
- [ ] Install on **physical iPhone**
- [ ] Smoke test (API, email auth, SSO, deep links) — [auth-sso-runbook.md](./auth-sso-runbook.md)

---

## 9. TestFlight checklist (future implementation)

Prerequisites: production API deployed, Prod Supabase ready, EAS production profile configured.

### Infrastructure

- [ ] Deploy **production Django** backend; URL in EAS secrets
- [ ] Backend env: **Prod** Supabase JWT verification
- [ ] Create/configure **PubPlus Prod** Supabase
- [ ] Email/password enabled on Prod
- [ ] Google / Facebook / Apple providers on **Prod** (prod OAuth clients)
- [ ] Prod redirect allow-list (`pubplus://auth/callback`, etc.)

### EAS / Apple

- [ ] `eas.json` **production** profile with Prod env vars
- [ ] iOS **bundle ID** finalised in `app.json` + Apple Developer + App Store Connect
- [ ] EAS iOS credentials / signing
- [ ] **Build** iOS archive (`eas build --platform ios --profile production` or equivalent)
- [ ] **Submit** to App Store Connect / TestFlight
- [ ] Invite **internal testers**

### TestFlight smoke

- [ ] Cold start, tabs, API errors handled gracefully
- [ ] Email/password auth
- [ ] Google, Facebook, Apple SSO on **physical device**
- [ ] Authenticated API (no 401 JWT mismatch)
- [ ] Location permission + search/discovery smoke
- [ ] Log issues; compare Expo Go vs native behaviour

### Capture blockers

Document failures for auth runbook updates (e.g. need `expo-apple-authentication`, deep-link handler).

---

## 10. Apple Sign In decision point

| Topic | Current state |
| ----- | ------------- |
| **Implementation** | `signInWithAppleIOS()` → Supabase OAuth → `WebBrowser.openAuthSessionAsync` |
| **Native SDK** | **`expo-apple-authentication` not installed** |
| **Validation** | Must pass on **iOS dev build or TestFlight** — Expo Go is insufficient for launch sign-off |
| **App Store** | If Google/Facebook login is offered, Sign in with Apple is typically required on iOS |

### After first native Apple test

| Outcome | Action |
| ------- | ------ |
| Supabase OAuth Apple works on TestFlight | Document as accepted approach; monitor App Review feedback |
| Fails UX, review, or provider errors | Evaluate adding **`expo-apple-authentication`** in a later **code** stage (not Stage 4) |

Do not add dependencies in documentation-only stages.

---

## 11. Risks and blockers

| Blocker | Impact |
| ------- | ------ |
| **No EAS project link** | Run `eas init` before cloud build |
| **No Apple Developer** | Signing, Sign in with Apple, TestFlight blocked |
| **EAS Supabase secrets** | Auth will fail in native builds until set |
| **SSO provider setup incomplete** | Native OAuth smoke will fail until dashboards done |
| **Bundle ID provisional** | Confirm `com.pubplus.mobile` before public launch |
| **No native build smoke yet** | OAuth and location behaviour unverified outside Expo Go |
| **Possible OAuth cold-start gap** | Deep link not handled on app resume — [auth-sso-runbook.md](./auth-sso-runbook.md) |
| **Basic icon/splash** | May block polished store submission; not necessarily TestFlight internal |
| **`newArchEnabled: true`** | First native build may surface RN/New Arch issues |

---

## 12. Recommended next implementation stages

Documentation and implementation order (do not execute in Stage 4):

| Stage | Focus |
| ----- | ----- |
| **Stage 5** | Production backend deployment readiness (hosting, env, CORS, Prod Supabase JWT) |
| **Stage 6** | EAS / native config (`eas.json`, bundle ID, `expo-dev-client`) | **Done in repo** — provisional identifiers only |
| **Stage 6B** | Brand-neutral pause; rename checklist; release hold | **Current** — no `eas init` / `eas build` / store records |
| **Stage 7** | iOS dev build smoke on physical iPhone | **Paused** until brand decision |
| **Stage 8** | SSO provider setup and validation (Dev then Prod) — extends [auth-sso-runbook.md](./auth-sso-runbook.md) |
| **Stage 9** | TestFlight build, upload, internal tester smoke |
| **Stage 10** | App Store metadata, privacy policy, encryption questionnaire, screenshots |

Android Play internal testing can parallel Stage 9+ once package name and signing are defined.
