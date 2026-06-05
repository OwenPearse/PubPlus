import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenueBasicsPage } from "@/owner/pages/OwnerVenueBasicsPage";

const ownerVenueDetail = vi.fn();
const ownerPatchOperationalProfile = vi.fn();
const ownerPatchHours = vi.fn();
const ownerRestrictedChangeRequest = vi.fn();
const referenceLocalities = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerVenueDetail: (id: string) => ownerVenueDetail(id),
  ownerPatchOperationalProfile: (id: string, body: unknown) =>
    ownerPatchOperationalProfile(id, body),
  ownerPatchHours: (id: string, body: unknown) => ownerPatchHours(id, body),
  ownerRestrictedChangeRequest: (id: string, body: unknown) =>
    ownerRestrictedChangeRequest(id, body),
  referenceLocalities: () => referenceLocalities(),
  formatApiError: (err: unknown) =>
    err && typeof err === "object" && "message" in err
      ? String((err as { message: string }).message)
      : String(err),
  isApiRequestError: (err: unknown) =>
    Boolean(err && typeof err === "object" && "code" in err),
  parseApiValidationDetails: (err: unknown) => {
    if (!err || typeof err !== "object" || !("details" in err)) return {};
    const data = (err as { details?: { error?: { details?: Record<string, string[]> } } })
      .details;
    return data?.error?.details ?? {};
  },
}));

function baseDetail(overrides: Record<string, unknown> = {}) {
  return {
    venue_id: "v-1",
    display_name: "Harbour Hotel",
    listing: { discovery_eligibility_status: "eligible", operational_status: "open" },
    relationship: {
      lifecycle: "approved",
      business_id: "b-1",
      capabilities: [],
    },
    published: {
      profile: { display_name: "Harbour Hotel", slug: "harbour", operational_status: "open" },
      location: {
        locality_id: "loc-1",
        locality_name: "Docklands",
        state_code: "VIC",
        address_line_1: "1 Pier St",
        address_line_2: null,
        postal_code: "3008",
        country_code: "AU",
        latitude: null,
        longitude: null,
      },
      descriptions: { short_description: "Waterfront.", long_description: null },
      hours: {
        uncertainty_level: "resolved_confident",
        regular: [
          {
            day_of_week: 5,
            opens_at: "12:00",
            closes_at: "23:00",
            crosses_midnight: false,
          },
        ],
        exceptions: [],
      },
      contact: { supported: false, phone: null, email: null, website: null },
    },
    draft: {
      proposal_id: null,
      lifecycle_status: null,
      last_saved_at: null,
      payload_preview: { display_name: null, address_line_1: null, locality_id: null },
      core_details_payload: null,
    },
    pending_review: {
      proposal_id: null,
      lifecycle_status: null,
      submitted_at: null,
      reviewed_at: null,
      review_outcome: null,
    },
    completeness: {
      percent: 40,
      required_basics_complete: false,
      sections: [],
    },
    sections_available: {
      core_details: true,
      events: false,
      meal_specials: false,
      tap_list: false,
      features: false,
      photos: false,
    },
    ...overrides,
  };
}

function renderBasics(path = "/owner/venues/v-1/basics") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/owner/venues/:venueId/basics" element={<OwnerVenueBasicsPage />} />
        <Route path="/owner/venues/:venueId" element={<div data-testid="venue-hub" />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("OwnerVenueBasicsPage", () => {
  beforeEach(() => {
    ownerVenueDetail.mockReset();
    ownerPatchOperationalProfile.mockReset();
    ownerPatchHours.mockReset();
    ownerRestrictedChangeRequest.mockReset();
    referenceLocalities.mockReset();
    referenceLocalities.mockResolvedValue({
      data: {
        localities: [
          {
            id: "loc-1",
            name: "Docklands",
            state: "VIC",
            geographic_region_id: "gr-1",
            geographic_region_name: "Victoria",
          },
        ],
      },
    });
  });

  it("renders operational and restricted sections", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    renderBasics();
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Listing details you can update now" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: "Details that require approval" }),
      ).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Request change" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Submit for review" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save progress" })).not.toBeInTheDocument();
  });

  it("hydrates operational fields from published values", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Waterfront.")).toBeInTheDocument();
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
      expect(screen.getByDisplayValue("1 Pier St")).toBeInTheDocument();
    });
  });

  it("does not show contact fields or google place id", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    const { container } = renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
    });
    expect(screen.queryByLabelText(/phone/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/website/i)).not.toBeInTheDocument();
    expect(container.textContent).not.toMatch(/google_place_id/i);
  });

  it("save changes calls operational PATCH helpers", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    ownerPatchOperationalProfile.mockResolvedValue({
      data: {
        venue_id: "v-1",
        updated: { short_description: "Updated copy.", long_description: null },
        message: "Changes saved.",
      },
    });
    ownerVenueDetail.mockResolvedValueOnce({ data: baseDetail() });
    ownerVenueDetail.mockResolvedValueOnce({
      data: baseDetail({
        published: {
          ...baseDetail().published,
          descriptions: { short_description: "Updated copy.", long_description: null },
        },
      }),
    });

    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Waterfront.")).toBeInTheDocument();
    });

    await user.clear(screen.getByLabelText(/Short description/i));
    await user.type(screen.getByLabelText(/Short description/i), "Updated copy.");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(ownerPatchOperationalProfile).toHaveBeenCalledWith("v-1", {
        short_description: "Updated copy.",
      });
    });
    expect(
      screen.getByText("Saved. These updates are now reflected on your listing."),
    ).toBeInTheDocument();
  });

  it("save changes calls hours PATCH when hours change", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    ownerPatchHours.mockResolvedValue({
      data: {
        venue_id: "v-1",
        hours: {
          uncertainty_level: "resolved_confident",
          regular: [],
          exceptions: [],
          notes: null,
        },
        message: "Opening hours saved.",
      },
    });
    ownerVenueDetail.mockResolvedValueOnce({ data: baseDetail() });
    ownerVenueDetail.mockResolvedValueOnce({ data: baseDetail() });

    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByText("Monday")).toBeInTheDocument();
    });

    const mondayRow = screen.getByText("Monday").closest("div")!;
    const closedCheckbox = mondayRow.querySelector('input[type="checkbox"]') as HTMLInputElement;
    await user.click(closedCheckbox);
    const opensInput = mondayRow.querySelectorAll("input[type='text']")[0];
    await user.clear(opensInput);
    await user.type(opensInput, "10:00");
    const closesInput = mondayRow.querySelectorAll("input[type='text']")[1];
    await user.clear(closesInput);
    await user.type(closesInput, "22:00");

    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(ownerPatchHours).toHaveBeenCalled();
      const body = ownerPatchHours.mock.calls[0]?.[1] as {
        regular_hours_json: Array<{ day_of_week: number; opens_at: string; closes_at: string }>;
      };
      expect(body.regular_hours_json).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            day_of_week: 1,
            opens_at: "10:00",
            closes_at: "22:00",
          }),
        ]),
      );
    });
  });

  it("request change calls restricted helper and shows review copy", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    ownerRestrictedChangeRequest.mockResolvedValue({
      data: {
        proposal_id: "prop-r",
        venue_id: "v-1",
        section: "identity_location",
        lifecycle_status: "in_review",
        submitted_at: "2026-06-01T00:00:00Z",
        message: "Change request submitted.",
      },
    });
    ownerVenueDetail.mockResolvedValueOnce({ data: baseDetail() });
    ownerVenueDetail.mockResolvedValueOnce({
      data: baseDetail({
        pending_review: {
          proposal_id: "prop-r",
          lifecycle_status: "in_review",
          submitted_at: "2026-06-01T00:00:00Z",
          reviewed_at: null,
          review_outcome: null,
        },
      }),
    });

    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
    });

    await user.clear(screen.getByLabelText(/Display name/i));
    await user.type(screen.getByLabelText(/Display name/i), "New Harbour Name");
    await user.click(screen.getByRole("button", { name: "Request change" }));

    await waitFor(() => {
      expect(ownerRestrictedChangeRequest).toHaveBeenCalledWith(
        "v-1",
        expect.objectContaining({
          section: "identity_location",
          payload: expect.objectContaining({ display_name: "New Harbour Name" }),
        }),
      );
    });
    expect(
      screen.getByText(
        "Change request submitted. We'll review it before updating your listing.",
      ),
    ).toBeInTheDocument();
  });

  it("shows pending review banner and disables restricted section", async () => {
    ownerVenueDetail.mockResolvedValue({
      data: baseDetail({
        pending_review: {
          proposal_id: "p-1",
          lifecycle_status: "in_review",
          submitted_at: "2026-01-02T00:00:00Z",
          reviewed_at: null,
          review_outcome: null,
        },
      }),
    });
    renderBasics();
    await waitFor(() => {
      expect(screen.getByText("Name/address change pending review.")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: "Request change" })).toBeDisabled();
  });

  it("shows already waiting copy when restricted duplicate returns 200", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    ownerRestrictedChangeRequest.mockResolvedValue({
      data: {
        proposal_id: "prop-dup",
        venue_id: "v-1",
        section: "identity_location",
        lifecycle_status: "in_review",
        submitted_at: "2026-06-01T00:00:00Z",
        message: "Your change request is already waiting for review.",
      },
    });

    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
    });

    await user.clear(screen.getByLabelText(/Display name/i));
    await user.type(screen.getByLabelText(/Display name/i), "Another Name");
    await user.click(screen.getByRole("button", { name: "Request change" }));

    await waitFor(() => {
      expect(
        screen.getByText("Your change request is already waiting for review."),
      ).toBeInTheDocument();
    });
  });

  it("shows friendly error on 403/404", async () => {
    ownerVenueDetail.mockRejectedValue({ code: "forbidden", message: "denied", status: 403 });
    renderBasics();
    await waitFor(() => {
      expect(
        screen.getByText("We could not open this venue for your account."),
      ).toBeInTheDocument();
    });
  });
});
