import { describe, expect, it } from "vitest";

import { applyQuickFilter, buildListQueryParams } from "@/lib/filters";
import { DEFAULT_LIST_FILTERS } from "@/lib/types";

describe("buildListQueryParams", () => {
  it("maps default VIC filters to query params", () => {
    const params = buildListQueryParams(DEFAULT_LIST_FILTERS);
    expect(params.state).toBe("VIC");
    expect(params.sort).toBe("founder_fit_score_desc");
    expect(params.limit).toBe("50");
    expect(params.include_do_not_contact).toBeUndefined();
  });

  it("includes boolean filters when enabled", () => {
    const params = buildListQueryParams({
      ...DEFAULT_LIST_FILTERS,
      needs_review: true,
      missing_email: true,
      score_min: "80",
    });
    expect(params.needs_review).toBe("true");
    expect(params.missing_email).toBe("true");
    expect(params.score_min).toBe("80");
  });
});

describe("applyQuickFilter", () => {
  it("sets VIC 80+ preset", () => {
    const next = applyQuickFilter("vic_80_plus", DEFAULT_LIST_FILTERS);
    expect(next.state).toBe("VIC");
    expect(next.score_min).toBe("80");
  });

  it("sets needs review preset", () => {
    const next = applyQuickFilter("vic_needs_review", DEFAULT_LIST_FILTERS);
    expect(next.needs_review).toBe(true);
    expect(next.state).toBe("VIC");
  });

  it("sets no contact channels preset", () => {
    const next = applyQuickFilter("no_contact_channels", DEFAULT_LIST_FILTERS);
    expect(next.missing_email).toBe(true);
    expect(next.missing_website).toBe(true);
    expect(next.missing_phone).toBe(true);
  });

  it("sets VIC 80+ not contacted preset", () => {
    const next = applyQuickFilter("vic_80_not_contacted", DEFAULT_LIST_FILTERS);
    expect(next.score_min).toBe("80");
    expect(next.outreach_status).toBe("not_contacted");
  });
});
