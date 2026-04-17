import { StyleSheet, Text } from 'react-native';

import { ScreenContainer, ScreenSection, ScreenStatePlaceholder } from '../../../app/shell';

export function HomeScreen() {
  return (
    <ScreenContainer testID="home-screen" centered>
      <ScreenSection testID="home-screen-main">
        <Text testID="home-screen-title" style={styles.title}>
          Home
        </Text>
        <ScreenStatePlaceholder
          variant="empty"
          message="Discovery placeholder"
          testID="home-screen-placeholder"
        />
      </ScreenSection>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
    width: '100%',
  },
});
