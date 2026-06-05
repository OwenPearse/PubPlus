import type {
  OwnerHoursPatchRequest,
  OwnerOpeningHoursPayload,
  OwnerOperationalProfilePatchRequest,
  OwnerRestrictedIdentityPayload,
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
};

export type PublishedBaselines = {
  shortDescription: string;
  longDescription: string;
  weeklyHours: DayHoursState[];
  hoursNotes: string;
  displayName: string;
  addressLine1: string;
  addressLine2: string;
  postalCode: string;
  localityId: string;
  countryCode: string;
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

function restrictedPreviewFromDetail(detail: OwnerVenueDetail) {
  const draftPayload = detail.draft.core_details_payload;
  const preview = detail.draft.payload_preview;
  const published = detail.published;

  return {
    displayName:
      preview.display_name ??
      draftPayload?.display_name ??
      published.profile.display_name ??
      "",
    addressLine1:
      preview.address_line_1 ??
      draftPayload?.address_line_1 ??
      published.location.address_line_1 ??
      "",
    addressLine2: draftPayload?.address_line_2 ?? published.location.address_line_2 ?? "",
    postalCode: draftPayload?.postal_code ?? published.location.postal_code ?? "",
    localityId:
      preview.locality_id ??
      draftPayload?.locality_id ??
      published.location.locality_id ??
      "",
    countryCode: draftPayload?.country_code ?? published.location.country_code ?? "AU",
  };
}

/**
 * Operational fields hydrate from published truth (direct saves update published).
 * Restricted fields hydrate from published, with draft preview when a legacy draft exists.
 */
export function hydrateBasicsFormFromDetail(detail: OwnerVenueDetail): BasicsFormValues {
  const published = detail.published;
  const restricted = restrictedPreviewFromDetail(detail);

  return {
    displayName: restricted.displayName,
    addressLine1: restricted.addressLine1,
    addressLine2: restricted.addressLine2,
    postalCode: restricted.postalCode,
    localityId: restricted.localityId,
    countryCode: restricted.countryCode,
    shortDescription: published.descriptions.short_description ?? "",
    longDescription: published.descriptions.long_description ?? "",
    hoursNotes: "",
    weeklyHours: weeklyHoursFromRegular(published.hours.regular),
  };
}

export function publishedBaselinesFromDetail(detail: OwnerVenueDetail): PublishedBaselines {
  const values = hydrateBasicsFormFromDetail(detail);
  return {
    shortDescription: values.shortDescription,
    longDescription: values.longDescription,
    weeklyHours: values.weeklyHours.map((day) => ({ ...day })),
    hoursNotes: values.hoursNotes,
    displayName: detail.published.profile.display_name ?? "",
    addressLine1: detail.published.location.address_line_1 ?? "",
    addressLine2: detail.published.location.address_line_2 ?? "",
    postalCode: detail.published.location.postal_code ?? "",
    localityId: detail.published.location.locality_id ?? "",
    countryCode: detail.published.location.country_code ?? "AU",
  };
}

export function buildOpeningHoursPayload(
  weeklyHours: DayHoursState[],
  hoursNotes: string,
): OwnerOpeningHoursPayload {
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

  return {
    uncertainty_level: regularHours.length > 0 ? "resolved_confident" : "unknown",
    regular_hours_json: regularHours,
    exceptions_json: [],
    notes: trimmedNotes || null,
  };
}

export function buildOperationalProfilePatch(
  values: BasicsFormValues,
  baseline: PublishedBaselines,
): OwnerOperationalProfilePatchRequest | null {
  const patch: OwnerOperationalProfilePatchRequest = {};
  const short = values.shortDescription.trim();
  const long = values.longDescription.trim();

  if (short !== baseline.shortDescription.trim()) {
    patch.short_description = short || null;
  }
  if (long !== (baseline.longDescription.trim() || "")) {
    patch.long_description = long || null;
  }

  return Object.keys(patch).length > 0 ? patch : null;
}

export function buildHoursPatch(
  values: BasicsFormValues,
  baseline: PublishedBaselines,
): OwnerHoursPatchRequest | null {
  const payload = buildOpeningHoursPayload(values.weeklyHours, values.hoursNotes);
  const baselinePayload = buildOpeningHoursPayload(
    baseline.weeklyHours,
    baseline.hoursNotes,
  );

  if (JSON.stringify(payload) === JSON.stringify(baselinePayload)) {
    return null;
  }
  return payload;
}

export function buildRestrictedChangePayload(
  values: BasicsFormValues,
  baseline: PublishedBaselines,
): OwnerRestrictedIdentityPayload | null {
  const payload: OwnerRestrictedIdentityPayload = {};

  const displayName = values.displayName.trim();
  if (displayName && displayName !== baseline.displayName.trim()) {
    payload.display_name = displayName;
  }

  const address1 = values.addressLine1.trim();
  if (address1 && address1 !== baseline.addressLine1.trim()) {
    payload.address_line_1 = address1;
  }

  const address2 = values.addressLine2.trim();
  if (address2 !== (baseline.addressLine2.trim() || "")) {
    payload.address_line_2 = address2 || null;
  }

  const postal = values.postalCode.trim();
  if (postal !== (baseline.postalCode.trim() || "")) {
    payload.postal_code = postal || undefined;
  }

  if (values.localityId && values.localityId !== baseline.localityId) {
    payload.locality_id = values.localityId;
  }

  const country = values.countryCode.trim() || "AU";
  if (country !== baseline.countryCode) {
    payload.country_code = country;
  }

  return Object.keys(payload).length > 0 ? payload : null;
}

export function hasRestrictedPendingReview(detail: OwnerVenueDetail): boolean {
  const { pending_review: pending } = detail;
  return Boolean(
    pending.proposal_id &&
      pending.lifecycle_status === "in_review" &&
      pending.submitted_at,
  );
}

export function operationalFormChanged(
  values: BasicsFormValues,
  baseline: PublishedBaselines,
): boolean {
  return (
    buildOperationalProfilePatch(values, baseline) !== null ||
    buildHoursPatch(values, baseline) !== null
  );
}
