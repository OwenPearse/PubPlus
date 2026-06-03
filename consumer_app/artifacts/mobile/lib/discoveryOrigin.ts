import type { LocalityReference } from "@/hooks/useLocalities";
import { isValidSearchOrigin, type SearchOriginCoordinates } from "@/lib/searchOrigin";

export type DiscoveryOriginSource = "device" | "suburb" | "profile" | null;

export type ResolvedDiscoveryOrigin = {
  origin: SearchOriginCoordinates | null;
  source: DiscoveryOriginSource;
};

export function coordsFromLocality(
  locality: LocalityReference | undefined
): SearchOriginCoordinates | null {
  if (!locality) return null;
  const { latitude, longitude } = locality;
  if (latitude == null || longitude == null) return null;
  const candidate = { lat: latitude, lng: longitude };
  return isValidSearchOrigin(candidate) ? candidate : null;
}

export function getSearchOriginFromLocalityName(
  suburbName: string | null | undefined,
  localities: LocalityReference[]
): SearchOriginCoordinates | null {
  if (!suburbName?.trim()) return null;
  const trimmed = suburbName.trim();
  const fromApi = localities.find((l) => l.name === trimmed);
  return coordsFromLocality(fromApi);
}

export function getProfileDefaultOrigin(
  defaultLocalityId: string | null | undefined,
  localities: LocalityReference[]
): SearchOriginCoordinates | null {
  if (!defaultLocalityId) return null;
  const locality = localities.find((l) => l.id === defaultLocalityId);
  return coordsFromLocality(locality) ?? getSearchOriginFromLocalityName(locality?.name, localities);
}

/** Priority: device → selected suburb → profile default → none. */
export function resolveDiscoveryOrigin(input: {
  device?: SearchOriginCoordinates | null;
  suburb?: SearchOriginCoordinates | null;
  profileDefault?: SearchOriginCoordinates | null;
}): ResolvedDiscoveryOrigin {
  if (isValidSearchOrigin(input.device)) {
    return { origin: input.device, source: "device" };
  }
  if (isValidSearchOrigin(input.suburb)) {
    return { origin: input.suburb, source: "suburb" };
  }
  if (isValidSearchOrigin(input.profileDefault)) {
    return { origin: input.profileDefault, source: "profile" };
  }
  return { origin: null, source: null };
}

/** Map viewport (~5 km) centered on an origin; falls back to Melbourne inner defaults. */
export function mapViewportAroundOrigin(
  origin: SearchOriginCoordinates | null,
  delta = 0.045
): { north: number; south: number; east: number; west: number } {
  if (!isValidSearchOrigin(origin)) {
    return {
      north: -37.74,
      south: -37.86,
      east: 145.03,
      west: 144.9,
    };
  }
  return {
    north: origin.lat + delta,
    south: origin.lat - delta,
    east: origin.lng + delta,
    west: origin.lng - delta,
  };
}
