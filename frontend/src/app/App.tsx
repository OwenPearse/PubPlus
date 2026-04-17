import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { HomeScreen } from '../features/discovery/screens/HomeScreen';
import { SearchScreen } from '../features/search/screens/SearchScreen';

const Tab = createBottomTabNavigator();

/** Jest / web have no native safe-area event; without initial insets, Provider renders null children. */
const safeAreaFallbackInsets = { top: 0, right: 0, bottom: 0, left: 0 };

export default function App() {
  return (
    <SafeAreaProvider initialSafeAreaInsets={safeAreaFallbackInsets}>
      <StatusBar style="auto" />
      <NavigationContainer>
        <Tab.Navigator>
          <Tab.Screen
            name="Home"
            component={HomeScreen}
            options={{ tabBarButtonTestID: 'tab-home' }}
          />
          <Tab.Screen
            name="Search"
            component={SearchScreen}
            options={{ tabBarButtonTestID: 'tab-search' }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
