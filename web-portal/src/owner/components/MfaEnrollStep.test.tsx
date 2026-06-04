import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MfaEnrollStep } from "@/owner/components/MfaEnrollStep";

const enrollTotpFactor = vi.fn();
const challengeMfaFactor = vi.fn();
const verifyMfaChallenge = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  enrollTotpFactor: (...args: unknown[]) => enrollTotpFactor(...args),
  challengeMfaFactor: (...args: unknown[]) => challengeMfaFactor(...args),
  verifyMfaChallenge: (...args: unknown[]) => verifyMfaChallenge(...args),
}));

describe("MfaEnrollStep", () => {
  beforeEach(() => {
    enrollTotpFactor.mockReset();
    challengeMfaFactor.mockReset();
    verifyMfaChallenge.mockReset();
    enrollTotpFactor.mockResolvedValue({
      factorId: "factor-enroll",
      qrCode: "data:image/svg+xml,qr",
      secret: "SECRET123",
    });
  });

  it("renders QR and manual secret when enrollment succeeds", async () => {
    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByAltText("QR code for authenticator app")).toBeInTheDocument();
    });
    expect(screen.getByText("SECRET123")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Verify code" })).toBeDisabled();
  });

  it("verifies code and calls onComplete", async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn();
    challengeMfaFactor.mockResolvedValue("challenge-1");
    verifyMfaChallenge.mockResolvedValue({});

    render(<MfaEnrollStep onComplete={onComplete} onSignOut={vi.fn()} />);

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

  it("shows error when verification fails", async () => {
    const user = userEvent.setup();
    challengeMfaFactor.mockResolvedValue("challenge-1");
    verifyMfaChallenge.mockRejectedValue(new Error("Invalid TOTP code"));

    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByLabelText("Authenticator verification code")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Authenticator verification code"), "000000");
    await user.click(screen.getByRole("button", { name: "Verify code" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Invalid TOTP code");
    });
  });

  it("disables submit while verifying", async () => {
    const user = userEvent.setup();
    let resolveChallenge: (value: string) => void = () => {};
    challengeMfaFactor.mockReturnValue(
      new Promise<string>((resolve) => {
        resolveChallenge = resolve;
      }),
    );

    render(<MfaEnrollStep onComplete={vi.fn()} onSignOut={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByLabelText("Authenticator verification code")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("Authenticator verification code"), "123456");
    await user.click(screen.getByRole("button", { name: "Verify code" }));

    expect(screen.getByRole("button", { name: "Verifying…" })).toBeDisabled();

    resolveChallenge("challenge-1");
    verifyMfaChallenge.mockResolvedValue({});
    await waitFor(() => {
      expect(verifyMfaChallenge).toHaveBeenCalled();
    });
  });
});
