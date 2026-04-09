/**
 * Login Screen — matches the web ERP login design.
 */
import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ActivityIndicator, KeyboardAvoidingView,
  Platform, ScrollView, I18nManager,
} from 'react-native';
import { useAuth } from '../../../App';
import { mobileAPI } from '../../services/api';

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [companyCode, setCompanyCode] = useState('');
  const [username, setUsername]       = useState('');
  const [password, setPassword]       = useState('');
  const [showPass, setShowPass]       = useState(false);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');

  const handleLogin = async () => {
    setError('');
    if (!companyCode.trim()) {
      setError('رمز الشركة مطلوب');
      return;
    }
    if (!username.trim() || !password) {
      setError('يرجى تعبئة جميع الحقول');
      return;
    }
    setLoading(true);
    try {
      const data = await mobileAPI.login(
        companyCode.trim(),
        username.trim(),
        password,
      );
      await signIn(data.access_token, data.user || { username });
    } catch (err) {
      setError(err.message || 'تحقق من البيانات وحاول مجدداً');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.card}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>نظام أمان ERP</Text>
            <Text style={styles.subtitle}>تسجيل الدخول للمتابعة</Text>
          </View>

          {/* Inline error */}
          {!!error && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Company Code — always required for mobile */}
          <View style={styles.formGroup}>
            <Text style={styles.label}>رمز الشركة</Text>
            <TextInput
              style={styles.input}
              placeholder="أدخل رمز الشركة"
              placeholderTextColor="#aaa"
              value={companyCode}
              onChangeText={setCompanyCode}
              autoCapitalize="none"
              autoCorrect={false}
              textAlign={I18nManager.isRTL ? 'right' : 'left'}
            />
            <Text style={styles.hint}>يمكن الحصول عليه من مسؤول الشركة</Text>
          </View>

          {/* Username */}
          <View style={styles.formGroup}>
            <Text style={styles.label}>اسم المستخدم</Text>
            <TextInput
              style={styles.input}
              placeholder="username"
              placeholderTextColor="#aaa"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              autoCorrect={false}
              textAlign={I18nManager.isRTL ? 'right' : 'left'}
            />
          </View>

          {/* Password */}
          <View style={styles.formGroup}>
            <Text style={styles.label}>كلمة المرور</Text>
            <View style={styles.inputRow}>
              <TextInput
                style={[styles.input, styles.inputFlex]}
                placeholder="••••••••"
                placeholderTextColor="#aaa"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPass}
                textAlign={I18nManager.isRTL ? 'right' : 'left'}
              />
              <TouchableOpacity style={styles.eyeBtn} onPress={() => setShowPass((p) => !p)}>
                <Text style={styles.eyeText}>{showPass ? 'إخفاء' : 'إظهار'}</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Submit */}
          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading
              ? <ActivityIndicator color="#fff" />
              : <Text style={styles.buttonText}>تسجيل الدخول</Text>}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const PRIMARY = '#1976d2';

const styles = StyleSheet.create({
  container:  { flex: 1, backgroundColor: '#f0f4f8' },
  scroll:     { flexGrow: 1, justifyContent: 'center', padding: 20 },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 28,
    elevation: 4, shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08, shadowRadius: 10,
  },
  header:   { alignItems: 'center', marginBottom: 24 },
  title:    { fontSize: 26, fontWeight: '700', color: PRIMARY, marginBottom: 4 },
  subtitle: { fontSize: 14, color: '#666' },
  errorBox: {
    backgroundColor: '#fff2f2', borderWidth: 1, borderColor: '#f5c6cb',
    borderRadius: 8, padding: 12, marginBottom: 16,
  },
  errorText: { color: '#c0392b', fontSize: 13, textAlign: 'right' },
  formGroup: { marginBottom: 16 },
  label:    { fontSize: 13, fontWeight: '600', color: '#333', marginBottom: 6, textAlign: 'right' },
  hint:     { fontSize: 11, color: '#999', marginTop: 4, textAlign: 'right' },
  input: {
    borderWidth: 1, borderColor: '#dce1e7', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 10,
    fontSize: 15, color: '#222', backgroundColor: '#fafbfc',
  },
  inputRow:  { flexDirection: 'row', alignItems: 'center' },
  inputFlex: { flex: 1, borderTopRightRadius: 0, borderBottomRightRadius: 0 },
  eyeBtn: {
    borderWidth: 1, borderColor: '#dce1e7', borderLeftWidth: 0,
    borderTopRightRadius: 8, borderBottomRightRadius: 8,
    paddingHorizontal: 12, paddingVertical: 10, backgroundColor: '#f5f7fa',
  },
  eyeText:      { fontSize: 13, color: PRIMARY },
  button: {
    backgroundColor: PRIMARY, borderRadius: 8,
    paddingVertical: 14, alignItems: 'center', marginTop: 8,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText:   { color: '#fff', fontSize: 16, fontWeight: '600' },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '600' },
});
