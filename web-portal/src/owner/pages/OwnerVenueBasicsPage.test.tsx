import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OwnerVenueBasicsPage } from "@/owner/pages/OwnerVenueBasicsPage";

const ownerVenueDetail = vi.fn();
const ownerVenueProposal = vi.fn();
const referenceLocalities = vi.fn();

vi.mock("@/shared/lib/api", () => ({
  ownerVenueDetail: (id: string) => ownerVenueDetail(id),
  ownerVenueProposal: (id: string, body: unknown) => ownerVenueProposal(id, body),
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
    sections_available: { core_details: true, events: false, meal_specials: false, tap_list: false, features: false, photos: false },
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
    ownerVenueProposal.mockReset();
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

  it("loads venue detail and locality options and hydrates published values", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("1 Pier St")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Waterfront.")).toBeInTheDocument();
    expect(ownerVenueDetail).toHaveBeenCalledWith("v-1");
    expect(referenceLocalities).toHaveBeenCalled();
    expect(screen.getByRole("link", { name: /Back to checklist/i })).toHaveAttribute(
      "href",
      "/owner/venues/v-1",
    );
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

  it("shows pending review and draft banners", async () => {
    ownerVenueDetail.mockResolvedValue({
      data: baseDetail({
        draft: {
          proposal_id: "d-1",
          lifecycle_status: "staged",
          last_saved_at: "2026-01-01T00:00:00Z",
          payload_preview: { display_name: null, address_line_1: null, locality_id: null },
        },
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
      expect(
        screen.getByText("Your latest changes are waiting for review."),
      ).toBeInTheDocument();
      expect(screen.getByText("You have a saved draft.")).toBeInTheDocument();
    });
  });

  it("saves partial draft with intent draft", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    ownerVenueProposal.mockResolvedValue({
      data: {
        proposal_id: "prop-1",
        venue_id: "v-1",
        section: "core_details",
        intent: "draft",
        lifecycle_status: "staged",
        submitted_at: null,
        message: "Draft saved.",
      },
    });
    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
    });

    await user.clear(screen.getByLabelText(/Display name/i));
    await user.type(screen.getByLabelText(/Display name/i), "Draft Name");
    await user.click(screen.getByRole("button", { name: "Save progress" }));

    await waitFor(() => {
      expect(ownerVenueProposal).toHaveBeenCalledWith(
        "v-1",
        expect.objectContaining({ intent: "draft", section: "core_details" }),
      );
    });
    expect(
      screen.getByText("Saved. You can come back anytime to finish or submit."),
    ).toBeInTheDocument();
  });

  it("shows client validation errors on submit when required fields missing", async () => {
    ownerVenueDetail.mockResolvedValue({
      data: baseDetail({
        published: {
          ...baseDetail().published,
          profile: { display_name: "", slug: null, operational_status: "open" },
          location: {
            locality_id: null,
            locality_name: null,
            state_code: null,
            address_line_1: "",
            address_line_2: null,
            postal_code: null,
            country_code: "AU",
            latitude: null,
            longitude: null,
          },
          descriptions: { short_description: "", long_description: null },
          hours: { uncertainty_level: "resolved_confident", regular: [], exceptions: [] },
        },
      }),
    });
    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Submit for review" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Submit for review" }));
    await waitFor(() => {
      expect(screen.getByText("Please check the highlighted fields.")).toBeInTheDocument();
    });
    expect(ownerVenueProposal).not.toHaveBeenCalled();
    expect(screen.getAllByText("This field is required.").length).toBeGreaterThan(0);
  });

  it("requires management confirmation on submit", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Submit for review" }));
    await waitFor(() => {
      expect(
        screen.getByText("You must confirm you manage this venue."),
      ).toBeInTheDocument();
    });
    expect(ownerVenueProposal).not.toHaveBeenCalled();
  });

  it("submits for review with core_details payload", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    ownerVenueProposal.mockResolvedValue({
      data: {
        proposal_id: "prop-2",
        venue_id: "v-1",
        section: "core_details",
        intent: "submit",
        lifecycle_status: "in_review",
        submitted_at: "2026-06-01T00:00:00Z",
        message: "Submitted.",
      },
    });
    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
    });

    await user.click(
      screen.getByRole("checkbox", {
        name: /I confirm I manage this venue/i,
      }),
    );
    await user.click(screen.getByRole("button", { name: "Submit for review" }));

    await waitFor(() => {
      expect(ownerVenueProposal).toHaveBeenCalledWith(
        "v-1",
        expect.objectContaining({
          intent: "submit",
          section: "core_details",
          payload: expect.objectContaining({
            display_name: "Harbour Hotel",
            owner_confirms_management: true,
            opening_hours: expect.objectContaining({
              regular_hours_json: expect.arrayContaining([
                expect.objectContaining({
                  day_of_week: 5,
                  opens_at: "12:00",
                  closes_at: "23:00",
                  crosses_midnight: false,
                }),
              ]),
              exceptions_json: [],
            }),
          }),
        }),
      );
    });
    expect(
      screen.getByText(
        "Submitted for review. Your changes will be reviewed before they appear publicly.",
      ),
    ).toBeInTheDocument();
  });

  it("maps opening hours: closed days omitted, crosses midnight included", async () => {
    ownerVenueDetail.mockResolvedValue({
      data: baseDetail({
        published: {
          ...baseDetail().published,
          hours: { uncertainty_level: "resolved_confident", regular: [], exceptions: [] },
        },
      }),
    });
    ownerVenueProposal.mockResolvedValue({
      data: {
        proposal_id: "prop-3",
        venue_id: "v-1",
        section: "core_details",
        intent: "draft",
        lifecycle_status: "staged",
        submitted_at: null,
        message: "Draft saved.",
      },
    });
    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByText("Monday")).toBeInTheDocument();
    });

    const mondayRow = screen.getByText("Monday").closest("div")!;
    const closedCheckbox = mondayRow.querySelector('input[type="checkbox"]') as HTMLInputElement;
    await user.click(closedCheckbox);

    const opensInput = mondayRow.querySelectorAll("input[type='text']")[0];
    const closesInput = mondayRow.querySelectorAll("input[type='text']")[1];
    await user.clear(opensInput);
    await user.type(opensInput, "10:00");
    await user.clear(closesInput);
    await user.type(closesInput, "02:00");

    const midnightCheckbox = mondayRow.querySelectorAll("input[type='checkbox']")[1];
    await user.click(midnightCheckbox);

    await user.click(screen.getByRole("button", { name: "Save progress" }));

    await waitFor(() => {
      const call = ownerVenueProposal.mock.calls[0]?.[1] as {
        payload: { opening_hours: { regular_hours_json: unknown[] } };
      };
      expect(call.payload.opening_hours.regular_hours_json).toEqual([
        expect.objectContaining({
          day_of_week: 1,
          opens_at: "10:00",
          closes_at: "02:00",
          crosses_midnight: true,
        }),
      ]);
      expect(call.payload.opening_hours.regular_hours_json).toHaveLength(1);
    });
  });

  it("shows invalid time validation", async () => {
    ownerVenueDetail.mockResolvedValue({
      data: baseDetail({
        published: {
          ...baseDetail().published,
          hours: { uncertainty_level: "resolved_confident", regular: [], exceptions: [] },
        },
      }),
    });
    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByText("Tuesday")).toBeInTheDocument();
    });

    const tuesdayRow = screen.getByText("Tuesday").closest("div")!;
    const closedCheckbox = tuesdayRow.querySelector('input[type="checkbox"]') as HTMLInputElement;
    await user.click(closedCheckbox);

    const opensInput = tuesdayRow.querySelectorAll("input[type='text']")[0];
    await user.clear(opensInput);
    await user.type(opensInput, "25:99");

    await user.click(screen.getByRole("button", { name: "Submit for review" }));
    await waitFor(() => {
      expect(screen.getByText("Time must be HH:MM (24-hour).")).toBeInTheDocument();
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

  it("handles localities load failure", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    referenceLocalities.mockRejectedValue(new Error("localities failed"));
    renderBasics();
    await waitFor(() => {
      expect(screen.getByText(/Could not load locality options/i)).toBeInTheDocument();
    });
  });

  it("renders server validation errors", async () => {
    ownerVenueDetail.mockResolvedValue({ data: baseDetail() });
    ownerVenueProposal.mockRejectedValue({
      code: "validation_error",
      message: "Please check the highlighted fields.",
      status: 400,
      details: {
        error: {
          code: "validation_error",
          message: "Please check the highlighted fields.",
          details: { display_name: ["Must be between 2 and 120 characters."] },
        },
      },
    });
    const user = userEvent.setup();
    renderBasics();
    await waitFor(() => {
      expect(screen.getByDisplayValue("Harbour Hotel")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Save progress" }));
    await waitFor(() => {
      expect(
        screen.getByText("Must be between 2 and 120 characters."),
      ).toBeInTheDocument();
    });
  });
});
