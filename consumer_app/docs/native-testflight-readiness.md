# Native, EAS, and TestFlight Readiness — Consumer Mobile App

Source of truth for moving from **Expo Go** smoke success to **EAS native builds**, **iOS dev builds**, and **TestFlight** (production-like). This document plans future implementation; it does **not** create `eas.json`, bundle IDs, or native config.

Related docs:

- [environment-strategy.md](./environment-strategy.md) — env vars, dev/prod Supabase, backend alignment
- [auth-sso-runbook.md](./auth-sso-runbook.md) — OAuth providers, redirect URLs, Apple validation
- [README.local-run.md](../README.local-run.md) — Expo Go local run

---

## 1. Current native readiness summary

| Area | State |
| ---- | ----- |
| **Expo Go** | Suitable for smoke testing; previously passed for core flows |
| **Email/password auth** | Works when Supabase Dev env is configured |
| **Native dev builds** | Not configured — no `eas.json`, no iOS bundle ID |
| **EAS** | Intended; owner has Expo account; **EAS project/link not confirmed in repo** |
| **TestFlight** | Not started — blocked on production API, EAS, identifiers, Prod Supabase |
| **SSO (Google/Facebook/Apple)** | Code exists; provider dashboards incomplete; **native validation required** for launch |
| **Apple Sign In** | Supabase browser OAuth via `expo-web-browser` — not `expo-apple-authentication` |
| **Typecheck / OpenAPI lint** | Pass from `consumer_app/` |
| **Mobile lint/test scripts** | None defined |
| **Replit deploy** | Legacy — not required for current release path |

**Bottom line:** Expo Go proves JS bundle and integration; **TestFlight readiness is a separate track** requiring EAS, native identifiers, deployed production backend, and Prod Supabase.

---

## 2. Target release path

Primary path is **iOS first** (TestFlight). Android internal testing is follow-up unless Owen prioritises it sooner.

```text
Expo Go smoke (done / ongoing for JS-level QA)
  -> EAS project setup + eas.json
  -> iOS development build (expo-dev-client TBD)
  -> native iPhone smoke (API, auth, SSO, core tabs)
  -> deploy production Django backend (URL TBD)
  -> configure Prod Supabase + provider OAuth (prod)
  -> TestFlight build (Prod Supabase + production API via EAS env)
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

## 4. Native identifiers and naming decisions

These are **not final**. Do not create permanent App Store / Play records or hardcode production names in repo docs until Owen confirms.

| Item | Current / placeholder | Notes |
| ---- | --------------------- | ----- |
| **App display name** | `PubPlus` in `app.json` `expo.name` | Final public name **not chosen** |
| **Expo slug** | `mobile` | May differ from store listing name |
| **iOS bundle ID** | **Missing** in `app.json` | Required for EAS iOS + Apple Developer |
| **Android package name** | **Missing** in `app.json` `android.package` | Required for Play; follow-up after iOS |
| **URL scheme / deep link** | `pubplus` (`scheme` in `app.json`) | Used for `pubplus://auth/callback`; may change with final branding |
| **Production API URL** | **Unknown** | Must exist before TestFlight |
| **Production web domain** | **Unknown** | Only if web OAuth against prod domain later |
| **Privacy policy / support URLs** | **Unknown** | Required for store + OAuth consent screens |

### Placeholder policy

- Use `PubPlus Dev` / `PubPlus Prod` and `<bundle-id TBD>` in planning docs.
- Avoid committing real bundle IDs or store IDs until a dedicated implementation stage.
- EAS env injection should carry secrets/URLs — not source-controlled `.env` for prod.

---

## 5. EAS setup requirements (future implementation)

A later stage will **create** configuration; this section lists decisions only.

### EAS project

- [ ] Link `artifacts/mobile` to an EAS project (`eas init` or equivalent) under owner Expo account.
- [ ] Confirm org/team name on Expo — **unknown** from repo.

### `eas.json` (to be created later)

Likely build profiles:

| Profile | Purpose |
| ------- | ------- |
| **development** | Dev client, internal device testing, **PubPlus Dev** Supabase + dev/reachable API |
| **preview** (optional) | Internal distribution before TestFlight |
| **production** | TestFlight / App Store archive, **PubPlus Prod** + **production API** |

### Environment variables (EAS)

Inject at build time (secrets), not in git:

- `EXPO_PUBLIC_API_BASE_URL`
- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`
- `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` (likely `pubplus` until scheme changes)

**TestFlight production profile** must use **Prod** Supabase and **deployed production** Django base URL.

### iOS credentials

- [ ] Apple Developer team ID — **unknown**
- [ ] Distribution certificate / provisioning via EAS credentials or manual
- [ ] App Store Connect app record — **after** bundle ID and name strategy

### Workflow decisions (TBD)

| Decision | Options / notes |
| -------- | ---------------- |
| **`expo-dev-client`** | Not in `package.json` today; likely needed for reliable dev native + OAuth smoke |
| **Managed vs prebuild** | Current `app.json` plugins suggest managed workflow; confirm at implementation |
| **Runtime version / OTA** | No `runtimeVersion` or `updates` in `app.json` today — decide for EAS Update later or skip initially |

**Do not create `eas.json` in documentation-only stages.**

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
| `expo.ios.bundleIdentifier` | **Not set** | **Blocker** for iOS EAS |
| `expo.android` | `{}` empty | **No `package`** — Android release blocked |
| `expo.android.adaptiveIcon` | **Not set** | Android store gap |
| `expo.web.favicon` | `./assets/images/icon.png` | Web only |

### Plugins (`expo.plugins`)

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

- **No** `expo-dev-client`, **no** `expo-apple-authentication`
- **No** `eas-cli` script; EAS invoked via `npx eas` / global CLI at implementation time
- Replit `dev` / `build` / `serve` scripts — **legacy**, not TestFlight path

### Obvious release gaps

- Missing iOS bundle ID and Android package
- No `eas.json`
- Minimal icon/splash (store marketing TBD)
- No App Store privacy manifest / encryption export compliance docs in repo (add at submission stage)
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
| `EXPO_PUBLIC_API_BASE_URL` | `https://<production-api-url>` (**unknown**) |
| `EXPO_PUBLIC_SUPABASE_URL` | `https://<pubplus-prod-project-ref>.supabase.co` |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Prod anon key (EAS secret) |
| `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` | `pubplus` (unless scheme changes) |

Inject via **EAS secrets / environment** for the production build profile — do not commit prod values to git.

Backend deployment must use matching **Prod** `SUPABASE_URL`, JWT issuer, and JWKS (see [environment-strategy.md](./environment-strategy.md)).

---

## 8. iOS development build checklist (future implementation)

Use **PubPlus Dev** + local or LAN Django unless explicitly testing against deployed API.

- [ ] Decide **bundle ID** strategy (final vs temporary dev bundle — coordinate with Apple Developer)
- [ ] Create/link **EAS project** for `artifacts/mobile`
- [ ] Add **`eas.json`** with development profile
- [ ] Set **`expo.ios.bundleIdentifier`** in `app.json` (implementation stage)
- [ ] Add **`expo-dev-client`** if dev builds require custom native client (likely for OAuth reliability)
- [ ] Configure **Apple Developer team** in EAS
- [ ] Run **EAS development build** for iOS
- [ ] Install on **physical iPhone**
- [ ] Smoke test:
  - [ ] App launches
  - [ ] `GET /api/v1/health` (or Home load) succeeds
  - [ ] Email/password sign-in, sign-out, session after restart
  - [ ] Google SSO
  - [ ] Facebook SSO
  - [ ] Apple SSO (iOS)
  - [ ] Saved venues, profile PATCH, submission/correction if in scope
- [ ] Note OAuth/cold-start issues — see [auth-sso-runbook.md](./auth-sso-runbook.md) implementation gaps

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
| **No production API** | Cannot complete meaningful TestFlight against real launch backend |
| **Production API URL unknown** | Cannot set EAS prod `EXPO_PUBLIC_API_BASE_URL` |
| **No `eas.json` / EAS project** | No native binaries |
| **No iOS bundle ID** | Cannot register app or build for TestFlight |
| **Apple Developer not confirmed** | Signing, Sign in with Apple, TestFlight blocked |
| **PubPlus Prod Supabase may not exist** | Prod auth/OAuth blocked |
| **SSO provider setup incomplete** | Launch-day requirement; native testing will fail until done |
| **Final app name / domain not chosen** | Store metadata and OAuth consent URLs blocked |
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
| **Stage 6** | EAS / native config implementation (`eas.json`, bundle ID, `expo-dev-client` decision, `app.json` iOS block) |
| **Stage 7** | iOS dev build smoke on physical iPhone |
| **Stage 8** | SSO provider setup and validation (Dev then Prod) — extends [auth-sso-runbook.md](./auth-sso-runbook.md) |
| **Stage 9** | TestFlight build, upload, internal tester smoke |
| **Stage 10** | App Store metadata, privacy policy, encryption questionnaire, screenshots |

Android Play internal testing can parallel Stage 9+ once package name and signing are defined.
