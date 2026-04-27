import { useRouter } from "expo-router";
import React, { useState } from "react";
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
import { useSubmissions } from "@/hooks/useSubmissions";
import { useColors } from "@/hooks/useColors";

export default function SuggestVenueScreen() {
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { isAuthenticated } = useAuthSession();
  const { suggestNewVenue, submitting, error, fieldErrors, authRequired } = useSubmissions();

  const [name, setName] = useState("");
  const [addressLine1, setAddressLine1] = useState("");
  const [addressLine2, setAddressLine2] = useState("");
  const [postcode, setPostcode] = useState("");
  const [countryCode, setCountryCode] = useState("AU");
  const [note, setNote] = useState("");
  const [localValidationError, setLocalValidationError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const topInset = Platform.OS === "web" ? 24 : insets.top + 8;

  async function handleSubmit() {
    setLocalValidationError(null);
    setSuccessMessage(null);
    if (!name.trim()) {
      setLocalValidationError("Venue name is required.");
      return;
    }
    if (!addressLine1.trim()) {
      setLocalValidationError("Address line 1 is required.");
      return;
    }
    if (countryCode.trim() && countryCode.trim().length !== 2) {
      setLocalValidationError("Country code must be 2 letters.");
      return;
    }

    try {
      const response = await suggestNewVenue({
        name: name.trim(),
        address_line_1: addressLine1.trim(),
        address_line_2: addressLine2.trim() || undefined,
        postcode: postcode.trim() || undefined,
        country_code: countryCode.trim() ? countryCode.trim().toUpperCase() : undefined,
        note: note.trim() || undefined,
      });
      setSuccessMessage(response.message);
      setName("");
      setAddressLine1("");
      setAddressLine2("");
      setPostcode("");
      setNote("");
    } catch {
      // handled by hook state
    }
  }

  if (!isAuthenticated || authRequired) {
    return (
      <View style={[styles.authWrap, { backgroundColor: colors.background, paddingTop: topInset }]}>
        <Text style={[styles.title, { color: colors.foreground }]}>Sign in required</Text>
        <Text style={[styles.subtitle, { color: colors.mutedForeground }]}>
          Sign in to suggest a venue for review.
        </Text>
        <TouchableOpacity
          style={[styles.primaryBtn, { backgroundColor: colors.primary }]}
          onPress={() => router.push("/auth" as never)}
          accessibilityRole="button"
          accessibilityLabel="Sign in to suggest a new venue"
          testID="suggest-venue-auth-cta"
        >
          <Text style={[styles.primaryText, { color: colors.primaryForeground }]}>Sign in</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: colors.background }]}
      contentContainerStyle={[styles.content, { paddingTop: topInset, paddingBottom: insets.bottom + 24 }]}
      keyboardShouldPersistTaps="handled"
      testID="suggest-venue-screen"
    >
      <Text style={[styles.title, { color: colors.foreground }]}>Suggest a new venue</Text>
      <Text style={[styles.subtitle, { color: colors.mutedForeground }]}>
        Share a missing venue and the team will review it before publishing.
      </Text>

      <Text style={[styles.label, { color: colors.foreground }]}>Venue name *</Text>
      <TextInput
        value={name}
        onChangeText={setName}
        style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
        placeholder="Venue name"
        placeholderTextColor={colors.mutedForeground}
        accessibilityLabel="Suggested venue name"
        testID="suggest-venue-name"
      />

      <Text style={[styles.label, { color: colors.foreground }]}>Address line 1 *</Text>
      <TextInput
        value={addressLine1}
        onChangeText={setAddressLine1}
        style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
        placeholder="Street address"
        placeholderTextColor={colors.mutedForeground}
        accessibilityLabel="Suggested venue address line 1"
        testID="suggest-venue-address-line-1"
      />

      <Text style={[styles.label, { color: colors.foreground }]}>Address line 2</Text>
      <TextInput
        value={addressLine2}
        onChangeText={setAddressLine2}
        style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
        placeholder="Suite, unit, or level"
        placeholderTextColor={colors.mutedForeground}
        accessibilityLabel="Suggested venue address line 2"
        testID="suggest-venue-address-line-2"
      />

      <Text style={[styles.label, { color: colors.foreground }]}>Postcode</Text>
      <TextInput
        value={postcode}
        onChangeText={setPostcode}
        style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
        placeholder="3000"
        placeholderTextColor={colors.mutedForeground}
        accessibilityLabel="Suggested venue postcode"
        testID="suggest-venue-postcode"
      />

      <Text style={[styles.label, { color: colors.foreground }]}>Country code</Text>
      <TextInput
        value={countryCode}
        onChangeText={setCountryCode}
        style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
        placeholder="AU"
        placeholderTextColor={colors.mutedForeground}
        accessibilityLabel="Suggested venue country code"
        testID="suggest-venue-country-code"
        maxLength={2}
        autoCapitalize="characters"
      />

      <Text style={[styles.label, { color: colors.foreground }]}>Optional note</Text>
      <TextInput
        value={note}
        onChangeText={setNote}
        style={[
          styles.input,
          styles.multiline,
          { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card },
        ]}
        placeholder="Any extra context for moderation review"
        placeholderTextColor={colors.mutedForeground}
        accessibilityLabel="Suggested venue note"
        testID="suggest-venue-note"
        multiline
        maxLength={2000}
      />

      {localValidationError ? <Text style={[styles.errorText, { color: colors.destructive }]}>{localValidationError}</Text> : null}
      {error ? <Text style={[styles.errorText, { color: colors.destructive }]}>{error}</Text> : null}
      {fieldErrors ? (
        <Text style={[styles.errorText, { color: colors.destructive }]} testID="suggest-venue-field-errors">
          {Object.entries(fieldErrors)
            .map(([key, value]) => `${key}: ${value.join(", ")}`)
            .join(" | ")}
        </Text>
      ) : null}
      {successMessage ? <Text style={[styles.successText, { color: colors.primary }]}>{successMessage}</Text> : null}

      <TouchableOpacity
        style={[styles.primaryBtn, { backgroundColor: colors.primary }]}
        onPress={handleSubmit}
        disabled={submitting}
        accessibilityRole="button"
        accessibilityLabel="Submit new venue suggestion"
        testID="suggest-venue-submit-button"
      >
        {submitting ? (
          <ActivityIndicator color={colors.primaryForeground} />
        ) : (
          <Text style={[styles.primaryText, { color: colors.primaryForeground }]}>Submit suggestion</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { paddingHorizontal: 16 },
  authWrap: { flex: 1, paddingHorizontal: 16 },
  title: { fontFamily: "Inter_700Bold", fontSize: 24 },
  subtitle: { fontFamily: "Inter_400Regular", fontSize: 13, marginTop: 6, marginBottom: 14 },
  label: { fontFamily: "Inter_500Medium", fontSize: 13, marginBottom: 6, marginTop: 4 },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 10,
    fontFamily: "Inter_400Regular",
  },
  multiline: { minHeight: 84, textAlignVertical: "top" },
  primaryBtn: { minHeight: 42, borderRadius: 10, alignItems: "center", justifyContent: "center", marginTop: 8 },
  primaryText: { fontFamily: "Inter_600SemiBold", fontSize: 14 },
  errorText: { fontFamily: "Inter_500Medium", fontSize: 12, marginBottom: 8 },
  successText: { fontFamily: "Inter_500Medium", fontSize: 12, marginBottom: 8 },
});
