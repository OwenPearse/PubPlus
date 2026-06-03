import type {
  HomeFeedResponse,
  HomeFeedSection,
  MapVenueMarker,
  MapVenuesResponse,
  PublicVenueCard,
  SearchVenuesResponse,
  VenueDetailResponse,
} from "@workspace/api-client-react";
import type { Event, OpeningHours, Special, Venue } from "@/data/mockData";

export type {
  HomeFeedResponse,
  HomeFeedSection,
  MapVenueMarker,
  MapVenuesResponse,
  PublicVenueCard,
  SearchVenuesResponse,
  VenueDetailResponse,
};

/** @deprecated Use `HomeFeedResponse` — alias kept for existing screen imports. */
export type HomeResponse = HomeFeedResponse;

/** @deprecated Use `SearchVenuesResponse` — alias kept for existing screen imports. */
export type SearchResponse = SearchVenuesResponse;

/** @deprecated Use `MapVenuesResponse` — alias kept for existing screen imports. */
export type MapResponse = MapVenuesResponse;

const DEFAULT_IMAGE_COLOR = "#2c3e50";
const DAY_INDEX_TO_KEY: Array<keyof OpeningHours> = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function normalizeVenueType(value: string | null | undefined): Venue["type"] {
  const normalized = (value ?? "").toLowerCase();
  if (normalized.includes("rooftop")) return "rooftop";
  if (normalized.includes("sports")) return "sports bar";
  if (normalized.includes("craft")) return "craft beer";
  if (normalized.includes("bar")) return "bar";
  return "pub";
}

function openNowToLabel(openNow: boolean | null | undefined): string {
  if (openNow === true) return "Open now";
  if (openNow === false) return "Closed now";
  return "Hours listed";
}

function toSpecials(items: PublicVenueCard["specials_summary"]): Special[] {
  return items.map((title, index) => ({
    id: `special-${index}-${title}`,
    title,
    description: title,
    validUntil: "See venue details",
  }));
}

/** Map API event summaries only when the backend sends non-empty published data. */
function toEvents(items: PublicVenueCard["events_summary"]): Event[] {
  if (!items.length) return [];
  return items.map((title, index) => ({
    id: `event-${index}-${title}`,
    title,
    date: "Upcoming",
    time: "See details",
    description: "",
  }));
}

/** Map compact map marker payload into the shared venue card mapper. */
export function mapMapMarkerToVenue(marker: MapVenueMarker): Venue {
  return mapCardToVenue({
    ...marker,
    venue_type: "pub",
    address_short: marker.suburb,
    distance_m: null,
    feature_badges: [],
    specials_summary: [],
    events_summary: [],
    drink_highlights: [],
  });
}

export function mapCardToVenue(card: PublicVenueCard): Venue {
  const mealSpecial = card.specials_summary[0];
  return {
    id: card.id,
    name: card.name,
    suburb: card.suburb,
    address: card.address_short,
    type: normalizeVenueType(card.venue_type),
    isOpen: card.open_now === true,
    closingTime: openNowToLabel(card.open_now),
    rating: 0,
    reviewCount: 0,
    tapBeers: card.drink_highlights,
    specials: toSpecials(card.specials_summary),
    events: toEvents(card.events_summary),
    features: card.feature_badges,
    description: "Details available on venue page.",
    imageColor: DEFAULT_IMAGE_COLOR,
    latitude: card.latitude,
    longitude: card.longitude,
    mealDeal: mealSpecial as Venue["mealDeal"],
    isSaved: card.is_saved ?? false,
    openingHours: {
      Mon: "See details",
      Tue: "See details",
      Wed: "See details",
      Thu: "See details",
      Fri: "See details",
      Sat: "See details",
      Sun: "See details",
    },
  };
}

function formatTime(isoLike: string | null | undefined): string {
  if (!isoLike) return "TBC";
  const date = new Date(isoLike);
  if (Number.isNaN(date.getTime())) return isoLike;
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function mapRegularHours(regular: VenueDetailResponse["data"]["hours"]["regular"]): OpeningHours {
  const result: OpeningHours = {
    Mon: "Closed",
    Tue: "Closed",
    Wed: "Closed",
    Thu: "Closed",
    Fri: "Closed",
    Sat: "Closed",
    Sun: "Closed",
  };
  for (const row of regular) {
    const key = DAY_INDEX_TO_KEY[row.day_of_week];
    if (!key) continue;
    result[key] = `${formatTime(row.opens_at)} - ${formatTime(row.closes_at)}`;
  }
  return result;
}

function mapContact(details: VenueDetailResponse["data"]["contact"]["items"]): {
  phone?: string;
  website?: string;
} {
  const phone = details.find((item) => item.link_type === "phone")?.value;
  const website = details.find((item) => item.link_type === "website")?.value;
  return { phone, website };
}

export function mapVenueDetailResponse(response: VenueDetailResponse): Venue {
  const { data } = response;
  const location = data.location;
  const description = data.identity.long_description ?? data.identity.short_description ?? "No description provided.";
  const drinks = data.drinks.highlights.map((item) => item.product_name ?? item.line_label);
  const features = data.features.items.map((item) =>
    item.value_label ?? item.label
  );
  const specials: Special[] = data.specials.items.map((item) => ({
    id: item.id,
    title: item.short_label,
    description: item.headline ?? item.short_label,
    validUntil: "Check venue for timing",
  }));
  const events: Event[] = data.events.items.length
    ? data.events.items.map((item) => ({
    id: item.id,
    title: item.title,
    date: "Upcoming",
    time: formatTime(item.starts_at),
    description: item.description ?? "",
      }))
    : [];
  const contact = mapContact(data.contact.items);
  return {
    id: data.identity.id,
    name: data.identity.name,
    suburb: location.suburb,
    address: [location.address_line_1, location.address_line_2].filter(Boolean).join(", "),
    type: normalizeVenueType(data.identity.venue_type),
    isOpen: data.hours.open_now === true,
    closingTime: openNowToLabel(data.hours.open_now),
    rating: 0,
    reviewCount: 0,
    tapBeers: drinks,
    specials,
    events,
    features,
    description,
    imageColor: DEFAULT_IMAGE_COLOR,
    latitude: location.latitude,
    longitude: location.longitude,
    isSaved: data.authenticated_actions.is_saved ?? false,
    phone: contact.phone,
    website: contact.website,
    openingHours: mapRegularHours(data.hours.regular),
  };
}
