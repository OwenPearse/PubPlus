import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { OwnerClaimStatusState } from "@/owner/pages/OwnerClaimStatusState";
import type { OwnerClaimStatus } from "@/shared/lib/api";

const baseClaim: OwnerClaimStatus = {
  claim_request_id: "claim-1",
  claim_lifecycle_status: "submitted",
  submitted_venue_name: "Royal Hotel",
  submitted_address_line_1: "1 Main St",
  locality_name: "Fitzroy",
  submitted_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

describe("OwnerClaimStatusState", () => {
  it("shows pending review copy for submitted claims", () => {
    render(<OwnerClaimStatusState claim={baseClaim} />);
    expect(
      screen.getByRole("heading", { name: "Your venue request is under review" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Royal Hotel/i)).toBeInTheDocument();
    expect(screen.queryByText(/duplicate/i)).not.toBeInTheDocument();
  });

  it("shows needs-more-info copy and admin message", () => {
    render(
      <OwnerClaimStatusState
        claim={{
          ...baseClaim,
          claim_lifecycle_status: "needs_more_info",
          admin_message: "Please send your ABN.",
        }}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "We need a bit more information" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Please send your ABN.")).toBeInTheDocument();
  });

  it("shows denied copy and submit-new action", () => {
    const onSubmitNew = vi.fn();
    render(
      <OwnerClaimStatusState
        claim={{ ...baseClaim, claim_lifecycle_status: "denied" }}
        onSubmitNew={onSubmitNew}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Your venue request wasn't approved" }),
    ).toBeInTheDocument();
    screen.getByRole("button", { name: "Submit a new request" }).click();
    expect(onSubmitNew).toHaveBeenCalledTimes(1);
  });
});
