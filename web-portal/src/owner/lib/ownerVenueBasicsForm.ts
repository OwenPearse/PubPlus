import type {
  OwnerCoreDetailsPayload,
  OwnerOpeningHoursPayload,
  OwnerVenueDetail,
  OwnerVenueHoursRegular,
} from "@/shared/lib/api";

export const WEEKDAY_LABELS = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
] as const;

export type DayHoursState = {
  dayOfWeek: number;
  label: string;
  closed: boolean;
  opensAt: string;
  closesAt: string;
  crossesMidnight: boolean;
};

export type BasicsFormValues = {
  displayName: string;
  addressLine1: string;
  addressLine2: string;
  postalCode: string;
  localityId: string;
  countryCode: string;
  shortDescription: string;
  longDescription: string;
  hoursNotes: string;
  weeklyHours: DayHoursState[];
  ownerConfirmsManagement: boolean;
};

export function createDefaultWeeklyHours(): DayHoursState[] {
  return WEEKDAY_LABELS.map((label, dayOfWeek) => ({
    dayOfWeek,
    label,
    closed: true,
    opensAt: "12:00",
    closesAt: "23:00",
    crossesMidnight: false,
  }));
}

export function weeklyHoursFromRegular(regular: OwnerVenueHoursRegular[]): DayHoursState[] {
  const byDay = new Map(regular.map((row) => [row.day_of_week, row]));
  return WEEKDAY_LABELS.map((label, dayOfWeek) => {
    const row = byDay.get(dayOfWeek);
    if (!row) {
      return {
        dayOfWeek,
        label,
        closed: true,
        opensAt: "12:00",
        closesAt: "23:00",
        crossesMidnight: false,
      };
    }
    return {
      dayOfWeek,
      label,
      closed: false,
      opensAt: row.opens_at,
      closesAt: row.closes_at,
      crossesMidnight: row.crosses_midnight,
    };
  });
}

/**
 * Hydrates form state from venue detail. Draft `payload_preview` only includes
 * display_name, address_line_1, and locality_id — other fields use published values.
 */
export function hydrateBasicsFormFromDetail(detail: OwnerVenueDetail): BasicsFormValues {
  const preview = detail.draft.payload_preview;
  const published = detail.published;

  return {
    displayName: preview.display_name ?? published.profile.display_name ?? "",
    addressLine1: preview.address_line_1 ?? published.location.address_line_1 ?? "",
    addressLine2: published.location.address_line_2 ?? "",
    postalCode: published.location.postal_code ?? "",
    localityId: preview.locality_id ?? published.location.locality_id ?? "",
    countryCode: published.location.country_code ?? "AU",
    shortDescription: published.descriptions.short_description ?? "",
    longDescription: published.descriptions.long_description ?? "",
    hoursNotes: "",
    weeklyHours: weeklyHoursFromRegular(published.hours.regular),
    ownerConfirmsManagement: false,
  };
}

export function buildOpeningHoursPayload(
  weeklyHours: DayHoursState[],
  hoursNotes: string,
): OwnerOpeningHoursPayload | undefined {
  const regularHours = weeklyHours
    .filter((day) => !day.closed)
    .map((day, index) => ({
      day_of_week: day.dayOfWeek,
      opens_at: day.opensAt,
      closes_at: day.closesAt,
      crosses_midnight: day.crossesMidnight,
      sort_order: index,
    }));

  const trimmedNotes = hoursNotes.trim();
  const hasHoursInput = regularHours.length > 0 || trimmedNotes.length > 0;

  if (!hasHoursInput) {
    return undefined;
  }

  return {
    uncertainty_level: regularHours.length > 0 ? "resolved_confident" : undefined,
    regular_hours_json: regularHours,
    exceptions_json: [],
    notes: trimmedNotes || null,
  };
}

export function buildCoreDetailsPayload(values: BasicsFormValues): OwnerCoreDetailsPayload {
  const openingHours = buildOpeningHoursPayload(values.weeklyHours, values.hoursNotes);
  const payload: OwnerCoreDetailsPayload = {
    display_name: values.displayName.trim() || undefined,
    address_line_1: values.addressLine1.trim() || undefined,
    address_line_2: values.addressLine2.trim() ? values.addressLine2.trim() : null,
    postal_code: values.postalCode.trim() || undefined,
    locality_id: values.localityId || undefined,
    country_code: values.countryCode.trim() || "AU",
    short_description: values.shortDescription.trim() || undefined,
    long_description: values.longDescription.trim() ? values.longDescription.trim() : null,
    owner_confirms_management: values.ownerConfirmsManagement || undefined,
  };

  if (openingHours) {
    payload.opening_hours = openingHours;
  }

  return payload;
}

export function hasPendingReview(detail: OwnerVenueDetail): boolean {
  const { pending_review: pending } = detail;
  return Boolean(
    pending.proposal_id &&
      (pending.lifecycle_status === "in_review" || pending.submitted_at),
  );
}

export function hasSavedDraft(detail: OwnerVenueDetail): boolean {
  return Boolean(detail.draft.proposal_id && detail.draft.lifecycle_status === "staged");
}
