/**
 * Offline local storage layer — AsyncStorage-based cache for
 * inventory, quotations, orders, approvals.
 *
 * Uses AsyncStorage as the storage backend (SQLite via react-native-sqlite-storage
 * can be swapped in when more complex queries are needed).
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = {
  PRODUCTS: '@aman_cache_products',
  QUOTATIONS: '@aman_cache_quotations',
  ORDERS: '@aman_cache_orders',
  APPROVALS: '@aman_cache_approvals',
};

const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

// ── Generic helpers ───────────────────────────────────────────────────────────

async function _getCache(key) {
  const raw = await AsyncStorage.getItem(key);
  if (!raw) return null;
  const { data, ts } = JSON.parse(raw);
  if (Date.now() - ts > CACHE_TTL) return null; // expired
  return data;
}

async function _setCache(key, data) {
  await AsyncStorage.setItem(key, JSON.stringify({ data, ts: Date.now() }));
}

// ── Products / Inventory ──────────────────────────────────────────────────────

export async function cacheProducts(products) {
  await _setCache(KEYS.PRODUCTS, products);
}

export async function getProducts(search = '') {
  const items = (await _getCache(KEYS.PRODUCTS)) || [];
  if (!search) return items;
  const q = search.toLowerCase();
  return items.filter(
    (p) =>
      (p.name || '').toLowerCase().includes(q) ||
      (p.product_name || '').toLowerCase().includes(q) ||
      (p.sku || '').toLowerCase().includes(q) ||
      (p.product_code || '').toLowerCase().includes(q)
  );
}

// ── Quotations ────────────────────────────────────────────────────────────────

export async function cacheQuotations(quotations) {
  await _setCache(KEYS.QUOTATIONS, quotations);
}

export async function getQuotations() {
  return (await _getCache(KEYS.QUOTATIONS)) || [];
}

export async function addOfflineQuotation(quotation) {
  const items = await getQuotations();
  items.unshift({ ...quotation, id: `offline_${Date.now()}`, _offline: true });
  await _setCache(KEYS.QUOTATIONS, items);
}

// ── Orders ────────────────────────────────────────────────────────────────────

export async function cacheOrders(orders) {
  await _setCache(KEYS.ORDERS, orders);
}

export async function getOrders() {
  return (await _getCache(KEYS.ORDERS)) || [];
}

// ── Approvals ─────────────────────────────────────────────────────────────────

export async function cacheApprovals(approvals) {
  await _setCache(KEYS.APPROVALS, approvals);
}

export async function getApprovals() {
  return (await _getCache(KEYS.APPROVALS)) || [];
}

// ── Clear all cache ───────────────────────────────────────────────────────────

export async function clearCache() {
  await AsyncStorage.multiRemove(Object.values(KEYS));
}
