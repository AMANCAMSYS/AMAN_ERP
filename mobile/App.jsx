/**
 * AMAN ERP Mobile App - Entry Point
 * React Native app for inventory, quotations, orders, and approvals with offline sync.
 */
import React, { useState, useEffect, createContext, useContext } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

import LoginScreen from './src/screens/Auth/LoginScreen';
import DashboardScreen from './src/screens/Dashboard/DashboardScreen';
import InventoryScreen from './src/screens/Inventory/InventoryScreen';
import QuotationForm from './src/screens/Quotations/QuotationForm';
import OrderList from './src/screens/Orders/OrderList';
import ApprovalList from './src/screens/Approvals/ApprovalList';
import ConflictScreen from './src/screens/Sync/ConflictScreen';
import CustomersScreen from './src/screens/Customers/CustomersScreen';
import InvoicesScreen from './src/screens/Invoices/InvoicesScreen';
import EmployeesScreen from './src/screens/HR/EmployeesScreen';
import ReportsScreen from './src/screens/Reports/ReportsScreen';
import PurchaseInvoicesScreen from './src/screens/Purchases/PurchaseInvoicesScreen';
import SuppliersScreen from './src/screens/Suppliers/SuppliersScreen';

// ── Auth Context ──────────────────────────────────────────────────────────────
export const AuthContext = createContext(null);
export const NetworkContext = createContext({ isConnected: true });

export function useAuth() {
  return useContext(AuthContext);
}

export function useNetwork() {
  return useContext(NetworkContext);
}

const Stack = createNativeStackNavigator();

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(true);

  // Restore token from storage on startup
  useEffect(() => {
    (async () => {
      try {
        const saved = await AsyncStorage.getItem('auth_token');
        const savedUser = await AsyncStorage.getItem('auth_user');
        if (saved) setToken(saved);
        if (savedUser) setUser(JSON.parse(savedUser));
      } catch {
        // ignore
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  // Monitor network connectivity
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      setIsConnected(state.isConnected ?? true);
    });
    return () => unsubscribe();
  }, []);

  const authActions = {
    token,
    user,
    signIn: async (newToken, userData) => {
      await AsyncStorage.setItem('auth_token', newToken);
      await AsyncStorage.setItem('auth_user', JSON.stringify(userData));
      setToken(newToken);
      setUser(userData);
    },
    signOut: async () => {
      await AsyncStorage.multiRemove(['auth_token', 'auth_user']);
      setToken(null);
      setUser(null);
    },
  };

  if (isLoading) return null; // splash screen placeholder

  return (
    <SafeAreaProvider>
    <AuthContext.Provider value={authActions}>
      <NetworkContext.Provider value={{ isConnected }}>
        <NavigationContainer>
          <Stack.Navigator
            screenOptions={{
              headerStyle: { backgroundColor: '#1976d2' },
              headerTintColor: '#fff',
              headerTitleStyle: { fontWeight: 'bold' },
            }}
          >
            {!token ? (
              <Stack.Screen
                name="Login"
                component={LoginScreen}
                options={{ headerShown: false }}
              />
            ) : (
              <>
                <Stack.Screen
                  name="Dashboard"
                  component={DashboardScreen}
                  options={{ title: 'لوحة التحكم' }}
                />
                <Stack.Screen
                  name="Inventory"
                  component={InventoryScreen}
                  options={{ title: 'المخزون' }}
                />
                <Stack.Screen
                  name="QuotationForm"
                  component={QuotationForm}
                  options={{ title: 'عرض سعر جديد' }}
                />
                <Stack.Screen
                  name="Orders"
                  component={OrderList}
                  options={{ title: 'الطلبات' }}
                />
                <Stack.Screen
                  name="Approvals"
                  component={ApprovalList}
                  options={{ title: 'الموافقات' }}
                />
                <Stack.Screen
                  name="Conflicts"
                  component={ConflictScreen}
                  options={{ title: 'حل التعارضات' }}
                />
                <Stack.Screen
                  name="Customers"
                  component={CustomersScreen}
                  options={{ title: 'العملاء (مبيعات)' }}
                />
                <Stack.Screen
                  name="Invoices"
                  component={InvoicesScreen}
                  options={{ title: 'فواتير المبيعات' }}
                />
                <Stack.Screen
                  name="PurchaseInvoices"
                  component={PurchaseInvoicesScreen}
                  options={{ title: 'فواتير المشتريات' }}
                />
                <Stack.Screen
                  name="Suppliers"
                  component={SuppliersScreen}
                  options={{ title: 'الموردون' }}
                />
                <Stack.Screen
                  name="Employees"
                  component={EmployeesScreen}
                  options={{ title: 'الموظفون' }}
                />
                <Stack.Screen
                  name="Reports"
                  component={ReportsScreen}
                  options={{ title: 'التقارير' }}
                />
              </>
            )}
          </Stack.Navigator>
        </NavigationContainer>
      </NetworkContext.Provider>
    </AuthContext.Provider>
    </SafeAreaProvider>
  );
}
