import { createClient, type Session, type SupabaseClient } from "@supabase/supabase-js";

import { getSupabasePublishableKey, getSupabaseUrl, hasSupabaseAuthConfig } from "@/shared/lib/env";

let client: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (client) return client;
  const url = getSupabaseUrl();
  const key = getSupabasePublishableKey();
  if (!url || !key) {
    throw new Error("Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY.");
  }
  client = createClient(url, key, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
  return client;
}

export async function getAccessToken(): Promise<string | null> {
  if (!hasSupabaseAuthConfig()) return null;
  const { data } = await getSupabaseClient().auth.getSession();
  return data.session?.access_token ?? null;
}

export async function getCurrentSession(): Promise<Session | null> {
  if (!hasSupabaseAuthConfig()) return null;
  const { data } = await getSupabaseClient().auth.getSession();
  return data.session;
}

export async function signInWithPassword(email: string, password: string) {
  const { data, error } = await getSupabaseClient().auth.signInWithPassword({
    email,
    password,
  });
  if (error) throw error;
  return data.session;
}

export async function signUpWithPassword(email: string, password: string) {
  const { data, error } = await getSupabaseClient().auth.signUp({ email, password });
  if (error) throw error;
  return data;
}

export async function signOut() {
  await getSupabaseClient().auth.signOut();
}

export function onAuthStateChange(
  callback: (session: Session | null) => void,
): () => void {
  const { data } = getSupabaseClient().auth.onAuthStateChange((_event, session) => {
    callback(session);
  });
  return () => data.subscription.unsubscribe();
}

// --- MFA (TOTP via Supabase Auth) ---

export type AuthenticatorAssuranceLevel = {
  currentLevel: "aal1" | "aal2" | null;
  nextLevel: "aal1" | "aal2" | null;
};

export type MfaTotpFactor = {
  id: string;
  friendlyName?: string;
  status: "verified" | "unverified";
};

export type MfaTotpEnrollment = {
  factorId: string;
  qrCode: string;
  secret: string;
};

export type PostAuthMfaStep = "complete" | "enroll" | "verify";

export function isMfaSatisfied(aal: AuthenticatorAssuranceLevel): boolean {
  return aal.currentLevel === "aal2" && aal.nextLevel === "aal2";
}

export function needsMfaVerification(aal: AuthenticatorAssuranceLevel): boolean {
  return aal.currentLevel === "aal1" && aal.nextLevel === "aal2";
}

function toAssuranceLevel(
  level: string | null | undefined,
): AuthenticatorAssuranceLevel["currentLevel"] {
  if (level === "aal1" || level === "aal2") return level;
  return null;
}

export async function getAuthenticatorAssuranceLevel(): Promise<AuthenticatorAssuranceLevel> {
  const { data, error } = await getSupabaseClient().auth.mfa.getAuthenticatorAssuranceLevel();
  if (error) throw error;
  return {
    currentLevel: toAssuranceLevel(data.currentLevel),
    nextLevel: toAssuranceLevel(data.nextLevel),
  };
}

export async function listMfaFactors(): Promise<MfaTotpFactor[]> {
  const { data, error } = await getSupabaseClient().auth.mfa.listFactors();
  if (error) throw error;
  const totp = data.totp ?? [];
  return totp.map((factor) => ({
    id: factor.id,
    friendlyName: factor.friendly_name ?? undefined,
    status: factor.status as "verified" | "unverified",
  }));
}

export async function getVerifiedTotpFactorId(): Promise<string | null> {
  const factors = await listMfaFactors();
  const verified = factors.find((f) => f.status === "verified");
  return verified?.id ?? null;
}

export async function resolvePostAuthMfaStep(): Promise<PostAuthMfaStep> {
  const aal = await getAuthenticatorAssuranceLevel();
  if (isMfaSatisfied(aal)) return "complete";
  if (needsMfaVerification(aal)) {
    const factorId = await getVerifiedTotpFactorId();
    return factorId ? "verify" : "enroll";
  }
  return "enroll";
}

export async function enrollTotpFactor(friendlyName = "Authenticator app"): Promise<MfaTotpEnrollment> {
  const { data, error } = await getSupabaseClient().auth.mfa.enroll({
    factorType: "totp",
    friendlyName,
  });
  if (error) throw error;
  if (!data?.id || !data.totp) {
    throw new Error("Could not start authenticator enrollment. Please try again.");
  }
  return {
    factorId: data.id,
    qrCode: data.totp.qr_code,
    secret: data.totp.secret,
  };
}

export async function challengeMfaFactor(factorId: string): Promise<string> {
  const { data, error } = await getSupabaseClient().auth.mfa.challenge({ factorId });
  if (error) throw error;
  if (!data?.id) {
    throw new Error("Could not start verification challenge. Please try again.");
  }
  return data.id;
}

export async function verifyMfaChallenge(params: {
  factorId: string;
  challengeId: string;
  code: string;
}) {
  const { data, error } = await getSupabaseClient().auth.mfa.verify({
    factorId: params.factorId,
    challengeId: params.challengeId,
    code: params.code.trim(),
  });
  if (error) throw error;
  return data;
}

export async function unenrollMfaFactor(factorId: string) {
  const { data, error } = await getSupabaseClient().auth.mfa.unenroll({ factorId });
  if (error) throw error;
  return data;
}
