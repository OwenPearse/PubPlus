import { describe, expect, it, vi, beforeEach } from "vitest";

import {
  markFounderVenueCalled,
  markFounderVenueDoNotContact,
  markFounderVenueEmailed,
} from "@/lib/outreach";

const patchFounderVenueLead = vi.fn();
const markLeadDoNotContact = vi.fn();

vi.mock("@/lib/api", () => ({
  patchFounderVenueLead: (...args: unknown[]) => patchFounderVenueLead(...args),
  markLeadDoNotContact: (...args: unknown[]) => markLeadDoNotContact(...args),
}));

describe("outreach helpers", () => {
  beforeEach(() => {
    patchFounderVenueLead.mockReset();
    markLeadDoNotContact.mockReset();
    patchFounderVenueLead.mockResolvedValue({ lead: {} });
    markLeadDoNotContact.mockResolvedValue({ lead: {} });
  });

  it("mark called PATCHes outreach fields", async () => {
    await markFounderVenueCalled("lead-1");
    expect(patchFounderVenueLead).toHaveBeenCalledWith(
      "lead-1",
      expect.objectContaining({
        outreach_status: "called",
        last_contact_channel: "phone",
        last_contacted_at: expect.any(String),
      }),
    );
  });

  it("mark emailed PATCHes email channel", async () => {
    await markFounderVenueEmailed("lead-1");
    expect(patchFounderVenueLead).toHaveBeenCalledWith(
      "lead-1",
      expect.objectContaining({
        outreach_status: "emailed",
        last_contact_channel: "email",
      }),
    );
  });

  it("DNC uses DNC endpoint", async () => {
    await markFounderVenueDoNotContact("lead-1", "test");
    expect(markLeadDoNotContact).toHaveBeenCalledWith("lead-1", "test");
    expect(patchFounderVenueLead).not.toHaveBeenCalled();
  });
});
