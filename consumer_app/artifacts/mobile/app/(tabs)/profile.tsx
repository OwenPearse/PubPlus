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

import { Chip } from "@/components/Chip";
import { EmptyState } from "@/components/EmptyState";
import { ProfileRow } from "@/components/ProfileRow";
import { SectionHeader } from "@/components/SectionHeader";
import { DRINK_TYPES, SUBURBS, VENUE_FEATURES } from "@/data/mockData";
import { useColors } from "@/hooks/useColors";

const PROFILE_USER = {
  name: "Alex M.",
  email: "alex@example.com",
  joinedDate: "April 2026",
  stats: { checkins: 12, saved: 3, reviews: 5 },
};

export default function ProfileScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const [isSignedIn] = useState(true);

  const topInset = Platform.OS === "web" ? 67 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : 0;

  const [preferredSuburbs, setPreferredSuburbs] = useState<Set<string>>(
    new Set(["Fitzroy", "Richmond"])
  );
  const [preferredDrinks, setPreferredDrinks] = useState<Set<string>>(
    new Set(["Craft Beer", "IPA"])
  );
  const [preferredFeatures, setPreferredFeatures] = useState<Set<string>>(
    new Set(["Beer Garden", "Live Music"])
  );
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  function toggleSuburb(s: string) {
    Haptics.selectionAsync();
    setPreferredSuburbs((prev) => {
      const next = new Set(prev);
      if (next.has(s)) next.delete(s);
      else next.add(s);
      return next;
    });
  }

  function toggleDrink(d: string) {
    Haptics.selectionAsync();
    setPreferredDrinks((prev) => {
      const next = new Set(prev);
      if (next.has(d)) next.delete(d);
      else next.add(d);
      return next;
    });
  }

  function toggleFeature(f: string) {
    Haptics.selectionAsync();
    setPreferredFeatures((prev) => {
      const next = new Set(prev);
      if (next.has(f)) next.delete(f);
      else next.add(f);
      return next;
    });
  }

  if (!isSignedIn) {
    return (
      <View
        style={[
          styles.container,
          { backgroundColor: colors.background, paddingTop: topInset },
        ]}
      >
        <EmptyState
          icon="user"
          title="Sign in to save your preferences"
          subtitle="Keep track of your favourite venues, set suburb preferences, and get personalised suggestions."
          actionLabel="Sign in"
          onAction={() => {}}
        />
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={[
        styles.content,
        { paddingTop: topInset + 8, paddingBottom: bottomInset + 90 },
      ]}
      showsVerticalScrollIndicator={false}
    >
      <View style={[styles.heroCard, { backgroundColor: colors.primary }]}>
        <View style={[styles.avatar, { backgroundColor: "rgba(255,255,255,0.18)" }]}>
          <Text style={styles.avatarText}>{PROFILE_USER.name.charAt(0)}</Text>
        </View>
        <View style={styles.heroInfo}>
          <Text style={[styles.heroName, { color: "#ffffff" }]}>{PROFILE_USER.name}</Text>
          <Text style={[styles.heroEmail, { color: "rgba(255,255,255,0.72)" }]}>
            {PROFILE_USER.email}
          </Text>
          <Text style={[styles.heroJoined, { color: "rgba(255,255,255,0.55)" }]}>
            Joined {PROFILE_USER.joinedDate}
          </Text>
        </View>
        <TouchableOpacity style={styles.editBtn}>
          <Feather name="edit-2" size={16} color="rgba(255,255,255,0.8)" />
        </TouchableOpacity>
      </View>

      <View
        style={[
          styles.statsRow,
          { backgroundColor: colors.card, borderColor: colors.border },
        ]}
      >
        {[
          { label: "Check-ins", value: PROFILE_USER.stats.checkins },
          { label: "Saved", value: PROFILE_USER.stats.saved },
          { label: "Reviews", value: PROFILE_USER.stats.reviews },
        ].map((stat, i) => (
          <View
            key={i}
            style={[
              styles.statItem,
              i < 2 && {
                borderRightColor: colors.border,
                borderRightWidth: StyleSheet.hairlineWidth,
              },
            ]}
          >
            <Text style={[styles.statValue, { color: colors.primary }]}>
              {stat.value}
            </Text>
            <Text style={[styles.statLabel, { color: colors.mutedForeground }]}>
              {stat.label}
            </Text>
          </View>
        ))}
      </View>

      <SectionHeader title="Suburb preferences" subtitle="Personalise your home feed" />
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.prefChips}
      >
        {SUBURBS.map((s) => (
          <Chip
            key={s}
            label={s}
            selected={preferredSuburbs.has(s)}
            onPress={() => toggleSuburb(s)}
            size="sm"
          />
        ))}
      </ScrollView>

      <SectionHeader title="Drink preferences" />
      <View style={styles.prefChipsWrap}>
        {DRINK_TYPES.map((d) => (
          <Chip
            key={d}
            label={d}
            selected={preferredDrinks.has(d)}
            onPress={() => toggleDrink(d)}
            size="sm"
          />
        ))}
      </View>

      <SectionHeader title="Venue preferences" />
      <View style={styles.prefChipsWrap}>
        {VENUE_FEATURES.map((f) => (
          <Chip
            key={f}
            label={f}
            selected={preferredFeatures.has(f)}
            onPress={() => toggleFeature(f)}
            size="sm"
          />
        ))}
      </View>

      <SectionHeader title="Settings" />
      <View
        style={[
          styles.settingsGroup,
          { backgroundColor: colors.card, borderColor: colors.border },
        ]}
      >
        <ProfileRow
          icon="bell"
          label="Notifications"
          value={notificationsEnabled ? "On" : "Off"}
          onPress={() => {
            Haptics.selectionAsync();
            setNotificationsEnabled((v) => !v);
          }}
        />
        <ProfileRow
          icon="map-pin"
          label="Default location"
          value="Fitzroy"
          onPress={() => {}}
        />
        <ProfileRow icon="moon" label="Dark mode" value="System" onPress={() => {}} />
        <ProfileRow icon="shield" label="Privacy" onPress={() => {}} />
        <ProfileRow icon="help-circle" label="Help & Support" onPress={() => {}} />
        <ProfileRow icon="info" label="About PubPlus" onPress={() => {}} />
      </View>

      <View
        style={[
          styles.settingsGroup,
          styles.settingsGroupTop,
          { backgroundColor: colors.card, borderColor: colors.border },
        ]}
      >
        <ProfileRow
          icon="log-out"
          label="Sign out"
          onPress={() => {}}
          dangerous
          showChevron={false}
        />
      </View>
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
  heroCard: {
    marginHorizontal: 16,
    borderRadius: 20,
    padding: 20,
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    marginBottom: 14,
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
  },
  avatarText: {
    fontSize: 20,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
    color: "#ffffff",
  },
  heroInfo: {
    flex: 1,
  },
  heroName: {
    fontSize: 17,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
  },
  heroEmail: {
    fontSize: 13,
    fontFamily: "Inter_400Regular",
    marginTop: 2,
  },
  heroJoined: {
    fontSize: 11,
    fontFamily: "Inter_400Regular",
    marginTop: 2,
  },
  editBtn: {
    padding: 6,
  },
  statsRow: {
    marginHorizontal: 16,
    borderRadius: 14,
    borderWidth: 1,
    flexDirection: "row",
    marginBottom: 22,
  },
  statItem: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 13,
  },
  statValue: {
    fontSize: 22,
    fontWeight: "700",
    fontFamily: "Inter_700Bold",
  },
  statLabel: {
    fontSize: 11,
    fontFamily: "Inter_400Regular",
    marginTop: 2,
  },
  prefChips: {
    paddingHorizontal: 16,
    paddingBottom: 4,
    gap: 6,
    flexDirection: "row",
  },
  prefChipsWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    paddingHorizontal: 16,
    paddingBottom: 4,
  },
  settingsGroup: {
    marginHorizontal: 16,
    borderRadius: 14,
    borderWidth: 1,
    overflow: "hidden",
    marginBottom: 10,
  },
  settingsGroupTop: {
    marginTop: 4,
  },
});
