import { beforeEach, describe, expect, it, vi } from "vitest";

const waitForAccessToken = vi.fn();

vi.mock("@/shared/lib/supabase", () => ({
  waitForAccessToken: () => waitForAccessToken(),
}));

vi.mock("@/shared/lib/env", () => ({
  getApiBaseUrl: () => "http://api.test",
}));

import {
  ownerVenueDetail,
  ownerVenueList,
  ownerVenueProposal,
  parseApiValidationDetails,
  referenceLocalities,
} from "@/shared/lib/api";

const listEnvelope = {
  data: {
    venues: [
      {
        venue_id: "v-1",
        display_name: "Test Pub",
        locality_name: "Fitzroy",
        state_code: "VIC",
        relationship_lifecycle: "approved",
        onboarding_status: "in_progress",
        pending_proposal_count: 0,
        completeness_percent: 50,
        required_basics_complete: false,
      },
    ],
    meta: { total: 1, default_venue_id: "v-1" },
  },
};

const detailEnvelope = {
  data: {
    venue_id: "v-1",
    display_name: "Test Pub",
    listing: { discovery_eligibility_status: "eligible", operational_status: "open" },
    relationship: {
      lifecycle: "approved",
      business_id: "b-1",
      capabilities: ["submit_restricted_changes_for_review"],
    },
    published: {
      profile: { display_name: "Test Pub", slug: "test-pub", operational_status: "open" },
      location: {
        locality_id: "loc-1",
        locality_name: "Fitzroy",
        state_code: "VIC",
        address_line_1: "1 St",
        address_line_2: null,
        postal_code: "3065",
        country_code: "AU",
        latitude: null,
        longitude: null,
      },
      descriptions: { short_description: "Hi", long_description: null },
      hours: { uncertainty_level: "resolved_confident", regular: [], exceptions: [] },
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
      percent: 50,
      required_basics_complete: false,
      sections: [
        {
          key: "core_details",
          label: "Pub details",
          status: "partial",
          required: true,
          available: true,
        },
      ],
    },
    sections_available: {
      core_details: true,
      events: false,
      meal_specials: false,
      tap_list: false,
      features: false,
      photos: false,
    },
  },
};

describe("owner venue API wrappers", () => {
  beforeEach(() => {
    waitForAccessToken.mockReset();
    waitForAccessToken.mockResolvedValue("token-abc");
    vi.stubGlobal("fetch", vi.fn());
  });

  it("ownerVenueList parses data envelope", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(listEnvelope), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const result = await ownerVenueList();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/owner/venues",
      expect.any(Object),
    );
    expect(result.data.venues).toHaveLength(1);
    expect(result.data.meta.default_venue_id).toBe("v-1");
    expect(result.data.venues[0].display_name).toBe("Test Pub");
  });

  it("ownerVenueDetail parses data envelope", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(detailEnvelope), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    const result = await ownerVenueDetail("v-1");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/owner/venues/v-1",
      expect.any(Object),
    );
    expect(result.data.published.contact.supported).toBe(false);
    expect(result.data.published.contact.phone).toBeNull();
  });

  it("ownerVenueList throws on error envelope", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ error: { code: "forbidden", message: "Denied." } }),
        { status: 403, headers: { "content-type": "application/json" } },
      ),
    );

    await expect(ownerVenueList()).rejects.toMatchObject({
      code: "forbidden",
      message: "Denied.",
    });
  });

  it("ownerVenueProposal sends correct path and body", async () => {
    const fetchMock = vi.mocked(fetch);
    const proposalResponse = {
      data: {
        proposal_id: "prop-1",
        venue_id: "v-1",
        section: "core_details",
        intent: "draft",
        lifecycle_status: "staged",
        submitted_at: null,
        message: "Draft saved.",
      },
    };
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(proposalResponse), {
        status: 201,
        headers: { "content-type": "application/json" },
      }),
    );

    const body = {
      section: "core_details" as const,
      intent: "draft" as const,
      payload: { display_name: "Test Pub" },
    };
    const result = await ownerVenueProposal("v-1", body);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/owner/venues/v-1/proposals",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(body),
      }),
    );
    expect(result.data.proposal_id).toBe("prop-1");
    expect(result.data.lifecycle_status).toBe("staged");
  });

  it("ownerVenueProposal parses submit response", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          data: {
            proposal_id: "prop-2",
            venue_id: "v-1",
            section: "core_details",
            intent: "submit",
            lifecycle_status: "in_review",
            submitted_at: "2026-06-01T00:00:00Z",
            message: "Submitted for review.",
          },
        }),
        { status: 201, headers: { "content-type": "application/json" } },
      ),
    );

    const result = await ownerVenueProposal("v-1", {
      section: "core_details",
      intent: "submit",
      payload: { display_name: "Done Pub", owner_confirms_management: true },
    });
    expect(result.data.intent).toBe("submit");
    expect(result.data.lifecycle_status).toBe("in_review");
    expect(result.data.submitted_at).toBe("2026-06-01T00:00:00Z");
  });

  it("ownerVenueProposal surfaces validation error envelope", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          error: {
            code: "validation_error",
            message: "Please check the highlighted fields.",
            details: { display_name: ["This field is required."] },
          },
        }),
        { status: 400, headers: { "content-type": "application/json" } },
      ),
    );

    let caught: unknown;
    try {
      await ownerVenueProposal("v-1", {
        section: "core_details",
        intent: "submit",
        payload: {},
      });
    } catch (err) {
      caught = err;
    }
    expect(caught).toMatchObject({
      code: "validation_error",
      message: "Please check the highlighted fields.",
    });
    expect(parseApiValidationDetails(caught)).toEqual({
      display_name: ["This field is required."],
    });
  });

  it("referenceLocalities parses data envelope", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          data: {
            localities: [
              {
                id: "loc-1",
                name: "Fitzroy",
                state: "VIC",
                geographic_region_id: "gr-1",
                geographic_region_name: "Victoria",
              },
            ],
          },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const result = await referenceLocalities();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/reference/localities",
      expect.any(Object),
    );
    expect(result.data.localities[0].name).toBe("Fitzroy");
  });
});
