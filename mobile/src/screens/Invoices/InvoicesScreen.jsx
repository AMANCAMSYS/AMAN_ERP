/**
 * Invoices Screen — list sales invoices with search and status filters.
 * Matches web frontend: frontend/src/pages/Sales/InvoiceList.jsx
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TextInput,
  RefreshControl, ActivityIndicator, TouchableOpacity,
} from 'react-native';
import { useNetwork } from '../../../App';
import { invoiceAPI } from '../../services/api';
import { formatAmount, formatDate, getMobileCurrencyCode } from '../../utils/formatters';

const STATUS_MAP = {
  draft: { label: 'مسودة', color: '#546e7a', bg: '#eceff1' },
  posted: { label: 'مرحّلة', color: '#1565c0', bg: '#e3f2fd' },
  paid: { label: 'مدفوعة', color: '#2e7d32', bg: '#e8f5e9' },
  partial: { label: 'مدفوعة جزئيًا', color: '#e65100', bg: '#fff3e0' },
  overdue: { label: 'متأخرة', color: '#c62828', bg: '#ffebee' },
  cancelled: { label: 'ملغاة', color: '#78909c', bg: '#f5f5f5' },
};

const FILTERS = [
  { key: '', label: 'الكل' },
  { key: 'draft', label: 'مسودة' },
  { key: 'posted', label: 'مرحّلة' },
  { key: 'paid', label: 'مدفوعة' },
  { key: 'partial', label: 'جزئية' },
];

export default function InvoicesScreen() {
  const { isConnected } = useNetwork();
  const [invoices, setInvoices] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currencyCode, setCurrencyCode] = useState('SAR');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const params = { limit: 50 };
        if (search) params.search = search;
        if (statusFilter) params.status_filter = statusFilter;
        const res = await invoiceAPI.list(params);
        setInvoices(Array.isArray(res) ? res : []);
      }
      setCurrencyCode(await getMobileCurrencyCode());
    } catch { /* ignore */ }
    finally { setLoading(false); setRefreshing(false); }
  }, [isConnected, search, statusFilter]);

  useEffect(() => { load(); }, [load]);

  const renderItem = ({ item }) => {
    const statusKey = (item.status || 'draft').toLowerCase();
    const statusCfg = STATUS_MAP[statusKey] || { label: item.status, color: '#546e7a', bg: '#f5f5f5' };

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={[styles.badge, { backgroundColor: statusCfg.bg }]}>
            <Text style={[styles.badgeText, { color: statusCfg.color }]}>{statusCfg.label}</Text>
          </View>
          <View style={styles.cardTitles}>
            <Text style={styles.invoiceNum}>{item.invoice_number || `INV-${item.id}`}</Text>
            <Text style={styles.customer}>{item.customer_name || '—'}</Text>
          </View>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{formatAmount(item.total ?? 0, currencyCode)}</Text>
            <Text style={styles.statLbl}>الإجمالي</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={[styles.statNum, { color: '#2e7d32' }]}>{formatAmount(item.paid_amount ?? 0, currencyCode)}</Text>
            <Text style={styles.statLbl}>المدفوع</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={[styles.statNum, { color: (item.total - (item.paid_amount || 0)) > 0 ? '#c62828' : '#2e7d32' }]}>
              {formatAmount((item.total ?? 0) - (item.paid_amount ?? 0), currencyCode)}
            </Text>
            <Text style={styles.statLbl}>المتبقي</Text>
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.date}>{formatDate(item.invoice_date || item.created_at)}</Text>
          {item.due_date ? <Text style={styles.dueDate}>الاستحقاق: {formatDate(item.due_date)}</Text> : null}
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ تحميل الفواتير...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.search} placeholder="بحث عن فاتورة..."
          value={search} onChangeText={setSearch} onSubmitEditing={load}
          textAlign="right" placeholderTextColor="#90a4ae" returnKeyType="search"
        />
      </View>

      {/* Status filter chips */}
      <View style={styles.filterRow}>
        {FILTERS.map((f) => (
          <TouchableOpacity
            key={f.key}
            style={[styles.filterChip, statusFilter === f.key && styles.filterChipActive]}
            onPress={() => setStatusFilter(f.key)}
          >
            <Text style={[styles.filterText, statusFilter === f.key && styles.filterTextActive]}>{f.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={invoices}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }} tintColor="#1976d2" />
        }
        ListEmptyComponent={
          <View style={styles.emptyWrap}>
            <Text style={styles.emptyIcon}>🧾</Text>
            <Text style={styles.empty}>لا توجد فواتير</Text>
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
    backgroundColor: '#fff', margin: 14, marginBottom: 8, borderRadius: 12,
    elevation: 2, paddingHorizontal: 14, borderWidth: 1, borderColor: '#e0e7ef',
  },
  searchIcon: { fontSize: 16, marginLeft: 8 },
  search: { flex: 1, paddingVertical: 13, fontSize: 15, color: '#1a2332' },

  filterRow: {
    flexDirection: 'row-reverse', paddingHorizontal: 14,
    marginBottom: 10, gap: 8,
  },
  filterChip: {
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20,
    backgroundColor: '#fff', borderWidth: 1, borderColor: '#e0e7ef',
  },
  filterChipActive: { backgroundColor: '#1976d2', borderColor: '#1976d2' },
  filterText: { fontSize: 13, color: '#546e7a', fontWeight: '600' },
  filterTextActive: { color: '#fff' },

  list: { paddingHorizontal: 14, paddingBottom: 20 },

  card: {
    backgroundColor: '#fff', borderRadius: 12, marginBottom: 10, padding: 16,
    elevation: 3, shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07, shadowRadius: 4,
  },
  cardHeader: { flexDirection: 'row-reverse', alignItems: 'flex-start', marginBottom: 12 },
  cardTitles: { flex: 1 },
  invoiceNum: { fontSize: 17, fontWeight: '700', color: '#1a2332', textAlign: 'right' },
  customer: { fontSize: 13, color: '#546e7a', textAlign: 'right', marginTop: 2 },
  badge: { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4, marginLeft: 0 },
  badgeText: { fontSize: 12, fontWeight: '700' },

  statsRow: { flexDirection: 'row-reverse', backgroundColor: '#f8fafc', borderRadius: 8, overflow: 'hidden' },
  statBox: { flex: 1, alignItems: 'center', paddingVertical: 10 },
  statDivider: { width: 1, backgroundColor: '#e0e7ef' },
  statNum: { fontSize: 14, fontWeight: '700', color: '#1976d2' },
  statLbl: { fontSize: 10, color: '#90a4ae', marginTop: 2 },

  footer: {
    flexDirection: 'row-reverse', justifyContent: 'space-between',
    alignItems: 'center', marginTop: 12, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#f0f4f8',
  },
  date: { fontSize: 12, color: '#90a4ae' },
  dueDate: { fontSize: 12, color: '#e65100' },

  emptyWrap: { alignItems: 'center', paddingVertical: 60 },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  empty: { color: '#90a4ae', fontSize: 16 },
});
