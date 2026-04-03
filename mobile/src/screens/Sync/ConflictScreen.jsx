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
import { resolveConflict, diffVersions } from '../../services/conflictResolver';

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
      <Text style={styles.title}>تعارضات غير محلولة</Text>
      <Text style={styles.count}>{item.count}</Text>
      <Text style={styles.hint}>
        تم تعديل بيانات على الجهاز والخادم في نفس الوقت.
        يرجى مراجعة التعارضات وحلها.
      </Text>
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.serverBtn}
          onPress={() => Alert.alert(
            'حل جميع التعارضات',
            'اختر الإصدار المطلوب',
            [
              { text: 'إلغاء', style: 'cancel' },
              { text: 'الاحتفاظ بالخادم', onPress: () => handleResolve(item, 'keep_server') },
              { text: 'الاحتفاظ بالجهاز', onPress: () => handleResolve(item, 'keep_device') },
            ]
          )}
        >
          <Text style={styles.btnText}>حل التعارضات</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color="#1976d2" /></View>;
  }

  return (
    <View style={styles.container}>
      {!isConnected && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>⚡ يتطلب اتصال بالإنترنت لحل التعارضات</Text>
        </View>
      )}
      <FlatList
        data={conflicts}
        keyExtractor={(_, idx) => String(idx)}
        renderItem={renderConflictSummary}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>✅</Text>
            <Text style={styles.emptyText}>لا توجد تعارضات</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  offlineBanner: { backgroundColor: '#ff9800', padding: 8, alignItems: 'center' },
  offlineText: { color: '#fff', fontWeight: 'bold' },
  card: {
    backgroundColor: '#fff', borderRadius: 8, margin: 12, padding: 16, elevation: 2,
    borderLeftWidth: 4, borderLeftColor: '#ff9800',
  },
  title: { fontSize: 18, fontWeight: 'bold', textAlign: 'right', marginBottom: 8 },
  count: { fontSize: 36, fontWeight: 'bold', textAlign: 'center', color: '#ff9800', marginVertical: 8 },
  hint: { fontSize: 14, color: '#666', textAlign: 'right', lineHeight: 22, marginBottom: 12 },
  actions: { flexDirection: 'row-reverse' },
  serverBtn: { flex: 1, backgroundColor: '#1976d2', borderRadius: 8, padding: 12, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: '600', fontSize: 15 },
  emptyContainer: { alignItems: 'center', padding: 60 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: { fontSize: 18, color: '#4caf50', fontWeight: '600' },
});
