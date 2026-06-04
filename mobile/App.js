import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';

import AppNavigator from './src/navigation/AppNavigator';
import { requestPermissions } from './src/utils/notifications';

const GreenIOTTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: '#0f0f1a',
    card: '#0f0f1a',
    border: '#1e1e2e',
    primary: '#4ade80',
    text: '#ffffff',
  },
};

export default function App() {
  useEffect(() => {
    requestPermissions().catch(() => {
      // Permission request errors are non-fatal — ignore silently.
    });
  }, []);

  return (
    <SafeAreaProvider>
      <View style={styles.root}>
        <StatusBar style="light" backgroundColor="#0f0f1a" />
        <NavigationContainer theme={GreenIOTTheme}>
          <AppNavigator />
        </NavigationContainer>
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#0f0f1a',
  },
});
