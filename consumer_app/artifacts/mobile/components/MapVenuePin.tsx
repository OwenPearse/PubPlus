import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useColors } from "@/hooks/useColors";
import type { Venue } from "@/data/mockData";

type PinProps = {
  venue: Venue;
  selected?: boolean;
  onPress?: () => void;
};

export function MapVenuePin({ venue, selected = false, onPress }: PinProps) {
  const colors = useColors();

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.85}>
      <View
        style={[
          styles.pin,
          {
            backgroundColor: selected ? colors.primary : colors.card,
            borderColor: selected ? colors.primary : colors.border,
            shadowColor: colors.foreground,
          },
        ]}
      >
        <Text style={[styles.pinText, { color: selected ? colors.primaryForeground : colors.foreground }]}>
          {venue.name}
        </Text>
        <View style={[styles.dot, { backgroundColor: venue.isOpen ? colors.success : colors.destructive }]} />
      </View>
      <View style={[styles.triangle, { borderTopColor: selected ? colors.primary : colors.card }]} />
    </TouchableOpacity>
  );
}

type PreviewCardProps = {
  venue: Venue;
  onPress?: () => void;
  onDismiss?: () => void;
};

export function MapPreviewCard({ venue, onPress, onDismiss }: PreviewCardProps) {
  const colors = useColors();

  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.9}
      style={[
        styles.previewCard,
        {
          backgroundColor: colors.card,
          borderColor: colors.border,
          shadowColor: colors.foreground,
        },
      ]}
    >
      <View style={[styles.previewImage, { backgroundColor: venue.imageColor }]}>
        <View style={[styles.previewOpenBadge, { backgroundColor: venue.isOpen ? "rgba(45,138,74,0.9)" : "rgba(180,60,40,0.9)" }]}>
          <View style={[styles.previewDot, { backgroundColor: venue.isOpen ? "#7dff9e" : "#ff9e7d" }]} />
          <Text style={styles.previewOpenText}>{venue.isOpen ? "Open" : "Closed"}</Text>
        </View>
      </View>
      <View style={styles.previewBody}>
        <View style={styles.previewTop}>
          <View style={styles.previewInfo}>
            <Text style={[styles.previewName, { color: colors.foreground }]} numberOfLines={1}>
              {venue.name}
            </Text>
            <Text style={[styles.previewSuburb, { color: colors.mutedForeground }]}>
              {venue.suburb} · {venue.type}
            </Text>
          </View>
          <View style={styles.previewRating}>
            <Feather name="star" size={12} color={colors.accent} />
            <Text style={[styles.previewRatingText, { color: colors.foreground }]}>{venue.rating}</Text>
          </View>
        </View>
        {venue.specials.length > 0 ? (
          <View style={[styles.previewSpecial, { backgroundColor: colors.secondary }]}>
            <Feather name="tag" size={11} color={colors.primary} />
            <Text style={[styles.previewSpecialText, { color: colors.primary }]} numberOfLines={1}>
              {venue.specials[0].title}
            </Text>
          </View>
        ) : null}
      </View>
      {onDismiss ? (
        <TouchableOpacity onPress={onDismiss} style={styles.dismissBtn} hitSlop={{ top: 8, left: 8, right: 8, bottom: 8 }}>
          <Feather name="x" size={16} color={colors.mutedForeground} />
        </TouchableOpacity>
      ) : null}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  pin: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1.5,
    gap: 5,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 4,
  },
  pinText: {
    fontSize: 12,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },
  triangle: {
    width: 0,
    height: 0,
    borderLeftWidth: 6,
    borderRightWidth: 6,
    borderTopWidth: 7,
    borderLeftColor: "transparent",
    borderRightColor: "transparent",
    alignSelf: "center",
    marginTop: -1,
  },
  previewCard: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
    flexDirection: "row",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 12,
    elevation: 6,
  },
  previewImage: {
    width: 80,
    justifyContent: "flex-end",
    padding: 8,
  },
  previewOpenBadge: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 5,
    paddingVertical: 3,
    borderRadius: 6,
    gap: 3,
    alignSelf: "flex-start",
  },
  previewDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
  },
  previewOpenText: {
    color: "#ffffff",
    fontSize: 10,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  previewBody: {
    flex: 1,
    padding: 12,
    gap: 8,
    justifyContent: "center",
  },
  previewTop: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },
  previewInfo: {
    flex: 1,
    marginRight: 8,
  },
  previewName: {
    fontSize: 15,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
  },
  previewSuburb: {
    fontSize: 12,
    fontFamily: "Inter_400Regular",
    marginTop: 2,
    textTransform: "capitalize",
  },
  previewRating: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
  },
  previewRatingText: {
    fontSize: 13,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  previewSpecial: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  previewSpecialText: {
    fontSize: 12,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    flex: 1,
  },
  dismissBtn: {
    position: "absolute",
    top: 8,
    right: 8,
  },
});
