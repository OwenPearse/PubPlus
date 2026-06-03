import type { SearchFiltersData, SearchFiltersResponse } from "@workspace/api-client-react";
import { useCallback, useEffect, useState } from "react";

import { publicApiRequest } from "@/lib/api";

export type {
  SearchFilterDrinkType as DrinkTypeFilter,
  SearchFilterKeyLabel as EventFilter,
  SearchFilterKeyLabel as MealSpecialFilter,
  SearchFiltersData,
  SearchFilterVenueFeature,
  SearchFilterKeyLabel as VenueFeatureFilter,
} from "@workspace/api-client-react";

const EMPTY_FILTERS: SearchFiltersData = {
  venue_features: [],
  drink_types: [],
  meal_specials: [],
  event_filters: [],
};

/**
 * Search filter reference from the backend. Render `event_filters` chips only when
 * `event_filters.length > 0` (empty means event discovery is not available yet).
 */
export function useSearchFilters() {
  const [filters, setFilters] = useState<SearchFiltersData>(EMPTY_FILTERS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await publicApiRequest<SearchFiltersResponse>("/api/v1/search/filters");
      setFilters(response.data ?? EMPTY_FILTERS);
    } catch {
      setFilters(EMPTY_FILTERS);
      setError("Filter options could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    filters,
    loading,
    error,
    refresh,
  };
}
