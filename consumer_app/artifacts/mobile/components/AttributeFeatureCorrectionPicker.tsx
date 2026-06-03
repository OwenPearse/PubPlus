import type { SearchFilterVenueFeature } from "@workspace/api-client-react";
import React, { useMemo } from "react";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from "react-native";

import { useColors } from "@/hooks/useColors";

export type FeatureCorrectionChoice = "unchanged" | "present" | "absent";

type Props = {
  features: SearchFilterVenueFeature[];
  choices: Record<string, FeatureCorrectionChoice>;
  onChoiceChange: (definitionId: string, choice: FeatureCorrectionChoice) => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
};

const CHOICE_OPTIONS: Array<{ value: FeatureCorrectionChoice; label: string }> = [
  { value: "unchanged", label: "No change" },
  { value: "present", label: "Present" },
  { value: "absent", label: "Not present" },
];

function groupLabel(raw: string | null | undefined): string {
  if (!raw?.trim()) return "Other";
  return raw
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function AttributeFeatureCorrectionPicker({
  features,
  choices,
  onChoiceChange,
  loading,
  error,
  onRetry,
}: Props) {
  const colors = useColors();

  const grouped = useMemo(() => {
    const map = new Map<string, SearchFilterVenueFeature[]>();
    for (const feature of features) {
      const label = groupLabel(feature.group);
      const bucket = map.get(label) ?? [];
      bucket.push(feature);
      map.set(label, bucket);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [features]);

  if (loading) {
    return (
      <View style={styles.stateRow}>
        <ActivityIndicator color={colors.primary} />
        <Text style={[styles.helper, { color: colors.mutedForeground }]}>Loading features...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.stateRow}>
        <Text style={[styles.helper, { color: colors.destructive }]}>{error}</Text>
        {onRetry ? (
          <TouchableOpacity onPress={onRetry} accessibilityRole="button" accessibilityLabel="Retry loading features">
            <Text style={[styles.retry, { color: colors.primary }]}>Retry</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    );
  }

  if (features.length === 0) {
    return (
      <Text style={[styles.helper, { color: colors.mutedForeground }]}>
        No venue features are available to correct right now.
      </Text>
    );
  }

  return (
    <View style={styles.wrap}>
      {grouped.map(([group, items]) => (
        <View key={group} style={styles.group}>
          <Text style={[styles.groupTitle, { color: colors.mutedForeground }]}>{group}</Text>
          {items.map((feature) => {
            const definitionId = feature.definition_id;
            const selected = choices[definitionId] ?? "unchanged";
            return (
              <View key={definitionId} style={styles.row} testID={`correction-feature-row-${feature.key}`}>
                <Text style={[styles.featureLabel, { color: colors.foreground }]}>{feature.label}</Text>
                <View style={styles.choiceRow}>
                  {CHOICE_OPTIONS.map((option) => (
                    <TouchableOpacity
                      key={option.value}
                      style={[
                        styles.choiceBtn,
                        {
                          backgroundColor: selected === option.value ? colors.primary : colors.card,
                          borderColor: colors.border,
                        },
                      ]}
                      onPress={() => onChoiceChange(definitionId, option.value)}
                      accessibilityRole="button"
                      accessibilityLabel={`${feature.label}: ${option.label}`}
                      testID={`correction-feature-${feature.key}-${option.value}`}
                    >
                      <Text
                        style={{
                          color: selected === option.value ? colors.primaryForeground : colors.foreground,
                          fontFamily: "Inter_500Medium",
                          fontSize: 11,
                        }}
                      >
                        {option.label}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            );
          })}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 12 },
  group: { gap: 8 },
  groupTitle: { fontFamily: "Inter_600SemiBold", fontSize: 12, textTransform: "uppercase", letterSpacing: 0.4 },
  row: { gap: 6 },
  featureLabel: { fontFamily: "Inter_500Medium", fontSize: 14 },
  choiceRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  choiceBtn: { borderWidth: 1, borderRadius: 16, paddingVertical: 6, paddingHorizontal: 10 },
  helper: { fontFamily: "Inter_400Regular", fontSize: 12 },
  retry: { fontFamily: "Inter_600SemiBold", fontSize: 12, marginTop: 6 },
  stateRow: { alignItems: "center", gap: 8, paddingVertical: 12 },
});
