-- Grant internal admin: link Supabase auth user to public.admin_account.
-- auth_user_id must exist in auth.users (sign up in Supabase Auth first).
--
-- Usage: replace 00000000-0000-0000-0000-000000000000 with your Supabase JWT sub, then run
-- in the Supabase SQL editor or via psql \i database/sql/seeds/grant_admin_account.sql

DO $$
DECLARE
  target_auth_user_id uuid := '00000000-0000-0000-0000-000000000000'::uuid;
  found_email text;
  new_admin_id uuid;
BEGIN
  IF target_auth_user_id = '00000000-0000-0000-0000-000000000000'::uuid THEN
    RAISE EXCEPTION
      'Replace the placeholder UUID with your Supabase auth.users id (JWT sub) before running.';
  END IF;

  SELECT email INTO found_email
  FROM auth.users
  WHERE id = target_auth_user_id;

  IF found_email IS NULL THEN
    RAISE EXCEPTION
      'auth.users row not found for %. Sign in via Supabase Auth first, then re-run.',
      target_auth_user_id;
  END IF;

  INSERT INTO public.admin_account (auth_user_id)
  VALUES (target_auth_user_id)
  ON CONFLICT (auth_user_id) DO UPDATE
    SET auth_user_id = EXCLUDED.auth_user_id
  RETURNING id INTO new_admin_id;

  RAISE NOTICE 'admin_account granted for % (email: %, admin_account.id: %)',
    target_auth_user_id, found_email, new_admin_id;
END $$;

SELECT
  a.id AS admin_account_id,
  a.auth_user_id,
  u.email
FROM public.admin_account a
JOIN auth.users u ON u.id = a.auth_user_id
WHERE a.auth_user_id = '00000000-0000-0000-0000-000000000000'::uuid;
