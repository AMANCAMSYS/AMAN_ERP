/**
 * Login Screen — company code + username + password authentication.
 */
import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ActivityIndicator, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useAuth } from '../../../App';
import { mobileAPI } from '../../services/api';

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [companyCode, setCompanyCode] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!companyCode || !username || !password) {
      Alert.alert('خطأ', 'يرجى تعبئة جميع الحقول');
      return;
    }
    setLoading(true);
    try {
      const data = await mobileAPI.login(companyCode, username, password);
      await signIn(data.access_token, data.user || { username });
    } catch (err) {
      Alert.alert('فشل تسجيل الدخول', err.message || 'تحقق من البيانات');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.card}>
        <Text style={styles.title}>نظام أمان ERP</Text>
        <Text style={styles.subtitle}>تسجيل الدخول</Text>

        <TextInput
          style={styles.input}
          placeholder="رمز الشركة"
          value={companyCode}
          onChangeText={setCompanyCode}
          autoCapitalize="none"
          textAlign="right"
        />
        <TextInput
          style={styles.input}
          placeholder="اسم المستخدم"
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          textAlign="right"
        />
        <TextInput
          style={styles.input}
          placeholder="كلمة المرور"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          textAlign="right"
        />

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleLogin}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>دخول</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', backgroundColor: '#f5f5f5', padding: 20 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 24,
    elevation: 4, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 8,
  },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', color: '#1976d2', marginBottom: 4 },
  subtitle: { fontSize: 16, textAlign: 'center', color: '#666', marginBottom: 24 },
  input: {
    borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 12, marginBottom: 14,
    fontSize: 16, backgroundColor: '#fafafa',
  },
  button: {
    backgroundColor: '#1976d2', borderRadius: 8, padding: 14, alignItems: 'center', marginTop: 8,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '600' },
});
