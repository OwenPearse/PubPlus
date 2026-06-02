import { beforeEach, describe, expect, it, vi } from "vitest";

import { downloadExportCsv } from "@/lib/filters";
import { DEFAULT_LIST_FILTERS } from "@/lib/types";

describe("downloadExportCsv", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(new Blob(["id,name"])),
        headers: { get: () => 'attachment; filename="test.csv"' },
      }),
    );
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:mock"),
      revokeObjectURL: vi.fn(),
    });
    const anchor = { click: vi.fn() } as unknown as HTMLAnchorElement;
    vi.spyOn(document, "createElement").mockReturnValue(anchor);
  });

  it("requests export.csv with filter query params", async () => {
    await downloadExportCsv("http://localhost:8000", DEFAULT_LIST_FILTERS, "token");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/internal/founder-venues/export.csv?"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer token",
        }),
      }),
    );
    const url = String((fetch as ReturnType<typeof vi.fn>).mock.calls[0][0]);
    expect(url).toContain("state=VIC");
    expect(url).toContain("sort=founder_fit_score_desc");
  });
});
