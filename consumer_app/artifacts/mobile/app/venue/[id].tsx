import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { useLocalSearchParams, useRouter } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Linking,
  Platform,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { EmptyState } from "@/components/EmptyState";
import { useColors } from "@/hooks/useColors";
import { useSavedVenues } from "@/hooks/useSavedVenues";
import { useAuthSession } from "@/hooks/useAuthSession";
import { publicApiRequest } from "@/lib/api";
import { mapVenueDetailResponse, type VenueDetailResponse } from "@/lib/mappers";
import type { Venue } from "@/data/mockData";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] as const;

export default function VenueDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();

  const topInset = Platform.OS === "web" ? 0 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : insets.bottom;

  const [venue, setVenue] = useState<Venue | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isSaved, toggleSaved, authMessage, clearAuthMessage } = useSavedVenues();
  const { isAuthenticated } = useAuthSession();

  useEffect(() => {
    let cancelled = false;
    async function loadVenue() {
      if (!id) return;
      setLoading(true);
      setError(null);
      try {
        const response = await publicApiRequest<VenueDetailResponse>(`/api/v1/venues/${id}`);
        if (cancelled) return;
        const mapped = mapVenueDetailResponse(response);
        setVenue(mapped);
      } catch {
        if (cancelled) return;
        setVenue(null);
        setError("Could not load this venue.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadVenue();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <View style={[styles.notFound, { backgroundColor: colors.background }]}>
        <ActivityIndicator color={colors.primary} />
        <Text style={[styles.notFoundText, { color: colors.mutedForeground }]}>Loading venue...</Text>
      </View>
    );
  }

  if (!venue && error) {
    return (
      <View style={[styles.notFound, { backgroundColor: colors.background }]}>
        <EmptyState
          icon="alert-circle"
          title="Venue unavailable"
          subtitle={error}
          actionLabel="Go back"
          onAction={() => router.back()}
        />
      </View>
    );
  }

  if (!venue) {
    return (
      <View style={[styles.notFound, { backgroundColor: colors.background }]}>
        <Text style={[styles.notFoundText, { color: colors.mutedForeground }]}>
          Venue not found
        </Text>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={[styles.backLink, { color: colors.primary }]}>Go back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  function handleCall() {
    if (venue?.phone) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      Linking.openURL(`tel:${venue.phone.replace(/\s/g, "")}`);
    }
  }

  function handleWebsite() {
    if (venue?.website) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      const url = venue.website.startsWith("http://") || venue.website.startsWith("https://")
        ? venue.website
        : `https://${venue.website}`;
      Linking.openURL(url);
    }
  }

  function handleDirections() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const query = encodeURIComponent(venue?.address ?? "");
    Linking.openURL(`https://maps.google.com/?q=${query}`);
  }

  async function handleShare() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await Share.share({
        message: `Check out ${venue?.name} at ${venue?.address} on PubPlus`,
      });
    } catch {}
  }

  function toggleSave() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (!venue) return;
    toggleSaved(venue.id);
  }

  return (
    <View style={[styles.outer, { backgroundColor: colors.background }]}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={{ paddingBottom: bottomInset + 32 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero */}
        <View style={[styles.hero, { backgroundColor: venue.imageColor }]}>
          <View style={[styles.heroOverlay]} />

          <View style={[styles.heroTop, { paddingTop: topInset + 12 }]}>
            <TouchableOpacity
              style={[styles.iconBtn, { backgroundColor: "rgba(0,0,0,0.28)" }]}
              onPress={() => router.back()}
              hitSlop={{ top: 8, left: 8, right: 8, bottom: 8 }}
            >
              <Feather name="arrow-left" size={20} color="#ffffff" />
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.iconBtn,
                {
                  backgroundColor: isSaved(venue.id)
                    ? "rgba(194,124,0,0.88)"
                    : "rgba(0,0,0,0.28)",
                },
              ]}
              onPress={toggleSave}
              hitSlop={{ top: 8, left: 8, right: 8, bottom: 8 }}
            >
              <Feather name="bookmark" size={20} color="#ffffff" />
            </TouchableOpacity>
          </View>

          <View style={styles.heroBottom}>
            <View style={[styles.typeBadge, { backgroundColor: "rgba(0,0,0,0.40)" }]}>
              <Text style={styles.typeBadgeText}>{venue.type}</Text>
            </View>
            <Text style={styles.heroName}>{venue.name}</Text>
            <View style={styles.heroMeta}>
              <View style={styles.heroMetaItem}>
                <Feather name="map-pin" size={13} color="rgba(255,255,255,0.85)" />
                <Text style={styles.heroMetaText}>{venue.suburb}</Text>
              </View>
              <View style={styles.heroMetaDot} />
              <View style={styles.heroMetaItem}>
                <Feather name="star" size={13} color="#f5c842" />
                <Text style={styles.heroMetaText}>
                  {venue.rating} ({venue.reviewCount})
                </Text>
              </View>
            </View>
          </View>
        </View>

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
            testID="venue-auth-required-cta"
          >
            <Text style={[styles.authRequiredText, { color: colors.primary }]}>{authMessage}</Text>
          </TouchableOpacity>
        ) : null}

        <View style={[styles.submissionEntryWrap, { borderBottomColor: colors.border }]}>
          <TouchableOpacity
            style={[styles.submissionEntryBtn, { backgroundColor: colors.card, borderColor: colors.border }]}
            onPress={() => {
              if (!isAuthenticated) {
                router.push("/auth" as never);
                return;
              }
              router.push(
                {
                  pathname: "/venue/[id]/correction",
                  params: { id: venue.id, name: venue.name },
                } as never
              );
            }}
            accessibilityRole="button"
            accessibilityLabel="Suggest an edit for this venue"
            testID="venue-correction-entry"
          >
            <Feather name="edit-2" size={14} color={colors.primary} />
            <Text style={[styles.submissionEntryText, { color: colors.primary }]}>Suggest an edit</Text>
          </TouchableOpacity>
        </View>

        {/* Open status bar */}
        <View
          style={[
            styles.statusBar,
            {
              backgroundColor: venue.isOpen
                ? "rgba(30,110,58,0.1)"
                : "rgba(150,45,30,0.08)",
              borderBottomColor: colors.border,
            },
          ]}
        >
          <View
            style={[
              styles.statusDot,
              { backgroundColor: venue.isOpen ? "#3aaf60" : "#e05040" },
            ]}
          />
          <Text
            style={[
              styles.statusText,
              { color: venue.isOpen ? "#237842" : "#b03020" },
            ]}
          >
            {venue.isOpen ? `Open now · Closes ${venue.closingTime}` : venue.closingTime}
          </Text>
        </View>

        {/* Quick actions */}
        <View style={[styles.actionsRow, { borderBottomColor: colors.border }]}>
          {venue.phone ? (
            <TouchableOpacity style={styles.actionItem} onPress={handleCall}>
              <View style={[styles.actionIcon, { backgroundColor: colors.muted }]}>
                <Feather name="phone" size={18} color={colors.primary} />
              </View>
              <Text style={[styles.actionLabel, { color: colors.mutedForeground }]}>Call</Text>
            </TouchableOpacity>
          ) : null}
          <TouchableOpacity style={styles.actionItem} onPress={handleDirections}>
            <View style={[styles.actionIcon, { backgroundColor: colors.muted }]}>
              <Feather name="navigation" size={18} color={colors.primary} />
            </View>
            <Text style={[styles.actionLabel, { color: colors.mutedForeground }]}>
              Directions
            </Text>
          </TouchableOpacity>
          {venue.website ? (
            <TouchableOpacity style={styles.actionItem} onPress={handleWebsite}>
              <View style={[styles.actionIcon, { backgroundColor: colors.muted }]}>
                <Feather name="globe" size={18} color={colors.primary} />
              </View>
              <Text style={[styles.actionLabel, { color: colors.mutedForeground }]}>
                Website
              </Text>
            </TouchableOpacity>
          ) : null}
          <TouchableOpacity style={styles.actionItem} onPress={handleShare}>
            <View style={[styles.actionIcon, { backgroundColor: colors.muted }]}>
              <Feather name="share-2" size={18} color={colors.primary} />
            </View>
            <Text style={[styles.actionLabel, { color: colors.mutedForeground }]}>Share</Text>
          </TouchableOpacity>
        </View>

        {/* About */}
        <View style={[styles.section, { borderBottomColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.foreground }]}>About</Text>
          <Text style={[styles.description, { color: colors.mutedForeground }]}>
            {venue.description}
          </Text>
          {venue.features.length > 0 ? (
            <View style={styles.featureChips}>
              {venue.features.map((f) => (
                <View key={f} style={[styles.featureChip, { backgroundColor: colors.muted, borderColor: colors.border }]}>
                  <Text style={[styles.featureChipText, { color: colors.foreground }]}>{f}</Text>
                </View>
              ))}
            </View>
          ) : null}
        </View>

        {/* Specials */}
        {venue.specials.length > 0 ? (
          <View style={[styles.section, { borderBottomColor: colors.border }]}>
            <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
              Specials
            </Text>
            {venue.specials.map((s) => (
              <View
                key={s.id}
                style={[styles.specialCard, { backgroundColor: colors.secondary, borderColor: colors.border }]}
              >
                <View style={styles.specialCardHeader}>
                  <Feather name="tag" size={14} color={colors.primary} />
                  <Text style={[styles.specialTitle, { color: colors.primary }]}>
                    {s.title}
                  </Text>
                </View>
                <Text style={[styles.specialDesc, { color: colors.foreground }]}>
                  {s.description}
                </Text>
                <View style={styles.specialFooter}>
                  <Feather name="clock" size={11} color={colors.mutedForeground} />
                  <Text style={[styles.specialValid, { color: colors.mutedForeground }]}>
                    {s.validUntil}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        ) : null}

        {/* Happy Hour */}
        {venue.happyHour ? (
          <View style={[styles.section, { borderBottomColor: colors.border }]}>
            <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
              Happy Hour
            </Text>
            <View
              style={[
                styles.happyHourCard,
                { backgroundColor: "rgba(30,110,58,0.08)", borderColor: "rgba(35,120,65,0.25)" },
              ]}
            >
              <View style={styles.happyHourHeader}>
                <Feather name="sun" size={16} color="#237842" />
                <Text style={[styles.happyHourTime, { color: "#237842" }]}>
                  {venue.happyHour.days} · {venue.happyHour.times}
                </Text>
              </View>
              <Text style={[styles.happyHourDeal, { color: colors.foreground }]}>
                {venue.happyHour.deal}
              </Text>
            </View>
          </View>
        ) : null}

        {/* Opening Hours */}
        <View style={[styles.section, { borderBottomColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
            Opening Hours
          </Text>
          <View
            style={[
              styles.hoursTable,
              { backgroundColor: colors.card, borderColor: colors.border },
            ]}
          >
            {DAYS.map((day, i) => {
              const hours = venue.openingHours[day];
              const isClosed = hours === "Closed";
              const isToday = i === new Date().getDay() - 1;
              return (
                <View
                  key={day}
                  style={[
                    styles.hoursRow,
                    i < DAYS.length - 1 && { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
                    isToday && { backgroundColor: colors.secondary },
                  ]}
                >
                  <View style={styles.hoursDay}>
                    {isToday ? (
                      <View style={[styles.todayDot, { backgroundColor: colors.primary }]} />
                    ) : null}
                    <Text
                      style={[
                        styles.hoursDayText,
                        { color: isToday ? colors.primary : colors.foreground },
                        isToday && styles.hoursDayToday,
                      ]}
                    >
                      {day}
                    </Text>
                    {isToday ? (
                      <Text style={[styles.todayLabel, { color: colors.primary }]}>today</Text>
                    ) : null}
                  </View>
                  <Text
                    style={[
                      styles.hoursTime,
                      { color: isClosed ? colors.mutedForeground : colors.foreground },
                      isClosed && styles.hoursTimeClosed,
                    ]}
                  >
                    {hours}
                  </Text>
                </View>
              );
            })}
          </View>
        </View>

        {/* Events */}
        {venue.events.length > 0 ? (
          <View style={[styles.section, { borderBottomColor: colors.border }]}>
            <Text style={[styles.sectionTitle, { color: colors.foreground }]}>Events</Text>
            {venue.events.map((ev) => (
              <View
                key={ev.id}
                style={[
                  styles.eventCard,
                  { backgroundColor: colors.card, borderColor: colors.border },
                ]}
              >
                <View style={styles.eventHeader}>
                  <View>
                    <Text style={[styles.eventTitle, { color: colors.foreground }]}>
                      {ev.title}
                    </Text>
                    <View style={styles.eventMeta}>
                      <Feather name="calendar" size={12} color={colors.mutedForeground} />
                      <Text style={[styles.eventMetaText, { color: colors.mutedForeground }]}>
                        {ev.date} · {ev.time}
                      </Text>
                    </View>
                  </View>
                  <View style={[styles.eventTimeBadge, { backgroundColor: colors.primary }]}>
                    <Text style={[styles.eventTimeBadgeText, { color: colors.primaryForeground }]}>
                      {ev.time}
                    </Text>
                  </View>
                </View>
                {ev.description ? (
                  <Text style={[styles.eventDesc, { color: colors.mutedForeground }]}>
                    {ev.description}
                  </Text>
                ) : null}
              </View>
            ))}
          </View>
        ) : null}

        {/* On Tap */}
        {venue.tapBeers.length > 0 ? (
          <View style={[styles.section, { borderBottomColor: colors.border }]}>
            <Text style={[styles.sectionTitle, { color: colors.foreground }]}>On Tap</Text>
            <View style={styles.tapGrid}>
              {venue.tapBeers.map((beer, i) => (
                <View
                  key={i}
                  style={[styles.tapTag, { backgroundColor: colors.muted, borderColor: colors.border }]}
                >
                  <Feather name="droplet" size={11} color={colors.mutedForeground} />
                  <Text style={[styles.tapTagText, { color: colors.foreground }]}>{beer}</Text>
                </View>
              ))}
            </View>
          </View>
        ) : null}

        {/* Menu */}
        {venue.menuItems && venue.menuItems.length > 0 ? (
          <View style={[styles.section, { borderBottomColor: colors.border }]}>
            <Text style={[styles.sectionTitle, { color: colors.foreground }]}>Menu</Text>
            {venue.menuItems.map((category) => (
              <View key={category.category} style={styles.menuCategory}>
                <Text style={[styles.menuCategoryTitle, { color: colors.mutedForeground }]}>
                  {category.category}
                </Text>
                <View
                  style={[
                    styles.menuItems,
                    { backgroundColor: colors.card, borderColor: colors.border },
                  ]}
                >
                  {category.items.map((item, i) => (
                    <View
                      key={i}
                      style={[
                        styles.menuItem,
                        i < category.items.length - 1 && {
                          borderBottomWidth: StyleSheet.hairlineWidth,
                          borderBottomColor: colors.border,
                        },
                      ]}
                    >
                      <View style={styles.menuItemLeft}>
                        <Text style={[styles.menuItemName, { color: colors.foreground }]}>
                          {item.name}
                        </Text>
                        {item.description ? (
                          <Text
                            style={[styles.menuItemDesc, { color: colors.mutedForeground }]}
                          >
                            {item.description}
                          </Text>
                        ) : null}
                      </View>
                      {item.price ? (
                        <Text style={[styles.menuItemPrice, { color: colors.primary }]}>
                          {item.price}
                        </Text>
                      ) : null}
                    </View>
                  ))}
                </View>
              </View>
            ))}
          </View>
        ) : null}

        {/* Contact */}
        <View style={[styles.section, { borderBottomColor: colors.border }]}>
          <Text style={[styles.sectionTitle, { color: colors.foreground }]}>Contact</Text>
          <View
            style={[
              styles.contactList,
              { backgroundColor: colors.card, borderColor: colors.border },
            ]}
          >
            <View style={[styles.contactRow, { borderBottomColor: colors.border }]}>
              <Feather name="map-pin" size={15} color={colors.primary} />
              <Text style={[styles.contactText, { color: colors.foreground }]}>
                {venue.address}
              </Text>
            </View>
            {venue.phone ? (
              <TouchableOpacity
                style={[styles.contactRow, { borderBottomColor: colors.border }]}
                onPress={handleCall}
              >
                <Feather name="phone" size={15} color={colors.primary} />
                <Text style={[styles.contactText, { color: colors.foreground }]}>
                  {venue.phone}
                </Text>
                <Feather name="chevron-right" size={14} color={colors.mutedForeground} />
              </TouchableOpacity>
            ) : null}
            {venue.website ? (
              <TouchableOpacity style={styles.contactRowLast} onPress={handleWebsite}>
                <Feather name="globe" size={15} color={colors.primary} />
                <Text style={[styles.contactText, { color: colors.foreground }]}>
                  {venue.website}
                </Text>
                <Feather name="chevron-right" size={14} color={colors.mutedForeground} />
              </TouchableOpacity>
            ) : null}
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  notFound: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
  },
  notFoundText: {
    fontSize: 16,
    fontFamily: "Inter_400Regular",
  },
  backLink: {
    fontSize: 15,
    fontFamily: "Inter_600SemiBold",
    fontWeight: "600",
  },

  // Hero
  hero: {
    height: 240,
    justifyContent: "space-between",
  },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.28)",
  },
  heroTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 16,
  },
  iconBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: "center",
    justifyContent: "center",
  },
  heroBottom: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 6,
  },
  typeBadge: {
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  typeBadgeText: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    textTransform: "capitalize",
  },
  heroName: {
    fontSize: 26,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    color: "#ffffff",
    letterSpacing: -0.5,
  },
  heroMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  heroMetaItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  heroMetaText: {
    color: "rgba(255,255,255,0.88)",
    fontSize: 13,
    fontFamily: "Inter_400Regular",
  },
  heroMetaDot: {
    width: 3,
    height: 3,
    borderRadius: 2,
    backgroundColor: "rgba(255,255,255,0.5)",
  },

  // Status bar
  statusBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 11,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 13,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },

  // Quick actions
  actionsRow: {
    flexDirection: "row",
    paddingVertical: 18,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    gap: 4,
  },
  actionItem: {
    flex: 1,
    alignItems: "center",
    gap: 6,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
  },
  actionLabel: {
    fontSize: 11,
    fontFamily: "Inter_500Medium",
    fontWeight: "500",
  },

  // Sections
  section: {
    paddingHorizontal: 16,
    paddingVertical: 20,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    marginBottom: 12,
    letterSpacing: -0.2,
  },

  // About
  description: {
    fontSize: 14,
    fontFamily: "Inter_400Regular",
    lineHeight: 22,
    marginBottom: 12,
  },
  featureChips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  featureChip: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
  },
  featureChipText: {
    fontSize: 12,
    fontFamily: "Inter_500Medium",
    fontWeight: "500",
  },

  // Specials
  specialCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 13,
    marginBottom: 10,
    gap: 6,
  },
  specialCardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  specialTitle: {
    fontSize: 14,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
  },
  specialDesc: {
    fontSize: 14,
    fontFamily: "Inter_400Regular",
    lineHeight: 20,
  },
  specialFooter: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  specialValid: {
    fontSize: 12,
    fontFamily: "Inter_400Regular",
  },

  // Happy hour
  happyHourCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    gap: 8,
  },
  happyHourHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
  },
  happyHourTime: {
    fontSize: 14,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
  },
  happyHourDeal: {
    fontSize: 14,
    fontFamily: "Inter_400Regular",
    lineHeight: 20,
  },

  // Hours table
  hoursTable: {
    borderRadius: 12,
    borderWidth: 1,
    overflow: "hidden",
  },
  hoursRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 11,
  },
  hoursDay: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  todayDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  hoursDayText: {
    fontSize: 14,
    fontFamily: "Inter_400Regular",
    width: 32,
  },
  hoursDayToday: {
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
  },
  todayLabel: {
    fontSize: 11,
    fontFamily: "Inter_500Medium",
    fontWeight: "500",
  },
  hoursTime: {
    fontSize: 14,
    fontFamily: "Inter_400Regular",
  },
  hoursTimeClosed: {
    fontStyle: "italic",
  },

  // Events
  eventCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 13,
    marginBottom: 10,
    gap: 8,
  },
  eventHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 10,
  },
  eventTitle: {
    fontSize: 14,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    marginBottom: 4,
    flex: 1,
  },
  eventMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  eventMetaText: {
    fontSize: 12,
    fontFamily: "Inter_400Regular",
  },
  eventTimeBadge: {
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 8,
  },
  eventTimeBadgeText: {
    fontSize: 11,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  eventDesc: {
    fontSize: 13,
    fontFamily: "Inter_400Regular",
    lineHeight: 19,
  },

  // On Tap
  tapGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 7,
  },
  tapTag: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
  },
  tapTagText: {
    fontSize: 12,
    fontFamily: "Inter_400Regular",
  },

  // Menu
  menuCategory: {
    marginBottom: 16,
  },
  menuCategoryTitle: {
    fontSize: 12,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    textTransform: "uppercase",
    letterSpacing: 0.6,
    marginBottom: 8,
  },
  menuItems: {
    borderRadius: 12,
    borderWidth: 1,
    overflow: "hidden",
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 12,
    gap: 10,
  },
  menuItemLeft: {
    flex: 1,
    gap: 3,
  },
  menuItemName: {
    fontSize: 14,
    fontFamily: "Inter_500Medium",
    fontWeight: "500",
  },
  menuItemDesc: {
    fontSize: 12,
    fontFamily: "Inter_400Regular",
    lineHeight: 17,
  },
  menuItemPrice: {
    fontSize: 14,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    minWidth: 36,
    textAlign: "right",
  },

  // Contact
  contactList: {
    borderRadius: 12,
    borderWidth: 1,
    overflow: "hidden",
  },
  contactRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 13,
    gap: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  contactRowLast: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 13,
    gap: 10,
  },
  contactText: {
    fontSize: 14,
    fontFamily: "Inter_400Regular",
    flex: 1,
  },
  authRequiredCard: {
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  authRequiredText: {
    fontSize: 12,
    fontFamily: "Inter_500Medium",
  },
  submissionEntryWrap: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  submissionEntryBtn: {
    borderWidth: 1,
    borderRadius: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 10,
  },
  submissionEntryText: {
    fontSize: 13,
    fontFamily: "Inter_600SemiBold",
  },
});
