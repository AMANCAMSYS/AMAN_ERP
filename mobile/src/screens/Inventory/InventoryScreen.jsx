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

  const load = useCallback(async () => {
    try {
      if (isConnected) {
        const res = await inventoryAPI.list({ search, limit: 50 });
        setProducts(res.items || res || []);
      } else {
        const cached = await getProducts(search);
        setProducts(cached);
      }
    } catch {
      const cached = await getProducts(search);
      setProducts(cached);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isConnected, search]);

  useEffect(() => { load(); }, [load]);

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.productName}>{item.name || item.product_name}</Text>
        <Text style={styles.sku}>{item.sku || item.product_code || ''}</Text>
      </View>
      <View style={styles.cardBody}>
        <View style={styles.stat}>
          <Text style={styles.statLabel}>الكمية</Text>
          <Text style={styles.statValue}>{item.quantity_on_hand ?? '—'}</Text>
        </View>
        <View style={styles.stat}>
          <Text style={styles.statLabel}>السعر</Text>
          <Text style={styles.statValue}>{item.selling_price ?? item.price ?? '—'}</Text>
        </View>
        <View style={styles.stat}>
          <Text style={styles.statLabel}>الحالة</Text>
          <Text style={[styles.statValue, item.quantity_on_hand > 0 ? styles.inStock : styles.outStock]}>
            {item.quantity_on_hand > 0 ? 'متوفر' : 'نفد'}
          </Text>
        </View>
      </View>
    </View>
  );

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color="#1976d2" /></View>;
  }

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.search}
        placeholder="بحث عن منتج..."
        value={search}
        onChangeText={setSearch}
        onSubmitEditing={load}
        textAlign="right"
      />
      <FlatList
        data={products}
        keyExtractor={(item) => String(item.id)}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} />}
        ListEmptyComponent={<Text style={styles.empty}>لا توجد منتجات</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  search: {
    margin: 12, padding: 12, backgroundColor: '#fff', borderRadius: 8,
    borderWidth: 1, borderColor: '#ddd', fontSize: 16,
  },
  card: {
    backgroundColor: '#fff', borderRadius: 8, marginHorizontal: 12, marginBottom: 8,
    padding: 12, elevation: 1,
  },
  cardHeader: { flexDirection: 'row-reverse', justifyContent: 'space-between', marginBottom: 8 },
  productName: { fontSize: 16, fontWeight: '600', textAlign: 'right', flex: 1 },
  sku: { fontSize: 12, color: '#999', marginRight: 8 },
  cardBody: { flexDirection: 'row-reverse', justifyContent: 'space-around' },
  stat: { alignItems: 'center' },
  statLabel: { fontSize: 12, color: '#666' },
  statValue: { fontSize: 16, fontWeight: '600', marginTop: 2 },
  inStock: { color: '#4caf50' },
  outStock: { color: '#f44336' },
  empty: { textAlign: 'center', padding: 40, color: '#999', fontSize: 16 },
});
