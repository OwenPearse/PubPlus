import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";

import { EmptyState } from "@/components/EmptyState";
import { VenueRow } from "@/components/VenueRow";
import { publicApiRequest } from "@/lib/api";
import { mapCardToVenue, type HomeResponse } from "@/lib/mappers";
import { useColors } from "@/hooks/useColors";
import { useSavedVenues } from "@/hooks/useSavedVenues";

const CURRENT_SUBURB = "Fitzroy";

export default function HomeScreen() {
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const [sections, setSections] = useState<HomeResponse["data"]["sections"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { savedVenueIds, toggleSaved, authMessage, clearAuthMessage } = useSavedVenues();

  const topInset = Platform.OS === "web" ? 67 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : 0;

  function toggleSave(id: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    toggleSaved(id);
  }

  useEffect(() => {
    let cancelled = false;
    async function loadHome() {
      setLoading(true);
      setError(null);
      try {
        const response = await publicApiRequest<HomeResponse>("/api/v1/home");
        if (cancelled) return;
        setSections(response.data.sections ?? []);
      } catch {
        if (cancelled) return;
        setSections([]);
        setError("Could not load home feed.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadHome();
    return () => {
      cancelled = true;
    };
  }, []);

  const mappedSections = useMemo(
    () =>
      sections.map((section) => ({
        ...section,
        venues: section.venues.map(mapCardToVenue),
      })),
    [sections]
  );

  const allVenues = useMemo(() => mappedSections.flatMap((section) => section.venues), [mappedSections]);
  const openNowCount = allVenues.filter((venue) => venue.isOpen).length;
  const eventsCount = allVenues.filter((venue) => venue.events.length > 0).length;

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={[
        styles.content,
        { paddingTop: topInset + 8, paddingBottom: bottomInset + 90 },
      ]}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <View>
          <Text style={[styles.greeting, { color: colors.mutedForeground }]}>
            Good evening
          </Text>
          <TouchableOpacity style={styles.locationRow}>
            <Text style={[styles.suburb, { color: colors.foreground }]}>
              {CURRENT_SUBURB}
            </Text>
            <Feather name="chevron-down" size={17} color={colors.primary} />
          </TouchableOpacity>
        </View>
        <TouchableOpacity style={[styles.notifBtn, { backgroundColor: colors.muted }]}>
          <Feather name="bell" size={19} color={colors.foreground} />
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        activeOpacity={0.82}
        style={[styles.tonightBanner, { backgroundColor: colors.primary }]}
      >
        <View>
          <Text style={[styles.bannerLabel, { color: "rgba(255,255,255,0.72)" }]}>
            Tonight near you
          </Text>
          <Text style={[styles.bannerTitle, { color: "#ffffff" }]}>
            {openNowCount} pubs open · {eventsCount} events on
          </Text>
        </View>
        <View style={styles.bannerRight}>
          <Feather name="map" size={22} color="rgba(255,255,255,0.55)" />
          <View style={[styles.bannerArrow, { backgroundColor: "rgba(255,255,255,0.15)" }]}>
            <Feather name="arrow-right" size={14} color="rgba(255,255,255,0.85)" />
          </View>
        </View>
      </TouchableOpacity>

      {!loading && authMessage ? (
        <TouchableOpacity
          style={[styles.authRequiredCard, { backgroundColor: colors.secondary }]}
          onPress={() => {
            clearAuthMessage();
            router.push("/auth" as never);
          }}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel="Sign in to save venues"
          testID="home-auth-required-cta"
        >
          <Text style={[styles.authRequiredText, { color: colors.primary }]}>{authMessage}</Text>
        </TouchableOpacity>
      ) : null}

      {loading ? (
        <View style={styles.stateWrap}>
          <ActivityIndicator color={colors.primary} />
          <Text style={[styles.stateText, { color: colors.mutedForeground }]}>Loading venues...</Text>
        </View>
      ) : null}

      {!loading && error ? (
        <EmptyState
          icon="alert-circle"
          title="Home unavailable"
          subtitle={error}
          actionLabel="Try again"
          onAction={() => {
            setLoading(true);
            setError(null);
            publicApiRequest<HomeResponse>("/api/v1/home")
              .then((response) => setSections(response.data.sections ?? []))
              .catch(() => setError("Could not load home feed."))
              .finally(() => setLoading(false));
          }}
        />
      ) : null}

      {!loading && !error && mappedSections.length === 0 ? (
        <EmptyState
          icon="home"
          title="No home sections yet"
          subtitle="Check back soon for nearby venues and tonight highlights."
        />
      ) : null}

      {!loading && !error
        ? mappedSections.map((section) => (
            <VenueRow
              key={section.id}
              title={section.title}
              subtitle={section.id === "open_now" ? "Currently open" : undefined}
              venues={section.venues}
              savedIds={savedVenueIds}
              onSave={toggleSave}
              onSeeAll={() => {}}
            />
          ))
        : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 0,
  },
  header: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    marginBottom: 18,
  },
  greeting: {
    fontSize: 13,
    fontFamily: "Inter_400Regular",
    marginBottom: 2,
  },
  locationRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  suburb: {
    fontSize: 24,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    letterSpacing: -0.5,
  },
  notifBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 6,
  },
  tonightBanner: {
    marginHorizontal: 16,
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 22,
  },
  bannerLabel: {
    fontSize: 12,
    fontFamily: "Inter_500Medium",
    marginBottom: 3,
  },
  bannerTitle: {
    fontSize: 15,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
  },
  bannerRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  bannerArrow: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  stateWrap: {
    alignItems: "center",
    gap: 8,
    paddingVertical: 24,
  },
  stateText: {
    fontSize: 13,
    fontFamily: "Inter_400Regular",
  },
  authRequiredCard: {
    marginHorizontal: 16,
    marginBottom: 6,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  authRequiredText: {
    fontSize: 12,
    fontFamily: "Inter_500Medium",
  },
});
