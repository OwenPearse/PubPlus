import type { BasicsFormValues } from "@/owner/lib/ownerVenueBasicsForm";

export type BasicsValidationIntent = "draft" | "submit";

export type BasicsFieldErrors = Record<string, string>;

const TIME_RE = /^([01]\d|2[0-3]):[0-5]\d$/;
const POSTAL_RE = /^[A-Za-z0-9 \-]+$/;

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

export function validateBasicsForm(
  values: BasicsFormValues,
  intent: BasicsValidationIntent,
): BasicsFieldErrors {
  const submit = intent === "submit";
  const errors: BasicsFieldErrors = {};

  validateRequiredString(errors, "displayName", values.displayName, {
    minLen: 2,
    maxLen: 120,
    required: submit,
  });
  if (values.displayName.trim() && !submit) {
    validateRequiredString(errors, "displayName", values.displayName, {
      minLen: 2,
      maxLen: 120,
      required: false,
    });
  }

  validateRequiredString(errors, "addressLine1", values.addressLine1, {
    minLen: 3,
    maxLen: 200,
    required: submit,
  });
  if (values.addressLine1.trim() && !submit) {
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

  if (!values.localityId.trim()) {
    if (submit) {
      setError(errors, "localityId", "This field is required.");
    }
  }

  validateOptionalString(errors, "shortDescription", values.shortDescription, {
    maxLen: 500,
  });
  if (submit && !values.shortDescription.trim()) {
    setError(errors, "shortDescription", "This field is required.");
  }

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

  if (submit && !hoursAreSatisfied(values)) {
    setError(
      errors,
      "openingHours",
      "Provide at least one open day or hours notes (min 10 characters).",
    );
  }

  if (submit && !values.ownerConfirmsManagement) {
    setError(
      errors,
      "ownerConfirmsManagement",
      "You must confirm you manage this venue.",
    );
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
    owner_confirms_management: "ownerConfirmsManagement",
    opening_hours: "openingHours",
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

    if (serverKey.startsWith("opening_hours")) {
      errors.openingHours = message;
    }
  }

  return errors;
}
