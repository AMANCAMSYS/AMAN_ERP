/**
 * Suppliers Screen — الموردون
 * Lists suppliers from /parties/suppliers
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TextInput,
  RefreshControl, ActivityIndicator, TouchableOpacity, Linking,
} from 'react-native';
import { useNetwork } from '../../../App';
import { supplierAPI } from '../../services/api';

export default function SuppliersScreen() {
  const { isConnected } = useNetwork();
  const [suppliers, setSuppliers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      if (isConnected) {
        const res = await supplierAPI.list({ limit: 200 });
        setSuppliers(Array.isArray(res) ? res : []);
      }
    } catch (e) {
      setError(e.message || 'حدث خطأ أثناء تحميل الموردين');
      setSuppliers([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const filtered = !search
    ? suppliers
    : suppliers.filter(
        (s) =>
          (s.name || '').toLowerCase().includes(search.toLowerCase()) ||
          (s.phone || '').includes(search)
      );

  const renderItem = ({ item }) => {
    const balance = Number(item.balance ?? 0);
    const credit = Number(item.credit_limit ?? 0);
    const isActive = item.is_active !== false;

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={[styles.badge, isActive ? styles.badgeActive : styles.badgeInactive]}>
            <Text style={[styles.badgeText, isActive ? styles.badgeTextActive : styles.badgeTextInactive]}>
              {isActive ? 'نشط' : 'غير نشط'}
            </Text>
          </View>
          <View style={styles.nameBlock}>
            <Text style={styles.supplierName}>{item.name || '—'}</Text>
            {item.name_en ? (
              <Text style={styles.supplierNameEn}>{item.name_en}</Text>
            ) : null}
            {item.tax_number ? (
              <Text style={styles.taxNumber}>الرقم الضريبي: {item.tax_number}</Text>
            ) : null}
          </View>
        </View>

        {/* Contact */}
        <View style={styles.contactRow}>
          {item.phone ? (
            <TouchableOpacity
              style={styles.contactBtn}
              onPress={() => Linking.openURL(`tel:${item.phone}`)}
            >
              <Text style={styles.contactText}>📞 {item.phone}</Text>
            </TouchableOpacity>
          ) : null}
          {item.email ? (
            <TouchableOpacity
              style={styles.contactBtn}
              onPress={() => Linking.openURL(`mailto:${item.email}`)}
            >
              <Text style={[styles.contactText, { color: '#1565c0' }]}>✉ {item.email}</Text>
            </TouchableOpacity>
          ) : null}
        </View>

        {item.address ? (
          <Text style={styles.address}>📍 {item.address}</Text>
        ) : null}

        {/* Financials */}
        <View style={styles.statsRow}>
          <View style={styles.statCell}>
            <Text style={styles.statLabel}>الرصيد</Text>
            <Text style={[styles.statValue, { color: balance > 0 ? '#c62828' : '#2e7d32' }]}>
              {balance.toLocaleString('ar-SA', { minimumFractionDigits: 2 })} ر.س
            </Text>
          </View>
          {credit > 0 ? (
            <View style={styles.statCell}>
              <Text style={styles.statLabel}>حد الائتمان</Text>
              <Text style={styles.statValue}>
                {credit.toLocaleString('ar-SA', { minimumFractionDigits: 2 })} ر.س
              </Text>
            </View>
          ) : null}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.searchRow}>
        <TextInput
          style={styles.searchInput}
          placeholder="بحث باسم المورد أو الهاتف..."
          placeholderTextColor="#90a4ae"
          value={search}
          onChangeText={setSearch}
          textAlign="right"
        />
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#2e7d32" />
          <Text style={styles.loadingText}>جارٍ التحميل...</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={() => { setLoading(true); load(); }}>
            <Text style={styles.retryText}>إعادة المحاولة</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderItem}
          contentContainerStyle={filtered.length === 0 ? styles.emptyContainer : styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor="#2e7d32" />}
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyIcon}>🏭</Text>
              <Text style={styles.emptyTitle}>لا يوجد موردون</Text>
              <Text style={styles.emptySubtitle}>لم يتم إضافة أي مورد بعد</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f1f8e9' },
  searchRow: { padding: 12, paddingTop: 16 },
  searchInput: {
    backgroundColor: '#fff', borderRadius: 10, padding: 12,
    fontSize: 15, color: '#1a2332', elevation: 2,
  },
  listContent: { paddingHorizontal: 12, paddingBottom: 24 },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 80 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 60 },
  loadingText: { marginTop: 12, color: '#2e7d32', fontSize: 15 },
  errorText: { color: '#c62828', fontSize: 15, textAlign: 'center', marginHorizontal: 24 },
  retryBtn: { marginTop: 16, backgroundColor: '#2e7d32', paddingHorizontal: 24, paddingVertical: 10, borderRadius: 8 },
  retryText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: '#1a2332', marginBottom: 6 },
  emptySubtitle: { fontSize: 14, color: '#78909c', textAlign: 'center' },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginBottom: 12, elevation: 2,
  },
  cardHeader: { flexDirection: 'row-reverse', marginBottom: 10, gap: 10 },
  nameBlock: { flex: 1, alignItems: 'flex-end' },
  supplierName: { fontSize: 16, fontWeight: '700', color: '#1a2332', textAlign: 'right' },
  supplierNameEn: { fontSize: 13, color: '#546e7a', textAlign: 'right' },
  taxNumber: { fontSize: 12, color: '#78909c', textAlign: 'right', marginTop: 2 },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  badgeActive: { backgroundColor: '#e8f5e9' },
  badgeInactive: { backgroundColor: '#ffebee' },
  badgeText: { fontSize: 12, fontWeight: '600' },
  badgeTextActive: { color: '#2e7d32' },
  badgeTextInactive: { color: '#c62828' },
  contactRow: { flexDirection: 'row-reverse', flexWrap: 'wrap', gap: 8, marginBottom: 6 },
  contactBtn: { paddingVertical: 4, paddingHorizontal: 2 },
  contactText: { fontSize: 13, color: '#2e7d32' },
  address: { fontSize: 13, color: '#546e7a', textAlign: 'right', marginBottom: 8 },
  statsRow: { flexDirection: 'row-reverse', gap: 10, marginTop: 10 },
  statCell: { flex: 1, backgroundColor: '#f1f8e9', borderRadius: 8, padding: 10, alignItems: 'center' },
  statLabel: { fontSize: 11, color: '#78909c', marginBottom: 2 },
  statValue: { fontSize: 14, fontWeight: '700', color: '#1a2332', textAlign: 'center' },
});
