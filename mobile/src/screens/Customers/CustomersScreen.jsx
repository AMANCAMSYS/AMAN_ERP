/**
 * Customers Screen — list customers with search and details.
 * Matches web frontend: frontend/src/pages/Sales/CustomerList.jsx
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TextInput,
  RefreshControl, ActivityIndicator, TouchableOpacity, Linking,
} from 'react-native';
import { useNetwork } from '../../../App';
import { customerAPI } from '../../services/api';
import { formatAmount, getMobileCurrencyCode } from '../../utils/formatters';

const STATUS_MAP = {
  active: { label: 'نشط', color: '#2e7d32', bg: '#e8f5e9' },
  inactive: { label: 'غير نشط', color: '#c62828', bg: '#ffebee' },
  blocked: { label: 'محظور', color: '#e65100', bg: '#fff3e0' },
};

export default function CustomersScreen() {
  const { isConnected } = useNetwork();
  const [allCustomers, setAllCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [currencyCode, setCurrencyCode] = useState('SAR');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      setError('');
      if (isConnected) {
        const res = await customerAPI.list({ limit: 200 });
        setAllCustomers(Array.isArray(res) ? res : []);
      }
      setCurrencyCode(await getMobileCurrencyCode());
    } catch (e) { setError(e?.message || 'فشل تحميل العملاء'); }
    finally { setLoading(false); setRefreshing(false); }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const customers = search.trim()
    ? allCustomers.filter(c => {
        const q = search.trim().toLowerCase();
        return (c.name || '').toLowerCase().includes(q)
          || (c.party_code || '').toLowerCase().includes(q)
          || (c.phone || '').includes(q)
          || (c.mobile || '').includes(q);
      })
    : allCustomers;

  const renderItem = ({ item }) => {
    const statusCfg = STATUS_MAP[item.status] || STATUS_MAP.active;
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={[styles.badge, { backgroundColor: statusCfg.bg }]}>
            <Text style={[styles.badgeText, { color: statusCfg.color }]}>{statusCfg.label}</Text>
          </View>
          <View style={styles.cardTitles}>
            <Text style={styles.name}>{item.name}</Text>
            {item.party_code ? <Text style={styles.code}>{item.party_code}</Text> : null}
          </View>
        </View>

        {(item.phone || item.mobile) ? (
          <TouchableOpacity style={styles.contactRow} onPress={() => Linking.openURL(`tel:${item.phone || item.mobile}`)}>
            <Text style={styles.contactText}>{item.phone || item.mobile}</Text>
            <Text style={styles.contactIcon}>📞</Text>
          </TouchableOpacity>
        ) : null}

        {item.email ? (
          <TouchableOpacity style={styles.contactRow} onPress={() => Linking.openURL(`mailto:${item.email}`)}>
            <Text style={styles.contactText}>{item.email}</Text>
            <Text style={styles.contactIcon}>📧</Text>
          </TouchableOpacity>
        ) : null}

        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{formatAmount(item.current_balance ?? 0, currencyCode)}</Text>
            <Text style={styles.statLbl}>الرصيد</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{formatAmount(item.credit_limit ?? 0, currencyCode)}</Text>
            <Text style={styles.statLbl}>حد الائتمان</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{item.payment_terms ?? 30}</Text>
            <Text style={styles.statLbl}>أيام السداد</Text>
          </View>
        </View>

        {item.city || item.country ? (
          <Text style={styles.location}>📍 {[item.city, item.country].filter(Boolean).join('، ')}</Text>
        ) : null}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ تحميل العملاء...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.search}
          placeholder="بحث عن عميل..."
          value={search}
          onChangeText={setSearch}
          textAlign="right"
          placeholderTextColor="#90a4ae"
          returnKeyType="search"
        />
      </View>
      <FlatList
        data={customers}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }} tintColor="#1976d2" />
        }
        ListEmptyComponent={
          <View style={styles.emptyWrap}>
            <Text style={styles.emptyIcon}>{error ? '⚠️' : '👥'}</Text>
            <Text style={styles.empty}>{error || (search ? 'لا توجد نتائج' : 'لا يوجد عملاء')}</Text>
            {error ? <Text style={styles.retryHint}>اسحب للأسفل لإعادة المحاولة</Text> : null}
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f4f8' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f4f8' },
  loadingText: { marginTop: 12, color: '#546e7a', fontSize: 15 },

  searchWrap: {
    flexDirection: 'row-reverse', alignItems: 'center',
    backgroundColor: '#fff', margin: 14, borderRadius: 12,
    elevation: 2, paddingHorizontal: 14,
    borderWidth: 1, borderColor: '#e0e7ef',
  },
  searchIcon: { fontSize: 16, marginLeft: 8 },
  search: { flex: 1, paddingVertical: 13, fontSize: 15, color: '#1a2332' },

  list: { paddingHorizontal: 14, paddingBottom: 20 },

  card: {
    backgroundColor: '#fff', borderRadius: 12, marginBottom: 10, padding: 16,
    elevation: 3, shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07, shadowRadius: 4,
  },
  cardHeader: { flexDirection: 'row-reverse', alignItems: 'flex-start', marginBottom: 10 },
  cardTitles: { flex: 1 },
  name: { fontSize: 16, fontWeight: '700', color: '#1a2332', textAlign: 'right' },
  code: { fontSize: 12, color: '#90a4ae', textAlign: 'right', marginTop: 2 },
  badge: { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4, marginLeft: 0 },
  badgeText: { fontSize: 12, fontWeight: '700' },

  contactRow: {
    flexDirection: 'row-reverse', alignItems: 'center', marginBottom: 6,
  },
  contactIcon: { fontSize: 14, marginLeft: 8 },
  contactText: { fontSize: 13, color: '#1976d2' },

  statsRow: { flexDirection: 'row-reverse', backgroundColor: '#f8fafc', borderRadius: 8, marginTop: 10, overflow: 'hidden' },
  statBox: { flex: 1, alignItems: 'center', paddingVertical: 10 },
  statDivider: { width: 1, backgroundColor: '#e0e7ef' },
  statNum: { fontSize: 14, fontWeight: '700', color: '#1976d2' },
  statLbl: { fontSize: 10, color: '#90a4ae', marginTop: 2 },

  location: { fontSize: 12, color: '#546e7a', textAlign: 'right', marginTop: 8 },

  emptyWrap: { alignItems: 'center', paddingVertical: 60 },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  empty: { color: '#90a4ae', fontSize: 16 },
  retryHint: { color: '#b0bec5', fontSize: 13, marginTop: 6 },
});
