import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

type PlaceholderVariant = 'loading' | 'empty';

type ScreenStatePlaceholderProps = {
  variant: PlaceholderVariant;
  message?: string;
  testID?: string;
};

const defaultCopy: Record<PlaceholderVariant, string> = {
  loading: 'Loading…',
  empty: 'Nothing to show yet',
};

/** Minimal loading / empty states for list-driven screens in later stages. */
export function ScreenStatePlaceholder({
  variant,
  message,
  testID,
}: ScreenStatePlaceholderProps) {
  const label = message ?? defaultCopy[variant];

  return (
    <View style={styles.wrap} testID={testID}>
      {variant === 'loading' ? (
        <ActivityIndicator style={styles.spinner} accessibilityLabel="Loading" />
      ) : null}
      <Text style={styles.text}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  spinner: {
    marginBottom: 12,
  },
  text: {
    fontSize: 15,
    color: '#555',
    textAlign: 'center',
  },
});
