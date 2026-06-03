/**
 * Melbourne inner-locality IDs from `database/sql/seeds/dev_seed_reference_melbourne_localities.sql`.
 * Used for Profile default locality PATCH (FK-valid UUIDs only — do not invent IDs client-side).
 */
export const MELBOURNE_VIC_REGION_ID = "11111111-1111-4111-8111-111111111103";

export type LocalityRef = {
  localityId: string;
  geographicRegionId: string;
  name: string;
};

/** Seed-backed localities keyed by display label (Search suburb label where applicable). */
const LOCALITY_BY_LABEL: Record<string, LocalityRef> = {
  Abbotsford: {
    localityId: "22222222-2222-4222-8222-000000000001",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Abbotsford",
  },
  Brunswick: {
    localityId: "22222222-2222-4222-8222-000000000002",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Brunswick",
  },
  Carlton: {
    localityId: "22222222-2222-4222-8222-000000000004",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Carlton",
  },
  /** Search uses "CBD"; seed locality name is Melbourne. */
  CBD: {
    localityId: "22222222-2222-4222-8222-00000000000c",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Melbourne",
  },
  Collingwood: {
    localityId: "22222222-2222-4222-8222-000000000006",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Collingwood",
  },
  Cremorne: {
    localityId: "22222222-2222-4222-8222-000000000007",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Cremorne",
  },
  Fitzroy: {
    localityId: "22222222-2222-4222-8222-000000000009",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Fitzroy",
  },
  Hawthorn: {
    localityId: "22222222-2222-4222-8222-00000000000b",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Hawthorn",
  },
  "Port Melbourne": {
    localityId: "22222222-2222-4222-8222-00000000000d",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Port Melbourne",
  },
  Prahran: {
    localityId: "22222222-2222-4222-8222-00000000000e",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Prahran",
  },
  Richmond: {
    localityId: "22222222-2222-4222-8222-00000000000f",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Richmond",
  },
  "South Yarra": {
    localityId: "22222222-2222-4222-8222-000000000011",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "South Yarra",
  },
  "St Kilda": {
    localityId: "22222222-2222-4222-8222-000000000012",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "St Kilda",
  },
  Windsor: {
    localityId: "22222222-2222-4222-8222-000000000014",
    geographicRegionId: MELBOURNE_VIC_REGION_ID,
    name: "Windsor",
  },
};

const LOCALITY_ID_TO_LABEL = new Map<string, string>(
  Object.entries(LOCALITY_BY_LABEL).map(([label, ref]) => [ref.localityId, label])
);

/** Suburb labels that can be saved as `default_locality_id` (seed-backed only). */
export const PROFILE_PICKABLE_SUBURBS = Object.keys(LOCALITY_BY_LABEL).sort((a, b) =>
  a.localeCompare(b)
);

export function getLocalityRefForSuburbLabel(
  label: string | null | undefined
): LocalityRef | null {
  if (!label?.trim()) return null;
  return LOCALITY_BY_LABEL[label.trim()] ?? null;
}

export function getSuburbLabelForLocalityId(
  localityId: string | null | undefined
): string | null {
  if (!localityId) return null;
  return LOCALITY_ID_TO_LABEL.get(localityId) ?? null;
}

export function buildDefaultLocalityPatch(
  suburbLabel: string | null
): {
  default_locality_id: string | null;
  default_geographic_region_id: string | null;
} {
  if (!suburbLabel) {
    return {
      default_locality_id: null,
      default_geographic_region_id: null,
    };
  }
  const ref = getLocalityRefForSuburbLabel(suburbLabel);
  if (!ref) {
    return {
      default_locality_id: null,
      default_geographic_region_id: null,
    };
  }
  return {
    default_locality_id: ref.localityId,
    default_geographic_region_id: ref.geographicRegionId,
  };
}
