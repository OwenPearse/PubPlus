-- DEV/STAGING ONLY — do not run against production unless explicitly approved.
--
-- Marks a Supabase Auth user's email as confirmed so portal QA can sign in without
-- waiting for a confirmation email. Replace the placeholder email before running.
--
-- Run in Supabase SQL Editor (dev/staging project) or psql against your dev database.

update auth.users
set
  email_confirmed_at = coalesce(email_confirmed_at, now()),
  confirmed_at = coalesce(confirmed_at, now()),
  updated_at = now()
where lower(email) = lower('replace-with-test-email@example.com')
returning id, email, email_confirmed_at, confirmed_at;
