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

const STATUS_CONFIG = {
  draft:     { label: 'مسودة',       color: '#e65100', bg: '#fff3e0' },
  confirmed: { label: 'مؤكد',        color: '#1565c0', bg: '#e3f2fd' },
  delivered: { label: 'تم التسليم',  color: '#2e7d32', bg: '#e8f5e9' },
  cancelled: { label: 'ملغي',        color: '#c62828', bg: '#ffebee' },
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
        setOrders(Array.isArray(res) ? res : []);
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
    const statusCfg = STATUS_CONFIG[statusKey] || { label: item.status, color: '#546e7a', bg: '#f5f5f5' };
    return (
      <View style={styles.card}>
        <View style={styles.header}>
          <View style={[styles.badge, { backgroundColor: statusCfg.bg }]}>
            <Text style={[styles.badgeText, { color: statusCfg.color }]}>{statusCfg.label}</Text>
          </View>
          <Text style={styles.orderNum}>{item.order_number || `#${item.id}`}</Text>
        </View>

        <Text style={styles.customer}>{item.customer_name || '—'}</Text>

        <View style={styles.footer}>
          <Text style={styles.date}>{formatDate(item.created_at)}</Text>
          <Text style={styles.amount}>
            {formatAmount(item.total_amount, item.currency || item.currency_code || currencyCode)}
          </Text>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ تحميل الطلبات...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {!isConnected && (
        <View style={styles.offlineBanner}>
          <Text style={styles.bannerText}>⚡ وضع عدم الاتصال</Text>
        </View>
      )}
      <FlatList
        data={orders}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }}
            tintColor="#1976d2"
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyWrap}>
            <Text style={styles.emptyIcon}>🛒</Text>
            <Text style={styles.empty}>لا توجد طلبات</Text>
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

  offlineBanner: { backgroundColor: '#e65100', padding: 10, alignItems: 'center' },
  bannerText: { color: '#fff', fontWeight: '600', fontSize: 13 },

  list: { paddingHorizontal: 14, paddingTop: 10, paddingBottom: 20 },

  card: {
    backgroundColor: '#fff', borderRadius: 12, marginBottom: 10, padding: 16,
    elevation: 3, shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07, shadowRadius: 4,
  },
  header: {
    flexDirection: 'row-reverse', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: 8,
  },
  orderNum: { fontSize: 17, fontWeight: '700', color: '#1a2332' },
  badge: { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4 },
  badgeText: { fontSize: 12, fontWeight: '700' },

  customer: { fontSize: 14, color: '#546e7a', textAlign: 'right', marginBottom: 12 },

  footer: {
    flexDirection: 'row-reverse', justifyContent: 'space-between',
    alignItems: 'center', paddingTop: 12, borderTopWidth: 1, borderTopColor: '#f0f4f8',
  },
  amount: { fontSize: 16, fontWeight: '700', color: '#1976d2' },
  date: { fontSize: 12, color: '#90a4ae' },

  emptyWrap: { alignItems: 'center', paddingVertical: 60 },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  empty: { color: '#90a4ae', fontSize: 16 },
});

