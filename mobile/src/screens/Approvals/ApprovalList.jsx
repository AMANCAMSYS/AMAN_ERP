/**
 * Approval List — pending approvals with approve/reject actions.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity,
  RefreshControl, ActivityIndicator, Alert, TextInput,
} from 'react-native';
import { useNetwork } from '../../../App';
import { approvalAPI } from '../../services/api';
import { enqueue } from '../../services/syncService';

export default function ApprovalList() {
  const { isConnected } = useNetwork();
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const res = await approvalAPI.list({ status: 'pending', limit: 50 });
        setApprovals(res.items || res || []);
      }
    } catch {
      // keep existing list
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected]);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (item) => {
    setActionLoading(item.id);
    try {
      if (isConnected) {
        await approvalAPI.approve(item.id);
      } else {
        await enqueue('approval', item.id, 'update', { action: 'approve' });
      }
      setApprovals((prev) => prev.filter((a) => a.id !== item.id));
      Alert.alert('تم', 'تمت الموافقة بنجاح');
    } catch (err) {
      await enqueue('approval', item.id, 'update', { action: 'approve' });
      setApprovals((prev) => prev.filter((a) => a.id !== item.id));
      Alert.alert('تم الحفظ', 'ستُرسل الموافقة عند الاتصال');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = (item) => {
    Alert.prompt
      ? Alert.prompt('سبب الرفض', 'أدخل سبب الرفض', async (reason) => {
          await doReject(item, reason);
        })
      : doRejectWithConfirm(item);
  };

  const doRejectWithConfirm = (item) => {
    Alert.alert('رفض', 'هل أنت متأكد من رفض هذا الطلب؟', [
      { text: 'إلغاء', style: 'cancel' },
      { text: 'رفض', style: 'destructive', onPress: () => doReject(item, 'مرفوض من الجوال') },
    ]);
  };

  const doReject = async (item, reason) => {
    setActionLoading(item.id);
    try {
      if (isConnected) {
        await approvalAPI.reject(item.id, reason);
      } else {
        await enqueue('approval', item.id, 'update', { action: 'reject', reason });
      }
      setApprovals((prev) => prev.filter((a) => a.id !== item.id));
    } catch {
      await enqueue('approval', item.id, 'update', { action: 'reject', reason });
      setApprovals((prev) => prev.filter((a) => a.id !== item.id));
    } finally {
      setActionLoading(null);
    }
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.type}>{item.entity_type || item.type || 'طلب'}</Text>
        <Text style={styles.ref}>{item.reference || `#${item.id}`}</Text>
      </View>
      <Text style={styles.desc}>{item.description || item.notes || ''}</Text>
      {item.amount != null && (
        <Text style={styles.amount}>{item.amount} ر.س</Text>
      )}
      <Text style={styles.requester}>مقدم الطلب: {item.requester_name || '—'}</Text>

      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.approveBtn, actionLoading === item.id && styles.disabled]}
          onPress={() => handleApprove(item)}
          disabled={actionLoading === item.id}
        >
          {actionLoading === item.id ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.btnText}>✓ موافقة</Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.rejectBtn, actionLoading === item.id && styles.disabled]}
          onPress={() => handleReject(item)}
          disabled={actionLoading === item.id}
        >
          <Text style={styles.btnText}>✗ رفض</Text>
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
        <View style={styles.offlineBanner}><Text style={styles.offlineText}>⚡ وضع عدم الاتصال</Text></View>
      )}
      <FlatList
        data={approvals}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
        ListEmptyComponent={<Text style={styles.empty}>لا توجد موافقات معلقة</Text>}
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
  header: { flexDirection: 'row-reverse', justifyContent: 'space-between', marginBottom: 4 },
  type: { fontSize: 14, fontWeight: '700', color: '#1976d2', textAlign: 'right' },
  ref: { fontSize: 13, color: '#999' },
  desc: { fontSize: 14, color: '#555', textAlign: 'right', marginBottom: 4 },
  amount: { fontSize: 16, fontWeight: '600', color: '#333', textAlign: 'right', marginBottom: 4 },
  requester: { fontSize: 12, color: '#888', textAlign: 'right', marginBottom: 10 },
  actions: { flexDirection: 'row-reverse', gap: 8 },
  approveBtn: { flex: 1, backgroundColor: '#4caf50', borderRadius: 8, padding: 10, alignItems: 'center' },
  rejectBtn: { flex: 1, backgroundColor: '#f44336', borderRadius: 8, padding: 10, alignItems: 'center' },
  disabled: { opacity: 0.5 },
  btnText: { color: '#fff', fontWeight: '600', fontSize: 15 },
  empty: { textAlign: 'center', padding: 40, color: '#999', fontSize: 16 },
});
