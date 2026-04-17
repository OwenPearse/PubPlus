import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { shellSpacing } from './constants';

type ScreenSectionProps = {
  children: ReactNode;
  testID?: string;
};

/** Vertical grouping with consistent section spacing between blocks on a screen. */
export function ScreenSection({ children, testID }: ScreenSectionProps) {
  return (
    <View style={styles.section} testID={testID}>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    width: '100%',
    marginBottom: shellSpacing.sectionGap,
  },
});
