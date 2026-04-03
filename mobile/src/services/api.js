/**
 * Mobile API client — wraps fetch with auth token and base URL.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE = __DEV__ ? 'http://10.0.2.2:8000/api' : 'https://erp.aman.sa/api';

async function request(method, path, { body, params } = {}) {
  const token = await AsyncStorage.getItem('auth_token');
  const url = new URL(`${API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v != null) url.searchParams.set(k, v);
    });
  }

  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(url.toString(), {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    await AsyncStorage.removeItem('auth_token');
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  get: (path, opts) => request('GET', path, opts),
  post: (path, body) => request('POST', path, { body }),
  put: (path, body) => request('PUT', path, { body }),
  delete: (path) => request('DELETE', path),
};

// ── Mobile-specific endpoints ──
export const mobileAPI = {
  login: (companyCode, username, password) =>
    request('POST', '/auth/login', {
      body: { company_code: companyCode, username, password },
    }),
  dashboard: () => api.get('/mobile/dashboard'),
  batchSync: (deviceId, items) =>
    api.post('/mobile/sync', { device_id: deviceId, items }),
  syncStatus: (deviceId) =>
    api.get('/mobile/sync/status', { params: { device_id: deviceId } }),
  resolveConflict: (syncQueueId, resolution, mergedPayload) =>
    api.post('/mobile/sync/resolve', {
      sync_queue_id: syncQueueId,
      resolution,
      merged_payload: mergedPayload,
    }),
  registerDevice: (deviceId, platform, fcmToken) =>
    api.post('/mobile/register-device', {
      device_id: deviceId,
      platform,
      fcm_token: fcmToken,
    }),
};

// ── Existing endpoints used by mobile ──
export const inventoryAPI = {
  list: (params) => api.get('/products', { params }),
  getProduct: (id) => api.get(`/products/${id}`),
};

export const quotationAPI = {
  list: (params) => api.get('/sales/quotations', { params }),
  create: (data) => api.post('/sales/quotations', data),
};

export const orderAPI = {
  list: (params) => api.get('/sales/orders', { params }),
};

export const approvalAPI = {
  list: (params) => api.get('/approvals', { params }),
  approve: (id) => api.post(`/approvals/${id}/approve`),
  reject: (id, reason) => api.post(`/approvals/${id}/reject`, { reason }),
};
