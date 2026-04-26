import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useState } from "react";
import {
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { VenueRow } from "@/components/VenueRow";
import { VENUES } from "@/data/mockData";
import { useColors } from "@/hooks/useColors";

const CURRENT_SUBURB = "Fitzroy";

export default function HomeScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  const topInset = Platform.OS === "web" ? 67 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : 0;

  function toggleSave(id: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const suggested = VENUES.filter(
    (v) => v.isOpen && (v.events.length > 0 || v.specials.length > 0)
  );
  const highlights = [...VENUES].sort((a, b) => b.rating - a.rating).slice(0, 6);
  const mealDeals = VENUES.filter((v) => v.mealDeal != null);
  const liveMusic = VENUES.filter(
    (v) =>
      v.features.includes("Live Music") ||
      v.events.some(
        (e) =>
          e.title.toLowerCase().includes("music") ||
          e.title.toLowerCase().includes("dj")
      )
  );
  const trivia = VENUES.filter((v) =>
    v.events.some(
      (e) =>
        e.title.toLowerCase().includes("trivia") ||
        e.title.toLowerCase().includes("quiz")
    )
  );

  const openNowCount = VENUES.filter((v) => v.isOpen).length;
  const eventsCount = VENUES.filter((v) => v.events.length > 0).length;

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

      <VenueRow
        title="Suggested"
        subtitle="Good picks for tonight"
        venues={suggested}
        savedIds={savedIds}
        onSave={toggleSave}
        onSeeAll={() => {}}
      />

      <VenueRow
        title="Highlights"
        subtitle="Trending this week"
        venues={highlights}
        savedIds={savedIds}
        onSave={toggleSave}
        onSeeAll={() => {}}
      />

      <VenueRow
        title="Meal deals nearby"
        subtitle="Parma, burger, steak and more"
        venues={mealDeals}
        savedIds={savedIds}
        onSave={toggleSave}
        onSeeAll={() => {}}
      />

      <VenueRow
        title="Live music"
        subtitle="Playing tonight"
        venues={liveMusic}
        savedIds={savedIds}
        onSave={toggleSave}
        onSeeAll={() => {}}
      />

      <VenueRow
        title="Trivia tonight"
        subtitle="Teams of 2–6"
        venues={trivia}
        savedIds={savedIds}
        onSave={toggleSave}
        onSeeAll={() => {}}
      />
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
});
