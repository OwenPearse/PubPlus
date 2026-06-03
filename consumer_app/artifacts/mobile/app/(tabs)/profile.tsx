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

import { EmptyState } from "@/components/EmptyState";
import { ProfileRow } from "@/components/ProfileRow";
import { SectionHeader } from "@/components/SectionHeader";
import { SuburbSelector } from "@/components/SuburbSelector";
import { useProfile } from "@/hooks/useProfile";
import { useColors } from "@/hooks/useColors";
import {
  buildDefaultLocalityPatch,
  getSuburbLabelForLocalityId,
  PROFILE_PICKABLE_SUBURBS,
} from "@/lib/localityReference";
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

  const savedSuburbLabel = useMemo(
    () => getSuburbLabelForLocalityId(profile?.default_locality_id),
    [profile?.default_locality_id]
  );

  const savedSuburbDisplay = useMemo(() => {
    if (savedSuburbLabel) return savedSuburbLabel;
    if (profile?.default_locality_id) return "Saved locality";
    return null;
  }, [savedSuburbLabel, profile?.default_locality_id]);

  async function handleDefaultSuburbChange(suburb: string | null) {
    Haptics.selectionAsync();
    const patch = buildDefaultLocalityPatch(suburb);
    const currentId = profile?.default_locality_id ?? null;
    const nextId = patch.default_locality_id;
    if (currentId === nextId) return;
    await patchProfile(patch);
  }

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

  async function toggleSmsMarketing() {
    Haptics.selectionAsync();
    if (!profile) return;
    await patchProfile({ sms_marketing_opt_in: !profile.sms_marketing_opt_in });
  }

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } finally {
      setSigningOut(false);
    }
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

      <SectionHeader
        title="Default suburb"
        subtitle="Choose a default suburb to make local discovery easier."
      />
      <View style={styles.localityRow}>
        <SuburbSelector
          selected={savedSuburbDisplay}
          onChange={handleDefaultSuburbChange}
          suburbs={PROFILE_PICKABLE_SUBURBS}
          placeholder="Choose default suburb"
        />
      </View>
      {profile?.default_locality_id && !savedSuburbLabel ? (
        <Text style={[styles.helperCopy, { color: colors.mutedForeground }]}>
          Your saved locality is not in the Melbourne inner seed list shown here.
        </Text>
      ) : null}
      <Text style={[styles.helperCopy, { color: colors.mutedForeground }]}>
        More taste and personalization controls are coming later.
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
          label="Push notifications"
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
          icon="message-circle"
          label="SMS marketing"
          value={profile?.sms_marketing_opt_in ? "On" : "Off"}
          onPress={toggleSmsMarketing}
        />
        <ProfileRow
          icon="moon"
          label="Quiet hours"
          value={
            profile?.quiet_hours_start_local && profile?.quiet_hours_end_local
              ? `${profile.quiet_hours_start_local} - ${profile.quiet_hours_end_local}`
              : "Not set"
          }
          showChevron={false}
        />
        <ProfileRow icon="shield" label="Privacy" value="Coming soon" showChevron={false} />
        <ProfileRow icon="help-circle" label="Help & Support" value="Coming soon" showChevron={false} />
        <ProfileRow icon="info" label="About PubPlus" value="Coming soon" showChevron={false} />
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
  localityRow: {
    paddingHorizontal: 16,
    paddingBottom: 6,
  },
  helperCopy: {
    paddingHorizontal: 16,
    paddingBottom: 12,
    fontSize: 12,
    fontFamily: "Inter_400Regular",
    lineHeight: 17,
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
