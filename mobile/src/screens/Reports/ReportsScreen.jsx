/**
 * Reports Screen — summary dashboard with key financial metrics.
 * Matches web frontend: frontend/src/pages/Dashboard.jsx + Reports section.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, RefreshControl, ActivityIndicator,
} from 'react-native';
import { useNetwork } from '../../../App';
import { dashboardAPI, reportsAPI, inventoryAPI, customerAPI } from '../../services/api';
import { formatAmount, getMobileCurrencyCode } from '../../utils/formatters';

export default function ReportsScreen() {
  const { isConnected } = useNetwork();
  const [data, setData] = useState(null);
  const [currencyCode, setCurrencyCode] = useState('SAR');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const [statsRes, salesRes, productsRes, customersRes] = await Promise.allSettled([
          dashboardAPI.stats(),
          reportsAPI.salesSummary(),
          inventoryAPI.list({ limit: 1 }),
          customerAPI.list({ limit: 1 }),
        ]);
        const stats = statsRes.status === 'fulfilled' ? statsRes.value : {};
        const sales = salesRes.status === 'fulfilled' ? salesRes.value : {};

        setData({
          sales: stats.sales ?? sales.total_sales ?? 0,
          expenses: stats.expenses ?? 0,
          profit: stats.profit ?? 0,
          cash: stats.cash ?? 0,
          cash_status: stats.cash_status || '',
          low_stock: stats.low_stock ?? 0,
          total_customers: sales.total_customers ?? (customersRes.status === 'fulfilled' ? (customersRes.value || []).length : 0),
          total_invoices: sales.total_invoices ?? 0,
          total_receivables: sales.total_receivables ?? 0,
          unpaid_count: sales.unpaid_count ?? 0,
        });
      }
      setCurrencyCode(await getMobileCurrencyCode());
    } catch { /* ignore */ }
    finally { setLoading(false); setRefreshing(false); }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ تحميل التقارير...</Text>
      </View>
    );
  }

  if (!data) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyIcon}>📊</Text>
        <Text style={styles.empty}>لا تتوفر بيانات</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing}
        onRefresh={() => { setRefreshing(true); load(); }} tintColor="#1976d2" />}
    >
      {/* Financial Summary */}
      <Text style={styles.sectionLabel}>الملخص المالي</Text>
      <View style={styles.cardsGrid}>
        <MetricCard title="المبيعات" value={formatAmount(data.sales, currencyCode)}
          icon="💰" color="#1976d2" bg="#e3f2fd" />
        <MetricCard title="المصروفات" value={formatAmount(data.expenses, currencyCode)}
          icon="📉" color="#c62828" bg="#ffebee" />
        <MetricCard title="الأرباح" value={formatAmount(data.profit, currencyCode)}
          icon="📈" color="#2e7d32" bg="#e8f5e9" />
        <MetricCard title="النقدية" value={formatAmount(data.cash, currencyCode)}
          icon="🏦" color="#6a1b9a" bg="#f3e5f5"
          subtitle={data.cash_status ? `الحالة: ${data.cash_status}` : null} />
      </View>

      {/* Operations Summary */}
      <Text style={styles.sectionLabel}>ملخص العمليات</Text>
      <View style={styles.opsCard}>
        <OpsRow label="عدد العملاء" value={data.total_customers} icon="👥" />
        <View style={styles.opsDivider} />
        <OpsRow label="عدد الفواتير" value={data.total_invoices} icon="🧾" />
        <View style={styles.opsDivider} />
        <OpsRow label="المستحقات" value={formatAmount(data.total_receivables, currencyCode)} icon="💳"
          valueColor={data.total_receivables > 0 ? '#c62828' : '#2e7d32'} />
        <View style={styles.opsDivider} />
        <OpsRow label="فواتير غير مدفوعة" value={data.unpaid_count} icon="⏳"
          valueColor={data.unpaid_count > 0 ? '#e65100' : '#2e7d32'} />
        <View style={styles.opsDivider} />
        <OpsRow label="منتجات مخزون منخفض" value={data.low_stock} icon="📦"
          valueColor={data.low_stock > 0 ? '#c62828' : '#2e7d32'} />
      </View>
    </ScrollView>
  );
}

function MetricCard({ title, value, icon, color, bg, subtitle }) {
  return (
    <View style={[styles.metricCard, { backgroundColor: bg }]}>
      <Text style={styles.metricIcon}>{icon}</Text>
      <Text style={[styles.metricValue, { color }]}>{value}</Text>
      <Text style={styles.metricTitle}>{title}</Text>
      {subtitle ? <Text style={styles.metricSub}>{subtitle}</Text> : null}
    </View>
  );
}

function OpsRow({ label, value, icon, valueColor }) {
  return (
    <View style={styles.opsRow}>
      <Text style={[styles.opsValue, valueColor && { color: valueColor }]}>{value}</Text>
      <View style={styles.opsLabelWrap}>
        <Text style={styles.opsLabel}>{label}</Text>
        <Text style={styles.opsIcon}>{icon}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f4f8' },
  content: { paddingBottom: 32 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f4f8' },
  loadingText: { marginTop: 12, color: '#546e7a', fontSize: 15 },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  empty: { color: '#90a4ae', fontSize: 16 },

  sectionLabel: {
    fontSize: 13, fontWeight: '700', color: '#546e7a', textAlign: 'right',
    marginHorizontal: 16, marginTop: 20, marginBottom: 10,
    textTransform: 'uppercase', letterSpacing: 0.5,
  },

  cardsGrid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12 },
  metricCard: {
    width: '46%', borderRadius: 12, padding: 16, margin: '2%',
    alignItems: 'center', elevation: 2,
  },
  metricIcon: { fontSize: 24, marginBottom: 6 },
  metricValue: { fontSize: 18, fontWeight: 'bold' },
  metricTitle: { fontSize: 12, color: '#546e7a', marginTop: 4, textAlign: 'center' },
  metricSub: { fontSize: 10, color: '#90a4ae', marginTop: 2 },

  opsCard: {
    backgroundColor: '#fff', borderRadius: 12, marginHorizontal: 16,
    elevation: 3, overflow: 'hidden',
  },
  opsRow: {
    flexDirection: 'row-reverse', justifyContent: 'space-between',
    alignItems: 'center', paddingVertical: 14, paddingHorizontal: 16,
  },
  opsLabelWrap: { flexDirection: 'row-reverse', alignItems: 'center', gap: 8 },
  opsIcon: { fontSize: 16 },
  opsLabel: { fontSize: 15, fontWeight: '500', color: '#1a2332' },
  opsValue: { fontSize: 16, fontWeight: '700', color: '#1976d2' },
  opsDivider: { height: 1, backgroundColor: '#f0f4f8', marginHorizontal: 16 },
});
