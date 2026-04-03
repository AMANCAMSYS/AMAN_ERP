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

export default function DashboardScreen({ navigation }) {
  const { signOut } = useAuth();
  const { isConnected } = useNetwork();
  const [data, setData] = useState(null);
  const [queueSize, setQueueSize] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const res = await mobileAPI.dashboard();
        setData(res);
      }
      setQueueSize(await getQueueSize());
    } catch {
      // offline or error
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color="#1976d2" /></View>;
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {!isConnected && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>⚡ وضع عدم الاتصال</Text>
        </View>
      )}

      {queueSize > 0 && (
        <View style={styles.syncBanner}>
          <Text style={styles.syncText}>📤 {queueSize} عمليات في الانتظار</Text>
        </View>
      )}

      {/* Summary Cards */}
      <View style={styles.row}>
        <Card title="المنتجات" value={data?.inventory_summary?.total_products ?? '—'} color="#4caf50" />
        <Card title="المخزون" value={data?.inventory_summary?.total_stock ?? '—'} color="#2196f3" />
      </View>
      <View style={styles.row}>
        <Card title="طلبات معلقة" value={data?.pending_orders ?? '—'} color="#ff9800" />
        <Card title="موافقات" value={data?.pending_approvals ?? '—'} color="#f44336" />
      </View>

      {/* Navigation Tiles */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>الإجراءات السريعة</Text>
        <NavTile label="المخزون" icon="📦" onPress={() => navigation.navigate('Inventory')} />
        <NavTile label="عرض سعر جديد" icon="📝" onPress={() => navigation.navigate('QuotationForm')} />
        <NavTile label="الطلبات" icon="🛒" onPress={() => navigation.navigate('Orders')} />
        <NavTile label="الموافقات" icon="✅" onPress={() => navigation.navigate('Approvals')} />
        <NavTile label="حل التعارضات" icon="🔄" onPress={() => navigation.navigate('Conflicts')} />
      </View>

      <TouchableOpacity style={styles.logoutBtn} onPress={signOut}>
        <Text style={styles.logoutText}>تسجيل الخروج</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function Card({ title, value, color }) {
  return (
    <View style={[styles.card, { borderLeftColor: color }]}>
      <Text style={styles.cardValue}>{value}</Text>
      <Text style={styles.cardTitle}>{title}</Text>
    </View>
  );
}

function NavTile({ label, icon, onPress }) {
  return (
    <TouchableOpacity style={styles.tile} onPress={onPress}>
      <Text style={styles.tileIcon}>{icon}</Text>
      <Text style={styles.tileLabel}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  offlineBanner: { backgroundColor: '#ff9800', padding: 8, alignItems: 'center' },
  offlineText: { color: '#fff', fontWeight: 'bold' },
  syncBanner: { backgroundColor: '#2196f3', padding: 8, alignItems: 'center' },
  syncText: { color: '#fff', fontWeight: '600' },
  row: { flexDirection: 'row', paddingHorizontal: 12, marginTop: 12 },
  card: {
    flex: 1, backgroundColor: '#fff', borderRadius: 8, padding: 16, marginHorizontal: 4,
    borderLeftWidth: 4, elevation: 2,
  },
  cardValue: { fontSize: 24, fontWeight: 'bold', textAlign: 'center' },
  cardTitle: { fontSize: 13, color: '#666', textAlign: 'center', marginTop: 4 },
  section: { padding: 12, marginTop: 8 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 8, textAlign: 'right' },
  tile: {
    flexDirection: 'row-reverse', alignItems: 'center', backgroundColor: '#fff',
    padding: 14, borderRadius: 8, marginBottom: 8, elevation: 1,
  },
  tileIcon: { fontSize: 22, marginLeft: 12 },
  tileLabel: { fontSize: 16, fontWeight: '500', textAlign: 'right', flex: 1 },
  logoutBtn: { margin: 16, padding: 14, backgroundColor: '#eee', borderRadius: 8, alignItems: 'center' },
  logoutText: { color: '#f44336', fontWeight: '600' },
});
