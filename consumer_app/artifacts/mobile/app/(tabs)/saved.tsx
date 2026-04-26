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

import { useRouter } from "expo-router";

import { EmptyState } from "@/components/EmptyState";
import { VenueCard } from "@/components/VenueCard";
import { VENUES } from "@/data/mockData";
import { useColors } from "@/hooks/useColors";

const INITIAL_SAVED = ["1", "6", "8"];

export default function SavedScreen() {
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();

  const topInset = Platform.OS === "web" ? 67 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : 0;

  const [savedIds, setSavedIds] = useState<Set<string>>(new Set(INITIAL_SAVED));

  function unsave(id: string) {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    setSavedIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }

  const savedVenues = VENUES.filter((v) => savedIds.has(v.id));

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={[
        styles.content,
        { paddingTop: topInset + 8, paddingBottom: bottomInset + 90 },
      ]}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.titleRow}>
        <Text style={[styles.title, { color: colors.foreground }]}>Saved</Text>
        {savedVenues.length > 0 ? (
          <View style={[styles.countBadge, { backgroundColor: colors.muted }]}>
            <Text style={[styles.countText, { color: colors.mutedForeground }]}>
              {savedVenues.length}
            </Text>
          </View>
        ) : null}
      </View>

      {savedVenues.length === 0 ? (
        <EmptyState
          icon="bookmark"
          title="Nothing saved yet"
          subtitle="Tap the bookmark icon on any venue to save it for later"
        />
      ) : (
        savedVenues.map((venue) => (
          <View key={venue.id} style={styles.cardWrap}>
            <VenueCard
              venue={{ ...venue, isSaved: true }}
              onPress={() => router.push(`/venue/${venue.id}`)}
              onSave={() => unsave(venue.id)}
            />
            <View style={[styles.actions, { borderColor: colors.border }]}>
              <TouchableOpacity
                style={[styles.actionBtn, { borderRightColor: colors.border }]}
                onPress={() => {}}
              >
                <Feather name="share-2" size={13} color={colors.mutedForeground} />
                <Text style={[styles.actionText, { color: colors.mutedForeground }]}>Share</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.actionBtn}
                onPress={() => unsave(venue.id)}
              >
                <Feather name="trash-2" size={13} color={colors.destructive} />
                <Text style={[styles.actionText, { color: colors.destructive }]}>Remove</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))
      )}
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
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    letterSpacing: -0.5,
  },
  countBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  countText: {
    fontSize: 13,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
  },
  cardWrap: {
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  actions: {
    flexDirection: "row",
    borderWidth: StyleSheet.hairlineWidth,
    borderTopWidth: 0,
    borderBottomLeftRadius: 12,
    borderBottomRightRadius: 12,
    overflow: "hidden",
    marginTop: -4,
  },
  actionBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    paddingVertical: 9,
    borderRightWidth: StyleSheet.hairlineWidth,
  },
  actionText: {
    fontSize: 12,
    fontWeight: "500",
    fontFamily: "Inter_500Medium",
  },
});
