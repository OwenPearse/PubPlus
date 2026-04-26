import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React from "react";
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { useColors } from "@/hooks/useColors";

export type FilterPill = {
  key: string;
  label: string;
  category?: "location" | "meal" | "open" | "preference";
  onRemove: () => void;
};

type Props = {
  pills: FilterPill[];
  onClearAll?: () => void;
};

export function ActiveFilters({ pills, onClearAll }: Props) {
  const colors = useColors();

  if (pills.length === 0) return null;

  function getPillStyle(category?: FilterPill["category"]) {
    switch (category) {
      case "location":
        return { backgroundColor: colors.primary, borderColor: colors.primary };
      case "meal":
        return { backgroundColor: colors.accent, borderColor: colors.accent };
      case "open":
        return {
          backgroundColor: "rgba(35,120,65,0.12)",
          borderColor: "rgba(35,120,65,0.3)",
        };
      default:
        return { backgroundColor: colors.secondary, borderColor: colors.border };
    }
  }

  function getPillTextColor(category?: FilterPill["category"]) {
    switch (category) {
      case "location":
        return colors.primaryForeground;
      case "meal":
        return "#ffffff";
      default:
        return colors.foreground;
    }
  }

  function getXColor(category?: FilterPill["category"]) {
    switch (category) {
      case "location":
        return "rgba(255,255,255,0.75)";
      case "meal":
        return "rgba(255,255,255,0.75)";
      default:
        return colors.mutedForeground;
    }
  }

  return (
    <View style={[styles.container, { borderBottomColor: colors.border }]}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.row}
        keyboardShouldPersistTaps="handled"
      >
        {pills.map((pill) => (
          <View
            key={pill.key}
            style={[styles.pill, getPillStyle(pill.category)]}
          >
            <Text
              style={[
                styles.pillText,
                { color: getPillTextColor(pill.category) },
              ]}
              numberOfLines={1}
            >
              {pill.label}
            </Text>
            <TouchableOpacity
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                pill.onRemove();
              }}
              hitSlop={{ top: 8, left: 8, right: 8, bottom: 8 }}
            >
              <Feather name="x" size={11} color={getXColor(pill.category)} />
            </TouchableOpacity>
          </View>
        ))}

        {onClearAll ? (
          <TouchableOpacity
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              onClearAll();
            }}
            style={[styles.clearAll, { borderColor: colors.border }]}
          >
            <Text style={[styles.clearAllText, { color: colors.mutedForeground }]}>
              Clear all
            </Text>
          </TouchableOpacity>
        ) : null}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  row: {
    paddingHorizontal: 16,
    paddingVertical: 9,
    gap: 6,
    flexDirection: "row",
    alignItems: "center",
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
  },
  pillText: {
    fontSize: 12,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
    maxWidth: 120,
  },
  clearAll: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
  },
  clearAllText: {
    fontSize: 12,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
  },
});
