import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useRouter } from "expo-router";

import { ActiveFilters, type FilterPill } from "@/components/ActiveFilters";
import { Chip } from "@/components/Chip";
import { EmptyState } from "@/components/EmptyState";
import { SectionHeader } from "@/components/SectionHeader";
import { SuburbSelector } from "@/components/SuburbSelector";
import { VenueCard } from "@/components/VenueCard";
import {
  DISTANCE_OPTIONS,
  DRINK_TYPES,
  MEAL_SPECIALS,
  VENUE_FEATURES,
} from "@/data/mockData";
import { publicApiRequest } from "@/lib/api";
import { mapCardToVenue, type SearchResponse } from "@/lib/mappers";
import { useColors } from "@/hooks/useColors";
import { useSavedVenues } from "@/hooks/useSavedVenues";
import { useAuthSession } from "@/hooks/useAuthSession";

export default function SearchScreen() {
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();

  const topInset = Platform.OS === "web" ? 67 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : 0;

  const [query, setQuery] = useState("");
  const [selectedSuburb, setSelectedSuburb] = useState<string | null>(null);
  const [selectedDrinks, setSelectedDrinks] = useState<Set<string>>(new Set());
  const [selectedFeatures, setSelectedFeatures] = useState<Set<string>>(new Set());
  const [selectedMealSpecials, setSelectedMealSpecials] = useState<Set<string>>(new Set());
  const [openNowOnly, setOpenNowOnly] = useState(false);
  const [distanceKm, setDistanceKm] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [venues, setVenues] = useState<ReturnType<typeof mapCardToVenue>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { savedVenueIds, toggleSaved, authMessage, clearAuthMessage } = useSavedVenues();
  const { isAuthenticated, loading: authLoading } = useAuthSession();

  function toggleDrink(d: string) {
    Haptics.selectionAsync();
    setSelectedDrinks((prev) => {
      const next = new Set(prev);
      if (next.has(d)) next.delete(d);
      else next.add(d);
      return next;
    });
  }

  function toggleFeature(f: string) {
    Haptics.selectionAsync();
    setSelectedFeatures((prev) => {
      const next = new Set(prev);
      if (next.has(f)) next.delete(f);
      else next.add(f);
      return next;
    });
  }

  function toggleMealSpecial(m: string) {
    Haptics.selectionAsync();
    setSelectedMealSpecials((prev) => {
      const next = new Set(prev);
      if (next.has(m)) next.delete(m);
      else next.add(m);
      return next;
    });
  }

  function clearFilters() {
    setSelectedSuburb(null);
    setSelectedDrinks(new Set());
    setSelectedFeatures(new Set());
    setSelectedMealSpecials(new Set());
    setOpenNowOnly(false);
    setDistanceKm(null);
    setQuery("");
  }

  const activeFilterPills = useMemo((): FilterPill[] => {
    const pills: FilterPill[] = [];
    if (selectedSuburb) {
      pills.push({
        key: "suburb",
        label: selectedSuburb,
        category: "location",
        onRemove: () => setSelectedSuburb(null),
      });
    }
    if (distanceKm !== null) {
      pills.push({
        key: "distance",
        label: `Within ${distanceKm} km`,
        category: "location",
        onRemove: () => setDistanceKm(null),
      });
    }
    if (openNowOnly) {
      pills.push({
        key: "open",
        label: "Open now",
        category: "open",
        onRemove: () => setOpenNowOnly(false),
      });
    }
    for (const m of Array.from(selectedMealSpecials)) {
      pills.push({
        key: `meal:${m}`,
        label: m,
        category: "meal",
        onRemove: () => toggleMealSpecial(m),
      });
    }
    for (const d of Array.from(selectedDrinks)) {
      pills.push({
        key: `drink:${d}`,
        label: d,
        category: "preference",
        onRemove: () => toggleDrink(d),
      });
    }
    for (const f of Array.from(selectedFeatures)) {
      pills.push({
        key: `feat:${f}`,
        label: f,
        category: "preference",
        onRemove: () => toggleFeature(f),
      });
    }
    return pills;
  }, [selectedSuburb, distanceKm, openNowOnly, selectedMealSpecials, selectedDrinks, selectedFeatures]);

  const searchQuery = useMemo(
    () => ({
      suburb: selectedSuburb ?? undefined,
      open_now: openNowOnly ? true : undefined,
      radius_m: distanceKm ? distanceKm * 1000 : undefined,
      meal_specials: Array.from(selectedMealSpecials),
      drink_types: Array.from(selectedDrinks),
      venue_features: Array.from(selectedFeatures),
    }),
    [distanceKm, openNowOnly, selectedDrinks, selectedFeatures, selectedMealSpecials, selectedSuburb]
  );

  useEffect(() => {
    let cancelled = false;
    async function loadSearch() {
      setLoading(true);
      setError(null);
      try {
        const response = await publicApiRequest<SearchResponse>("/api/v1/search/venues", {
          query: searchQuery,
        });
        if (cancelled) return;
        setVenues((response.data.venues ?? []).map(mapCardToVenue));
      } catch {
        if (cancelled) return;
        setVenues([]);
        setError("Could not load search results.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadSearch();
    return () => {
      cancelled = true;
    };
  }, [searchQuery]);

  const results = useMemo(() => venues, [venues]);

  const activeFilterCount = activeFilterPills.length;

  return (
    <View style={[styles.outer, { backgroundColor: colors.background }]}>
      <View
        style={[
          styles.topBar,
          {
            paddingTop: topInset + 10,
            backgroundColor: colors.background,
            borderBottomColor: colors.border,
          },
        ]}
      >
        <View style={[styles.searchBar, { backgroundColor: colors.muted, borderColor: colors.border }]}>
          <Feather name="search" size={16} color={colors.mutedForeground} />
          <TextInput
            style={[styles.searchInput, { color: colors.foreground }]}
            placeholder="Search pubs and bars..."
            placeholderTextColor={colors.mutedForeground}
            value={query}
            onChangeText={setQuery}
            returnKeyType="search"
          />
          {query.length > 0 ? (
            <TouchableOpacity
              onPress={() => setQuery("")}
              hitSlop={{ top: 8, left: 8, right: 8, bottom: 8 }}
            >
              <Feather name="x" size={15} color={colors.mutedForeground} />
            </TouchableOpacity>
          ) : null}
        </View>

        <TouchableOpacity
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            setShowFilters(!showFilters);
          }}
          style={[
            styles.filterBtn,
            {
              backgroundColor:
                activeFilterCount > 0
                  ? colors.primary
                  : showFilters
                  ? colors.muted
                  : colors.muted,
              borderColor:
                showFilters && activeFilterCount === 0 ? colors.border : "transparent",
            },
          ]}
        >
          <Feather
            name="sliders"
            size={17}
            color={activeFilterCount > 0 ? colors.primaryForeground : colors.foreground}
          />
          {activeFilterCount > 0 ? (
            <View style={[styles.filterBadge, { backgroundColor: colors.primaryForeground }]}>
              <Text style={[styles.filterBadgeText, { color: colors.primary }]}>
                {activeFilterCount}
              </Text>
            </View>
          ) : null}
        </TouchableOpacity>
      </View>

      <ActiveFilters
        pills={activeFilterPills}
        onClearAll={activeFilterCount > 0 ? clearFilters : undefined}
      />

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
          testID="search-auth-required-cta"
        >
          <Text style={[styles.authRequiredText, { color: colors.primary }]}>{authMessage}</Text>
        </TouchableOpacity>
      ) : null}

      {showFilters ? (
        <ScrollView
          style={[styles.filtersPanel, { borderBottomColor: colors.border }]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.filterGroup}>
            <View style={styles.filterGroupHeader}>
              <Feather name="navigation" size={13} color={colors.primary} />
              <Text style={[styles.filterGroupLabel, { color: colors.foreground }]}>
                Location
              </Text>
            </View>

            <View style={[styles.filterGroupBody, { backgroundColor: colors.card, borderColor: colors.border }]}>
              <View style={[styles.filterRow, { borderBottomColor: colors.border }]}>
                <View style={styles.filterRowLeft}>
                  <Text style={[styles.filterInlineLabel, { color: colors.foreground }]}>
                    Suburb
                  </Text>
                </View>
                <SuburbSelector selected={selectedSuburb} onChange={setSelectedSuburb} />
              </View>

              <View style={[styles.filterRow, { borderBottomColor: colors.border }]}>
                <Text style={[styles.filterInlineLabel, { color: colors.foreground }]}>
                  Distance
                </Text>
                <View style={styles.distanceRow}>
                  {DISTANCE_OPTIONS.map((km) => (
                    <TouchableOpacity
                      key={km}
                      onPress={() => {
                        Haptics.selectionAsync();
                        setDistanceKm(distanceKm === km ? null : km);
                      }}
                      style={[
                        styles.distanceBtn,
                        {
                          backgroundColor:
                            distanceKm === km ? colors.primary : colors.muted,
                          borderColor:
                            distanceKm === km ? colors.primary : colors.border,
                        },
                      ]}
                    >
                      <Text
                        style={[
                          styles.distanceBtnText,
                          {
                            color:
                              distanceKm === km
                                ? colors.primaryForeground
                                : colors.mutedForeground,
                          },
                        ]}
                      >
                        {km} km
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <View style={styles.filterRowLast}>
                <Text style={[styles.filterInlineLabel, { color: colors.foreground }]}>
                  Open now
                </Text>
                <TouchableOpacity
                  onPress={() => {
                    Haptics.selectionAsync();
                    setOpenNowOnly(!openNowOnly);
                  }}
                  style={[
                    styles.toggle,
                    {
                      backgroundColor: openNowOnly ? colors.primary : colors.muted,
                      borderColor: colors.border,
                    },
                  ]}
                >
                  <View
                    style={[
                      styles.toggleThumb,
                      { transform: [{ translateX: openNowOnly ? 20 : 2 }] },
                    ]}
                  />
                </TouchableOpacity>
              </View>
            </View>
          </View>

          <View style={styles.filterGroup}>
            <View style={styles.filterGroupHeader}>
              <Feather name="coffee" size={13} color={colors.accent} />
              <Text style={[styles.filterGroupLabel, { color: colors.foreground }]}>
                Meal specials
              </Text>
              <View style={[styles.mealBadge, { backgroundColor: colors.accent }]}>
                <Text style={styles.mealBadgeText}>Tonight</Text>
              </View>
            </View>
            <View
              style={[
                styles.filterGroupBody,
                styles.filterGroupBodyWrap,
                { backgroundColor: colors.card, borderColor: colors.border },
              ]}
            >
              {MEAL_SPECIALS.map((m) => (
                <Chip
                  key={m}
                  label={m}
                  selected={selectedMealSpecials.has(m)}
                  onPress={() => toggleMealSpecial(m)}
                  size="sm"
                />
              ))}
            </View>
          </View>

          <View style={styles.filterGroup}>
            <View style={styles.filterGroupHeader}>
              <Feather name="droplet" size={13} color={colors.primary} />
              <Text style={[styles.filterGroupLabel, { color: colors.foreground }]}>
                Drink type
              </Text>
            </View>
            <View
              style={[
                styles.filterGroupBody,
                styles.filterGroupBodyWrap,
                { backgroundColor: colors.card, borderColor: colors.border },
              ]}
            >
              {DRINK_TYPES.map((d) => (
                <Chip
                  key={d}
                  label={d}
                  selected={selectedDrinks.has(d)}
                  onPress={() => toggleDrink(d)}
                  size="sm"
                />
              ))}
            </View>
          </View>

          <View style={[styles.filterGroup, styles.filterGroupLast]}>
            <View style={styles.filterGroupHeader}>
              <Feather name="star" size={13} color={colors.primary} />
              <Text style={[styles.filterGroupLabel, { color: colors.foreground }]}>
                Venue features
              </Text>
            </View>
            <View
              style={[
                styles.filterGroupBody,
                styles.filterGroupBodyWrap,
                { backgroundColor: colors.card, borderColor: colors.border },
              ]}
            >
              {VENUE_FEATURES.map((f) => (
                <Chip
                  key={f}
                  label={f}
                  selected={selectedFeatures.has(f)}
                  onPress={() => toggleFeature(f)}
                  size="sm"
                />
              ))}
            </View>
          </View>
        </ScrollView>
      ) : null}

      <ScrollView
        style={styles.results}
        contentContainerStyle={[styles.resultsContent, { paddingBottom: bottomInset + 90 }]}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <SectionHeader
          title={loading ? "Loading venues" : results.length > 0 ? `${results.length} venues` : "No results"}
          subtitle={
            activeFilterCount > 0
              ? `${activeFilterCount} filter${activeFilterCount !== 1 ? "s" : ""} active`
              : query
              ? "Text search is deferred; filters are live"
              : "All Melbourne"
          }
        />

        <TouchableOpacity
          style={[
            styles.suggestVenueCta,
            { backgroundColor: colors.card, borderColor: colors.border, opacity: authLoading ? 0.6 : 1 },
          ]}
          onPress={() => {
            if (authLoading) return;
            router.push((isAuthenticated ? "/suggest-venue" : "/auth") as never);
          }}
          disabled={authLoading}
          accessibilityRole="button"
          accessibilityLabel="Suggest a missing venue"
          testID="search-suggest-venue-entry"
        >
          <Feather name="plus-circle" size={14} color={colors.primary} />
          <Text style={[styles.suggestVenueCtaText, { color: colors.primary }]}>
            Can't find a venue? Suggest one
          </Text>
        </TouchableOpacity>

        {query ? (
          <Text style={[styles.queryDeferred, { color: colors.mutedForeground }]}>
            Text search is not available on the backend yet. Filters are live.
          </Text>
        ) : null}

        {loading ? (
          <View style={styles.loadingWrap}>
            <ActivityIndicator color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.mutedForeground }]}>Loading results...</Text>
          </View>
        ) : null}

        {!loading && error ? (
          <EmptyState
            icon="alert-circle"
            title="Search unavailable"
            subtitle={error}
            actionLabel="Try again"
            onAction={() => {
              setLoading(true);
              setError(null);
              publicApiRequest<SearchResponse>("/api/v1/search/venues", { query: searchQuery })
                .then((response) => setVenues((response.data.venues ?? []).map(mapCardToVenue)))
                .catch(() => setError("Could not load search results."))
                .finally(() => setLoading(false));
            }}
          />
        ) : null}

        {!loading && !error && results.length === 0 ? (
          <EmptyState
            icon="search"
            title="No venues found"
            subtitle="Try adjusting your filters or search term"
            actionLabel="Clear filters"
            onAction={clearFilters}
          />
        ) : (
          !loading &&
          !error &&
          results.map((venue) => (
            <View key={venue.id} style={styles.cardWrap}>
              <VenueCard
                venue={{ ...venue, isSaved: savedVenueIds.has(venue.id) }}
                onPress={() => router.push(`/venue/${venue.id}`)}
                onSave={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  toggleSaved(venue.id);
                }}
              />
            </View>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    flex: 1,
  },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  searchBar: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    paddingHorizontal: 13,
    paddingVertical: 10,
    borderRadius: 13,
    borderWidth: 1,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    fontFamily: "Inter_400Regular",
    padding: 0,
  },
  filterBtn: {
    width: 42,
    height: 42,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  filterBadge: {
    position: "absolute",
    top: 5,
    right: 5,
    width: 15,
    height: 15,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  filterBadgeText: {
    fontSize: 9,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
  },
  filtersPanel: {
    maxHeight: 360,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  filterGroup: {
    paddingHorizontal: 16,
    paddingTop: 14,
  },
  filterGroupLast: {
    paddingBottom: 14,
  },
  filterGroupHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 8,
  },
  filterGroupLabel: {
    fontSize: 13,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  mealBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  mealBadgeText: {
    color: "#ffffff",
    fontSize: 10,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  filterGroupBody: {
    borderRadius: 12,
    borderWidth: 1,
    overflow: "hidden",
  },
  filterGroupBodyWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    padding: 12,
  },
  filterRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderBottomWidth: StyleSheet.hairlineWidth,
    gap: 12,
  },
  filterRowLast: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 11,
  },
  filterRowLeft: {
    flex: 1,
  },
  filterInlineLabel: {
    fontSize: 14,
    fontFamily: "Inter_400Regular",
  },
  distanceRow: {
    flexDirection: "row",
    gap: 5,
  },
  distanceBtn: {
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: "center",
  },
  distanceBtnText: {
    fontSize: 12,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
  },
  toggle: {
    width: 44,
    height: 26,
    borderRadius: 13,
    justifyContent: "center",
    borderWidth: 1,
  },
  toggleThumb: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: "#ffffff",
    shadowColor: "#000",
    shadowOpacity: 0.18,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
  },
  results: {
    flex: 1,
  },
  resultsContent: {
    paddingTop: 6,
  },
  cardWrap: {
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  loadingWrap: {
    alignItems: "center",
    gap: 8,
    paddingVertical: 24,
  },
  loadingText: {
    fontSize: 13,
    fontFamily: "Inter_400Regular",
  },
  queryDeferred: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    fontSize: 12,
    fontFamily: "Inter_400Regular",
  },
  authRequiredCard: {
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  authRequiredText: {
    fontSize: 12,
    fontFamily: "Inter_500Medium",
  },
  suggestVenueCta: {
    marginHorizontal: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 9,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
  suggestVenueCtaText: {
    fontSize: 13,
    fontFamily: "Inter_600SemiBold",
  },
});
