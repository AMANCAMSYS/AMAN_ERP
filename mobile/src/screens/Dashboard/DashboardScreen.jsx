/**
 * Dashboard Screen — inventory summary, pending orders, pending approvals.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  RefreshControl, ActivityIndicator,
} from 'react-native';
import { useAuth, useNetwork } from '../../../App';
import { mobileAPI } from '../../services/api';
import { getQueueSize } from '../../services/syncService';
import { setMobileCurrencyCode, formatAmount } from '../../utils/formatters';

const EMPTY_DASHBOARD = {
  inventory_summary: {
    total_products: 0,
    total_stock: 0,
  },
  pending_orders: 0,
  pending_approvals: 0,
  recent_quotations: [],
  currency_code: 'SAR',
  sales: 0,
  expenses: 0,
  profit: 0,
  cash: 0,
};

export default function DashboardScreen({ navigation }) {
  const { signOut } = useAuth();
  const { isConnected } = useNetwork();
  const [data, setData] = useState(EMPTY_DASHBOARD);
  const [queueSize, setQueueSize] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const res = await mobileAPI.dashboard();
        setData({ ...EMPTY_DASHBOARD, ...res, inventory_summary: { ...EMPTY_DASHBOARD.inventory_summary, ...(res?.inventory_summary || {}) } });
        await setMobileCurrencyCode(res?.currency_code);
      }
      setQueueSize(await getQueueSize());
    } catch {
      setData(EMPTY_DASHBOARD);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ التحميل...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#1976d2" />}
    >
      {/* Header */}
      <View style={styles.headerBand}>
        <Text style={styles.headerTitle}>لوحة التحكم</Text>
        <Text style={styles.headerSub}>نظرة عامة على العمليات</Text>
      </View>

      {!isConnected && (
        <View style={styles.offlineBanner}>
          <Text style={styles.bannerText}>⚡ وضع عدم الاتصال</Text>
        </View>
      )}

      {queueSize > 0 && (
        <View style={styles.syncBanner}>
          <Text style={styles.bannerText}>📤 {queueSize} عمليات في انتظار المزامنة</Text>
        </View>
      )}

      {/* Summary Cards */}
      <Text style={styles.sectionLabel}>الملخص</Text>
      <View style={styles.statsGrid}>
        <StatCard
          title="المنتجات"
          value={data?.inventory_summary?.total_products ?? 0}
          icon="📦"
          color="#1976d2"
          bg="#e3f2fd"
        />
        <StatCard
          title="إجمالي المخزون"
          value={data?.inventory_summary?.total_stock ?? 0}
          icon="🏪"
          color="#2e7d32"
          bg="#e8f5e9"
        />
        <StatCard
          title="طلبات معلقة"
          value={data?.pending_orders ?? 0}
          icon="🛒"
          color="#e65100"
          bg="#fff3e0"
        />
        <StatCard
          title="موافقات معلقة"
          value={data?.pending_approvals ?? 0}
          icon="✅"
          color="#c62828"
          bg="#ffebee"
        />
      </View>

      {/* Financial Summary */}
      {(data?.sales > 0 || data?.expenses > 0 || data?.cash > 0) ? (
        <>
          <Text style={styles.sectionLabel}>المالية</Text>
          <View style={styles.statsGrid}>
            <StatCard title="المبيعات" value={formatAmount(data?.sales ?? 0, data?.currency_code || 'SAR')}
              icon="💰" color="#1976d2" bg="#e3f2fd" />
            <StatCard title="المصروفات" value={formatAmount(data?.expenses ?? 0, data?.currency_code || 'SAR')}
              icon="📉" color="#c62828" bg="#ffebee" />
            <StatCard title="الأرباح" value={formatAmount(data?.profit ?? 0, data?.currency_code || 'SAR')}
              icon="📈" color="#2e7d32" bg="#e8f5e9" />
            <StatCard title="النقدية" value={formatAmount(data?.cash ?? 0, data?.currency_code || 'SAR')}
              icon="🏦" color="#6a1b9a" bg="#f3e5f5" />
          </View>
        </>
      ) : null}

      {/* Quick Actions */}
      <Text style={styles.sectionLabel}>الإجراءات السريعة</Text>
      <View style={styles.actionsCard}>
        <NavTile label="المخزون" icon="📦" onPress={() => navigation.navigate('Inventory')} />
        <View style={styles.divider} />
        <NavTile label="العملاء (مبيعات)" icon="👥" onPress={() => navigation.navigate('Customers')} />
        <View style={styles.divider} />
        <NavTile label="فواتير مبيعات" icon="🧾" onPress={() => navigation.navigate('Invoices')} />
        <View style={styles.divider} />
        <NavTile label="فواتير مشتريات" icon="🛒" onPress={() => navigation.navigate('PurchaseInvoices')} />
        <View style={styles.divider} />
        <NavTile label="الموردون" icon="🏭" onPress={() => navigation.navigate('Suppliers')} />
        <View style={styles.divider} />
        <NavTile label="الطلبات" icon="📋" onPress={() => navigation.navigate('Orders')} />
        <View style={styles.divider} />
        <NavTile label="عرض سعر جديد" icon="📝" onPress={() => navigation.navigate('QuotationForm')} />
        <View style={styles.divider} />
        <NavTile label="الموافقات" icon="✅" onPress={() => navigation.navigate('Approvals')} />
        <View style={styles.divider} />
        <NavTile label="الموظفون" icon="👤" onPress={() => navigation.navigate('Employees')} />
        <View style={styles.divider} />
        <NavTile label="التقارير" icon="📊" onPress={() => navigation.navigate('Reports')} />
        <View style={styles.divider} />
        <NavTile label="حل التعارضات" icon="🔄" onPress={() => navigation.navigate('Conflicts')} />
      </View>

      <TouchableOpacity style={styles.logoutBtn} onPress={signOut}>
        <Text style={styles.logoutText}>تسجيل الخروج</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function StatCard({ title, value, icon, color, bg }) {
  return (
    <View style={[styles.statCard, { backgroundColor: bg }]}>
      <Text style={styles.statIcon}>{icon}</Text>
      <Text style={[styles.statValue, { color }]}>{value}</Text>
      <Text style={styles.statTitle}>{title}</Text>
    </View>
  );
}

function NavTile({ label, icon, onPress }) {
  return (
    <TouchableOpacity style={styles.tile} onPress={onPress} activeOpacity={0.7}>
      <Text style={styles.tileChevron}>‹</Text>
      <Text style={styles.tileLabel}>{label}</Text>
      <Text style={styles.tileIcon}>{icon}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f0f4f8' },
  content: { paddingBottom: 32 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f4f8' },
  loadingText: { marginTop: 12, color: '#546e7a', fontSize: 15 },

  headerBand: {
    backgroundColor: '#1976d2', paddingTop: 24, paddingBottom: 20, paddingHorizontal: 20,
  },
  headerTitle: { fontSize: 22, fontWeight: 'bold', color: '#fff', textAlign: 'right' },
  headerSub: { fontSize: 13, color: '#bbdefb', textAlign: 'right', marginTop: 2 },

  offlineBanner: { backgroundColor: '#e65100', padding: 10, alignItems: 'center' },
  syncBanner: { backgroundColor: '#1565c0', padding: 10, alignItems: 'center' },
  bannerText: { color: '#fff', fontWeight: '600', fontSize: 13 },

  sectionLabel: {
    fontSize: 13, fontWeight: '700', color: '#546e7a', textAlign: 'right',
    marginHorizontal: 16, marginTop: 20, marginBottom: 10,
    textTransform: 'uppercase', letterSpacing: 0.5,
  },

  statsGrid: {
    flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12,
  },
  statCard: {
    width: '46%', borderRadius: 12, padding: 16, margin: '2%',
    alignItems: 'center', elevation: 2,
  },
  statIcon: { fontSize: 24, marginBottom: 6 },
  statValue: { fontSize: 26, fontWeight: 'bold' },
  statTitle: { fontSize: 12, color: '#546e7a', marginTop: 4, textAlign: 'center' },

  actionsCard: {
    backgroundColor: '#fff', borderRadius: 12, marginHorizontal: 16,
    elevation: 3, overflow: 'hidden',
  },
  tile: {
    flexDirection: 'row-reverse', alignItems: 'center',
    paddingVertical: 16, paddingHorizontal: 20,
  },
  tileIcon: { fontSize: 20 },
  tileLabel: { fontSize: 16, fontWeight: '500', color: '#1a2332', textAlign: 'right', flex: 1, marginRight: 12 },
  tileChevron: { fontSize: 22, color: '#b0bec5', transform: [{ rotate: '180deg' }] },
  divider: { height: 1, backgroundColor: '#f0f4f8', marginHorizontal: 20 },

  logoutBtn: {
    marginHorizontal: 16, marginTop: 24, paddingVertical: 14,
    borderWidth: 2, borderColor: '#ef9a9a', borderRadius: 12, alignItems: 'center',
  },
  logoutText: { color: '#c62828', fontWeight: '700', fontSize: 15 },
});
