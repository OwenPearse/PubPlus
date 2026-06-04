export const portalBrand = {
  productName: import.meta.env.VITE_PORTAL_PRODUCT_NAME?.trim() || "Venue Portal",
  tagline: import.meta.env.VITE_PORTAL_PRODUCT_TAGLINE?.trim() || "",
  logoSrc: "/brand/placeholder-mark.svg",
  logoAlt: "Portal",
} as const;
