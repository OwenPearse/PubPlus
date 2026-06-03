import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useState } from "react";
import {
  FlatList,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { SUBURBS } from "@/data/mockData";
import { useColors } from "@/hooks/useColors";

type Props = {
  selected: string | null;
  onChange: (suburb: string | null) => void;
  /** When set, only these suburb labels appear (e.g. seed-backed profile localities). */
  suburbs?: string[];
  placeholder?: string;
};

export function SuburbSelector({
  selected,
  onChange,
  suburbs,
  placeholder = "Any suburb",
}: Props) {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const [modalOpen, setModalOpen] = useState(false);
  const [query, setQuery] = useState("");

  const options = suburbs ?? SUBURBS;
  const filtered = options.filter((s) =>
    s.toLowerCase().includes(query.toLowerCase())
  );

  function handleSelect(suburb: string) {
    Haptics.selectionAsync();
    onChange(suburb);
    setModalOpen(false);
    setQuery("");
  }

  function handleClear() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onChange(null);
  }

  if (selected) {
    return (
      <View
        style={[
          styles.bubble,
          { backgroundColor: colors.primary },
        ]}
      >
        <Text style={[styles.bubbleText, { color: colors.primaryForeground }]}>
          {selected}
        </Text>
        <TouchableOpacity
          onPress={handleClear}
          hitSlop={{ top: 8, left: 8, right: 8, bottom: 8 }}
        >
          <Feather name="x" size={13} color={colors.primaryForeground} />
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <>
      <TouchableOpacity
        onPress={() => setModalOpen(true)}
        style={[styles.trigger, { backgroundColor: colors.muted, borderColor: colors.border }]}
        activeOpacity={0.75}
      >
        <Feather name="map-pin" size={14} color={colors.mutedForeground} />
        <Text style={[styles.triggerText, { color: colors.mutedForeground }]}>
          {placeholder}
        </Text>
        <Feather name="chevron-down" size={14} color={colors.mutedForeground} />
      </TouchableOpacity>

      <Modal
        visible={modalOpen}
        animationType="slide"
        transparent
        onRequestClose={() => setModalOpen(false)}
      >
        <TouchableOpacity
          style={styles.overlay}
          activeOpacity={1}
          onPress={() => setModalOpen(false)}
        />
        <View
          style={[
            styles.sheet,
            {
              backgroundColor: colors.background,
              paddingBottom: insets.bottom + 16,
            },
          ]}
        >
          <View style={[styles.sheetHandle, { backgroundColor: colors.border }]} />
          <Text style={[styles.sheetTitle, { color: colors.foreground }]}>
            Select suburb
          </Text>
          <View
            style={[
              styles.searchBar,
              { backgroundColor: colors.muted, borderColor: colors.border },
            ]}
          >
            <Feather name="search" size={16} color={colors.mutedForeground} />
            <TextInput
              style={[styles.searchInput, { color: colors.foreground }]}
              placeholder="Search suburbs..."
              placeholderTextColor={colors.mutedForeground}
              value={query}
              onChangeText={setQuery}
              autoFocus
            />
            {query.length > 0 ? (
              <TouchableOpacity onPress={() => setQuery("")}>
                <Feather name="x" size={14} color={colors.mutedForeground} />
              </TouchableOpacity>
            ) : null}
          </View>
          <FlatList
            data={filtered}
            keyExtractor={(item) => item}
            style={styles.list}
            keyboardShouldPersistTaps="handled"
            renderItem={({ item }) => (
              <TouchableOpacity
                onPress={() => handleSelect(item)}
                style={[styles.listItem, { borderBottomColor: colors.border }]}
                activeOpacity={0.7}
              >
                <Feather name="map-pin" size={14} color={colors.mutedForeground} />
                <Text style={[styles.listItemText, { color: colors.foreground }]}>
                  {item}
                </Text>
                <Feather name="chevron-right" size={14} color={colors.border} />
              </TouchableOpacity>
            )}
          />
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  trigger: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
  },
  triggerText: {
    fontSize: 13,
    fontFamily: "Inter_500Medium",
    fontWeight: "500",
    flex: 1,
  },
  bubble: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
  },
  bubbleText: {
    fontSize: 13,
    fontWeight: "600",
    fontFamily: "Inter_600SemiBold",
  },
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.35)",
  },
  sheet: {
    maxHeight: "65%",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 12,
    paddingHorizontal: 16,
  },
  sheetHandle: {
    width: 36,
    height: 4,
    borderRadius: 2,
    alignSelf: "center",
    marginBottom: 14,
  },
  sheetTitle: {
    fontSize: 17,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    marginBottom: 12,
  },
  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    fontFamily: "Inter_400Regular",
    padding: 0,
  },
  list: {
    flexGrow: 0,
  },
  listItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 13,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  listItemText: {
    flex: 1,
    fontSize: 15,
    fontFamily: "Inter_400Regular",
  },
});
