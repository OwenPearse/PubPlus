import { Feather } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import React, { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuthSession } from "@/hooks/useAuthSession";
import { useColors } from "@/hooks/useColors";
import { hasSupabaseAuthConfig } from "@/lib/env";
import {
  signInWithAppleIOS,
  signInWithEmailPassword,
  signInWithFacebook,
  signInWithGoogle,
  signUpWithEmailPassword,
} from "@/lib/supabase";

type AuthMode = "sign_in" | "sign_up";

export default function AuthScreen() {
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { isAuthenticated, loading: authLoading } = useAuthSession();

  const [mode, setMode] = useState<AuthMode>("sign_in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const configMissing = !hasSupabaseAuthConfig();
  const canSubmit = useMemo(
    () => email.trim().length > 0 && password.trim().length >= 6 && !busy && !configMissing,
    [busy, configMissing, email, password]
  );

  useEffect(() => {
    if (isAuthenticated) {
      if (router.canGoBack()) {
        router.back();
      } else {
        router.replace("/(tabs)/profile");
      }
    }
  }, [isAuthenticated, router]);

  async function runAuthAction(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  if (authLoading) {
    return (
      <View
        style={[
          styles.container,
          styles.loadingWrap,
          { backgroundColor: colors.background, paddingTop: Platform.OS === "web" ? 28 : insets.top + 8 },
        ]}
      >
        <ActivityIndicator color={colors.primary} />
        <Text style={[styles.helpText, { color: colors.mutedForeground }]}>Checking sign-in...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={[
        styles.content,
        { paddingTop: (Platform.OS === "web" ? 28 : insets.top + 8), paddingBottom: insets.bottom + 24 },
      ]}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
      testID="auth-screen"
    >
      <TouchableOpacity
        style={styles.backBtn}
        onPress={() => router.back()}
        accessibilityRole="button"
        accessibilityLabel="Back from authentication"
        testID="auth-back-button"
      >
        <Feather name="arrow-left" size={18} color={colors.mutedForeground} />
        <Text style={[styles.backText, { color: colors.mutedForeground }]}>Back</Text>
      </TouchableOpacity>

      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.foreground }]}>
          {mode === "sign_in" ? "Sign in" : "Create account"}
        </Text>
        <Text style={[styles.subtitle, { color: colors.mutedForeground }]}>
          Use your PubPlus account to save venues and manage your profile.
        </Text>
      </View>

      {configMissing ? (
        <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
          <Text style={[styles.cardTitle, { color: colors.foreground }]}>Supabase config required</Text>
          <Text style={[styles.helpText, { color: colors.mutedForeground }]}>
            Add EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY, EXPO_PUBLIC_AUTH_REDIRECT_SCHEME,
            and EXPO_PUBLIC_API_BASE_URL in your Expo environment to enable sign-in.
          </Text>
        </View>
      ) : null}

      <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <Text style={[styles.label, { color: colors.mutedForeground }]}>Email</Text>
        <TextInput
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
          placeholder="you@example.com"
          placeholderTextColor={colors.mutedForeground}
          style={[styles.input, { color: colors.foreground, borderColor: colors.border, backgroundColor: colors.background }]}
          editable={!busy && !configMissing}
          accessibilityLabel="Email address"
          testID="auth-email-input"
        />

        <Text style={[styles.label, { color: colors.mutedForeground }]}>Password</Text>
        <TextInput
          value={password}
          onChangeText={setPassword}
          autoCapitalize="none"
          secureTextEntry
          placeholder="Minimum 6 characters"
          placeholderTextColor={colors.mutedForeground}
          style={[styles.input, { color: colors.foreground, borderColor: colors.border, backgroundColor: colors.background }]}
          editable={!busy && !configMissing}
          accessibilityLabel="Password"
          testID="auth-password-input"
        />

        <TouchableOpacity
          style={[
            styles.primaryBtn,
            { backgroundColor: canSubmit ? colors.primary : colors.muted, opacity: canSubmit ? 1 : 0.7 },
          ]}
          disabled={!canSubmit}
          onPress={() =>
            runAuthAction(() =>
              mode === "sign_in"
                ? signInWithEmailPassword(email.trim(), password)
                : signUpWithEmailPassword(email.trim(), password)
            )
          }
          accessibilityRole="button"
          accessibilityLabel={mode === "sign_in" ? "Sign in with email" : "Create account with email"}
          testID={mode === "sign_in" ? "auth-submit-sign-in" : "auth-submit-sign-up"}
        >
          {busy ? (
            <ActivityIndicator size="small" color={colors.primaryForeground} />
          ) : (
            <Text style={[styles.primaryBtnText, { color: colors.primaryForeground }]}>
              {mode === "sign_in" ? "Sign in with email" : "Create account"}
            </Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.switchModeBtn}
          onPress={() => setMode((current) => (current === "sign_in" ? "sign_up" : "sign_in"))}
          disabled={busy}
          accessibilityRole="button"
          accessibilityLabel={mode === "sign_in" ? "Switch to sign up mode" : "Switch to sign in mode"}
          testID="auth-switch-mode-button"
        >
          <Text style={[styles.switchModeText, { color: colors.primary }]}>
            {mode === "sign_in"
              ? "Need an account? Sign up"
              : "Already have an account? Sign in"}
          </Text>
        </TouchableOpacity>
      </View>

      <View style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}>
        <Text style={[styles.cardTitle, { color: colors.foreground }]}>Social sign in</Text>
        <TouchableOpacity
          style={[styles.socialBtn, { borderColor: colors.border }]}
          onPress={() => runAuthAction(() => signInWithGoogle())}
          disabled={busy || configMissing}
          accessibilityRole="button"
          accessibilityLabel="Continue with Google"
          testID="auth-social-google"
        >
          <Text style={[styles.socialBtnText, { color: colors.foreground }]}>Continue with Google</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.socialBtn, { borderColor: colors.border }]}
          onPress={() => runAuthAction(() => signInWithFacebook())}
          disabled={busy || configMissing}
          accessibilityRole="button"
          accessibilityLabel="Continue with Facebook"
          testID="auth-social-facebook"
        >
          <Text style={[styles.socialBtnText, { color: colors.foreground }]}>Continue with Facebook</Text>
        </TouchableOpacity>
        {Platform.OS === "ios" ? (
          <TouchableOpacity
            style={[styles.socialBtn, { borderColor: colors.border }]}
            onPress={() => runAuthAction(() => signInWithAppleIOS())}
            disabled={busy || configMissing}
            accessibilityRole="button"
            accessibilityLabel="Continue with Apple"
            testID="auth-social-apple"
          >
            <Text style={[styles.socialBtnText, { color: colors.foreground }]}>Continue with Apple</Text>
          </TouchableOpacity>
        ) : (
          <Text style={[styles.helpText, { color: colors.mutedForeground }]}>
            Apple Sign In is available on iOS only.
          </Text>
        )}
      </View>

      {error ? (
        <View style={[styles.errorWrap, { backgroundColor: colors.secondary }]}>
          <Text style={[styles.errorText, { color: colors.destructive }]}>{error}</Text>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  loadingWrap: { alignItems: "center", justifyContent: "center", paddingHorizontal: 16, gap: 10 },
  content: { paddingHorizontal: 16 },
  backBtn: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 12, alignSelf: "flex-start" },
  backText: { fontSize: 13, fontFamily: "Inter_500Medium" },
  header: { marginBottom: 14 },
  title: { fontSize: 28, fontFamily: "Inter_700Bold", letterSpacing: -0.4 },
  subtitle: { marginTop: 6, fontSize: 13, fontFamily: "Inter_400Regular" },
  card: { borderWidth: 1, borderRadius: 14, padding: 14, marginBottom: 12 },
  cardTitle: { fontSize: 14, fontFamily: "Inter_600SemiBold", marginBottom: 8 },
  label: { fontSize: 12, fontFamily: "Inter_500Medium", marginBottom: 6 },
  input: { borderWidth: 1, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, marginBottom: 10, fontFamily: "Inter_400Regular", fontSize: 14 },
  primaryBtn: { borderRadius: 10, minHeight: 42, alignItems: "center", justifyContent: "center", marginTop: 2 },
  primaryBtnText: { fontSize: 14, fontFamily: "Inter_600SemiBold" },
  switchModeBtn: { alignSelf: "center", marginTop: 10 },
  switchModeText: { fontSize: 13, fontFamily: "Inter_500Medium" },
  socialBtn: { borderWidth: 1, borderRadius: 10, minHeight: 42, alignItems: "center", justifyContent: "center", marginTop: 8 },
  socialBtnText: { fontSize: 13, fontFamily: "Inter_500Medium" },
  helpText: { fontSize: 12, lineHeight: 18, fontFamily: "Inter_400Regular" },
  errorWrap: { borderRadius: 10, paddingHorizontal: 12, paddingVertical: 9, marginTop: 2 },
  errorText: { fontSize: 12, fontFamily: "Inter_500Medium" },
});
