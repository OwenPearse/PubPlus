export const PHOTOS_PAGE_TITLE = "Photos";
export const PHOTOS_PAGE_HELPER =
  "Add photos that show customers what your pub looks like. Start with a profile photo, then add a few gallery photos.";
export const PHOTOS_UPLOAD_LABEL = "Upload photo";
export const PHOTOS_SUCCESS_MESSAGE =
  "Photo saved. These updates are now reflected on your listing.";
export const PHOTOS_MISSING_CAPABILITY_MESSAGE =
  "Direct listing edits are not enabled for your account. Contact support if you manage this venue.";
export const PHOTOS_HUB_DESCRIPTION =
  "Add photos that show customers what your venue looks like.";

export const PHOTOS_ALLOWED_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
] as const;

export const PHOTOS_MAX_BYTES = 5 * 1024 * 1024;

export function formatPhotoPurpose(purpose: "profile" | "gallery"): string {
  return purpose === "profile" ? "Profile photo" : "Gallery photo";
}
