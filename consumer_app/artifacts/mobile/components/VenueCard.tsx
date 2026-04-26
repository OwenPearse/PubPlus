import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { useColors } from "@/hooks/useColors";
import type { Venue } from "@/data/mockData";

type Props = {
  venue: Venue;
  onPress?: () => void;
  onSave?: () => void;
  compact?: boolean;
};

export function VenueCard({ venue, onPress, onSave, compact = false }: Props) {
  const colors = useColors();

  function handleSave() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onSave?.();
  }

  const imageHeight = compact ? 110 : 144;

  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.87}
      style={[
        styles.card,
        compact && styles.cardCompact,
        {
          backgroundColor: colors.card,
          borderColor: colors.border,
          shadowColor: colors.foreground,
        },
      ]}
    >
      <View
        style={[
          styles.imagePlaceholder,
          { backgroundColor: venue.imageColor, height: imageHeight },
        ]}
      >
        <View style={[styles.typeTag, { backgroundColor: "rgba(0,0,0,0.40)" }]}>
          <Text style={styles.typeText}>{venue.type}</Text>
        </View>

        <TouchableOpacity
          style={[
            styles.saveBtn,
            {
              backgroundColor: venue.isSaved
                ? "rgba(194,124,0,0.88)"
                : "rgba(0,0,0,0.25)",
            },
          ]}
          onPress={handleSave}
          hitSlop={{ top: 8, left: 8, right: 8, bottom: 8 }}
        >
          <Feather
            name="bookmark"
            size={15}
            color={venue.isSaved ? "#ffffff" : "rgba(255,255,255,0.9)"}
          />
        </TouchableOpacity>

        <View
          style={[
            styles.openBadge,
            {
              backgroundColor: venue.isOpen
                ? "rgba(30,110,58,0.9)"
                : "rgba(150,45,30,0.9)",
            },
          ]}
        >
          <View
            style={[
              styles.openDot,
              { backgroundColor: venue.isOpen ? "#7dff9e" : "#ff9e7d" },
            ]}
          />
          <Text style={styles.openText}>
            {venue.isOpen ? `Open · ${venue.closingTime}` : venue.closingTime}
          </Text>
        </View>
      </View>

      <View style={[styles.body, compact && styles.bodyCompact]}>
        <View style={styles.nameRow}>
          <Text
            style={[
              styles.name,
              compact && styles.nameCompact,
              { color: colors.foreground },
            ]}
            numberOfLines={1}
          >
            {venue.name}
          </Text>
          <View style={styles.ratingRow}>
            <Feather name="star" size={11} color={colors.accent} />
            <Text style={[styles.rating, { color: colors.foreground }]}>
              {venue.rating}
            </Text>
          </View>
        </View>

        <View style={styles.metaRow}>
          <Feather name="map-pin" size={11} color={colors.mutedForeground} />
          <Text style={[styles.suburb, { color: colors.mutedForeground }]}>
            {venue.suburb}
          </Text>
          {!compact ? (
            <>
              <Text style={[styles.dot, { color: colors.border }]}> · </Text>
              <Text style={[styles.reviews, { color: colors.mutedForeground }]}>
                {venue.reviewCount} reviews
              </Text>
            </>
          ) : null}
        </View>

        {!compact ? (
          <>
            {venue.specials.length > 0 ? (
              <View style={[styles.tagRow, { backgroundColor: colors.secondary }]}>
                <Feather name="tag" size={11} color={colors.primary} />
                <Text
                  style={[styles.tagText, { color: colors.primary }]}
                  numberOfLines={1}
                >
                  {venue.specials[0].title}
                </Text>
              </View>
            ) : null}

            {venue.events.length > 0 ? (
              <View style={styles.eventRow}>
                <Feather name="calendar" size={11} color={colors.mutedForeground} />
                <Text
                  style={[styles.eventText, { color: colors.mutedForeground }]}
                  numberOfLines={1}
                >
                  {venue.events[0].title} · {venue.events[0].time}
                </Text>
              </View>
            ) : null}

            {venue.tapBeers.length > 0 ? (
              <View style={styles.tapsRow}>
                {venue.tapBeers.slice(0, 3).map((beer, i) => (
                  <View
                    key={i}
                    style={[styles.tapTag, { backgroundColor: colors.muted }]}
                  >
                    <Text
                      style={[styles.tapTagText, { color: colors.mutedForeground }]}
                      numberOfLines={1}
                    >
                      {beer}
                    </Text>
                  </View>
                ))}
                {venue.tapBeers.length > 3 ? (
                  <Text style={[styles.moreTaps, { color: colors.mutedForeground }]}>
                    +{venue.tapBeers.length - 3}
                  </Text>
                ) : null}
              </View>
            ) : null}

            {onPress !== undefined ? (
              <View style={[styles.listingRow, { borderTopColor: colors.border }]}>
                <Text style={[styles.listingText, { color: colors.mutedForeground }]}>
                  View listing
                </Text>
                <Feather name="arrow-right" size={12} color={colors.primary} />
              </View>
            ) : null}
          </>
        ) : null}

        {compact && venue.mealDeal ? (
          <View style={[styles.mealDealTag, { backgroundColor: colors.secondary }]}>
            <Feather name="tag" size={10} color={colors.primary} />
            <Text style={[styles.mealDealText, { color: colors.primary }]} numberOfLines={1}>
              {venue.mealDeal}
            </Text>
          </View>
        ) : null}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  cardCompact: {
    width: 200,
  },
  imagePlaceholder: {
    width: "100%",
    justifyContent: "flex-end",
    padding: 10,
  },
  typeTag: {
    position: "absolute",
    top: 9,
    left: 9,
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 6,
  },
  typeText: {
    color: "#ffffff",
    fontSize: 10,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    textTransform: "capitalize",
  },
  saveBtn: {
    position: "absolute",
    top: 9,
    right: 9,
    borderRadius: 16,
    padding: 6,
  },
  openBadge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    paddingHorizontal: 7,
    paddingVertical: 4,
    borderRadius: 7,
    gap: 4,
  },
  openDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  openText: {
    color: "#ffffff",
    fontSize: 10,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
  },
  body: {
    paddingHorizontal: 12,
    paddingTop: 11,
    paddingBottom: 0,
    gap: 5,
  },
  bodyCompact: {
    paddingHorizontal: 10,
    paddingTop: 9,
    paddingBottom: 10,
    gap: 4,
  },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  name: {
    fontSize: 14,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    flex: 1,
    marginRight: 6,
  },
  nameCompact: {
    fontSize: 13,
  },
  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
  },
  rating: {
    fontSize: 12,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
  },
  suburb: {
    fontSize: 11,
    fontFamily: "Inter_400Regular",
  },
  dot: {
    fontSize: 11,
  },
  reviews: {
    fontSize: 11,
    fontFamily: "Inter_400Regular",
  },
  tagRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 7,
    paddingVertical: 4,
    borderRadius: 7,
  },
  tagText: {
    fontSize: 11,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    flex: 1,
  },
  eventRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  eventText: {
    fontSize: 11,
    fontFamily: "Inter_400Regular",
    flex: 1,
  },
  tapsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 4,
  },
  tapTag: {
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 5,
  },
  tapTagText: {
    fontSize: 10,
    fontFamily: "Inter_400Regular",
  },
  moreTaps: {
    fontSize: 10,
    fontFamily: "Inter_400Regular",
    alignSelf: "center",
  },
  listingRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: 4,
    paddingTop: 9,
    paddingBottom: 11,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 2,
  },
  listingText: {
    fontSize: 12,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
  },
  mealDealTag: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: "flex-start",
  },
  mealDealText: {
    fontSize: 10,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
});
