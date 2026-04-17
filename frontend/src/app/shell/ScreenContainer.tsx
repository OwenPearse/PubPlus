import type { ReactNode } from 'react';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { shellSpacing } from './constants';

type ScreenContainerProps = {
  children: ReactNode;
  /** When true, main content is centered (placeholder screens). */
  centered?: boolean;
  testID?: string;
  contentStyle?: ViewStyle;
};

export function ScreenContainer({
  children,
  centered = false,
  testID,
  contentStyle,
}: ScreenContainerProps) {
  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <View
        testID={testID}
        style={[styles.content, centered && styles.contentCentered, contentStyle]}
      >
        {children}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    paddingHorizontal: shellSpacing.screenHorizontal,
  },
  contentCentered: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
