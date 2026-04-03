/**
 * AMAN ERP Mobile App - Entry Point
 * React Native app for inventory, quotations, orders, and approvals with offline sync.
 */
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Dashboard">
        {/* Screens will be added in Phase 9 (US7) */}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
