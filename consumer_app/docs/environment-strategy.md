# Environment and Supabase Strategy — Consumer Mobile App

Source of truth for how PubPlus should configure mobile environment variables, Supabase projects, and backend alignment across local dev, physical-device testing, TestFlight, and production.

**Guidance only** — this document does not implement EAS profiles, deploy backends, or configure provider dashboards. Auth/SSO provider setup: **[auth-sso-runbook.md](./auth-sso-runbook.md)**. Production Django API deployment readiness for TestFlight: **[backend/docs/PRODUCTION_API_READINESS.md](../../backend/docs/PRODUCTION_API_READINESS.md)**.

Entry point: [README.md](../README.md). Local run commands: [README.local-run.md](../README.local-run.md).

---

## Stage 6B — Provisional identifiers and release pause

**Owner decision:** The final public app name will **not** be PubPlus. Native release work is **paused** until permanent identifiers are chosen.

### Provisional values (temporary — revisit before release)

| Item | Provisional value |
| ---- | ----------------- |
| App display name | `PubPlus` |
| iOS bundle ID | `com.pubplus.mobile` |
| Android package | `com.pubplus.mobile` |
| URL scheme | `pubplus` |
| Production API domain | `pubplus-production.up.railway.app` |

The Railway URL is a **temporary dev/test backend** — useful for API smoke and performance work, not a permanent product domain.

### Do not proceed until brand is final

Do **not** run `eas init`, `eas build`, create App Store Connect / Play Console records, configure final Apple/Google/Facebook production OAuth apps, or submit TestFlight builds until the rename checklist in [native-testflight-readiness.md](./native-testflight-readiness.md#rename-checklist-when-new-brand-is-chosen) is complete.

### Safe to continue

- Local dev and Expo Go with **Supabase Dev** + local or Railway API
- Backend performance optimisation and Railway deploy/smoke
- Database migrations, import planning, and data work
- Supabase Dev/Prod split **planning** (display names can change later)
- Generic API testing (`EXPO_PUBLIC_API_BASE_URL` pointing at Railway for device smoke)
- UI/UX work that does not depend on final brand
- Documentation

### Blocked until brand decision

- EAS project linking and native builds for TestFlight
- App Store Connect / Play Console app creation
- Production OAuth provider branding (Google consent screen, Meta Live app, Apple Services ID for final bundle ID)
- Locking `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` / URL scheme in provider dashboards for production
- Final privacy policy and support URLs in store/OAuth flows

---

## 1. Environment overview

| Environment | Purpose | Mobile API target (`EXPO_PUBLIC_API_BASE_URL`) | Supabase target |
| ----------- | ------- | ---------------------------------------------- | --------------- |
| **Local dev** | Cursor/local Expo on simulator or web | `http://localhost:8000` (local Django) or other reachable **dev** backend | **Supabase Dev** |
| **Physical device / Expo Go** | Real phone smoke testing | LAN IP, ngrok, or **staging** URL — **not** `localhost` on the phone | **Supabase Dev** |
| **TestFlight** | iOS pre-release testing (production-like) | **`https://pubplus-production.up.railway.app`** | **Supabase Prod** (or current project for internal smoke) |
| **Production** | App Store / Play Store users | **`https://pubplus-production.up.railway.app`** | **Supabase Prod** |

### Notes

- **One mobile `.env` file per machine** is typical for local work (`artifacts/mobile/.env`). TestFlight/production values are usually injected at **EAS build time** — see [native-testflight-readiness.md](./native-testflight-readiness.md); not committed to git.
- **Supabase Dev** and **Supabase Prod** must never be mixed with the wrong backend JWT verification config (see [Backend alignment](#5-backend-alignment)).
- **Replit** (`EXPO_PUBLIC_DOMAIN`, `build.js`, `serve.js`) is **legacy/unconfirmed** — not the documented local or release path unless Owen confirms otherwise.

---

## 2. Recommended Supabase split

### Two projects (recommended)

| Project (suggested name) | Use for |
| ------------------------ | ------- |
| **PubPlus Dev** | Local development, Expo Go, simulators, internal smoke tests |
| **PubPlus Prod** | TestFlight, App Store, production users |

### Why two projects

- **Isolation** — test users, broken OAuth experiments, and seed data stay out of production auth and data.
- **Safer keys** — dev anon key exposure during local work does not compromise prod user sessions.
- **Provider config** — Google/Facebook/Apple OAuth apps can use dev callbacks on Dev and separate prod apps on Prod (required for launch; see [auth-sso-runbook.md](./auth-sso-runbook.md)).
- **JWT alignment** — Django verifies JWTs from the Supabase project configured in backend env; Dev mobile + Dev backend + Dev Supabase must match.

### Practices

- **Dev** can contain messy test accounts and repeated sign-up/delete cycles.
- **Prod** should be created early enough to configure TestFlight, but treat user data as real once TestFlight testers are invited.
- **Display names** in the Supabase dashboard (e.g. “PubPlus Dev”) can be renamed later if the public app name changes — project refs and URLs are what matter in env files.
- **Service role key** must **never** appear in the mobile app or any `EXPO_PUBLIC_*` variable. Backend may use it server-side only (`SUPABASE_SERVICE_ROLE_KEY` in `backend/.env.example`).
- **Anon / publishable key** is the expected frontend credential (`EXPO_PUBLIC_SUPABASE_ANON_KEY`).

---

## 3. Mobile environment variables

All mobile config is read from `EXPO_PUBLIC_*` variables (see `artifacts/mobile/lib/env.ts`). Expo embeds these at bundle time for the active build profile.

| Variable | Required | Example (placeholder) | Local dev | Physical device / Expo Go | TestFlight / Prod |
| -------- | -------- | --------------------- | --------- | ------------------------- | ----------------- |
| `EXPO_PUBLIC_API_BASE_URL` | Yes (has code default `http://localhost:8000`) | `http://localhost:8000` | Local Django on same machine | `http://<LAN-IP>:8000` or Railway URL for device smoke | **`https://pubplus-production.up.railway.app`** (EAS preview/production) |
| `EXPO_PUBLIC_SUPABASE_URL` | Yes for auth | `https://<pubplus-dev-project-ref>.supabase.co` | **Dev** project URL | **Dev** project URL | **Prod** project URL |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Yes for auth | `<pubplus-dev-anon-key>` | **Dev** anon key | **Dev** anon key | **Prod** anon key |
| `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME` | No (default `pubplus`) | `pubplus` | `pubplus` | `pubplus` | `pubplus` (unless native IDs change later) |
| `EXPO_PUBLIC_DOMAIN` | No | `your-replit-domain.replit.dev` | **Legacy / Replit** — omit for Cursor local dev | Same | Not used for standard EAS/TestFlight path unless Replit confirmed |

### Per-variable notes

**`EXPO_PUBLIC_API_BASE_URL`**

- Django API **origin only** (no trailing path); app calls `/api/v1/...` under this base.
- Physical devices: `localhost` points at the phone, not your PC.
- For TestFlight, backend must allow the deployment host in `DJANGO_ALLOWED_HOSTS` and CORS if web clients are used.
- Production URL: **`https://pubplus-production.up.railway.app`** — set in EAS `preview`/`production` profiles (`eas.json`); local `.env` stays on localhost for dev.

**`EXPO_PUBLIC_SUPABASE_URL`**

- Must match the Supabase project whose anon key you use.
- Wrong project → auth succeeds in client but Django JWT verification fails (401).

**`EXPO_PUBLIC_SUPABASE_ANON_KEY`**

- Public anon/publishable key only.
- Rotating keys requires updating mobile env and any running Metro bundler restart.

**`EXPO_PUBLIC_AUTH_REDIRECT_SCHEME`**

- Must match `scheme` in `artifacts/mobile/app.json` (currently `pubplus`).
- Native redirect shape: `{scheme}://auth/callback`.

**`EXPO_PUBLIC_DOMAIN`**

- Used by legacy Replit `dev` / `build.js` flows.
- **Not required** for local `mobile:start` / `mobile:web`.
- Treat as inactive unless Owen confirms Replit is still a deploy target.

---

## 4. Example env files

Copy `artifacts/mobile/.env.example` to `artifacts/mobile/.env`. **Do not commit** filled `.env` files.

### Local web / simulator

Same machine as Django:

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
EXPO_PUBLIC_SUPABASE_URL=https://<pubplus-dev-project-ref>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<pubplus-dev-anon-key>
EXPO_PUBLIC_AUTH_REDIRECT_SCHEME=pubplus
```

### Physical phone / Expo Go

Replace LAN IP with your computer’s address on the local network. Ensure Django listens on `0.0.0.0` or the LAN interface and `DJANGO_ALLOWED_HOSTS` / `DJANGO_CORS_ALLOWED_ORIGINS` allow the origin you use.

```bash
EXPO_PUBLIC_API_BASE_URL=http://<your-computer-lan-ip>:8000
EXPO_PUBLIC_SUPABASE_URL=https://<pubplus-dev-project-ref>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<pubplus-dev-anon-key>
EXPO_PUBLIC_AUTH_REDIRECT_SCHEME=pubplus
```

**Alternatives** to LAN IP:

- **ngrok** (or similar) tunnel to local Django — use the HTTPS tunnel origin as `EXPO_PUBLIC_API_BASE_URL`.
- **Hosted staging API** — if a staging deployment exists (**URL unknown**), point the phone at that URL and use backend env configured for **Supabase Dev** (or a dedicated staging Supabase — decision pending).

### Future TestFlight (and production builds)

Production API URL is configured in **`eas.json`** for `preview` and `production` profiles. Supabase values must be **EAS secrets** (not git):

```bash
EXPO_PUBLIC_API_BASE_URL=https://pubplus-production.up.railway.app
EXPO_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
EXPO_PUBLIC_AUTH_REDIRECT_SCHEME=pubplus
```

Create secrets:

```bash
cd consumer_app/artifacts/mobile
npx eas secret:create --name EXPO_PUBLIC_SUPABASE_URL --value "https://<ref>.supabase.co" --scope project
npx eas secret:create --name EXPO_PUBLIC_SUPABASE_ANON_KEY --value "<anon-key>" --scope project
```

**Internal smoke** may use the current single Supabase project temporarily. Create **PubPlus Prod** before inviting external TestFlight testers. Never put service role keys in EAS/mobile env.

See [native-testflight-readiness.md](./native-testflight-readiness.md) for profile details.

---

## 5. Backend alignment

The mobile app sends `Authorization: Bearer <supabase_access_token>` to Django. The backend validates JWTs against the Supabase project configured in **backend** environment (see `backend/.env.example`):

| Backend variable (conceptual) | Must align with mobile |
| ----------------------------- | ---------------------- |
| `SUPABASE_URL` | Same project as `EXPO_PUBLIC_SUPABASE_URL` |
| `SUPABASE_ANON_KEY` | Same project as `EXPO_PUBLIC_SUPABASE_ANON_KEY` (for some flows) |
| `SUPABASE_JWT_ISSUER` | `https://<project-ref>.supabase.co/auth/v1` for that project |
| `SUPABASE_JWT_JWKS_URL` | JWKS URL for that project |

### Rules

| Mobile build context | Supabase (mobile) | Backend deployment should use |
| -------------------- | ----------------- | ------------------------------ |
| Local dev, Expo Go, simulators | **PubPlus Dev** | Django configured for **Dev** Supabase (local `.env` or dev deployment) |
| TestFlight, App Store | **PubPlus Prod** | Django configured for **Prod** Supabase (production or agreed staging deployment) |

**Mismatch symptom:** sign-in appears to work in the app, then authenticated API calls return **401** from Django.

### CORS (Expo web only)

For local web on port 8081, `backend/.env.example` already lists `http://localhost:8081` and `http://127.0.0.1:8081` under `DJANGO_CORS_ALLOWED_ORIGINS`. If you change Expo web port or use a LAN IP for API from web, update backend CORS accordingly.

Native apps using Bearer tokens are less affected by browser CORS, but the API host must still be reachable and allowed.

---

## 6. Redirect URL planning

OAuth uses path `auth/callback` (see `artifacts/mobile/lib/supabase.ts`). Allow these in **each Supabase project** (Auth → URL configuration) and in provider dashboards. Full provider steps: **[auth-sso-runbook.md](./auth-sso-runbook.md)**.

| Flow | Redirect URL (pattern) |
| ---- | ---------------------- |
| Expo web local | `http://localhost:8081/auth/callback` (and `8082` if you change port) |
| Native / Expo Go / dev build | `pubplus://auth/callback` |
| TestFlight / prod native | `pubplus://auth/callback` (same scheme until native config changes) |
| Supabase provider callback | `https://<project-ref>.supabase.co/auth/v1/callback` |

### Important

- **Dev** and **Prod** Supabase projects have **different** `<project-ref>` → different Supabase callback URLs.
- Google, Facebook, and Apple each need allow-lists updated **per environment** (Dev providers for local/TestFlight internal testing; Prod providers for launch).
- Full Google/Facebook/Apple setup: **[auth-sso-runbook.md](./auth-sso-runbook.md)**.
- Some OAuth flows are more reliable in a **development build** than Expo Go — plan native validation before launch.

---

## 7. What changes when the app name is final

**Stage 6B:** All PubPlus-branded identifiers are **provisional**. Native release is **paused** until the checklist below is completed.

| Item | Current provisional status |
| ---- | -------------------------- |
| App display name | `PubPlus` — will change |
| iOS bundle ID | `com.pubplus.mobile` — will change |
| Android package | `com.pubplus.mobile` — will change |
| URL scheme | `pubplus` — likely will change |
| Production API domain | `pubplus-production.up.railway.app` — temporary; custom domain TBD |
| App Store Connect record | **Not created** (blocked) |
| Google Play package | **Not created** (blocked) |
| Production OAuth app display names | **Blocked** until final branding |
| Privacy policy / support URLs | **Unknown** — required before store + OAuth consent |

### Rename checklist (when new brand is chosen)

- [ ] App display name (`expo.name`, store title)
- [ ] Expo slug / EAS project name
- [ ] iOS bundle identifier (`expo.ios.bundleIdentifier`, Apple Developer, App Store Connect)
- [ ] Android package name (`expo.android.package`, Play Console)
- [ ] URL scheme (`expo.scheme`, `EXPO_PUBLIC_AUTH_REDIRECT_SCHEME`, Supabase + provider redirect allow-lists)
- [ ] Railway service/domain naming; `EXPO_PUBLIC_API_BASE_URL` in EAS profiles; `DJANGO_ALLOWED_HOSTS`
- [ ] Supabase project display names (dashboard labels only — refs unchanged unless projects recreated)
- [ ] OAuth redirect URLs in Google, Facebook, Apple dashboards per Dev/Prod project
- [ ] Google / Facebook / Apple app names on OAuth consent screens
- [ ] Privacy policy URL
- [ ] Support URL
- [ ] App Store / Play Store metadata (descriptions, screenshots, categories)

After rename: update `app.json`, `eas.json`, EAS secrets, [auth-sso-runbook.md](./auth-sso-runbook.md), and backend `DJANGO_ALLOWED_HOSTS` if the API domain changes.

Full pause details and blocked actions: [native-testflight-readiness.md](./native-testflight-readiness.md#stage-6b--brand-neutral-pause-current-status).

---

## 8. Recommended owner setup checklist

For Owen (manual steps in Supabase and local machine):

- [ ] Create or access Supabase organisation for PubPlus.
- [ ] Create project **PubPlus Dev** (display name can change later).
- [ ] Create project **PubPlus Prod** (keep prod data clean; use for TestFlight when ready).
- [ ] In **Dev**: enable email/password auth; note **Project URL** and **anon public** key.
- [ ] Copy Dev URL and anon key into `artifacts/mobile/.env` for local work (never commit).
- [ ] Configure **local Django** `backend/.env` with the **same Dev** `SUPABASE_URL`, JWT issuer/JWKS, and related values from `backend/.env.example`.
- [ ] Store **Prod** URL and anon key securely for EAS/TestFlight later — do not put Prod secrets in shared dev `.env` unless intentional.
- [ ] Confirm **service role** key stays server-side only — never in mobile `EXPO_PUBLIC_*`.
- [ ] Add Dev redirect URLs to Supabase Auth allow-list (localhost:8081, `pubplus://auth/callback`).
- [ ] Complete Google, Facebook, and Apple provider setup per **[auth-sso-runbook.md](./auth-sso-runbook.md)** (required for launch day).
- [ ] Decide production vs staging API URL before first TestFlight build with real data.
- [ ] Confirm whether separate **dev** and **prod** backend deployments will exist (unknown).

---

## 9. Open questions

| Question | Why it matters |
| -------- | -------------- |
| **Production API URL** | **`https://pubplus-production.up.railway.app`** — in EAS profiles |
| **TestFlight API target** | Production Railway backend (same as above) |
| **Final public app name** | Store listings and OAuth app names |
| **iOS bundle ID / Android package** | **`com.pubplus.mobile`** — confirm before stores |
| **EAS org / project linkage** | Run `eas init` — config in repo, link pending |
| **Dev + prod backend deployments** | Whether two Django deployments mirror two Supabase projects |
| **Replit** | Still required for any environment? Currently legacy/unconfirmed |
| **Dedicated staging Supabase** | Two-project split (Dev/Prod) may be enough, or a third “Staging” project may be needed later |

---

## Related documentation (planned)

| Stage | Topic |
| ----- | ----- |
| Auth / SSO / deep-link | [auth-sso-runbook.md](./auth-sso-runbook.md) (current) |
| Native / EAS / TestFlight | [native-testflight-readiness.md](./native-testflight-readiness.md) (current planning) |
| Production API deployment | [backend/docs/PRODUCTION_API_READINESS.md](../../backend/docs/PRODUCTION_API_READINESS.md) (current) |
| Stage 6+ | Release and App Store checklist (future) |
