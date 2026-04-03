/**
 * Order List — pending sales orders.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, RefreshControl, ActivityIndicator,
} from 'react-native';
import { useNetwork } from '../../../App';
import { orderAPI } from '../../services/api';
import { getOrders } from '../../store/offlineStore';
import { formatAmount, formatDate, getMobileCurrencyCode } from '../../utils/formatters';

const STATUS_LABELS = {
  draft: 'مسودة',
  confirmed: 'مؤكد',
  delivered: 'تم التسليم',
  cancelled: 'ملغي',
};
const STATUS_COLORS = {
  draft: '#ff9800',
  confirmed: '#2196f3',
  delivered: '#4caf50',
  cancelled: '#f44336',
};

export default function OrderList() {
  const { isConnected } = useNetwork();
  const [orders, setOrders] = useState([]);
  const [currencyCode, setCurrencyCode] = useState('SAR');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const res = await orderAPI.list({ limit: 50 });
        setOrders(res.items || res || []);
      } else {
        setOrders(await getOrders());
      }
      setCurrencyCode(await getMobileCurrencyCode());
    } catch {
      setOrders(await getOrders());
      setCurrencyCode(await getMobileCurrencyCode());
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const renderItem = ({ item }) => {
    const statusKey = (item.status || 'draft').toLowerCase();
    return (
      <View style={styles.card}>
        <View style={styles.header}>
          <Text style={styles.orderNum}>{item.order_number || `#${item.id}`}</Text>
          <View style={[styles.badge, { backgroundColor: STATUS_COLORS[statusKey] || '#999' }]}>
            <Text style={styles.badgeText}>{STATUS_LABELS[statusKey] || item.status}</Text>
          </View>
        </View>
        <Text style={styles.customer}>{item.customer_name || '—'}</Text>
        <View style={styles.footer}>
          <Text style={styles.amount}>{formatAmount(item.total_amount, item.currency || item.currency_code || currencyCode)}</Text>
          <Text style={styles.date}>
            {formatDate(item.created_at)}
          </Text>
        </View>
      </View>
    );
  };

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color="#1976d2" /></View>;
  }

  return (
    <View style={styles.container}>
      {!isConnected && (
        <View style={styles.offlineBanner}><Text style={styles.offlineText}>⚡ وضع عدم الاتصال</Text></View>
      )}
      <FlatList
        data={orders}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
        ListEmptyComponent={<Text style={styles.empty}>لا توجد طلبات</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  offlineBanner: { backgroundColor: '#ff9800', padding: 8, alignItems: 'center' },
  offlineText: { color: '#fff', fontWeight: 'bold' },
  card: { backgroundColor: '#fff', borderRadius: 8, marginHorizontal: 12, marginTop: 8, padding: 14, elevation: 1 },
  header: { flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  orderNum: { fontSize: 16, fontWeight: '700', textAlign: 'right' },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 12 },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  customer: { fontSize: 14, color: '#555', textAlign: 'right' },
  footer: { flexDirection: 'row-reverse', justifyContent: 'space-between', marginTop: 8 },
  amount: { fontSize: 15, fontWeight: '600', color: '#1976d2' },
  date: { fontSize: 13, color: '#999' },
  empty: { textAlign: 'center', padding: 40, color: '#999', fontSize: 16 },
});
