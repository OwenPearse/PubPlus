import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import type { Venue } from "@/data/mockData";
import { privateApiRequest, type ApiRequestError } from "@/lib/api";
import { mapCardToVenue } from "@/lib/mappers";
import { useAuthSession } from "@/hooks/useAuthSession";

type SavedVenuesResponse = {
  data: {
    venues: Array<{
      id: string;
      name: string;
      venue_type: string | null;
      suburb: string;
      address_short: string;
      latitude: number;
      longitude: number;
      hero_photo_url: string | null;
      open_now: boolean | null;
      open_now_uncomputed: boolean;
      distance_m: number | null;
      feature_badges: string[];
      specials_summary: string[];
      events_summary: string[];
      drink_highlights: string[];
      is_saved: boolean | null;
    }>;
  };
};

type SavedContextValue = {
  savedVenues: Venue[];
  savedVenueIds: Set<string>;
  isSaved: (venueId: string) => boolean;
  refreshSavedVenues: () => Promise<void>;
  toggleSaved: (venueId: string) => Promise<void>;
  saveVenue: (venueId: string) => Promise<void>;
  unsaveVenue: (venueId: string) => Promise<void>;
  loading: boolean;
  syncingVenueIds: Set<string>;
  error: string | null;
  authRequired: boolean;
  authMessage: string | null;
  clearAuthMessage: () => void;
};

const SavedVenuesContext = createContext<SavedContextValue | null>(null);

async function fetchSavedVenues(): Promise<Venue[]> {
  const response = await privateApiRequest<SavedVenuesResponse>("/api/v1/saved/venues");
  return (response.data.venues ?? []).map(mapCardToVenue);
}

export function SavedVenuesProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading: authLoading } = useAuthSession();
  const [savedVenues, setSavedVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authRequired, setAuthRequired] = useState(false);
  const [authMessage, setAuthMessage] = useState<string | null>(null);
  const [syncingVenueIds, setSyncingVenueIds] = useState<Set<string>>(new Set());
  const [optimisticSavedIds, setOptimisticSavedIds] = useState<Set<string>>(new Set());

  const markSyncing = useCallback((venueId: string, syncing: boolean) => {
    setSyncingVenueIds((current) => {
      const next = new Set(current);
      if (syncing) next.add(venueId);
      else next.delete(venueId);
      return next;
    });
  }, []);

  const refreshSavedVenues = useCallback(async () => {
    if (!isAuthenticated) {
      setSavedVenues([]);
      setOptimisticSavedIds(new Set());
      setLoading(false);
      setError(null);
      setAuthRequired(true);
      return;
    }

    setLoading(true);
    setError(null);
    setAuthRequired(false);
    try {
      const venues = await fetchSavedVenues();
      setSavedVenues(venues);
    } catch (err) {
      const requestError = err as ApiRequestError;
      if (requestError.isAuthRequired) {
        setAuthRequired(true);
        setSavedVenues([]);
        return;
      }
      setError("Could not load saved venues.");
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (authLoading) return;
    refreshSavedVenues();
  }, [authLoading, refreshSavedVenues]);

  const saveVenue = useCallback(
    async (venueId: string) => {
      if (!isAuthenticated) {
        setAuthRequired(true);
        setAuthMessage("Sign in to save venues.");
        return;
      }
      if (syncingVenueIds.has(venueId)) return;

      markSyncing(venueId, true);
      setOptimisticSavedIds((current) => new Set(current).add(venueId));
      try {
        await privateApiRequest<{ data: { saved: boolean; venue_id: string } }>("/api/v1/saved/venues", {
          method: "POST",
          body: { venue_id: venueId },
        });
        const venues = await fetchSavedVenues();
        setSavedVenues(venues);
      } catch (err) {
        if ((err as ApiRequestError).isAuthRequired) {
          setAuthRequired(true);
          setAuthMessage("Sign in to save venues.");
        }
        setOptimisticSavedIds((current) => {
          const next = new Set(current);
          next.delete(venueId);
          return next;
        });
        setError("Could not save this venue.");
      } finally {
        markSyncing(venueId, false);
      }
    },
    [isAuthenticated, markSyncing, syncingVenueIds]
  );

  const unsaveVenue = useCallback(
    async (venueId: string) => {
      if (!isAuthenticated) {
        setAuthRequired(true);
        setAuthMessage("Sign in to save venues.");
        return;
      }
      if (syncingVenueIds.has(venueId)) return;

      markSyncing(venueId, true);
      setOptimisticSavedIds((current) => {
        const next = new Set(current);
        next.delete(venueId);
        return next;
      });
      try {
        await privateApiRequest<null>(`/api/v1/saved/venues/${venueId}`, {
          method: "DELETE",
        });
        setSavedVenues((current) => current.filter((venue) => venue.id !== venueId));
      } catch (err) {
        if ((err as ApiRequestError).isAuthRequired) {
          setAuthRequired(true);
          setAuthMessage("Sign in to save venues.");
        }
        setOptimisticSavedIds((current) => new Set(current).add(venueId));
        setError("Could not update saved venues.");
      } finally {
        markSyncing(venueId, false);
      }
    },
    [isAuthenticated, markSyncing, syncingVenueIds]
  );

  const toggleSaved = useCallback(
    async (venueId: string) => {
      const currentlySaved = savedVenues.some((venue) => venue.id === venueId);
      if (currentlySaved) {
        await unsaveVenue(venueId);
      } else {
        await saveVenue(venueId);
      }
    },
    [savedVenues, saveVenue, unsaveVenue]
  );

  const savedVenueIds = useMemo(() => {
    const ids = new Set(savedVenues.map((venue) => venue.id));
    optimisticSavedIds.forEach((id) => ids.add(id));
    return ids;
  }, [optimisticSavedIds, savedVenues]);

  const value = useMemo<SavedContextValue>(
    () => ({
      savedVenues,
      savedVenueIds,
      isSaved: (venueId: string) => savedVenueIds.has(venueId),
      refreshSavedVenues,
      toggleSaved,
      saveVenue,
      unsaveVenue,
      loading: loading || authLoading,
      syncingVenueIds,
      error,
      authRequired,
      authMessage,
      clearAuthMessage: () => setAuthMessage(null),
    }),
    [
      authLoading,
      authMessage,
      authRequired,
      error,
      loading,
      refreshSavedVenues,
      saveVenue,
      savedVenueIds,
      savedVenues,
      syncingVenueIds,
      toggleSaved,
      unsaveVenue,
    ]
  );

  return <SavedVenuesContext.Provider value={value}>{children}</SavedVenuesContext.Provider>;
}

export function useSavedVenues() {
  const context = useContext(SavedVenuesContext);
  if (!context) {
    throw new Error("useSavedVenues must be used within a SavedVenuesProvider.");
  }
  return context;
}
