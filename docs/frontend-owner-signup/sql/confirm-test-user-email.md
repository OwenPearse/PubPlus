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
  confirmed_at = coalesce(confirmed_at, now()),
  updated_at = now()
where lower(email) = lower('replace-with-test-email@example.com')
returning id, email, email_confirmed_at, confirmed_at;
```

Canonical file: `database/sql/dev/confirm_test_user_email.sql`

## Notes

- Never commit a real personal email in SQL files; use placeholders only.
- If `confirmed_at` is not present in your Auth schema, remove that column from the `UPDATE` and keep `email_confirmed_at` only.
- Password reset after email link lands at `/access?mode=reset`; a dedicated “set new password” UI is a follow-up.
