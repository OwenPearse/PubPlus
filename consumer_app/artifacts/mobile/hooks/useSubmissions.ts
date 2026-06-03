import { useCallback, useState } from "react";

import type {
  CorrectionAttributeItem,
  CorrectionAttributesProposedValues,
} from "@workspace/api-client-react";
import { privateApiRequest, type ApiRequestError } from "@/lib/api";

export type CorrectionDomain = "profile" | "location" | "attributes" | "hours";

export type SubmitCorrectionPayload = {
  venue_id: string;
  domain: CorrectionDomain;
  proposed_values: Record<string, unknown> | CorrectionAttributesProposedValues;
  note?: string;
};

export type { CorrectionAttributeItem, CorrectionAttributesProposedValues };

export type SuggestVenuePayload = {
  name: string;
  address_line_1: string;
  address_line_2?: string;
  postcode?: string;
  country_code?: string;
  note?: string;
};

type SubmissionAck = {
  status: "received";
  message: string;
};

export function useSubmissions() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]> | null>(null);
  const [authRequired, setAuthRequired] = useState(false);

  const clearSubmissionState = useCallback(() => {
    setError(null);
    setFieldErrors(null);
    setAuthRequired(false);
  }, []);

  const handleError = useCallback((requestError: ApiRequestError) => {
    setError(requestError.message || "Could not submit. Please try again.");
    const details = requestError.details as
      | { error?: { details?: Record<string, string[]>; message?: string } }
      | undefined;
    setFieldErrors(details?.error?.details ?? null);
    setAuthRequired(Boolean(requestError.isAuthRequired));
  }, []);

  const submitCorrection = useCallback(
    async (payload: SubmitCorrectionPayload): Promise<SubmissionAck> => {
      setSubmitting(true);
      clearSubmissionState();
      try {
        return await privateApiRequest<SubmissionAck>("/api/v1/submissions/corrections", {
          method: "POST",
          body: payload,
        });
      } catch (errorValue) {
        handleError(errorValue as ApiRequestError);
        throw errorValue;
      } finally {
        setSubmitting(false);
      }
    },
    [clearSubmissionState, handleError]
  );

  const suggestNewVenue = useCallback(
    async (payload: SuggestVenuePayload): Promise<SubmissionAck> => {
      setSubmitting(true);
      clearSubmissionState();
      try {
        return await privateApiRequest<SubmissionAck>("/api/v1/submissions/new-venues", {
          method: "POST",
          body: payload,
        });
      } catch (errorValue) {
        handleError(errorValue as ApiRequestError);
        throw errorValue;
      } finally {
        setSubmitting(false);
      }
    },
    [clearSubmissionState, handleError]
  );

  return {
    submitting,
    error,
    fieldErrors,
    authRequired,
    clearSubmissionState,
    submitCorrection,
    suggestNewVenue,
  };
}
