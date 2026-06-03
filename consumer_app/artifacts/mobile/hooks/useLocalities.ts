import { useCallback, useEffect, useState } from "react";

import { publicApiRequest } from "@/lib/api";

export type LocalityReference = {
  id: string;
  name: string;
  state?: string;
  country_code?: string;
  geographic_region_id: string;
  geographic_region_name: string;
  latitude?: number;
  longitude?: number;
};

type LocalitiesResponse = {
  data: {
    localities: LocalityReference[];
  };
};

export function useLocalities() {
  const [localities, setLocalities] = useState<LocalityReference[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await publicApiRequest<LocalitiesResponse>(
        "/api/v1/reference/localities"
      );
      setLocalities(response.data?.localities ?? []);
    } catch {
      setLocalities([]);
      setError("Supported suburbs could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    localities,
    loading,
    error,
    refresh,
  };
}

export function findLocalityById(
  localities: LocalityReference[],
  id: string | null | undefined
): LocalityReference | undefined {
  if (!id) return undefined;
  return localities.find((l) => l.id === id);
}

export function findLocalityByName(
  localities: LocalityReference[],
  name: string | null | undefined
): LocalityReference | undefined {
  if (!name?.trim()) return undefined;
  const trimmed = name.trim();
  return localities.find((l) => l.name === trimmed);
}
