/**
 * Approval List — pending approvals with approve/reject actions.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity,
  RefreshControl, ActivityIndicator, Alert,
} from 'react-native';
import { useNetwork } from '../../../App';
import { approvalAPI } from '../../services/api';
import { enqueue } from '../../services/syncService';
import { formatAmount, getMobileCurrencyCode } from '../../utils/formatters';

export default function ApprovalList() {
  const { isConnected } = useNetwork();
  const [approvals, setApprovals] = useState([]);
  const [currencyCode, setCurrencyCode] = useState('SAR');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const res = await approvalAPI.list({ status: 'pending', limit: 50 });
        setApprovals(Array.isArray(res) ? res : []);
      }
      setCurrencyCode(await getMobileCurrencyCode());
    } catch {
      setCurrencyCode(await getMobileCurrencyCode());
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
      Alert.alert('تمت الموافقة', 'تمت الموافقة على الطلب بنجاح');
    } catch {
      await enqueue('approval', item.id, 'update', { action: 'approve' });
      setApprovals((prev) => prev.filter((a) => a.id !== item.id));
      Alert.alert('تم الحفظ', 'ستُرسل الموافقة عند الاتصال');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = (item) => {
    Alert.alert(
      'تأكيد الرفض',
      'هل أنت متأكد من رفض هذا الطلب؟',
      [
        { text: 'إلغاء', style: 'cancel' },
        { text: 'رفض', style: 'destructive', onPress: () => doReject(item, 'مرفوض من الجوال') },
      ]
    );
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
      <View style={styles.cardHeader}>
        <View style={styles.typeBadge}>
          <Text style={styles.typeText}>{item.entity_type || item.type || 'طلب'}</Text>
        </View>
        <Text style={styles.ref}>{item.reference || `#${item.id}`}</Text>
      </View>

      {!!item.description && (
        <Text style={styles.desc}>{item.description || item.notes}</Text>
      )}

      {item.amount != null && (
        <Text style={styles.amount}>
          {formatAmount(item.amount, item.currency || item.currency_code || currencyCode)}
        </Text>
      )}

      <View style={styles.requesterRow}>
        <Text style={styles.requesterLabel}>مقدم الطلب</Text>
        <Text style={styles.requesterName}>{item.requester_name || '—'}</Text>
      </View>

      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.rejectBtn, actionLoading === item.id && styles.btnDisabled]}
          onPress={() => handleReject(item)}
          disabled={actionLoading === item.id}
        >
          <Text style={styles.rejectBtnText}>✗ رفض</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.approveBtn, actionLoading === item.id && styles.btnDisabled]}
          onPress={() => handleApprove(item)}
          disabled={actionLoading === item.id}
        >
          {actionLoading === item.id ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.approveBtnText}>✓ موافقة</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ تحميل الموافقات...</Text>
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
        data={approvals}
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
            <Text style={styles.emptyIcon}>✅</Text>
            <Text style={styles.empty}>لا توجد موافقات معلقة</Text>
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
  cardHeader: {
    flexDirection: 'row-reverse', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: 10,
  },
  typeBadge: { backgroundColor: '#e3f2fd', borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4 },
  typeText: { fontSize: 12, fontWeight: '700', color: '#1565c0' },
  ref: { fontSize: 13, color: '#90a4ae' },

  desc: { fontSize: 14, color: '#546e7a', textAlign: 'right', marginBottom: 8 },
  amount: { fontSize: 20, fontWeight: '700', color: '#1a2332', textAlign: 'right', marginBottom: 8 },

  requesterRow: {
    flexDirection: 'row-reverse', alignItems: 'center', gap: 6,
    marginBottom: 14, paddingVertical: 8,
    borderTopWidth: 1, borderTopColor: '#f0f4f8',
  },
  requesterLabel: { fontSize: 12, color: '#90a4ae' },
  requesterName: { fontSize: 13, fontWeight: '600', color: '#546e7a' },

  actions: { flexDirection: 'row-reverse', gap: 10 },
  approveBtn: {
    flex: 1, backgroundColor: '#2e7d32', borderRadius: 10,
    paddingVertical: 13, alignItems: 'center',
  },
  approveBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  rejectBtn: {
    flex: 1, borderRadius: 10, paddingVertical: 13, alignItems: 'center',
    borderWidth: 2, borderColor: '#ef9a9a',
  },
  rejectBtnText: { color: '#c62828', fontWeight: '700', fontSize: 15 },
  btnDisabled: { opacity: 0.5 },

  emptyWrap: { alignItems: 'center', paddingVertical: 60 },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  empty: { color: '#90a4ae', fontSize: 16 },
});
