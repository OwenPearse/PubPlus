import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MfaVerifyStep } from "@/owner/components/MfaVerifyStep";

const challengeMfaFactor = vi.fn();
const verifyMfaChallenge = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  challengeMfaFactor: (...args: unknown[]) => challengeMfaFactor(...args),
  verifyMfaChallenge: (...args: unknown[]) => verifyMfaChallenge(...args),
}));

describe("MfaVerifyStep", () => {
  beforeEach(() => {
    challengeMfaFactor.mockReset();
    verifyMfaChallenge.mockReset();
    challengeMfaFactor.mockResolvedValue("challenge-verify");
    verifyMfaChallenge.mockResolvedValue({});
  });

  it("submits code through MFA verify helpers", async () => {
    const user = userEvent.setup();
    const onComplete = vi.fn();

    render(
      <MfaVerifyStep factorId="factor-verify" onComplete={onComplete} onSignOut={vi.fn()} />,
    );

    await user.type(screen.getByLabelText("Authenticator code"), "654321");
    await user.click(screen.getByRole("button", { name: "Verify and continue" }));

    await waitFor(() => {
      expect(challengeMfaFactor).toHaveBeenCalledWith("factor-verify");
      expect(verifyMfaChallenge).toHaveBeenCalledWith({
        factorId: "factor-verify",
        challengeId: "challenge-verify",
        code: "654321",
      });
      expect(onComplete).toHaveBeenCalled();
    });
  });

  it("shows human-readable error on failed verification", async () => {
    const user = userEvent.setup();
    verifyMfaChallenge.mockRejectedValue(new Error("Invalid verification code"));

    render(
      <MfaVerifyStep factorId="factor-verify" onComplete={vi.fn()} onSignOut={vi.fn()} />,
    );

    await user.type(screen.getByLabelText("Authenticator code"), "111111");
    await user.click(screen.getByRole("button", { name: "Verify and continue" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Invalid verification code");
    });
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("disables submit while verifying", async () => {
    const user = userEvent.setup();
    let resolveChallenge: (value: string) => void = () => {};
    challengeMfaFactor.mockReturnValue(
      new Promise<string>((resolve) => {
        resolveChallenge = resolve;
      }),
    );

    render(
      <MfaVerifyStep factorId="factor-verify" onComplete={vi.fn()} onSignOut={vi.fn()} />,
    );

    await user.type(screen.getByLabelText("Authenticator code"), "222222");
    await user.click(screen.getByRole("button", { name: "Verify and continue" }));

    expect(screen.getByRole("button", { name: "Verifying…" })).toBeDisabled();

    resolveChallenge("challenge-verify");
    await waitFor(() => {
      expect(verifyMfaChallenge).toHaveBeenCalled();
    });
  });
});
