import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Dimensions,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useRouter } from "expo-router";

import type { Venue } from "@/data/mockData";
import { EmptyState } from "@/components/EmptyState";
import { useDiscoveryOrigin } from "@/contexts/DiscoveryOriginContext";
import { useColors } from "@/hooks/useColors";
import { useSavedVenues } from "@/hooks/useSavedVenues";
import { mapViewportAroundOrigin } from "@/lib/discoveryOrigin";
import { publicApiRequest } from "@/lib/api";
import { mapMapMarkerToVenue, type MapResponse } from "@/lib/mappers";

const { height: SCREEN_HEIGHT } = Dimensions.get("window");
const POPUP_HEIGHT = Math.round(SCREEN_HEIGHT * 0.33);
/** Decorative map scaffold labels only — viewport/query use discoveryOrigin + GET /api/v1/map/venues. */
const SUBURB_LABELS = [
  { name: "Brunswick",   top: 0.10, left: 0.28 },
  { name: "Fitzroy",     top: 0.26, left: 0.50 },
  { name: "Carlton",     top: 0.37, left: 0.28 },
  { name: "Collingwood", top: 0.32, left: 0.62 },
  { name: "CBD",         top: 0.50, left: 0.36 },
  { name: "Richmond",    top: 0.62, left: 0.62 },
  { name: "South Yarra", top: 0.70, left: 0.52 },
];

const STREETS = [
  { horiz: true,  y: 0.25 },
  { horiz: true,  y: 0.45 },
  { horiz: true,  y: 0.62 },
  { horiz: false, x: 0.40 },
  { horiz: false, x: 0.56 },
];

export default function MapScreen() {
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const [selectedVenue, setSelectedVenue] = useState<Venue | null>(null);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isSaved, toggleSaved, authMessage, clearAuthMessage } = useSavedVenues();
  const { discoveryOrigin } = useDiscoveryOrigin();

  const mapBounds = useMemo(
    () => mapViewportAroundOrigin(discoveryOrigin.origin),
    [discoveryOrigin.origin]
  );

  const topInset = Platform.OS === "web" ? 67 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : insets.bottom;

  function handlePinPress(venue: Venue) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setSelectedVenue((prev) => (prev?.id === venue.id ? null : venue));
  }

  useEffect(() => {
    let cancelled = false;
    async function loadMap() {
      setLoading(true);
      setError(null);
      try {
        const response = await publicApiRequest<MapResponse>("/api/v1/map/venues", {
          query: mapBounds,
        });
        if (cancelled) return;
        const mapped = (response.data.venues ?? []).map(mapMapMarkerToVenue);
        setVenues(mapped);
      } catch {
        if (cancelled) return;
        setVenues([]);
        setError("Could not load map venues.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadMap();
    return () => {
      cancelled = true;
    };
  }, [mapBounds.east, mapBounds.north, mapBounds.south, mapBounds.west]);

  const coordinateBounds = useMemo(() => {
    if (venues.length === 0) return null;
    const latitudes = venues.map((venue) => venue.latitude);
    const longitudes = venues.map((venue) => venue.longitude);
    return {
      north: Math.max(...latitudes),
      south: Math.min(...latitudes),
      east: Math.max(...longitudes),
      west: Math.min(...longitudes),
    };
  }, [venues]);

  const venuePositions = useMemo(() => {
    if (!coordinateBounds) return {};
    const latRange = Math.max(coordinateBounds.north - coordinateBounds.south, 0.01);
    const lngRange = Math.max(coordinateBounds.east - coordinateBounds.west, 0.01);
    return Object.fromEntries(
      venues.map((venue) => {
        const top = 0.12 + (coordinateBounds.north - venue.latitude) / latRange * 0.72;
        const left = 0.15 + (venue.longitude - coordinateBounds.west) / lngRange * 0.7;
        return [venue.id, { top, left }];
      })
    ) as Record<string, { top: number; left: number }>;
  }, [coordinateBounds, venues]);

  return (
    <View style={[styles.outer, { backgroundColor: "#e8ddd0" }]}>
      <View style={[styles.mapArea, { backgroundColor: "#e8ddd0" }]}>
        {STREETS.map((s, i) => (
          <View
            key={i}
            style={[
              styles.street,
              s.horiz
                ? { top: `${s.y! * 100}%` as unknown as number, left: 0, right: 0, height: 3 }
                : { left: `${s.x! * 100}%` as unknown as number, top: 0, bottom: 0, width: 3 },
            ]}
          />
        ))}

        {SUBURB_LABELS.map((s) => (
          <View
            key={s.name}
            style={[
              styles.suburbLabel,
              {
                top: `${s.top * 100}%` as unknown as number,
                left: `${s.left * 100}%` as unknown as number,
              },
            ]}
          >
            <Text style={styles.suburbLabelText}>{s.name}</Text>
          </View>
        ))}

        {venues.map((venue) => {
          const pos = venuePositions[venue.id];
          if (!pos) return null;
          const isSelected = selectedVenue?.id === venue.id;

          return (
            <View
              key={venue.id}
              style={[
                styles.pinWrap,
                {
                  top: `${pos.top * 100}%` as unknown as number,
                  left: `${pos.left * 100}%` as unknown as number,
                  zIndex: isSelected ? 10 : 1,
                },
              ]}
            >
              <TouchableOpacity onPress={() => handlePinPress(venue)} activeOpacity={0.8}>
                <View
                  style={[
                    styles.pin,
                    {
                      backgroundColor: isSelected ? colors.primary : colors.card,
                      borderColor: isSelected ? colors.primary : colors.border,
                      shadowColor: colors.foreground,
                    },
                  ]}
                >
                  <View
                    style={[
                      styles.pinDot,
                      { backgroundColor: venue.isOpen ? "#3aaf60" : colors.destructive },
                    ]}
                  />
                  <Text
                    style={[
                      styles.pinLabel,
                      {
                        color: isSelected ? colors.primaryForeground : colors.foreground,
                      },
                    ]}
                    numberOfLines={1}
                  >
                    {venue.name}
                  </Text>
                </View>
                <View
                  style={[
                    styles.pinTail,
                    { borderTopColor: isSelected ? colors.primary : colors.card },
                  ]}
                />
              </TouchableOpacity>
            </View>
          );
        })}

        <View style={[styles.topOverlay, { top: topInset + 10, left: 16, right: 16 }]}>
          <View
            style={[
              styles.locationChip,
              {
                backgroundColor: colors.card,
                borderColor: colors.border,
                shadowColor: colors.foreground,
              },
            ]}
          >
            <Feather name="navigation" size={13} color={colors.primary} />
            <Text style={[styles.locationChipText, { color: colors.foreground }]}>
              Melbourne, VIC
            </Text>
          </View>
          <TouchableOpacity
            style={[
              styles.recenterBtn,
              {
                backgroundColor: colors.card,
                borderColor: colors.border,
                shadowColor: colors.foreground,
              },
            ]}
          >
            <Feather name="crosshair" size={17} color={colors.primary} />
          </TouchableOpacity>
        </View>

        {!selectedVenue ? (
          <View
            style={[
              styles.venueBadge,
              {
                backgroundColor: colors.card,
                borderColor: colors.border,
                bottom: 16,
                left: 16,
              },
            ]}
          >
            <Text style={[styles.venueBadgeText, { color: colors.mutedForeground }]}>
              {venues.filter((v) => v.isOpen).length} open nearby
            </Text>
          </View>
        ) : null}

        {authMessage ? (
          <TouchableOpacity
            style={[styles.authRequiredCard, { backgroundColor: colors.secondary }]}
            onPress={() => {
              clearAuthMessage();
              router.push("/auth" as never);
            }}
            activeOpacity={0.85}
            accessibilityRole="button"
            accessibilityLabel="Sign in to save venues"
            testID="map-auth-required-cta"
          >
            <Text style={[styles.authRequiredText, { color: colors.primary }]}>{authMessage}</Text>
          </TouchableOpacity>
        ) : null}

        {loading ? (
          <View style={styles.stateOverlay}>
            <ActivityIndicator color={colors.primary} />
            <Text style={[styles.stateText, { color: colors.foreground }]}>Loading map venues...</Text>
          </View>
        ) : null}

        {!loading && error ? (
          <View style={styles.stateOverlay}>
            <EmptyState
              icon="alert-circle"
              title="Map unavailable"
              subtitle={error}
              actionLabel="Try again"
              onAction={() => {
                setLoading(true);
                setError(null);
                publicApiRequest<MapResponse>("/api/v1/map/venues", { query: mapBounds })
                  .then((response) =>
                    setVenues((response.data.venues ?? []).map(mapMapMarkerToVenue))
                  )
                  .catch(() => setError("Could not load map venues."))
                  .finally(() => setLoading(false));
              }}
            />
          </View>
        ) : null}

        {!loading && !error && venues.length === 0 ? (
          <View style={styles.stateOverlay}>
            <EmptyState
              icon="map-pin"
              title="No map venues"
              subtitle="No venues found for the current map bounds."
            />
          </View>
        ) : null}
      </View>

      {selectedVenue ? (
        <View
          style={[
            styles.bottomPopup,
            {
              height: POPUP_HEIGHT,
              backgroundColor: colors.card,
              borderColor: colors.border,
              paddingBottom: bottomInset + 90,
              shadowColor: colors.foreground,
            },
          ]}
        >
          <View style={[styles.popupHandle, { backgroundColor: colors.border }]} />

          <View style={styles.popupContent}>
            <View style={[styles.popupImage, { backgroundColor: selectedVenue.imageColor }]}>
              <View
                style={[
                  styles.popupOpenBadge,
                  {
                    backgroundColor: selectedVenue.isOpen
                      ? "rgba(35,120,65,0.9)"
                      : "rgba(160,50,35,0.9)",
                  },
                ]}
              >
                <View
                  style={[
                    styles.popupOpenDot,
                    {
                      backgroundColor: selectedVenue.isOpen ? "#7dff9e" : "#ff9e7d",
                    },
                  ]}
                />
                <Text style={styles.popupOpenText}>
                  {selectedVenue.isOpen
                    ? `Open · ${selectedVenue.closingTime}`
                    : selectedVenue.closingTime}
                </Text>
              </View>
            </View>

            <View style={styles.popupBody}>
              <View style={styles.popupTitleRow}>
                <Text
                  style={[styles.popupName, { color: colors.foreground }]}
                  numberOfLines={1}
                >
                  {selectedVenue.name}
                </Text>
                <View style={styles.popupRating}>
                  <Feather name="star" size={12} color={colors.accent} />
                  <Text style={[styles.popupRatingText, { color: colors.foreground }]}>
                    {selectedVenue.rating}
                  </Text>
                </View>
              </View>

              <Text style={[styles.popupSuburb, { color: colors.mutedForeground }]}>
                {selectedVenue.suburb} · {selectedVenue.type}
              </Text>

              {selectedVenue.specials.length > 0 ? (
                <View style={[styles.popupSpecial, { backgroundColor: colors.secondary }]}>
                  <Feather name="tag" size={11} color={colors.primary} />
                  <Text
                    style={[styles.popupSpecialText, { color: colors.primary }]}
                    numberOfLines={1}
                  >
                    {selectedVenue.specials[0].title}
                  </Text>
                </View>
              ) : null}

              {selectedVenue.events.length > 0 ? (
                <View style={styles.popupEventRow}>
                  <Feather name="calendar" size={11} color={colors.mutedForeground} />
                  <Text
                    style={[styles.popupEventText, { color: colors.mutedForeground }]}
                    numberOfLines={1}
                  >
                    {selectedVenue.events[0].title} · {selectedVenue.events[0].time}
                  </Text>
                </View>
              ) : null}

              <View style={styles.popupActions}>
                <TouchableOpacity
                  style={[styles.popupCtaPrimary, { backgroundColor: colors.primary }]}
                  activeOpacity={0.85}
                  onPress={() => selectedVenue && router.push(`/venue/${selectedVenue.id}`)}
                >
                  <Text style={[styles.popupCtaPrimaryText, { color: colors.primaryForeground }]}>
                    View listing
                  </Text>
                  <Feather name="arrow-right" size={13} color={colors.primaryForeground} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.popupCtaSecondary, { borderColor: colors.border }]}
                  activeOpacity={0.75}
                  onPress={() => toggleSaved(selectedVenue.id)}
                >
                  <Feather
                    name="bookmark"
                    size={14}
                    color={isSaved(selectedVenue.id) ? colors.primary : colors.mutedForeground}
                  />
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity
              style={styles.popupDismiss}
              onPress={() => setSelectedVenue(null)}
              hitSlop={{ top: 10, left: 10, right: 10, bottom: 10 }}
            >
              <Feather name="x" size={18} color={colors.mutedForeground} />
            </TouchableOpacity>
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    flex: 1,
    position: "relative",
  },
  mapArea: {
    flex: 1,
    position: "relative",
    overflow: "hidden",
  },
  street: {
    position: "absolute",
    backgroundColor: "#d0c4b4",
  },
  suburbLabel: {
    position: "absolute",
  },
  suburbLabelText: {
    color: "#b0a090",
    fontSize: 10,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
    letterSpacing: 0.5,
    textTransform: "uppercase",
  },
  pinWrap: {
    position: "absolute",
  },
  pin: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 12,
    borderWidth: 1.5,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.14,
    shadowRadius: 6,
    elevation: 4,
  },
  pinDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  pinLabel: {
    fontSize: 10,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    maxWidth: 88,
  },
  pinTail: {
    width: 0,
    height: 0,
    borderLeftWidth: 4,
    borderRightWidth: 4,
    borderTopWidth: 5,
    borderLeftColor: "transparent",
    borderRightColor: "transparent",
    alignSelf: "center",
    marginTop: -1,
  },
  topOverlay: {
    position: "absolute",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  locationChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.09,
    shadowRadius: 8,
    elevation: 3,
  },
  locationChipText: {
    fontSize: 12,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  recenterBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.09,
    shadowRadius: 8,
    elevation: 3,
  },
  venueBadge: {
    position: "absolute",
    paddingHorizontal: 11,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
  },
  venueBadgeText: {
    fontSize: 11,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
  },
  bottomPopup: {
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    borderTopWidth: 1,
    borderLeftWidth: 1,
    borderRightWidth: 1,
    paddingTop: 10,
    paddingHorizontal: 16,
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 14,
    elevation: 12,
  },
  popupHandle: {
    width: 36,
    height: 4,
    borderRadius: 2,
    alignSelf: "center",
    marginBottom: 12,
  },
  popupContent: {
    flexDirection: "row",
    gap: 12,
    flex: 1,
  },
  popupImage: {
    width: 86,
    borderRadius: 12,
    justifyContent: "flex-end",
    padding: 7,
  },
  popupOpenBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    paddingHorizontal: 5,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: "flex-start",
  },
  popupOpenDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
  },
  popupOpenText: {
    color: "#ffffff",
    fontSize: 9,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  popupBody: {
    flex: 1,
    gap: 5,
  },
  popupTitleRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    marginRight: 22,
  },
  popupName: {
    fontSize: 16,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    flex: 1,
    marginRight: 6,
  },
  popupRating: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
  },
  popupRatingText: {
    fontSize: 13,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  popupSuburb: {
    fontSize: 12,
    fontFamily: "Inter_400Regular",
    textTransform: "capitalize",
  },
  popupSpecial: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 7,
    paddingVertical: 4,
    borderRadius: 6,
  },
  popupSpecialText: {
    fontSize: 11,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    flex: 1,
  },
  popupEventRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  popupEventText: {
    fontSize: 11,
    fontFamily: "Inter_400Regular",
    flex: 1,
  },
  popupActions: {
    flexDirection: "row",
    gap: 8,
    marginTop: 4,
  },
  popupCtaPrimary: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  popupCtaPrimaryText: {
    fontSize: 13,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  popupCtaSecondary: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  popupDismiss: {
    position: "absolute",
    top: 0,
    right: 0,
  },
  stateOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 20,
  },
  stateText: {
    marginTop: 8,
    fontSize: 13,
    fontFamily: "Inter_500Medium",
  },
  authRequiredCard: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 20,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 9,
    zIndex: 20,
  },
  authRequiredText: {
    fontSize: 12,
    fontFamily: "Inter_500Medium",
  },
});
