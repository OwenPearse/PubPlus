export const TAP_LIST_PAGE_TITLE = "Tap list & drinks";
export const TAP_LIST_PAGE_HELPER =
  "Add the key beers, wines, cocktails and non-alcoholic options customers can expect. This is for your public listing, not stock management.";
export const TAP_LIST_HUB_DESCRIPTION =
  "Add beers, wines, cocktails and non-alcoholic options customers can expect.";
export const TAP_LIST_ADD_LABEL = "Add drink";
export const TAP_LIST_SAVE_LABEL = "Save drink";
export const TAP_LIST_SUCCESS_MESSAGE =
  "Drink list saved. These updates are now reflected on your listing.";
export const TAP_LIST_MISSING_CAPABILITY_MESSAGE =
  "Direct listing edits are not enabled for your account. Contact support if you manage this venue.";

export const TAP_AVAILABILITY_OPTIONS = [
  { value: "permanent", label: "Permanent" },
  { value: "rotating", label: "Rotating" },
  { value: "seasonal", label: "Seasonal" },
  { value: "limited", label: "Limited" },
] as const;

export function formatTapAvailability(
  availability: string | null | undefined,
): string {
  const match = TAP_AVAILABILITY_OPTIONS.find((opt) => opt.value === availability);
  return match?.label ?? "Permanent";
}
