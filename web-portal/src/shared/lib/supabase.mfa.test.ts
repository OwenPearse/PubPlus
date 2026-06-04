import { beforeEach, describe, expect, it, vi } from "vitest";

const getAuthenticatorAssuranceLevel = vi.fn();
const listFactors = vi.fn();
const enroll = vi.fn();
const unenroll = vi.fn();
const resetPasswordForEmail = vi.fn();
const updateUser = vi.fn();

vi.mock("@/shared/lib/env", () => ({
  hasSupabaseAuthConfig: () => true,
  getSupabaseUrl: () => "https://example.supabase.co",
  getSupabasePublishableKey: () => "publishable-key",
}));

vi.mock("@supabase/supabase-js", () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn(() => ({ data: { subscription: { unsubscribe: vi.fn() } } })),
      resetPasswordForEmail,
      updateUser,
      mfa: {
        getAuthenticatorAssuranceLevel,
        listFactors,
        enroll,
        unenroll,
      },
    },
  }),
}));

import {
  DUPLICATE_MFA_FACTOR_MESSAGE,
  getPrimaryTotpFactor,
  getVerifiedTotpFactorId,
  isDuplicateMfaFactorError,
  isMfaSatisfied,
  needsMfaVerification,
  resolvePostAuthMfaStep,
  restartUnverifiedTotpEnrollment,
  formatPasswordUpdateError,
  sendPasswordResetEmail,
  startOrRecoverTotpEnrollment,
  updatePassword,
} from "@/shared/lib/supabase";

describe("MFA helpers", () => {
  beforeEach(() => {
    getAuthenticatorAssuranceLevel.mockReset();
    listFactors.mockReset();
    enroll.mockReset();
    unenroll.mockReset();
    resetPasswordForEmail.mockReset();
    updateUser.mockReset();
    resetPasswordForEmail.mockResolvedValue({ error: null });
    updateUser.mockResolvedValue({ data: { user: { id: "u1" } }, error: null });
  });

  it("isMfaSatisfied is true only at aal2/aal2", () => {
    expect(isMfaSatisfied({ currentLevel: "aal2", nextLevel: "aal2" })).toBe(true);
    expect(isMfaSatisfied({ currentLevel: "aal1", nextLevel: "aal2" })).toBe(false);
    expect(isMfaSatisfied({ currentLevel: "aal1", nextLevel: "aal1" })).toBe(false);
  });

  it("needsMfaVerification detects enrolled but unverified session", () => {
    expect(needsMfaVerification({ currentLevel: "aal1", nextLevel: "aal2" })).toBe(true);
    expect(needsMfaVerification({ currentLevel: "aal1", nextLevel: "aal1" })).toBe(false);
  });

  it("resolvePostAuthMfaStep returns complete when MFA satisfied", async () => {
    getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: { currentLevel: "aal2", nextLevel: "aal2" },
      error: null,
    });
    await expect(resolvePostAuthMfaStep()).resolves.toBe("complete");
  });

  it("resolvePostAuthMfaStep returns verify when challenge required", async () => {
    getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: { currentLevel: "aal1", nextLevel: "aal2" },
      error: null,
    });
    listFactors.mockResolvedValue({
      data: { totp: [{ id: "factor-1", status: "verified", friendly_name: "App" }] },
      error: null,
    });
    await expect(resolvePostAuthMfaStep()).resolves.toBe("verify");
    await expect(getVerifiedTotpFactorId()).resolves.toBe("factor-1");
  });

  it("resolvePostAuthMfaStep returns enroll when only unverified TOTP exists", async () => {
    getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: { currentLevel: "aal1", nextLevel: "aal2" },
      error: null,
    });
    listFactors.mockResolvedValue({
      data: {
        totp: [{ id: "factor-u", status: "unverified", friendly_name: "Authenticator app" }],
      },
      error: null,
    });
    await expect(resolvePostAuthMfaStep()).resolves.toBe("enroll");
  });

  it("resolvePostAuthMfaStep returns enroll when no MFA is set up", async () => {
    getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: { currentLevel: "aal1", nextLevel: "aal1" },
      error: null,
    });
    listFactors.mockResolvedValue({ data: { totp: [] }, error: null });
    await expect(resolvePostAuthMfaStep()).resolves.toBe("enroll");
  });

  it("getPrimaryTotpFactor prefers verified over unverified", async () => {
    listFactors.mockResolvedValue({
      data: {
        totp: [
          { id: "u1", status: "unverified", friendly_name: "A" },
          { id: "v1", status: "verified", friendly_name: "B" },
        ],
      },
      error: null,
    });
    await expect(getPrimaryTotpFactor()).resolves.toMatchObject({ id: "v1", status: "verified" });
  });

  it("startOrRecoverTotpEnrollment resumes unverified without enrolling", async () => {
    listFactors.mockResolvedValue({
      data: {
        totp: [{ id: "factor-u", status: "unverified", friendly_name: "Authenticator app" }],
      },
      error: null,
    });
    await expect(startOrRecoverTotpEnrollment()).resolves.toEqual({
      kind: "resume-unverified",
      factorId: "factor-u",
    });
    expect(enroll).not.toHaveBeenCalled();
  });

  it("startOrRecoverTotpEnrollment routes verified factor without enrolling", async () => {
    listFactors.mockResolvedValue({
      data: {
        totp: [{ id: "factor-v", status: "verified", friendly_name: "Authenticator app" }],
      },
      error: null,
    });
    await expect(startOrRecoverTotpEnrollment()).resolves.toEqual({
      kind: "existing-verified",
      factorId: "factor-v",
    });
    expect(enroll).not.toHaveBeenCalled();
  });

  it("startOrRecoverTotpEnrollment recovers from duplicate friendly-name enroll error", async () => {
    listFactors
      .mockResolvedValueOnce({ data: { totp: [] }, error: null })
      .mockResolvedValueOnce({
        data: {
          totp: [{ id: "factor-dup", status: "unverified", friendly_name: "Authenticator app" }],
        },
        error: null,
      });
    enroll.mockResolvedValue({
      data: null,
      error: { message: 'A factor with the friendly name "Authenticator app" for this user already exists' },
    });
    await expect(startOrRecoverTotpEnrollment()).resolves.toEqual({
      kind: "resume-unverified",
      factorId: "factor-dup",
    });
  });

  it("isDuplicateMfaFactorError detects friendly-name conflicts", () => {
    expect(
      isDuplicateMfaFactorError(
        new Error('A factor with the friendly name "Authenticator app" for this user already exists'),
      ),
    ).toBe(true);
    expect(isDuplicateMfaFactorError(new Error("Network error"))).toBe(false);
    expect(DUPLICATE_MFA_FACTOR_MESSAGE).toContain("authenticator setup already exists");
  });

  it("restartUnverifiedTotpEnrollment unenrolls only unverified factors", async () => {
    listFactors
      .mockResolvedValueOnce({
        data: {
          totp: [
            { id: "u1", status: "unverified", friendly_name: "A" },
            { id: "v1", status: "verified", friendly_name: "B" },
          ],
        },
        error: null,
      })
      .mockResolvedValueOnce({ data: { totp: [] }, error: null });
    unenroll.mockResolvedValue({ data: {}, error: null });
    enroll.mockResolvedValue({
      data: {
        id: "factor-new",
        totp: { qr_code: "qr", secret: "SECRET" },
      },
      error: null,
    });
    await expect(restartUnverifiedTotpEnrollment()).resolves.toMatchObject({
      factorId: "factor-new",
      secret: "SECRET",
    });
    expect(unenroll).toHaveBeenCalledTimes(1);
    expect(unenroll).toHaveBeenCalledWith({ factorId: "u1" });
    expect(unenroll).not.toHaveBeenCalledWith({ factorId: "v1" });
  });

  it("sendPasswordResetEmail calls Supabase reset API", async () => {
    await sendPasswordResetEmail("user@example.com", "https://portal.test/access?mode=reset");
    expect(resetPasswordForEmail).toHaveBeenCalledWith("user@example.com", {
      redirectTo: "https://portal.test/access?mode=reset",
    });
  });

  it("updatePassword calls Supabase updateUser", async () => {
    await updatePassword("new-secret-12");
    expect(updateUser).toHaveBeenCalledWith({ password: "new-secret-12" });
  });

  it("formatPasswordUpdateError maps expired session to friendly copy", () => {
    expect(
      formatPasswordUpdateError(new Error("Auth session missing"), "fallback"),
    ).toContain("invalid or has expired");
  });
});
