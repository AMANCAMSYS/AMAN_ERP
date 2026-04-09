/**
 * Inventory Screen — browse products and stock levels.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, StyleSheet, TextInput,
  RefreshControl, ActivityIndicator,
} from 'react-native';
import { useNetwork } from '../../../App';
import { inventoryAPI } from '../../services/api';
import { getProducts } from '../../store/offlineStore';

export default function InventoryScreen() {
  const { isConnected } = useNetwork();
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      if (isConnected) {
        const res = await inventoryAPI.list({ search: search || undefined, limit: 200 });
        setProducts(Array.isArray(res) ? res : []);
      } else {
        const cached = await getProducts(search);
        setProducts(cached);
      }
    } catch (e) {
      setError(e.message || 'حدث خطأ في تحميل المنتجات');
      try {
        const cached = await getProducts(search);
        setProducts(cached);
      } catch { /* ignore */ }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected, search]);

  useEffect(() => { load(); }, [load]);

  const renderItem = ({ item }) => {
    const qty = item.quantity_on_hand ?? null;
    const inStock = qty !== null && qty > 0;
    const lowStock = qty !== null && qty > 0 && qty < 10;
    const stockColor = inStock ? (lowStock ? '#e65100' : '#2e7d32') : '#c62828';
    const stockBg = inStock ? (lowStock ? '#fff3e0' : '#e8f5e9') : '#ffebee';
    const stockLabel = inStock ? (lowStock ? 'مخزون منخفض' : 'متوفر') : 'نفد';

    return (
      <View style={styles.card}>
        <View style={styles.cardTop}>
          <View style={[styles.stockBadge, { backgroundColor: stockBg }]}>
            <Text style={[styles.stockBadgeText, { color: stockColor }]}>{stockLabel}</Text>
          </View>
          <View style={styles.cardTitles}>
            <Text style={styles.productName}>{item.name || item.product_name}</Text>
            {(item.sku || item.product_code) ? (
              <Text style={styles.sku}>{item.sku || item.product_code}</Text>
            ) : null}
          </View>
        </View>
        <View style={styles.cardStats}>
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{qty ?? '—'}</Text>
            <Text style={styles.statLbl}>الكمية</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statBox}>
            <Text style={styles.statNum}>{item.selling_price ?? item.price ?? '—'}</Text>
            <Text style={styles.statLbl}>سعر البيع</Text>
          </View>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#1976d2" />
        <Text style={styles.loadingText}>جارٍ تحميل المخزون...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.searchWrap}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          style={styles.search}
          placeholder="بحث عن منتج..."
          value={search}
          onChangeText={setSearch}
          onSubmitEditing={load}
          textAlign="right"
          placeholderTextColor="#90a4ae"
          returnKeyType="search"
        />
      </View>
      <FlatList
        data={products}
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
            <Text style={styles.emptyIcon}>{error ? '⚠️' : '📦'}</Text>
            <Text style={styles.empty}>{error || 'لا توجد منتجات'}</Text>
            {error && (
              <Text style={{ color: '#78909c', fontSize: 13, marginTop: 6, textAlign: 'center' }}>
                اسحب للأسفل لإعادة المحاولة
              </Text>
            )}
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
    elevation: 2, paddingHorizontal: 14,
    borderWidth: 1, borderColor: '#e0e7ef',
  },
  searchIcon: { fontSize: 16, marginLeft: 8 },
  search: { flex: 1, paddingVertical: 13, fontSize: 15, color: '#1a2332' },

  list: { paddingHorizontal: 14, paddingBottom: 20 },

  card: {
    backgroundColor: '#fff', borderRadius: 12, marginBottom: 10,
    padding: 16, elevation: 3,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07, shadowRadius: 4,
  },
  cardTop: { flexDirection: 'row-reverse', alignItems: 'flex-start', marginBottom: 14 },
  cardTitles: { flex: 1, marginRight: 0 },
  productName: { fontSize: 16, fontWeight: '700', color: '#1a2332', textAlign: 'right' },
  sku: { fontSize: 12, color: '#90a4ae', textAlign: 'right', marginTop: 2 },
  stockBadge: { borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4, marginLeft: 0, alignSelf: 'flex-start' },
  stockBadgeText: { fontSize: 12, fontWeight: '700' },

  cardStats: { flexDirection: 'row-reverse', backgroundColor: '#f8fafc', borderRadius: 8, overflow: 'hidden' },
  statBox: { flex: 1, alignItems: 'center', paddingVertical: 10 },
  statDivider: { width: 1, backgroundColor: '#e0e7ef' },
  statNum: { fontSize: 18, fontWeight: '700', color: '#1976d2' },
  statLbl: { fontSize: 11, color: '#90a4ae', marginTop: 2 },

  emptyWrap: { alignItems: 'center', paddingVertical: 60 },
  emptyIcon: { fontSize: 40, marginBottom: 12 },
  empty: { color: '#90a4ae', fontSize: 16 },
});
