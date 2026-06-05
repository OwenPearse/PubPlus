# Auth, SSO, and Deep-Link Runbook — Consumer Mobile App

Source of truth for Supabase Auth, OAuth providers (Google, Facebook, Apple), redirect URLs, and testing across local dev, Expo Go, and future TestFlight/production builds.

**Stage 6:** EAS/native config in repo (`eas.json`, bundle ID). Does not configure Supabase dashboards or run cloud builds.

**Stage 6B:** Native release **paused** — provisional identifiers (`PubPlus`, `com.pubplus.mobile`, `pubplus`, `pubplus-production.up.railway.app`). Do **not** run `eas init`/`eas build`, create store records, or configure **production** OAuth branding until final brand is chosen. See [native-testflight-readiness.md](./native-testflight-readiness.md#stage-6b--brand-neutral-pause-current-status).

Related docs:

- [environment-strategy.md](./environment-strategy.md) — env vars, dev/prod Supabase split, backend JWT alignment
- [README.local-run.md](../README.local-run.md) — run commands and troubleshooting

---

## 1. Auth architecture summary

### Intended flow

```text
Mobile app (artifacts/mobile)
  -> Supabase Auth (email/password or OAuth)
  -> Supabase session + JWT (access_token)
  -> Django API requests: Authorization: Bearer <access_token>
  -> Django validates JWT against configured Supabase project (backend/.env)
```

### Summary

| Topic | Status |
| ----- | ------ |
| Email/password | Supported in app code (`signInWithPassword`, `signUp`) |
| Google / Facebook / Apple OAuth | Helpers exist; **provider + Supabase dashboard setup is external** |
| Launch requirement | Google, Facebook, and Apple SSO required for launch day |
| Apple validation | Must be verified on **native iOS** (dev build or TestFlight) — not only web/Android |
| Frontend secrets | Only `EXPO_PUBLIC_SUPABASE_ANON_KEY` — never service role or provider client secrets |
| TestFlight target | **PubPlus Prod** Supabase (or current project for internal smoke) + **`https://pubplus-production.up.railway.app`** |
| Local dev target | **PubPlus Dev** Supabase + local (or reachable dev) Django |

Provider client IDs and secrets are stored in the **Supabase dashboard** per project, not in mobile env files.

### Provisional identifiers (Stage 6B)

| Item | Provisional value | Notes |
| ---- | ----------------- | ----- |
| URL scheme | `pubplus` | Native redirect: `pubplus://auth/callback` |
| iOS bundle ID | `com.pubplus.mobile` | Apple Sign In production requires **final** bundle ID |
| App display name | `PubPlus` | OAuth consent screens and store listings |
| Backend URL | `https://pubplus-production.up.railway.app` | Temporary test backend; not permanent product domain |

**Release pause:** Do not configure final Google/Facebook/Apple **production** OAuth apps, App Store Connect Sign in with Apple, or TestFlight SSO validation until the [rename checklist](./native-testflight-readiness.md#rename-checklist-when-new-brand-is-chosen) is complete. Dev Supabase OAuth setup for local/Expo Go smoke may continue.

---

## 2. Current implementation findings

Based on inspection of `artifacts/mobile` (no code changes in this stage).

### Key files

| File | Role |
| ---- | ---- |
| `lib/supabase.ts` | Supabase client, email/password, OAuth, session, `signOut`, token bridge |
| `lib/env.ts` | `EXPO_PUBLIC_*` Supabase URL, anon key, redirect scheme |
| `lib/bootstrap.ts` | On startup: API base URL + `configureApiAuthTokenBridge()` |
| `hooks/useAuthSession.ts` | Session state via `getCurrentSession` + `onAuthStateChange` |
| `app/auth.tsx` | Auth UI: email/password, Google, Facebook, Apple (iOS only) |
| `app/_layout.tsx` | Registers `auth` stack screen; calls `initializeApiAndAuthBridge()` |
| `app.json` | `scheme`: `pubplus` (must match redirect scheme) |

Profile sign-out: `app/(tabs)/profile.tsx` calls `signOut()` from `lib/supabase.ts`. Other screens navigate to `/auth` when auth is required.

### Redirect URL construction

`getOAuthRedirectUrl()` in `lib/supabase.ts`:

| Platform | Redirect URL |
| -------- | -------------- |
| **Web** | `{window.location.origin}/auth/callback` (e.g. `http://localhost:8081/auth/callback`) |
| **iOS / Android / native** | `Linking.createURL("auth/callback", { scheme: getAuthRedirectScheme() })` → typically `pubplus://auth/callback` |

- **Scheme:** `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` or default `pubplus` (`lib/env.ts`).
- **Callback path:** `auth/callback` (fixed in code).
- **`app.json`:** `"scheme": "pubplus"` — should stay aligned with env.

### OAuth completion mechanism

1. `signInWithOAuth({ provider, options: { redirectTo, skipBrowserRedirect: true } })`
2. `WebBrowser.openAuthSessionAsync(supabaseOAuthUrl, redirectTo)`
3. On `result.type === "success"`, `completeOAuthSessionFromUrl(result.url)`:
   - Prefer `exchangeCodeForSession(code)` if `code` query param present
   - Else `setSession({ access_token, refresh_token })` from URL params/hash
4. `WebBrowser.maybeCompleteAuthSession()` at module load

**There is no dedicated Expo Router screen** at `app/auth/callback.tsx`. OAuth does not rely on the user landing on a routed callback page; completion uses the URL returned to `openAuthSessionAsync`.

### Supabase client auth options

- Storage: `@react-native-async-storage/async-storage`
- `persistSession: true`, `autoRefreshToken: true`
- `detectSessionInUrl: false` (session from OAuth handled manually, not URL detection)

### Platform: Apple

- `signInWithAppleIOS()` → `signInWithOAuthProvider("apple")` only when `Platform.OS === "ios"`.
- On non-iOS, UI shows “Apple Sign In is available on iOS only.”
- Uses **Supabase OAuth + `expo-web-browser`**, not `expo-apple-authentication` (not in dependencies).

### Gaps and risks (implementation)

| Gap | Risk |
| --- | ---- |
| **No cold-start deep-link handler** | No `Linking.getInitialURL` / `useURL` listener for `pubplus://auth/callback` if OAuth returns while app was backgrounded or closed — flow assumes `openAuthSessionAsync` returns in-session |
| **No `/auth/callback` route** | Direct navigation to `/auth/callback` on web may 404; normal OAuth path uses browser session return URL |
| **Expo Go vs dev build** | Provider OAuth may behave differently; Apple especially needs native/TestFlight validation |
| **iOS bundle ID** | **`com.pubplus.mobile`** in `app.json` — confirm before App Store |

### Proposed future work (not implemented in Stage 3)

- Add cold-start OAuth URL handling if testing shows missed sessions.
- Evaluate `expo-apple-authentication` after native/EAS discovery if Supabase OAuth-only Apple flow fails App Review or TestFlight.
- Add `app/auth/callback.tsx` only if web flow requires a landing route (optional).

---

## 3. Environment matrix for auth

| Environment | Supabase project | Backend (JWT must match) | Redirect shape | Notes |
| ----------- | ---------------- | ------------------------ | -------------- | ----- |
| **Local web** | PubPlus Dev | Local Django (Dev Supabase in `backend/.env`) | `http://localhost:8081/auth/callback` | Use mobile emulation; add `8082` if port changes |
| **Expo Go / local native** | PubPlus Dev | Local or LAN Django | `pubplus://auth/callback` | Some OAuth providers limited in Expo Go |
| **Future iOS dev build** | Dev or current Supabase | Dev backend or Railway prod API | `pubplus://auth/callback` | EAS `development` profile + `expo-dev-client` — [native-testflight-readiness.md](./native-testflight-readiness.md) |
| **TestFlight** | PubPlus Prod (or current for internal) | **`https://pubplus-production.up.railway.app`** | `pubplus://auth/callback` | EAS `production` profile + secrets |
| **App Store** | PubPlus Prod | Production API | `pubplus://auth/callback` | Same as TestFlight auth config |

**Owner direction:** Skip a third staging Supabase project for now. TestFlight uses **Prod** Supabase and production backend, not Dev.

---

## 4. Supabase Auth setup checklist

Repeat for **each** project: **PubPlus Dev** and **PubPlus Prod**.

### Per-project checklist

- [ ] Create project (display name can change later; note **project ref** for URLs).
- [ ] **Authentication → Providers → Email:** enable email provider; configure confirm-email policy as needed for dev vs prod.
- [ ] **Authentication → URL configuration:**
  - [ ] **Site URL** — dev: e.g. `http://localhost:8081` or Expo docs default; prod: TBD when web domain exists.
  - [ ] **Redirect URLs** — see [§5 Redirect URL allow-list](#5-redirect-url-allow-list).
- [ ] **Google:** enable provider; paste **Google OAuth client ID + secret** (from Google Cloud) into Supabase — not into mobile env.
- [ ] **Facebook:** enable provider; paste **Facebook App ID + secret** into Supabase.
- [ ] **Apple:** enable provider; paste Apple **Services ID / key / team** details per Supabase Apple provider docs.
- [ ] Copy **Project URL** + **anon public key** to the correct env:
  - Dev → `artifacts/mobile/.env` + local `backend/.env`
  - Prod → EAS secrets / prod backend env (Stage 4) — not shared dev `.env`
- [ ] Confirm **service role key** is never in mobile `EXPO_PUBLIC_*`.
- [ ] Configure **backend** `SUPABASE_URL`, `SUPABASE_JWT_ISSUER`, `SUPABASE_JWT_JWKS_URL` for the **same** project (see `backend/.env.example`).

---

## 5. Redirect URL allow-list

Add to **Supabase → Authentication → URL configuration → Redirect URLs** for each project.

### PubPlus Dev (examples)

```text
http://localhost:8081/auth/callback
http://127.0.0.1:8081/auth/callback
http://localhost:8082/auth/callback
http://127.0.0.1:8082/auth/callback
pubplus://auth/callback
```

Use the ports you actually run (`mobile:web` defaults to Expo’s localhost port; add alternates if you change port).

### PubPlus Prod (examples)

```text
pubplus://auth/callback
https://<future-production-web-domain>/auth/callback
```

Only add the `https://` web callback if you ship web auth against that domain later. **Do not invent domains.**

### Provider dashboards (Google / Facebook / Apple)

Each provider must allow Supabase’s OAuth callback for that project:

```text
https://<project-ref>.supabase.co/auth/v1/callback
```

Replace `<project-ref>` with the Dev or Prod project ref from the Supabase dashboard. **Dev and Prod have different refs** → configure each provider app (or separate OAuth clients) per environment.

---

## 6. Google SSO setup runbook

High-level steps (manual, in Google Cloud + Supabase).

### PubPlus Dev (local testing)

1. Create or select a **Google Cloud project** (can be separate from prod).
2. Configure **OAuth consent screen** (testing mode acceptable for dev).
3. Create **OAuth 2.0 Client ID** (type per Supabase docs — often Web application for Supabase callback).
4. In **Authorized redirect URIs**, add:
   ```text
   https://<pubplus-dev-project-ref>.supabase.co/auth/v1/callback
   ```
5. In **PubPlus Dev** Supabase → Authentication → Google: paste Client ID and Client Secret.
6. Ensure Dev redirect allow-list includes localhost and `pubplus://` (§5).
7. Test: Expo web (`mobile:web`) → Auth → Continue with Google; then Expo Go/native if needed.

### PubPlus Prod (TestFlight / launch)

1. Prefer a **separate** Google Cloud OAuth client (or project) for production.
2. Consent screen: production branding, privacy policy URL, support email — **URLs not finalised**.
3. Redirect URI:
   ```text
   https://<pubplus-prod-project-ref>.supabase.co/auth/v1/callback
   ```
4. Configure **PubPlus Prod** Supabase Google provider with prod client credentials.
5. Validate on **TestFlight build** ([native-testflight-readiness.md](./native-testflight-readiness.md)), not only Expo Go.

### Unresolved decisions

- Final **public app name** and store listing name
- **Privacy policy** and **support** URLs for production consent screen
- **Production domain** for any future web OAuth
- Whether Dev and Prod always use **separate** Google OAuth clients (recommended) vs temporary shared test client

---

## 7. Facebook SSO setup runbook

### PubPlus Dev

1. Create app in **Meta for Developers** (Facebook Login product).
2. Add **Valid OAuth Redirect URIs** (or Facebook Login settings):
   ```text
   https://<pubplus-dev-project-ref>.supabase.co/auth/v1/callback
   ```
3. While in **Development** mode: add test users as needed.
4. Paste **App ID** and **App Secret** into PubPlus Dev Supabase → Facebook provider.
5. Test web and native flows.

### PubPlus Prod

1. Separate Meta app or switch existing app to **Live** when ready for TestFlight/public users.
2. Redirect URI:
   ```text
   https://<pubplus-prod-project-ref>.supabase.co/auth/v1/callback
   ```
3. Configure privacy policy URL, app icon, category — **placeholders until branding finalised**.
4. Plan for **App Review** if Facebook requires it for public login at scale.

### Unresolved decisions

- Production **app display name** and branding assets
- **Privacy policy URL** (required for Meta/Facebook production)
- Whether Facebook Login is **public** or restricted at launch

---

## 8. Apple SSO setup runbook

### Requirements

- **Apple Developer Program** membership (account/team TBD).
- If the iOS app offers **Google or Facebook** sign-in, **Sign in with Apple** is typically required on iOS for App Store guidelines.
- Current app uses **Supabase Apple OAuth** via `expo-web-browser`, not native Apple Authentication SDK.

### PubPlus Dev (limited until bundle ID exists)

1. Apple Developer → **Identifiers** / **Services IDs** / **Keys** per Supabase Apple provider documentation.
2. Configure **Sign in with Apple** for a Services ID; associate with app identifier when **bundle ID is chosen** ([native-testflight-readiness.md](./native-testflight-readiness.md)).
3. In PubPlus Dev Supabase → Apple provider: enter Services ID, secret/key, team ID per Supabase UI.
4. Test on **iOS simulator or Expo Go** only as a smoke test; **full validation requires dev build or TestFlight**.

### PubPlus Prod (TestFlight / App Store)

1. Create **App ID** with Sign in with Apple capability — requires **final iOS bundle ID** (unknown).
2. Create **Services ID** and key for Supabase prod callback:
   ```text
   https://<pubplus-prod-project-ref>.supabase.co/auth/v1/callback
   ```
3. Configure PubPlus Prod Supabase Apple provider.
4. Validate on **TestFlight** with Prod Supabase + production backend.

### Unresolved decisions

- Final **iOS bundle ID**
- Final **app name** (App Store Connect)
- **Apple Developer team** account owner
- Whether **Supabase OAuth-only Apple** is sufficient for App Review, or **`expo-apple-authentication`** must be added later (evaluate in Stage 4/5 testing — do not add in Stage 3)

---

## 9. Testing checklists

Use **PubPlus Dev** + local dev backend unless noted. After OAuth success, confirm a protected action (e.g. save venue, profile PATCH) returns **200**, not **401**.

### Email/password

- [ ] Sign up with new email (Dev Supabase)
- [ ] Sign in with existing user
- [ ] Sign out from Profile
- [ ] Kill and reopen app — session persists (`AsyncStorage`)
- [ ] Authenticated API call succeeds (Bearer token)
- [ ] Missing `EXPO_PUBLIC_SUPABASE_*` — auth screen shows config message; buttons disabled

### Google

| Context | Checklist |
| ------- | --------- |
| Local web | [ ] Redirect completes; session established; API works |
| Expo Go / native | [ ] Attempt; note if provider blocks or Expo Go limits flow |
| iOS dev build | [ ] Planned Stage 4+ |
| TestFlight (Prod) | [ ] Planned after prod API + Prod Supabase + Google prod client |

### Facebook

| Context | Checklist |
| ------- | --------- |
| Local web | [ ] Redirect completes; session established |
| Expo Go / native | [ ] Attempt; dev mode test users if app in Development |
| iOS dev build | [ ] Planned Stage 4+ |
| TestFlight (Prod) | [ ] Planned with Prod Facebook app + Live mode if required |

### Apple

| Context | Checklist |
| ------- | --------- |
| Web / Android | [ ] Apple button hidden or shows iOS-only message |
| iOS Expo Go | [ ] Smoke only — may not match TestFlight behaviour |
| iOS dev build / TestFlight | [ ] **Required:** successful login; cancelled login shows error; Bearer works with **prod** backend on TestFlight build |
| Cancelled flow | [ ] User dismisses browser — app shows error, no partial session |

---

## 10. Known risks / blockers

| Risk | Detail |
| ---- | ------ |
| Final app name / domain | Store and OAuth branding URLs undecided |
| iOS bundle ID / Android package | **`com.pubplus.mobile`** (provisional — Stage 6B pause before App Store) |
| No EAS / native build yet | TestFlight and reliable Apple OAuth blocked — [native-testflight-readiness.md](./native-testflight-readiness.md) |
| No production API deployed yet | Must deploy before TestFlight; URL unknown |
| Supabase Dev/Prod | May not exist yet — owner checklist below |
| Provider dashboards | Google/Facebook/Apple not configured until manual setup |
| Expo Go vs native | OAuth may fail or differ in Expo Go; document results per provider |
| Apple on native | Likely needs TestFlight or dev build validation |
| Cold-start deep links | No handler if OAuth returns outside `openAuthSessionAsync` session |
| JWT mismatch | Dev mobile + Prod backend (or vice versa) → 401 on API after “successful” login |

---

## 11. Owner checklist

- [ ] Create **PubPlus Dev** and **PubPlus Prod** in Supabase.
- [ ] Enable email/password on both; configure redirect URLs (§5).
- [ ] Copy Dev URL + anon key → `artifacts/mobile/.env` and local `backend/.env` (JWT fields aligned).
- [ ] Store Prod URL + anon key securely for EAS/TestFlight (Stage 4).
- [ ] **Deploy production Django API** before TestFlight; configure prod backend for **Prod** Supabase JWT.
- [ ] **Google:** Dev client + Prod client (recommended); Supabase provider enabled per project.
- [ ] **Facebook:** Dev app + Prod app; redirect URIs per project ref.
- [ ] **Apple:** Developer account ready; defer production Services ID until **bundle ID** chosen.
- [ ] Confirm TestFlight uses **Supabase Prod + production backend** (not Dev).
- [ ] Do not put service role or provider secrets in mobile env.
- [ ] Complete EAS/native setup per [native-testflight-readiness.md](./native-testflight-readiness.md); run SSO smoke on TestFlight after upload.

---

## 12. Future implementation stages

| Stage | Topic |
| ----- | ----- |
| **Stage 6B** | Brand-neutral pause — no production OAuth branding or TestFlight SSO until rename |
| **Native/EAS** | [native-testflight-readiness.md](./native-testflight-readiness.md) — Stages 7–10 **paused** until brand |
| **Post-native** | Apple validation; decide on `expo-apple-authentication` if TestFlight fails |
| **TestFlight** | SSO smoke on Prod Supabase + production API — **after** brand + provider prod apps |
| **Launch** | App Store metadata, privacy, provider prod review |

Do not implement these in the auth runbook stage.
