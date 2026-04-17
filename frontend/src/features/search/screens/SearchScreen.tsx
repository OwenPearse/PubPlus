import { StyleSheet, Text } from 'react-native';

import { ScreenContainer, ScreenSection, ScreenStatePlaceholder } from '../../../app/shell';

export function SearchScreen() {
  return (
    <ScreenContainer testID="search-screen" centered>
      <ScreenSection testID="search-screen-main">
        <Text testID="search-screen-title" style={styles.title}>
          Search
        </Text>
        <ScreenStatePlaceholder
          variant="empty"
          message="Search placeholder"
          testID="search-screen-placeholder"
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
