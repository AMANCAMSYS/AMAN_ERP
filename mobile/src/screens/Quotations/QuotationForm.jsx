/**
 * Quotation Form — create quotation online or queue offline.
 */
import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, Alert, ActivityIndicator,
} from 'react-native';
import { useNetwork } from '../../../App';
import { quotationAPI } from '../../services/api';
import { enqueue } from '../../services/syncService';

export default function QuotationForm({ navigation }) {
  const { isConnected } = useNetwork();
  const [customerName, setCustomerName] = useState('');
  const [items, setItems] = useState([{ description: '', quantity: '', unit_price: '' }]);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const addLine = () => {
    setItems([...items, { description: '', quantity: '', unit_price: '' }]);
  };

  const updateLine = (index, field, value) => {
    const copy = [...items];
    copy[index] = { ...copy[index], [field]: value };
    setItems(copy);
  };

  const removeLine = (index) => {
    if (items.length <= 1) return;
    setItems(items.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!customerName.trim()) {
      Alert.alert('خطأ', 'يرجى إدخال اسم العميل');
      return;
    }
    const validItems = items.filter((i) => i.description && i.quantity && i.unit_price);
    if (validItems.length === 0) {
      Alert.alert('خطأ', 'يرجى إضافة بند واحد على الأقل');
      return;
    }

    const payload = {
      customer_name: customerName,
      notes,
      items: validItems.map((i) => ({
        description: i.description,
        quantity: parseFloat(i.quantity),
        unit_price: parseFloat(i.unit_price),
      })),
    };

    setLoading(true);
    try {
      if (isConnected) {
        await quotationAPI.create(payload);
        Alert.alert('تم', 'تم إنشاء عرض السعر بنجاح', [
          { text: 'حسنًا', onPress: () => navigation.goBack() },
        ]);
      } else {
        await enqueue('quotation', null, 'create', payload);
        Alert.alert('تم الحفظ محليًا', 'سيتم إرسال عرض السعر عند استعادة الاتصال', [
          { text: 'حسنًا', onPress: () => navigation.goBack() },
        ]);
      }
    } catch (err) {
      // Fallback to offline queue
      await enqueue('quotation', null, 'create', payload);
      Alert.alert('خطأ في الإرسال', 'تم حفظه محليًا وسيُرسل لاحقًا');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      {!isConnected && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>⚡ وضع عدم الاتصال — سيتم الحفظ محليًا</Text>
        </View>
      )}

      <Text style={styles.label}>اسم العميل</Text>
      <TextInput
        style={styles.input}
        value={customerName}
        onChangeText={setCustomerName}
        placeholder="أدخل اسم العميل"
        textAlign="right"
      />

      <Text style={styles.sectionTitle}>البنود</Text>
      {items.map((item, idx) => (
        <View key={idx} style={styles.lineCard}>
          <View style={styles.lineHeader}>
            <Text style={styles.lineNum}>بند {idx + 1}</Text>
            {items.length > 1 && (
              <TouchableOpacity onPress={() => removeLine(idx)}>
                <Text style={styles.removeBtn}>حذف</Text>
              </TouchableOpacity>
            )}
          </View>
          <TextInput
            style={styles.input}
            placeholder="الوصف"
            value={item.description}
            onChangeText={(v) => updateLine(idx, 'description', v)}
            textAlign="right"
          />
          <View style={styles.row}>
            <TextInput
              style={[styles.input, styles.halfInput]}
              placeholder="الكمية"
              value={item.quantity}
              onChangeText={(v) => updateLine(idx, 'quantity', v)}
              keyboardType="numeric"
              textAlign="right"
            />
            <TextInput
              style={[styles.input, styles.halfInput]}
              placeholder="سعر الوحدة"
              value={item.unit_price}
              onChangeText={(v) => updateLine(idx, 'unit_price', v)}
              keyboardType="numeric"
              textAlign="right"
            />
          </View>
        </View>
      ))}

      <TouchableOpacity style={styles.addBtn} onPress={addLine}>
        <Text style={styles.addBtnText}>+ إضافة بند</Text>
      </TouchableOpacity>

      <Text style={styles.label}>ملاحظات</Text>
      <TextInput
        style={[styles.input, styles.multiline]}
        value={notes}
        onChangeText={setNotes}
        placeholder="ملاحظات إضافية"
        multiline
        textAlign="right"
      />

      <TouchableOpacity
        style={[styles.submitBtn, loading && styles.disabled]}
        onPress={handleSubmit}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.submitText}>
            {isConnected ? 'إرسال عرض السعر' : 'حفظ محليًا'}
          </Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5', padding: 12 },
  offlineBanner: { backgroundColor: '#ff9800', padding: 8, borderRadius: 8, marginBottom: 12, alignItems: 'center' },
  offlineText: { color: '#fff', fontWeight: 'bold' },
  label: { fontSize: 15, fontWeight: '600', textAlign: 'right', marginBottom: 4, marginTop: 12 },
  input: {
    backgroundColor: '#fff', borderWidth: 1, borderColor: '#ddd', borderRadius: 8,
    padding: 12, fontSize: 15, marginBottom: 8,
  },
  multiline: { minHeight: 80, textAlignVertical: 'top' },
  sectionTitle: { fontSize: 17, fontWeight: 'bold', textAlign: 'right', marginTop: 16, marginBottom: 8 },
  lineCard: {
    backgroundColor: '#fff', borderRadius: 8, padding: 12, marginBottom: 8, elevation: 1,
  },
  lineHeader: { flexDirection: 'row-reverse', justifyContent: 'space-between', marginBottom: 8 },
  lineNum: { fontWeight: '600', textAlign: 'right' },
  removeBtn: { color: '#f44336', fontWeight: '600' },
  row: { flexDirection: 'row-reverse' },
  halfInput: { flex: 1, marginHorizontal: 4 },
  addBtn: { alignItems: 'center', padding: 12, borderWidth: 1, borderColor: '#1976d2', borderRadius: 8, borderStyle: 'dashed', marginBottom: 12 },
  addBtnText: { color: '#1976d2', fontWeight: '600' },
  submitBtn: { backgroundColor: '#1976d2', borderRadius: 8, padding: 16, alignItems: 'center', marginVertical: 16 },
  disabled: { opacity: 0.6 },
  submitText: { color: '#fff', fontSize: 18, fontWeight: '600' },
});
