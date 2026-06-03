import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  type ReactNode,
} from "react";

import { useCurrentLocation } from "@/hooks/useCurrentLocation";
import { useLocalities } from "@/hooks/useLocalities";
import { useProfile } from "@/hooks/useProfile";
import {
  getProfileDefaultOrigin,
  getSearchOriginFromLocalityName,
  resolveDiscoveryOrigin,
  type DiscoveryOriginSource,
  type ResolvedDiscoveryOrigin,
} from "@/lib/discoveryOrigin";
import type { SearchOriginCoordinates } from "@/lib/searchOrigin";

type DiscoveryOriginContextValue = {
  deviceCoords: SearchOriginCoordinates | null;
  devicePermission: "undetermined" | "granted" | "denied";
  deviceLocationLoading: boolean;
  profileDefaultOrigin: SearchOriginCoordinates | null;
  resolveSearchOrigin: (selectedSuburb: string | null) => ResolvedDiscoveryOrigin;
  discoveryOrigin: ResolvedDiscoveryOrigin;
};

const DiscoveryOriginContext = createContext<DiscoveryOriginContextValue | null>(null);

export function DiscoveryOriginProvider({ children }: { children: ReactNode }) {
  const {
    coords: deviceCoords,
    permission: devicePermission,
    loading: deviceLocationLoading,
  } = useCurrentLocation({ requestOnMount: true });
  const { profile } = useProfile();
  const { localities } = useLocalities();

  const profileDefaultOrigin = useMemo(
    () => getProfileDefaultOrigin(profile?.default_locality_id, localities),
    [profile?.default_locality_id, localities]
  );

  const resolveSearchOrigin = useCallback(
    (selectedSuburb: string | null): ResolvedDiscoveryOrigin => {
      const suburbOrigin = getSearchOriginFromLocalityName(selectedSuburb, localities);
      return resolveDiscoveryOrigin({
        device: deviceCoords,
        suburb: suburbOrigin,
        profileDefault: profileDefaultOrigin,
      });
    },
    [deviceCoords, localities, profileDefaultOrigin]
  );

  const discoveryOrigin = useMemo(
    () => resolveSearchOrigin(null),
    [resolveSearchOrigin]
  );

  const value = useMemo(
    (): DiscoveryOriginContextValue => ({
      deviceCoords,
      devicePermission,
      deviceLocationLoading,
      profileDefaultOrigin,
      resolveSearchOrigin,
      discoveryOrigin,
    }),
    [
      deviceCoords,
      devicePermission,
      deviceLocationLoading,
      profileDefaultOrigin,
      resolveSearchOrigin,
      discoveryOrigin,
    ]
  );

  return (
    <DiscoveryOriginContext.Provider value={value}>
      {children}
    </DiscoveryOriginContext.Provider>
  );
}

export function useDiscoveryOrigin() {
  const ctx = useContext(DiscoveryOriginContext);
  if (!ctx) {
    throw new Error("useDiscoveryOrigin must be used within DiscoveryOriginProvider");
  }
  return ctx;
}

export type { DiscoveryOriginSource, ResolvedDiscoveryOrigin };
