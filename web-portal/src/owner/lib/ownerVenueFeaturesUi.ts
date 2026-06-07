import type { OwnerVenueFeatureItem } from "@/shared/lib/api";

export const FEATURES_PAGE_TITLE = "Venue features";
export const FEATURES_PAGE_HELPER =
  "Choose the features that apply to your pub. These help customers find venues that match what they're looking for.";
export const FEATURES_SAVE_LABEL = "Save features";
export const FEATURES_SUCCESS_MESSAGE =
  "Features saved. These updates are now reflected on your listing.";
export const FEATURES_MISSING_CAPABILITY_MESSAGE =
  "Your account is not set up to edit this listing yet.";
export const FEATURES_HUB_DESCRIPTION =
  "Add features like beer garden, dog friendly, live music and sports screens.";

const GROUP_LABELS: Record<string, string> = {
  food: "Food & family",
  spaces: "Venue spaces",
  entertainment: "Entertainment",
  pets: "Pets",
};

const GROUP_ORDER = ["food", "spaces", "entertainment", "pets", "other"];

export function groupOwnerVenueFeatures(
  features: OwnerVenueFeatureItem[],
): Array<{ key: string; label: string; items: OwnerVenueFeatureItem[] }> {
  const buckets = new Map<string, OwnerVenueFeatureItem[]>();
  for (const feature of features) {
    const groupKey = feature.group?.trim() || "other";
    const list = buckets.get(groupKey) ?? [];
    list.push(feature);
    buckets.set(groupKey, list);
  }

  return GROUP_ORDER.filter((key) => buckets.has(key)).map((key) => ({
    key,
    label: GROUP_LABELS[key] ?? "Other",
    items: buckets.get(key) ?? [],
  }));
}
