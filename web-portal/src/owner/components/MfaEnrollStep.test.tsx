import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MfaEnrollStep } from "@/owner/components/MfaEnrollStep";
import { DUPLICATE_MFA_FACTOR_MESSAGE } from "@/shared/lib/supabase";

const startOrRecoverTotpEnrollment = vi.fn();
const restartUnverifiedTotpEnrollment = vi.fn();
const challengeMfaFactor = vi.fn();
const verifyMfaChallenge = vi.fn();

vi.mock("@/shared/lib/supabase", async () => {
  const actual = await vi.importActual<typeof import("@/shared/lib/supabase")>("@/shared/lib/supabase");
  return {
    ...actual,
    startOrRecoverTotpEnrollment: (...args: unknown[]) => startOrRecoverTotpEnrollment(...args),
    restartUnverifiedTotpEnrollment: (...args: unknown[]) => restartUnverifiedTotpEnrollment(...args),
    challengeMfaFactor: (...args: unknown[]) => challengeMfaFactor(...args),
    verifyMfaChallenge: (...args: unknown[]) => verifyMfaChallenge(...args),
  };
});

describe("MfaEnrollStep", () => {
  beforeEach(() => {
    startOrRecoverTotpEnrollment.mockReset();
    restartUnverifiedTotpEnrollment.mockReset();
    challengeMfaFactor.mockReset();
    verifyMfaChallenge.mockReset();
    startOrRecoverTotpEnrollment.mockResolvedValue({
      kind: "new",
      enrollment: {
        factorId: "factor-enroll",
        qrCode: "data:image/svg+xml,qr",
        secret: "SECRET123",
      },
    });
    restartUnverifiedTotpEnrollment.mockResolvedValue({
      factorId: "factor-restarted",
      qrCode: "data:image/svg+xml,qr2",
      secret: "NEWSECRET",
    });
  });

  it("renders QR and manual secret when enrollment succeeds", async () => {
    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} onNeedVerify={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByAltText("QR code for authenticator app")).toBeInTheDocument();
    });
    expect(screen.getByText("SECRET123")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verify code" })).toBeDisabled();
  });

  it("routes to verify when a verified factor already exists", async () => {
    const onNeedVerify = vi.fn();
    startOrRecoverTotpEnrollment.mockResolvedValue({
      kind: "existing-verified",
      factorId: "factor-verified",
    });

    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} onNeedVerify={onNeedVerify} />);

    await waitFor(() => {
      expect(onNeedVerify).toHaveBeenCalledWith("factor-verified");
    });
  });

  it("resumes unverified factor without calling enroll", async () => {
    startOrRecoverTotpEnrollment.mockResolvedValue({
      kind: "resume-unverified",
      factorId: "factor-stale",
    });

    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} onNeedVerify={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByLabelText("Authenticator verification code")).toBeInTheDocument();
    });
    expect(screen.queryByAltText("QR code for authenticator app")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Restart setup" })).toBeInTheDocument();
  });

  it("shows friendly copy on duplicate-factor recovery path", async () => {
    startOrRecoverTotpEnrollment.mockRejectedValue(
      new Error('A factor with the friendly name "Authenticator app" for this user already exists'),
    );

    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} onNeedVerify={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(DUPLICATE_MFA_FACTOR_MESSAGE);
    });
  });

  it("verifies code and calls onComplete", async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn();
    challengeMfaFactor.mockResolvedValue("challenge-1");
    verifyMfaChallenge.mockResolvedValue({});

    render(<MfaEnrollStep onComplete={onComplete} onSignOut={vi.fn()} onNeedVerify={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByLabelText("Authenticator verification code")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Authenticator verification code"), "123456");
    await user.click(screen.getByRole("button", { name: "Verify code" }));

    await waitFor(() => {
      expect(challengeMfaFactor).toHaveBeenCalledWith("factor-enroll");
      expect(verifyMfaChallenge).toHaveBeenCalledWith({
        factorId: "factor-enroll",
        challengeId: "challenge-1",
        code: "123456",
      });
      expect(onComplete).toHaveBeenCalled();
    });
  });

  it("restart setup replaces stale unverified enrollment", async () => {
    const user = userEvent.setup();
    startOrRecoverTotpEnrollment.mockResolvedValue({
      kind: "resume-unverified",
      factorId: "factor-stale",
    });

    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} onNeedVerify={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Restart setup" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Restart setup" }));

    await waitFor(() => {
      expect(restartUnverifiedTotpEnrollment).toHaveBeenCalled();
      expect(screen.getByText("NEWSECRET")).toBeInTheDocument();
    });
  });

  it("sign out is separated from retry actions", async () => {
    startOrRecoverTotpEnrollment.mockRejectedValue(new Error("setup failed"));

    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} onNeedVerify={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Retry setup" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument();
    });
  });
});
