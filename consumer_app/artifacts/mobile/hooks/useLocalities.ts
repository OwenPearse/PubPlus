import type { LocalitiesReferenceResponse, LocalityReference } from "@workspace/api-client-react";
import { useCallback, useEffect, useState } from "react";

import { publicApiRequest } from "@/lib/api";

export type { LocalityReference };

export function useLocalities() {
  const [localities, setLocalities] = useState<LocalityReference[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await publicApiRequest<LocalitiesReferenceResponse>(
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
