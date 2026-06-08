export const MEAL_SPECIALS_PAGE_TITLE = "Meal specials";
export const MEAL_SPECIALS_PAGE_HELPER =
  "Add the regular food specials your pub offers, like parma nights, steak nights or Sunday roasts.";
export const MEAL_SPECIALS_HUB_DESCRIPTION =
  "Add food specials like parma nights, steak nights and Sunday roasts.";
export const MEAL_SPECIALS_ADD_LABEL = "Add special";
export const MEAL_SPECIALS_SAVE_LABEL = "Save special";
export const MEAL_SPECIALS_SUCCESS_MESSAGE =
  "Special saved. These updates are now reflected on your listing.";
export const MEAL_SPECIALS_MISSING_CAPABILITY_MESSAGE =
  "Direct listing edits are not enabled for your account. Contact support if you manage this venue.";

export const DAY_LABELS = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
] as const;

export function formatDaysAvailable(days: number[]): string {
  if (days.length === 0) return "Every day";
  if (days.length === 7) return "Every day";
  return days.map((day) => DAY_LABELS[day] ?? `Day ${day}`).join(", ");
}

export function formatTimeWindow(
  startTime: string | null | undefined,
  endTime: string | null | undefined,
): string {
  if (!startTime && !endTime) return "All day";
  if (startTime && endTime) return `${startTime} – ${endTime}`;
  return startTime ?? endTime ?? "All day";
}
