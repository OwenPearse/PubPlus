import { beforeEach, describe, expect, it, vi } from "vitest";

const getAuthenticatorAssuranceLevel = vi.fn();
const listFactors = vi.fn();

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
      mfa: {
        getAuthenticatorAssuranceLevel,
        listFactors,
      },
    },
  }),
}));

import {
  getVerifiedTotpFactorId,
  isMfaSatisfied,
  needsMfaVerification,
  resolvePostAuthMfaStep,
} from "@/shared/lib/supabase";

describe("MFA helpers", () => {
  beforeEach(() => {
    getAuthenticatorAssuranceLevel.mockReset();
    listFactors.mockReset();
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

  it("resolvePostAuthMfaStep returns enroll when no MFA is set up", async () => {
    getAuthenticatorAssuranceLevel.mockResolvedValue({
      data: { currentLevel: "aal1", nextLevel: "aal1" },
      error: null,
    });
    await expect(resolvePostAuthMfaStep()).resolves.toBe("enroll");
  });
});
