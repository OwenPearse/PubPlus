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

/** Poll until Supabase persists a session token (post sign-in race). */
export async function waitForAccessToken(options?: {
  maxAttempts?: number;
  delayMs?: number;
}): Promise<string | null> {
  const maxAttempts = options?.maxAttempts ?? 6;
  const delayMs = options?.delayMs ?? 100;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const token = await getAccessToken();
    if (token) return token;
    if (attempt + 1 < maxAttempts) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  return null;
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

export const TOTP_FRIENDLY_NAME = "Authenticator app";

export const DUPLICATE_MFA_FACTOR_MESSAGE =
  "An authenticator setup already exists for this account. Continue by entering your verification code, or restart setup if you no longer have access.";

export function isDuplicateMfaFactorError(error: unknown): boolean {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "object" && error !== null && "message" in error
        ? String((error as { message: unknown }).message)
        : String(error);
  return /friendly name|already exists/i.test(message);
}

export function formatMfaError(error: unknown, fallback: string): string {
  if (isDuplicateMfaFactorError(error)) return DUPLICATE_MFA_FACTOR_MESSAGE;
  return error instanceof Error ? error.message : fallback;
}

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

/** Alias for listMfaFactors — existing TOTP factors for the signed-in user. */
export async function getExistingTotpFactors(): Promise<MfaTotpFactor[]> {
  return listMfaFactors();
}

/** Prefer a verified factor; otherwise the first unverified TOTP factor. */
export async function getPrimaryTotpFactor(): Promise<MfaTotpFactor | null> {
  const factors = await getExistingTotpFactors();
  return factors.find((f) => f.status === "verified") ?? factors.find((f) => f.status === "unverified") ?? null;
}

export async function getVerifiedTotpFactorId(): Promise<string | null> {
  const factors = await getExistingTotpFactors();
  return factors.find((f) => f.status === "verified")?.id ?? null;
}

export async function getUnverifiedTotpFactorId(): Promise<string | null> {
  const factors = await getExistingTotpFactors();
  return factors.find((f) => f.status === "unverified")?.id ?? null;
}

export async function resolvePostAuthMfaStep(): Promise<PostAuthMfaStep> {
  const aal = await getAuthenticatorAssuranceLevel();
  if (isMfaSatisfied(aal)) return "complete";
  if (needsMfaVerification(aal)) {
    const verifiedId = await getVerifiedTotpFactorId();
    if (verifiedId) return "verify";
    return "enroll";
  }
  const primary = await getPrimaryTotpFactor();
  if (primary?.status === "verified") return "verify";
  if (primary?.status === "unverified") return "enroll";
  return "enroll";
}

export type TotpEnrollmentStart =
  | { kind: "new"; enrollment: MfaTotpEnrollment }
  | { kind: "resume-unverified"; factorId: string }
  | { kind: "existing-verified"; factorId: string };

function classifyTotpEnrollmentStart(factors: MfaTotpFactor[]): TotpEnrollmentStart | null {
  const verified = factors.find((f) => f.status === "verified");
  if (verified) {
    return { kind: "existing-verified", factorId: verified.id };
  }
  const unverified = factors.find((f) => f.status === "unverified");
  if (unverified) {
    return { kind: "resume-unverified", factorId: unverified.id };
  }
  return null;
}

/** GoTrue factor list can lag briefly right after sign-in; retry before enrolling. */
export async function listTotpFactorsWithRetry(
  attempts = 4,
  delayMs = 300,
): Promise<MfaTotpFactor[]> {
  let factors: MfaTotpFactor[] = [];
  for (let attempt = 0; attempt < attempts; attempt++) {
    factors = await getExistingTotpFactors();
    if (factors.length > 0) return factors;
    if (attempt < attempts - 1) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  return factors;
}

export async function startOrRecoverTotpEnrollment(): Promise<TotpEnrollmentStart> {
  const existing = classifyTotpEnrollmentStart(await listTotpFactorsWithRetry());
  if (existing) return existing;
  try {
    const enrollment = await enrollTotpFactor(TOTP_FRIENDLY_NAME);
    return { kind: "new", enrollment };
  } catch (err) {
    if (!isDuplicateMfaFactorError(err)) throw err;
    const recovered = classifyTotpEnrollmentStart(await listTotpFactorsWithRetry(6, 400));
    if (recovered) return recovered;
    throw err;
  }
}

/** Removes stale unverified TOTP factors, then enrolls a new one. Never removes verified factors. */
export async function restartUnverifiedTotpEnrollment(): Promise<MfaTotpEnrollment> {
  const factors = await getExistingTotpFactors();
  for (const factor of factors.filter((f) => f.status === "unverified")) {
    await unenrollMfaFactor(factor.id);
  }
  return enrollTotpFactor(TOTP_FRIENDLY_NAME);
}

export async function enrollTotpFactor(friendlyName = TOTP_FRIENDLY_NAME): Promise<MfaTotpEnrollment> {
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

export function getPasswordResetRedirectUrl(): string {
  if (typeof window !== "undefined" && window.location?.origin) {
    return `${window.location.origin}/access?mode=reset`;
  }
  return "/access?mode=reset";
}

export async function sendPasswordResetEmail(email: string, redirectTo?: string) {
  const { error } = await getSupabaseClient().auth.resetPasswordForEmail(email.trim(), {
    redirectTo: redirectTo ?? getPasswordResetRedirectUrl(),
  });
  if (error) throw error;
}

export function formatPasswordUpdateError(error: unknown, fallback: string): string {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "object" && error !== null && "message" in error
        ? String((error as { message: unknown }).message)
        : String(error);
  if (/session missing|not authenticated|auth session|invalid token|expired|otp_expired/i.test(message)) {
    return "This reset link is invalid or has expired. Request a new password reset email from the sign-in page.";
  }
  return error instanceof Error ? error.message : fallback;
}

export async function updatePassword(newPassword: string) {
  const { data, error } = await getSupabaseClient().auth.updateUser({
    password: newPassword,
  });
  if (error) throw error;
  return data.user;
}
