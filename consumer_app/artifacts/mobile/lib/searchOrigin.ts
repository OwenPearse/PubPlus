import { SUBURB_ORIGIN_COORDINATES } from "@/data/mockData";

export type SearchOriginCoordinates = {
  lat: number;
  lng: number;
};

export function isValidSearchCoordinate(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function isValidSearchOrigin(
  origin: SearchOriginCoordinates | null | undefined
): origin is SearchOriginCoordinates {
  if (!origin) return false;
  const { lat, lng } = origin;
  if (!isValidSearchCoordinate(lat) || !isValidSearchCoordinate(lng)) {
    return false;
  }
  return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
}

/** Suburb label → approximate centroid for radius search (Melbourne inner MVP). */
export function getSearchOriginFromSuburb(
  suburb: string | null | undefined
): SearchOriginCoordinates | null {
  if (!suburb?.trim()) return null;
  const coords = SUBURB_ORIGIN_COORDINATES[suburb.trim()];
  if (!coords) return null;
  return isValidSearchOrigin(coords) ? coords : null;
}
