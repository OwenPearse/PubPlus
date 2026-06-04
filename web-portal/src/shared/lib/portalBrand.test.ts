import { afterEach, describe, expect, it, vi } from "vitest";

import { portalBrand as portalBrandLoaded } from "./portalBrand";

describe("portalBrand constants", () => {
  it("exposes fixed logo paths", () => {
    expect(portalBrandLoaded.logoSrc).toBe("/brand/placeholder-mark.svg");
    expect(portalBrandLoaded.logoAlt).toBe("Portal");
  });
});

describe("portalBrand env fallbacks", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("uses defaults when portal env vars are unset or empty", async () => {
    vi.stubEnv("VITE_PORTAL_PRODUCT_NAME", "");
    vi.stubEnv("VITE_PORTAL_PRODUCT_TAGLINE", "");

    const { portalBrand } = await import("./portalBrand");

    expect(portalBrand.productName).toBe("Venue Portal");
    expect(portalBrand.tagline).toBe("");
    expect(portalBrand.logoSrc).toBe("/brand/placeholder-mark.svg");
    expect(portalBrand.logoAlt).toBe("Portal");
  });

  it("reads trimmed values from env when set", async () => {
    vi.stubEnv("VITE_PORTAL_PRODUCT_NAME", "  Custom Portal  ");
    vi.stubEnv("VITE_PORTAL_PRODUCT_TAGLINE", "  Operator access  ");

    const { portalBrand } = await import("./portalBrand");

    expect(portalBrand.productName).toBe("Custom Portal");
    expect(portalBrand.tagline).toBe("Operator access");
  });
});
