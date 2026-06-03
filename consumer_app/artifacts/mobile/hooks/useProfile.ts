import { useCallback, useEffect, useState } from "react";

import { privateApiRequest } from "@/lib/api";
import { useAuthSession } from "@/hooks/useAuthSession";

export type ConsumerProfile = {
  display_name: string | null;
  avatar_storage_ref: string | null;
  default_locality_id: string | null;
  default_geographic_region_id: string | null;
  email_marketing_opt_in: boolean;
  email_transactional_opt_in: boolean;
  push_notifications_opt_in: boolean;
  sms_marketing_opt_in: boolean;
  sms_transactional_opt_in: boolean;
  quiet_hours_start_local: string | null;
  quiet_hours_end_local: string | null;
};

type ProfileResponse = { data: ConsumerProfile };

type ProfilePatch = Partial<
  Pick<
    ConsumerProfile,
    | "display_name"
    | "default_locality_id"
    | "default_geographic_region_id"
    | "email_marketing_opt_in"
    | "email_transactional_opt_in"
    | "push_notifications_opt_in"
    | "sms_marketing_opt_in"
    | "sms_transactional_opt_in"
    | "quiet_hours_start_local"
    | "quiet_hours_end_local"
  >
>;

export function useProfile() {
  const { isAuthenticated, loading: authLoading, session } = useAuthSession();
  const [profile, setProfile] = useState<ConsumerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshProfile = useCallback(async () => {
    if (!isAuthenticated) {
      setProfile(null);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await privateApiRequest<ProfileResponse>("/api/v1/profile/");
      setProfile(response.data);
    } catch {
      setError("Could not load profile.");
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (authLoading) return;
    refreshProfile();
  }, [authLoading, refreshProfile]);

  const patchProfile = useCallback(async (payload: ProfilePatch) => {
    setSaving(true);
    setError(null);
    try {
      const response = await privateApiRequest<ProfileResponse>("/api/v1/profile/", {
        method: "PATCH",
        body: payload,
      });
      setProfile(response.data);
      return response.data;
    } catch {
      setError("Could not update profile.");
      return null;
    } finally {
      setSaving(false);
    }
  }, []);

  return {
    session,
    isAuthenticated,
    profile,
    loading: loading || authLoading,
    saving,
    error,
    refreshProfile,
    patchProfile,
  };
}
