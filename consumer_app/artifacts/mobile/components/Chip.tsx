import React from "react";
import { StyleSheet, Text, TouchableOpacity } from "react-native";
import { useColors } from "@/hooks/useColors";

type Props = {
  label: string;
  selected?: boolean;
  onPress?: () => void;
  size?: "sm" | "md";
};

export function Chip({ label, selected = false, onPress, size = "md" }: Props) {
  const colors = useColors();

  return (
    <TouchableOpacity
      onPress={onPress}
      style={[
        styles.chip,
        size === "sm" && styles.chipSm,
        {
          backgroundColor: selected ? colors.primary : colors.muted,
          borderColor: selected ? colors.primary : colors.border,
        },
      ]}
      activeOpacity={0.75}
    >
      <Text
        style={[
          styles.label,
          size === "sm" && styles.labelSm,
          { color: selected ? colors.primaryForeground : colors.mutedForeground },
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    marginRight: 8,
  },
  chipSm: {
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  label: {
    fontSize: 13,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
  },
  labelSm: {
    fontSize: 12,
  },
});
