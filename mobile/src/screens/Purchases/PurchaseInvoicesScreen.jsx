/**
 * Purchase Invoices Screen — فواتير المشتريات
 * Lists purchase invoices from /buying/invoices
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TextInput,
  RefreshControl, ActivityIndicator, TouchableOpacity,
} from 'react-native';
import { useNetwork } from '../../../App';
import { purchaseInvoiceAPI } from '../../services/api';

const STATUS_FILTERS = [
  { key: 'all', label: 'الكل' },
  { key: 'draft', label: 'مسودة' },
  { key: 'posted', label: 'مرحّل' },
  { key: 'paid', label: 'مدفوع' },
  { key: 'partial', label: 'جزئي' },
];

const STATUS_LABEL = {
  draft: { label: 'مسودة', color: '#546e7a', bg: '#eceff1' },
  posted: { label: 'مرحّل', color: '#1565c0', bg: '#e3f2fd' },
  paid: { label: 'مدفوع', color: '#2e7d32', bg: '#e8f5e9' },
  partial: { label: 'جزئي', color: '#e65100', bg: '#fff3e0' },
};

export default function PurchaseInvoicesScreen() {
  const { isConnected } = useNetwork();
  const [invoices, setInvoices] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      if (isConnected) {
        const params = { limit: 100 };
        const res = await purchaseInvoiceAPI.list(params);
        setInvoices(Array.isArray(res) ? res : []);
      }
    } catch (e) {
      setError(e.message || 'حدث خطأ أثناء تحميل الفواتير');
      setInvoices([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const filtered = invoices.filter((inv) => {
    const matchStatus = statusFilter === 'all' || inv.status === statusFilter;
    const matchSearch = !search || (
      (inv.invoice_number || '').toLowerCase().includes(search.toLowerCase()) ||
      (inv.supplier_name || '').toLowerCase().includes(search.toLowerCase())
    );
    return matchStatus && matchSearch;
  });

  const renderItem = ({ item }) => {
    const st = STATUS_LABEL[item.status] || { label: item.status || '—', color: '#546e7a', bg: '#eceff1' };
    const total = Number(item.total ?? 0);
    const paid = Number(item.paid ?? 0);
    const remaining = total - paid;

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={[styles.badge, { backgroundColor: st.bg }]}>
            <Text style={[styles.badgeText, { color: st.color }]}>{st.label}</Text>
          </View>
          <Text style={styles.invoiceNumber}>{item.invoice_number || `#${item.id}`}</Text>
        </View>

        <Text style={styles.supplierName}>{item.supplier_name || '—'}</Text>

        {item.invoice_date ? (
          <Text style={styles.date}>
            📅 {new Date(item.invoice_date).toLocaleDateString('ar-SA')}
          </Text>
        ) : null}

        <View style={styles.amountsRow}>
          <View style={styles.amountCell}>
            <Text style={styles.amountLabel}>الإجمالي</Text>
            <Text style={styles.amountValue}>{total.toLocaleString('ar-SA', { minimumFractionDigits: 2 })} ر.س</Text>
          </View>
          {paid > 0 ? (
            <View style={styles.amountCell}>
              <Text style={styles.amountLabel}>المدفوع</Text>
              <Text style={[styles.amountValue, { color: '#2e7d32' }]}>
                {paid.toLocaleString('ar-SA', { minimumFractionDigits: 2 })} ر.س
              </Text>
            </View>
          ) : null}
          {remaining > 0 ? (
            <View style={styles.amountCell}>
              <Text style={styles.amountLabel}>المتبقي</Text>
              <Text style={[styles.amountValue, { color: '#c62828' }]}>
                {remaining.toLocaleString('ar-SA', { minimumFractionDigits: 2 })} ر.س
              </Text>
            </View>
          ) : null}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Search */}
      <View style={styles.searchRow}>
        <TextInput
          style={styles.searchInput}
          placeholder="بحث برقم الفاتورة أو المورد..."
          placeholderTextColor="#90a4ae"
          value={search}
          onChangeText={setSearch}
          textAlign="right"
        />
      </View>

      {/* Status Chips */}
      <View style={styles.chipBar}>
        {STATUS_FILTERS.map((f) => (
          <TouchableOpacity
            key={f.key}
            style={[styles.chip, statusFilter === f.key && styles.chipActive]}
            onPress={() => setStatusFilter(f.key)}
          >
            <Text style={[styles.chipText, statusFilter === f.key && styles.chipTextActive]}>
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#6a1b9a" />
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
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor="#6a1b9a" />}
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyIcon}>🧾</Text>
              <Text style={styles.emptyTitle}>لا توجد فواتير مشتريات</Text>
              <Text style={styles.emptySubtitle}>لم يتم إنشاء أي فاتورة شراء بعد</Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f0fa' },
  searchRow: { padding: 12, paddingTop: 16 },
  searchInput: {
    backgroundColor: '#fff', borderRadius: 10, padding: 12,
    fontSize: 15, color: '#1a2332', elevation: 2, textAlign: 'right',
  },
  chipBar: {
    flexDirection: 'row-reverse', paddingHorizontal: 12, paddingBottom: 8,
    flexWrap: 'wrap', gap: 6,
  },
  chip: {
    paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20,
    backgroundColor: '#fff', borderWidth: 1.5, borderColor: '#ce93d8',
  },
  chipActive: { backgroundColor: '#7b1fa2', borderColor: '#7b1fa2' },
  chipText: { fontSize: 13, color: '#6a1b9a', fontWeight: '500' },
  chipTextActive: { color: '#fff' },
  listContent: { paddingHorizontal: 12, paddingBottom: 24 },
  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 80 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 60 },
  loadingText: { marginTop: 12, color: '#7b1fa2', fontSize: 15 },
  errorText: { color: '#c62828', fontSize: 15, textAlign: 'center', marginHorizontal: 24 },
  retryBtn: { marginTop: 16, backgroundColor: '#7b1fa2', paddingHorizontal: 24, paddingVertical: 10, borderRadius: 8 },
  retryText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: '#1a2332', marginBottom: 6 },
  emptySubtitle: { fontSize: 14, color: '#78909c', textAlign: 'center' },
  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 16,
    marginBottom: 12, elevation: 2,
  },
  cardHeader: { flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  invoiceNumber: { fontSize: 16, fontWeight: '700', color: '#1a2332' },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  badgeText: { fontSize: 12, fontWeight: '600' },
  supplierName: { fontSize: 14, color: '#37474f', textAlign: 'right', marginBottom: 4 },
  date: { fontSize: 13, color: '#78909c', textAlign: 'right', marginBottom: 8 },
  amountsRow: { flexDirection: 'row-reverse', gap: 12, marginTop: 8 },
  amountCell: { flex: 1, alignItems: 'center', backgroundColor: '#f5f0fa', borderRadius: 8, padding: 8 },
  amountLabel: { fontSize: 11, color: '#78909c', marginBottom: 2, textAlign: 'center' },
  amountValue: { fontSize: 13, fontWeight: '700', color: '#1a2332', textAlign: 'center' },
});
