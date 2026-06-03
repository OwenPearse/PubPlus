import { useLocalSearchParams, useRouter } from "expo-router";
import React, { useMemo, useState } from "react";
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

import {
  AttributeFeatureCorrectionPicker,
  type FeatureCorrectionChoice,
} from "@/components/AttributeFeatureCorrectionPicker";
import { useAuthSession } from "@/hooks/useAuthSession";
import { useSearchFilters } from "@/hooks/useSearchFilters";
import { CorrectionDomain, useSubmissions } from "@/hooks/useSubmissions";
import { useColors } from "@/hooks/useColors";

const DOMAIN_OPTIONS: Array<{ value: CorrectionDomain; label: string }> = [
  { value: "profile", label: "Basic venue info" },
  { value: "location", label: "Location/address" },
  { value: "attributes", label: "Features & amenities" },
  { value: "hours", label: "Opening hours" },
];

export default function VenueCorrectionScreen() {
  const router = useRouter();
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const { id, name } = useLocalSearchParams<{ id: string; name?: string }>();
  const { isAuthenticated, loading: authLoading } = useAuthSession();
  const { submitCorrection, submitting, error, fieldErrors, authRequired } = useSubmissions();
  const {
    filters,
    loading: filtersLoading,
    error: filtersError,
    refresh: refreshFilters,
  } = useSearchFilters();

  const [domain, setDomain] = useState<CorrectionDomain>("profile");
  const [featureChoices, setFeatureChoices] = useState<Record<string, FeatureCorrectionChoice>>({});
  const [displayName, setDisplayName] = useState("");
  const [shortDescription, setShortDescription] = useState("");
  const [addressLine1, setAddressLine1] = useState("");
  const [postcode, setPostcode] = useState("");
  const [countryCode, setCountryCode] = useState("AU");
  const [hoursNote, setHoursNote] = useState("");
  const [note, setNote] = useState("");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [localValidationError, setLocalValidationError] = useState<string | null>(null);

  const topInset = Platform.OS === "web" ? 24 : insets.top + 8;
  const venueId = typeof id === "string" ? id : "";
  const venueName = typeof name === "string" && name.trim().length > 0 ? name : "this venue";

  const domainHelper = useMemo(() => {
    if (domain === "profile") return "Suggest corrected name or summary details.";
    if (domain === "location") return "Suggest corrected address information.";
    if (domain === "attributes") {
      return "Suggest whether features like beer garden, rooftop, pool table, sports screens or dog friendly access are available.";
    }
    return "Add a contextual note about opening hours changes.";
  }, [domain]);

  function handleFeatureChoiceChange(definitionId: string, choice: FeatureCorrectionChoice) {
    setFeatureChoices((prev) => ({ ...prev, [definitionId]: choice }));
  }

  async function handleSubmit() {
    setLocalValidationError(null);
    setSuccessMessage(null);
    if (!venueId) {
      setLocalValidationError("Venue ID is missing.");
      return;
    }

    if (domain === "profile" && !displayName.trim() && !shortDescription.trim()) {
      setLocalValidationError("Add at least one profile field.");
      return;
    }
    if (domain === "location" && !addressLine1.trim() && !postcode.trim()) {
      setLocalValidationError("Add at least one location field.");
      return;
    }
    if (domain === "hours" && !hoursNote.trim() && !note.trim()) {
      setLocalValidationError("Add a note for the hours correction.");
      return;
    }

    let proposedValues: Record<string, unknown> | { items: Array<{ attribute_definition_id: string; value_boolean: boolean }> };
    let submitNote: string | undefined = note.trim() || undefined;

    if (domain === "attributes") {
      const items = filters.venue_features
        .filter((feature) => {
          const choice = featureChoices[feature.definition_id] ?? "unchanged";
          return choice === "present" || choice === "absent";
        })
        .map((feature) => ({
          attribute_definition_id: feature.definition_id,
          value_boolean: (featureChoices[feature.definition_id] ?? "unchanged") === "present",
        }));
      if (items.length === 0) {
        setLocalValidationError("Mark at least one feature as Present or Not present.");
        return;
      }
      proposedValues = { items };
    } else if (domain === "profile") {
      proposedValues = {};
      if (displayName.trim()) proposedValues.display_name = displayName.trim();
      if (shortDescription.trim()) proposedValues.short_description = shortDescription.trim();
    } else if (domain === "location") {
      proposedValues = {};
      if (addressLine1.trim()) proposedValues.address_line_1 = addressLine1.trim();
      if (postcode.trim()) proposedValues.postcode = postcode.trim();
      if (countryCode.trim()) proposedValues.country_code = countryCode.trim().toUpperCase();
    } else {
      proposedValues = {
        regular_hours_json: [],
        exceptions_json: [],
      };
      submitNote = `${hoursNote.trim()} ${note.trim()}`.trim() || undefined;
    }

    try {
      const response = await submitCorrection({
        venue_id: venueId,
        domain,
        proposed_values: proposedValues,
        note: submitNote,
      });
      setSuccessMessage(response.message);
    } catch {
      // handled in hook state
    }
  }

  if (authLoading) {
    return (
      <View style={[styles.authWrap, styles.centerWrap, { backgroundColor: colors.background, paddingTop: topInset }]}>
        <ActivityIndicator color={colors.primary} />
        <Text style={[styles.subtitle, { color: colors.mutedForeground }]}>Checking sign-in...</Text>
      </View>
    );
  }

  if (!isAuthenticated || authRequired) {
    return (
      <View style={[styles.authWrap, { backgroundColor: colors.background, paddingTop: topInset }]}>
        <Text style={[styles.title, { color: colors.foreground }]}>Sign in required</Text>
        <Text style={[styles.subtitle, { color: colors.mutedForeground }]}>
          Sign in to submit a correction for {venueName}.
        </Text>
        <TouchableOpacity
          style={[styles.primaryBtn, { backgroundColor: colors.primary }]}
          onPress={() => router.push("/auth" as never)}
          accessibilityRole="button"
          accessibilityLabel="Sign in to submit correction"
          testID="correction-auth-cta"
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
      testID="correction-screen"
    >
      <Text style={[styles.title, { color: colors.foreground }]}>Submit correction</Text>
      <Text style={[styles.subtitle, { color: colors.mutedForeground }]}>Updating details for {venueName}</Text>

      <Text style={[styles.label, { color: colors.foreground }]}>Correction type</Text>
      <View style={styles.optionRow}>
        {DOMAIN_OPTIONS.map((option) => (
          <TouchableOpacity
            key={option.value}
            style={[
              styles.optionBtn,
              {
                backgroundColor: domain === option.value ? colors.primary : colors.card,
                borderColor: colors.border,
              },
            ]}
            onPress={() => setDomain(option.value)}
            accessibilityRole="button"
            accessibilityLabel={`Choose ${option.label}`}
            testID={`correction-domain-${option.value}`}
          >
            <Text
              style={{
                color: domain === option.value ? colors.primaryForeground : colors.foreground,
                fontFamily: "Inter_500Medium",
                fontSize: 12,
              }}
            >
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <Text style={[styles.helperText, { color: colors.mutedForeground }]}>{domainHelper}</Text>

      {domain === "profile" ? (
        <>
          <Text style={[styles.label, { color: colors.foreground }]}>Corrected name</Text>
          <TextInput
            value={displayName}
            onChangeText={setDisplayName}
            style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
            placeholder="Venue name"
            placeholderTextColor={colors.mutedForeground}
            accessibilityLabel="Corrected venue name"
            testID="correction-profile-display-name"
          />
          <Text style={[styles.label, { color: colors.foreground }]}>Summary</Text>
          <TextInput
            value={shortDescription}
            onChangeText={setShortDescription}
            style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
            placeholder="Short description"
            placeholderTextColor={colors.mutedForeground}
            accessibilityLabel="Corrected short description"
            testID="correction-profile-short-description"
          />
        </>
      ) : null}

      {domain === "location" ? (
        <>
          <Text style={[styles.label, { color: colors.foreground }]}>Address line 1</Text>
          <TextInput
            value={addressLine1}
            onChangeText={setAddressLine1}
            style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
            placeholder="Street address"
            placeholderTextColor={colors.mutedForeground}
            accessibilityLabel="Corrected address line 1"
            testID="correction-location-address-line-1"
          />
          <Text style={[styles.label, { color: colors.foreground }]}>Postcode</Text>
          <TextInput
            value={postcode}
            onChangeText={setPostcode}
            style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
            placeholder="3000"
            placeholderTextColor={colors.mutedForeground}
            accessibilityLabel="Corrected postcode"
            testID="correction-location-postcode"
          />
          <Text style={[styles.label, { color: colors.foreground }]}>Country code</Text>
          <TextInput
            value={countryCode}
            onChangeText={setCountryCode}
            style={[styles.input, { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card }]}
            placeholder="AU"
            placeholderTextColor={colors.mutedForeground}
            accessibilityLabel="Corrected country code"
            testID="correction-location-country-code"
            autoCapitalize="characters"
            maxLength={2}
          />
        </>
      ) : null}

      {domain === "attributes" ? (
        <AttributeFeatureCorrectionPicker
          features={filters.venue_features}
          choices={featureChoices}
          onChoiceChange={handleFeatureChoiceChange}
          loading={filtersLoading}
          error={filtersError}
          onRetry={refreshFilters}
        />
      ) : null}

      {domain === "hours" ? (
        <>
          <Text style={[styles.label, { color: colors.foreground }]}>Hours context</Text>
          <TextInput
            value={hoursNote}
            onChangeText={setHoursNote}
            style={[
              styles.input,
              styles.multiline,
              { borderColor: colors.border, color: colors.foreground, backgroundColor: colors.card },
            ]}
            placeholder="Example: Closes at 10pm on Sundays"
            placeholderTextColor={colors.mutedForeground}
            multiline
            accessibilityLabel="Opening hours correction context"
            testID="correction-hours-context"
          />
        </>
      ) : null}

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
        multiline
        maxLength={2000}
        accessibilityLabel="Correction note"
        testID="correction-note"
      />

      {localValidationError ? <Text style={[styles.errorText, { color: colors.destructive }]}>{localValidationError}</Text> : null}
      {error ? <Text style={[styles.errorText, { color: colors.destructive }]}>{error}</Text> : null}
      {fieldErrors ? (
        <Text style={[styles.helperText, { color: colors.destructive }]} testID="correction-field-errors">
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
        accessibilityLabel="Submit venue correction"
        testID="correction-submit-button"
      >
        {submitting ? (
          <ActivityIndicator color={colors.primaryForeground} />
        ) : (
          <Text style={[styles.primaryText, { color: colors.primaryForeground }]}>Submit correction</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { paddingHorizontal: 16 },
  authWrap: { flex: 1, paddingHorizontal: 16 },
  centerWrap: { justifyContent: "center", alignItems: "center" },
  title: { fontFamily: "Inter_700Bold", fontSize: 24 },
  subtitle: { fontFamily: "Inter_400Regular", fontSize: 13, marginTop: 6, marginBottom: 14 },
  label: { fontFamily: "Inter_500Medium", fontSize: 13, marginBottom: 6, marginTop: 4 },
  helperText: { fontFamily: "Inter_400Regular", fontSize: 12, marginBottom: 10 },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 10,
    fontFamily: "Inter_400Regular",
  },
  multiline: { minHeight: 84, textAlignVertical: "top" },
  optionRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 8 },
  optionBtn: { borderWidth: 1, borderRadius: 18, paddingVertical: 8, paddingHorizontal: 12 },
  primaryBtn: { minHeight: 42, borderRadius: 10, alignItems: "center", justifyContent: "center", marginTop: 8 },
  primaryText: { fontFamily: "Inter_600SemiBold", fontSize: 14 },
  errorText: { fontFamily: "Inter_500Medium", fontSize: 12, marginBottom: 8 },
  successText: { fontFamily: "Inter_500Medium", fontSize: 12, marginBottom: 8 },
});
