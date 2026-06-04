# Confirm test user email (dev/staging)

**DEV/STAGING ONLY — do not run against production unless explicitly approved.**

## Purpose

After creating a test account through Supabase sign-up on `/access`, mark the user's email as confirmed so QA can continue to sign-in and MFA without relying on email delivery.

## Steps

1. Create the account via `/access` → **Create account** (or Supabase dashboard).
2. Open the **dev/staging** Supabase project SQL Editor.
3. Run the SQL below after replacing the email placeholder.

## SQL

```sql
-- DEV/STAGING ONLY
update auth.users
set
  email_confirmed_at = coalesce(email_confirmed_at, now()),
  updated_at = now()
where lower(email) = lower('replace-with-test-email@example.com')
returning id, email, email_confirmed_at, confirmed_at;
```

Canonical file: `database/sql/dev/confirm_test_user_email.sql`

## Notes

- On current PubApp Auth schema, `confirmed_at` is a **generated** column — do not set it in `UPDATE`; only set `email_confirmed_at`.
- Never commit a real personal email in SQL files; use placeholders only.
- Supabase may reject `@test.com` and `@demo.pubplus.local` for sign-up; prefer disposable domains such as `@sharklasers.com` for E2E QA.
- Password reset after email link lands at `/access?mode=reset` to set a new password before signing in again.
- **Seeded demo users** (`*@demo.pubplus.local`): if sign-in shows `Database error querying schema`, run `repair-seeded-auth-users.md` / `database/sql/dev/repair_auth_users_null_tokens.sql` first.
