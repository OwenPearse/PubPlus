import * as Location from "expo-location";
import { useCallback, useEffect, useRef, useState } from "react";

import { isValidSearchOrigin, type SearchOriginCoordinates } from "@/lib/searchOrigin";

export type LocationPermissionStatus = "undetermined" | "granted" | "denied";

export const LOCATION_PERMISSION_MESSAGE =
  "PubPlus uses your location to show nearby pubs and distance-based search results.";

type State = {
  coords: SearchOriginCoordinates | null;
  permission: LocationPermissionStatus;
  loading: boolean;
};

const INITIAL: State = {
  coords: null,
  permission: "undetermined",
  loading: false,
};

/**
 * Foreground device location for session-local discovery origin only (never persisted).
 * Requests permission at most once per app session when still undetermined.
 */
export function useCurrentLocation(options?: { requestOnMount?: boolean }) {
  const requestOnMount = options?.requestOnMount ?? false;
  const [state, setState] = useState<State>(INITIAL);
  const requestedPermissionRef = useRef(false);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true }));
    try {
      const servicesEnabled = await Location.hasServicesEnabledAsync();
      if (!servicesEnabled) {
        setState({ coords: null, permission: "denied", loading: false });
        return;
      }

      let permission = await Location.getForegroundPermissionsAsync();
      if (
        permission.status === Location.PermissionStatus.UNDETERMINED &&
        !requestedPermissionRef.current
      ) {
        requestedPermissionRef.current = true;
        permission = await Location.requestForegroundPermissionsAsync();
      }

      if (permission.status !== Location.PermissionStatus.GRANTED) {
        setState({
          coords: null,
          permission: "denied",
          loading: false,
        });
        return;
      }

      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      const candidate = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
      };
      setState({
        coords: isValidSearchOrigin(candidate) ? candidate : null,
        permission: "granted",
        loading: false,
      });
    } catch {
      setState({ coords: null, permission: "denied", loading: false });
    }
  }, []);

  useEffect(() => {
    if (requestOnMount) {
      refresh();
    }
  }, [requestOnMount, refresh]);

  return {
    coords: state.coords,
    permission: state.permission,
    loading: state.loading,
    refresh,
  };
}
