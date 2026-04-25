/**
 * Conflict Screen — view and resolve sync conflicts.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity,
  RefreshControl, ActivityIndicator, Alert,
} from 'react-native';
import { useNetwork } from '../../../App';
import { mobileAPI } from '../../services/api';
import { getDeviceId } from '../../services/syncService';
import { resolveConflict } from '../../services/conflictResolver';

export default function ConflictScreen() {
  const { isConnected } = useNetwork();
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [resolving, setResolving] = useState(null);

  const load = useCallback(async () => {
    if (!isConnected) {
      setLoading(false);
      setRefreshing(false);
      return;
    }
    try {
      const deviceId = await getDeviceId();
      // Get conflicts from server sync status
      const status = await mobileAPI.syncStatus(deviceId);
      // The sync status gives counts; the actual conflict details come from the queue
      // For display, we query the full queue with conflict status
      // (backend would need a list endpoint — using status for now)
      setConflicts(status.conflicts > 0 ? [{ count: status.conflicts, device_id: deviceId }] : []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const handleResolve = async (item, resolution) => {
    if (!isConnected) {
      Alert.alert('يتطلب اتصال', 'حل التعارضات يتطلب اتصال بالإنترنت');
      return;
    }
    setResolving(item.id || 'resolving');
    try {
      await resolveConflict(item.id, resolution);
      Alert.alert('تم', 'تم حل التعارض بنجاح');
      load();
    } catch (err) {
      Alert.alert('خطأ', err.message || 'فشل في حل التعارض');
    } finally {
      setResolving(null);
    }
  };

  const renderConflictSummary = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardTop}>
        <Text style={styles.warningIcon}>⚠️</Text>
        <View style={styles.cardTitles}>
          <Text style={styles.title}>تعارضات غير محلولة</Text>
          <Text style={styles.subtitle}>معرّف الجهاز: {item.device_id?.slice(0, 8) || '—'}</Text>
        </View>
      </View>
      <View style={styles.countBadge}>
        <Text style={styles.count}>{item.count}</Text>
        <Text style={styles.countLabel}>تعارض</Text>
      </View>
      <Text style={styles.hint}>
        تم تعديل بيانات على الجهاز والخادم في نفس الوقت.
        اختر الإصدار الذي تريد الاحتفاظ به لحل هذه التعارضات.
      </Text>
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.deviceBtn}
          onPress={() => handleResolve(item, 'keep_device')}
        >
          <Text style={styles.deviceBtnText}>📱 الجهاز</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.serverBtn}
          onPress={() => handleResolve(item, 'keep_server')}
        >
          <Text style={styles.btnText}>☁️ الخادم</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ تحميل التعارضات...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {!isConnected && (
        <View style={styles.offlineBanner}>
          <Text style={styles.bannerText}>⚡ يتطلب اتصال بالإنترنت لحل التعارضات</Text>
        </View>
      )}
      <FlatList
        data={conflicts}
        keyExtractor={(_, idx) => String(idx)}
        renderItem={renderConflictSummary}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }}
            tintColor="#1976d2"
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>✅</Text>
            <Text style={styles.emptyText}>لا توجد تعارضات</Text>
            <Text style={styles.emptySubText}>جميع البيانات متزامنة</Text>
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

  list: { paddingHorizontal: 14, paddingTop: 14, paddingBottom: 20 },

  card: {
    backgroundColor: '#fff', borderRadius: 12, padding: 20, elevation: 3,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07, shadowRadius: 4,
    borderLeftWidth: 4, borderLeftColor: '#e65100',
  },
  cardTop: { flexDirection: 'row-reverse', alignItems: 'center', marginBottom: 14 },
  warningIcon: { fontSize: 28, marginLeft: 12 },
  cardTitles: { flex: 1 },
  title: { fontSize: 17, fontWeight: '700', color: '#1a2332', textAlign: 'right' },
  subtitle: { fontSize: 13, color: '#90a4ae', textAlign: 'right', marginTop: 2 },

  countBadge: {
    backgroundColor: '#fff3e0', borderRadius: 12, paddingVertical: 14,
    alignItems: 'center', marginBottom: 14,
  },
  count: { fontSize: 42, fontWeight: '700', color: '#e65100' },
  countLabel: { fontSize: 13, color: '#e65100', marginTop: 2 },

  hint: {
    fontSize: 14, color: '#546e7a', textAlign: 'right', lineHeight: 22,
    marginBottom: 16, backgroundColor: '#f8fafc', borderRadius: 8, padding: 12,
    borderRightWidth: 3, borderRightColor: '#90a4ae',
  },

  actions: { flexDirection: 'row-reverse', gap: 10 },
  serverBtn: {
    flex: 1, backgroundColor: '#1976d2', borderRadius: 10,
    paddingVertical: 13, alignItems: 'center',
  },
  deviceBtn: {
    flex: 1, borderWidth: 2, borderColor: '#1976d2', borderRadius: 10,
    paddingVertical: 13, alignItems: 'center',
  },
  deviceBtnText: { color: '#1976d2', fontWeight: '700', fontSize: 14 },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 14 },

  emptyContainer: { alignItems: 'center', paddingVertical: 80 },
  emptyIcon: { fontSize: 56, marginBottom: 16 },
  emptyText: { fontSize: 18, color: '#2e7d32', fontWeight: '700', marginBottom: 8 },
  emptySubText: { fontSize: 14, color: '#90a4ae' },
});
