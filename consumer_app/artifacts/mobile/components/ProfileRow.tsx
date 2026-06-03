import { Feather } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useColors } from "@/hooks/useColors";

type Props = {
  icon: React.ComponentProps<typeof Feather>["name"];
  label: string;
  value?: string;
  onPress?: () => void;
  dangerous?: boolean;
  showChevron?: boolean;
};

export function ProfileRow({ icon, label, value, onPress, dangerous = false, showChevron = true }: Props) {
  const colors = useColors();
  const color = dangerous ? colors.destructive : colors.foreground;
  const iconColor = dangerous ? colors.destructive : colors.primary;

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={!onPress}
      activeOpacity={0.7}
      style={[styles.row, { borderBottomColor: colors.border }]}
      accessibilityRole={onPress ? "button" : "text"}
    >
      <View style={[styles.iconWrap, { backgroundColor: dangerous ? "rgba(217,79,45,0.1)" : colors.secondary }]}>
        <Feather name={icon} size={18} color={iconColor} />
      </View>
      <Text style={[styles.label, { color }]}>{label}</Text>
      <View style={styles.right}>
        {value ? (
          <Text style={[styles.value, { color: colors.mutedForeground }]}>{value}</Text>
        ) : null}
        {showChevron ? (
          <Feather name="chevron-right" size={16} color={colors.mutedForeground} />
        ) : null}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 13,
    gap: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  label: {
    flex: 1,
    fontSize: 15,
    fontFamily: "Inter_500Medium",
    fontWeight: "500",
  },
  right: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  value: {
    fontSize: 14,
    fontFamily: "Inter_400Regular",
  },
});
