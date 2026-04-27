import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useMemo, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";

import { Chip } from "@/components/Chip";
import { EmptyState } from "@/components/EmptyState";
import { ProfileRow } from "@/components/ProfileRow";
import { SectionHeader } from "@/components/SectionHeader";
import { DRINK_TYPES, SUBURBS, VENUE_FEATURES } from "@/data/mockData";
import { useProfile } from "@/hooks/useProfile";
import { useColors } from "@/hooks/useColors";
import { signOut } from "@/lib/supabase";

export default function ProfileScreen() {
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { session, isAuthenticated, profile, loading, saving, error, refreshProfile, patchProfile } = useProfile();
  const [signingOut, setSigningOut] = useState(false);

  const topInset = Platform.OS === "web" ? 67 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : 0;

  const displayName = profile?.display_name ?? session?.user?.email?.split("@")[0] ?? "PubPlus user";
  const email = session?.user?.email ?? "Signed in";
  const joinedDate = useMemo(() => {
    const createdAt = session?.user?.created_at;
    if (!createdAt) return "recently";
    const date = new Date(createdAt);
    return date.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  }, [session?.user?.created_at]);

  async function togglePushNotifications() {
    Haptics.selectionAsync();
    if (!profile) return;
    await patchProfile({ push_notifications_opt_in: !profile.push_notifications_opt_in });
  }

  async function toggleMarketingEmails() {
    Haptics.selectionAsync();
    if (!profile) return;
    await patchProfile({ email_marketing_opt_in: !profile.email_marketing_opt_in });
  }

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } finally {
      setSigningOut(false);
    }
  }

  if (!isAuthenticated) {
    return (
      <View
        style={[
          styles.container,
          { backgroundColor: colors.background, paddingTop: topInset },
        ]}
      >
        <EmptyState
          icon="user"
          title="Sign in to manage your profile"
          subtitle="Profile preferences are available once you sign in."
          actionLabel="Sign in"
          actionAccessibilityLabel="Sign in to manage profile"
          actionTestID="profile-sign-in-cta"
          onAction={() => router.push("/auth" as never)}
        />
      </View>
    );
  }

  if (loading) {
    return (
      <View
        style={[
          styles.container,
          styles.loadingWrap,
          { backgroundColor: colors.background, paddingTop: topInset },
        ]}
      >
        <ActivityIndicator color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.mutedForeground }]}>Loading profile...</Text>
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
          <Text style={styles.avatarText}>{displayName.charAt(0).toUpperCase()}</Text>
        </View>
        <View style={styles.heroInfo}>
          <Text style={[styles.heroName, { color: "#ffffff" }]}>{displayName}</Text>
          <Text style={[styles.heroEmail, { color: "rgba(255,255,255,0.72)" }]}>
            {email}
          </Text>
          <Text style={[styles.heroJoined, { color: "rgba(255,255,255,0.55)" }]}>
            Joined {joinedDate}
          </Text>
        </View>
        <TouchableOpacity style={styles.editBtn} disabled>
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
          { label: "Push", value: profile?.push_notifications_opt_in ? "On" : "Off" },
          { label: "Emails", value: profile?.email_marketing_opt_in ? "On" : "Off" },
          { label: "SMS", value: profile?.sms_marketing_opt_in ? "On" : "Off" },
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

      {error ? (
        <EmptyState
          icon="alert-circle"
          title="Profile unavailable"
          subtitle={error}
          actionLabel="Retry"
          onAction={refreshProfile}
        />
      ) : null}

      <SectionHeader title="Suburb preferences" subtitle="Backend locality IDs are supported" />
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.prefChips}
      >
        <Chip
          label={profile?.default_locality_id ? "Default locality set" : "No default locality"}
          selected={Boolean(profile?.default_locality_id)}
          onPress={() => {}}
          size="sm"
        />
        <Chip
          label={profile?.default_geographic_region_id ? "Default region set" : "No default region"}
          selected={Boolean(profile?.default_geographic_region_id)}
          onPress={() => {}}
          size="sm"
        />
      </ScrollView>

      <SectionHeader title="Drink preferences" />
      <View style={styles.prefChipsWrap}>
        {DRINK_TYPES.slice(0, 6).map((d) => (
          <Chip
            key={d}
            label={d}
            selected={false}
            onPress={() => {}}
            size="sm"
          />
        ))}
      </View>
      <Text style={[styles.unsupportedCopy, { color: colors.mutedForeground }]}>
        Drink chips are not in the backend profile contract yet and are shown as coming soon.
      </Text>

      <SectionHeader title="Venue preferences" />
      <View style={styles.prefChipsWrap}>
        {VENUE_FEATURES.slice(0, 6).map((f) => (
          <Chip
            key={f}
            label={f}
            selected={false}
            onPress={() => {}}
            size="sm"
          />
        ))}
      </View>
      <Text style={[styles.unsupportedCopy, { color: colors.mutedForeground }]}>
        Venue feature chips are currently UI-only and are not sent to the backend.
      </Text>

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
          value={profile?.push_notifications_opt_in ? "On" : "Off"}
          onPress={togglePushNotifications}
        />
        <ProfileRow
          icon="mail"
          label="Marketing emails"
          value={profile?.email_marketing_opt_in ? "On" : "Off"}
          onPress={toggleMarketingEmails}
        />
        <ProfileRow
          icon="moon"
          label="Quiet hours"
          value={
            profile?.quiet_hours_start_local && profile?.quiet_hours_end_local
              ? `${profile.quiet_hours_start_local} - ${profile.quiet_hours_end_local}`
              : "Off"
          }
          onPress={() => {}}
        />
        <ProfileRow icon="shield" label="Privacy" value="Coming soon" onPress={() => {}} />
        <ProfileRow icon="help-circle" label="Help & Support" onPress={() => {}} />
        <ProfileRow icon="info" label="About PubPlus" onPress={() => {}} />
      </View>

      {saving ? (
        <View style={styles.savingRow}>
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.mutedForeground }]}>Saving changes...</Text>
        </View>
      ) : null}

      <View
        style={[
          styles.settingsGroup,
          styles.settingsGroupTop,
          { backgroundColor: colors.card, borderColor: colors.border },
        ]}
      >
        <ProfileRow
          icon="log-out"
          label={signingOut ? "Signing out..." : "Sign out"}
          onPress={handleSignOut}
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
  unsupportedCopy: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    fontSize: 12,
    fontFamily: "Inter_400Regular",
  },
  loadingWrap: {
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  loadingText: {
    fontSize: 13,
    fontFamily: "Inter_400Regular",
  },
  savingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
});
