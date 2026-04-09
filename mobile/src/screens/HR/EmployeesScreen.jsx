/**
 * Employees Screen — list employees with department and position info.
 * Matches web frontend: frontend/src/pages/HR/Employees.jsx
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TextInput,
  RefreshControl, ActivityIndicator, TouchableOpacity, Linking,
} from 'react-native';
import { useNetwork } from '../../../App';
import { hrAPI } from '../../services/api';
import { formatAmount, getMobileCurrencyCode } from '../../utils/formatters';

const STATUS_MAP = {
  active: { label: 'نشط', color: '#2e7d32', bg: '#e8f5e9' },
  inactive: { label: 'غير نشط', color: '#c62828', bg: '#ffebee' },
  suspended: { label: 'معلق', color: '#e65100', bg: '#fff3e0' },
  terminated: { label: 'منتهي', color: '#78909c', bg: '#eceff1' },
};

export default function EmployeesScreen() {
  const { isConnected } = useNetwork();
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState('');
  const [currencyCode, setCurrencyCode] = useState('SAR');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const res = await hrAPI.employees({ limit: 100 });
        setEmployees(Array.isArray(res) ? res : []);
      }
      setCurrencyCode(await getMobileCurrencyCode());
    } catch { /* ignore */ }
    finally { setLoading(false); setRefreshing(false); }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const filtered = employees.filter((e) => {
    if (!search) return true;
    const s = search.toLowerCase();
    const name = `${e.first_name || ''} ${e.last_name || ''}`.toLowerCase();
    return name.includes(s) || (e.employee_code || '').toLowerCase().includes(s)
      || (e.position || '').toLowerCase().includes(s) || (e.department || '').toLowerCase().includes(s);
  });

  const renderItem = ({ item }) => {
    const statusCfg = STATUS_MAP[item.status] || STATUS_MAP.active;
    const fullName = `${item.first_name || ''} ${item.last_name || ''}`.trim();
    const totalSalary = (item.salary || 0) + (item.housing_allowance || 0) + (item.transport_allowance || 0) + (item.other_allowances || 0);

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={[styles.badge, { backgroundColor: statusCfg.bg }]}>
            <Text style={[styles.badgeText, { color: statusCfg.color }]}>{statusCfg.label}</Text>
          </View>
          <View style={styles.cardTitles}>
            <Text style={styles.name}>{fullName || 'بدون اسم'}</Text>
            {item.employee_code ? <Text style={styles.code}>{item.employee_code}</Text> : null}
          </View>
        </View>

        <View style={styles.infoRow}>
          {item.position ? (
            <View style={styles.infoBadge}>
              <Text style={styles.infoText}>💼 {item.position}</Text>
            </View>
          ) : null}
          {item.department ? (
            <View style={styles.infoBadge}>
              <Text style={styles.infoText}>🏢 {item.department}</Text>
            </View>
          ) : null}
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{formatAmount(item.salary || 0, currencyCode)}</Text>
            <Text style={styles.statLbl}>الراتب الأساسي</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{formatAmount(item.housing_allowance || 0, currencyCode)}</Text>
            <Text style={styles.statLbl}>بدل السكن</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={[styles.statNum, { color: '#2e7d32' }]}>{formatAmount(totalSalary, currencyCode)}</Text>
            <Text style={styles.statLbl}>الإجمالي</Text>
          </View>
        </View>

        {(item.phone || item.email) ? (
          <View style={styles.contactArea}>
            {item.phone ? (
              <TouchableOpacity onPress={() => Linking.openURL(`tel:${item.phone}`)}>
                <Text style={styles.contactLink}>📞 {item.phone}</Text>
              </TouchableOpacity>
            ) : null}
            {item.email ? (
              <TouchableOpacity onPress={() => Linking.openURL(`mailto:${item.email}`)}>
                <Text style={styles.contactLink}>📧 {item.email}</Text>
              </TouchableOpacity>
            ) : null}
          </View>
        ) : null}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ تحميل الموظفين...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.search} placeholder="بحث عن موظف..."
          value={search} onChangeText={setSearch}
          textAlign="right" placeholderTextColor="#90a4ae" returnKeyType="search"
        />
      </View>
      <FlatList
        data={filtered}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }} tintColor="#1976d2" />
        }
        ListEmptyComponent={
          <View style={styles.emptyWrap}>
            <Text style={styles.emptyIcon}>👤</Text>
            <Text style={styles.empty}>لا يوجد موظفون</Text>
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
    elevation: 2, paddingHorizontal: 14, borderWidth: 1, borderColor: '#e0e7ef',
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
  badge: { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4 },
  badgeText: { fontSize: 12, fontWeight: '700' },

  infoRow: { flexDirection: 'row-reverse', flexWrap: 'wrap', gap: 8, marginBottom: 10 },
  infoBadge: { backgroundColor: '#f5f7fa', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 5 },
  infoText: { fontSize: 12, color: '#546e7a' },

  statsRow: { flexDirection: 'row-reverse', backgroundColor: '#f8fafc', borderRadius: 8, overflow: 'hidden', marginBottom: 10 },
  statBox: { flex: 1, alignItems: 'center', paddingVertical: 10 },
  statDivider: { width: 1, backgroundColor: '#e0e7ef' },
  statNum: { fontSize: 13, fontWeight: '700', color: '#1976d2' },
  statLbl: { fontSize: 10, color: '#90a4ae', marginTop: 2 },

  contactArea: { flexDirection: 'row-reverse', gap: 16, paddingTop: 8, borderTopWidth: 1, borderTopColor: '#f0f4f8' },
  contactLink: { fontSize: 13, color: '#1976d2' },

  emptyWrap: { alignItems: 'center', paddingVertical: 60 },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  empty: { color: '#90a4ae', fontSize: 16 },
});
