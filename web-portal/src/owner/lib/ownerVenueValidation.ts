import type { BasicsFormValues } from "@/owner/lib/ownerVenueBasicsForm";

export type BasicsFieldErrors = Record<string, string>;

const TIME_RE = /^([01]\d|2[0-3]):[0-5]\d$/;
const POSTAL_RE = /^[A-Za-z0-9 \-]+$/;
const HOURS_NOTES_MAX = 1000;

function setError(errors: BasicsFieldErrors, key: string, message: string) {
  if (!errors[key]) {
    errors[key] = message;
  }
}

function validateOptionalString(
  errors: BasicsFieldErrors,
  key: string,
  value: string,
  opts: { maxLen: number; pattern?: RegExp; patternMessage?: string },
) {
  const trimmed = value.trim();
  if (!trimmed) return;
  if (trimmed.length > opts.maxLen) {
    setError(errors, key, `Must be at most ${opts.maxLen} characters.`);
  }
  if (opts.pattern && !opts.pattern.test(trimmed)) {
    setError(errors, key, opts.patternMessage ?? "Invalid format.");
  }
}

function validateRequiredString(
  errors: BasicsFieldErrors,
  key: string,
  value: string,
  opts: { minLen: number; maxLen: number; required: boolean },
) {
  const trimmed = value.trim();
  if (!trimmed) {
    if (opts.required) {
      setError(errors, key, "This field is required.");
    }
    return;
  }
  if (trimmed.length < opts.minLen || trimmed.length > opts.maxLen) {
    setError(
      errors,
      key,
      `Must be between ${opts.minLen} and ${opts.maxLen} characters.`,
    );
  }
}

function hoursAreSatisfied(values: BasicsFormValues): boolean {
  const openDays = values.weeklyHours.filter((day) => !day.closed);
  if (openDays.length > 0) return true;
  return values.hoursNotes.trim().length >= 10;
}

export function validateOperationalForm(values: BasicsFormValues): BasicsFieldErrors {
  const errors: BasicsFieldErrors = {};

  const hasDescription =
    values.shortDescription.trim().length > 0 || values.longDescription.trim().length > 0;
  const hasHours = hoursAreSatisfied(values);

  if (!hasDescription && !hasHours) {
    setError(
      errors,
      "operational",
      "Update a description or opening hours before saving.",
    );
  }

  validateOptionalString(errors, "shortDescription", values.shortDescription, {
    maxLen: 500,
  });
  validateOptionalString(errors, "longDescription", values.longDescription, {
    maxLen: 2000,
  });

  values.weeklyHours.forEach((day) => {
    if (day.closed) return;
    const prefix = `hours.${day.dayOfWeek}`;
    if (!TIME_RE.test(day.opensAt)) {
      setError(errors, `${prefix}.opensAt`, "Time must be HH:MM (24-hour).");
    }
    if (!TIME_RE.test(day.closesAt)) {
      setError(errors, `${prefix}.closesAt`, "Time must be HH:MM (24-hour).");
    }
  });

  if (values.hoursNotes.trim().length > HOURS_NOTES_MAX) {
    setError(errors, "hoursNotes", `Must be at most ${HOURS_NOTES_MAX} characters.`);
  }

  if (!hasHours && (hasDescription || values.hoursNotes.trim())) {
    setError(
      errors,
      "openingHours",
      "Provide at least one open day or hours notes (min 10 characters).",
    );
  }

  return errors;
}

export function validateRestrictedForm(values: BasicsFormValues): BasicsFieldErrors {
  const errors: BasicsFieldErrors = {};

  const hasIdentity =
    values.displayName.trim() ||
    values.addressLine1.trim() ||
    values.addressLine2.trim() ||
    values.postalCode.trim() ||
    values.localityId.trim();

  if (!hasIdentity) {
    setError(errors, "restricted", "Change at least one name or address field.");
  }

  if (values.displayName.trim()) {
    validateRequiredString(errors, "displayName", values.displayName, {
      minLen: 2,
      maxLen: 120,
      required: false,
    });
  }

  if (values.addressLine1.trim()) {
    validateRequiredString(errors, "addressLine1", values.addressLine1, {
      minLen: 3,
      maxLen: 200,
      required: false,
    });
  }

  validateOptionalString(errors, "addressLine2", values.addressLine2, { maxLen: 200 });
  validateOptionalString(errors, "postalCode", values.postalCode, {
    maxLen: 12,
    pattern: POSTAL_RE,
    patternMessage:
      "Must be at most 12 characters (letters, digits, spaces, hyphens).",
  });

  if (values.localityId.trim() && !values.localityId) {
    setError(errors, "localityId", "Select a valid locality.");
  }

  return errors;
}

export function mapServerValidationToFormErrors(
  serverDetails: Record<string, string[]>,
): BasicsFieldErrors {
  const errors: BasicsFieldErrors = {};
  const keyMap: Record<string, string> = {
    display_name: "displayName",
    address_line_1: "addressLine1",
    address_line_2: "addressLine2",
    postal_code: "postalCode",
    locality_id: "localityId",
    short_description: "shortDescription",
    long_description: "longDescription",
    opening_hours: "openingHours",
    notes: "hoursNotes",
  };

  for (const [serverKey, messages] of Object.entries(serverDetails)) {
    const message = messages[0];
    if (!message) continue;

    const direct = keyMap[serverKey];
    if (direct) {
      errors[direct] = message;
      continue;
    }

    const hoursDayMatch = serverKey.match(
      /^opening_hours\.regular_hours_json\[(\d+)\]\.(opens_at|closes_at)$/,
    );
    if (hoursDayMatch) {
      const index = Number(hoursDayMatch[1]);
      const field = hoursDayMatch[2] === "opens_at" ? "opensAt" : "closesAt";
      errors[`hours.${index}.${field}`] = message;
      continue;
    }

    const flatHoursMatch = serverKey.match(
      /^regular_hours_json\[(\d+)\]\.(opens_at|closes_at)$/,
    );
    if (flatHoursMatch) {
      const index = Number(flatHoursMatch[1]);
      const field = flatHoursMatch[2] === "opens_at" ? "opensAt" : "closesAt";
      errors[`hours.${index}.${field}`] = message;
      continue;
    }

    if (serverKey.startsWith("opening_hours") || serverKey === "regular_hours_json") {
      errors.openingHours = message;
    }
  }

  return errors;
}
