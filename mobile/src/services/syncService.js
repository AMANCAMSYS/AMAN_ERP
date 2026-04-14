/**
 * Offline sync engine — queues operations while offline,
 * replays on reconnection with idempotent retries.
 */
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { mobileAPI } from './api';
import 'react-native-get-random-values';
import { v4 as uuidv4 } from 'uuid';

const QUEUE_KEY = '@aman_sync_queue';
const DEVICE_ID_KEY = '@aman_device_id';

// ── Device ID management ──────────────────────────────────────────────────────

let _deviceId = null;

export async function getDeviceId() {
  if (_deviceId) return _deviceId;
  let id = await AsyncStorage.getItem(DEVICE_ID_KEY);
  if (!id) {
    id = `device_${uuidv4()}`;
    await AsyncStorage.setItem(DEVICE_ID_KEY, id);
  }
  _deviceId = id;
  return id;
}

// ── Queue management ──────────────────────────────────────────────────────────

async function _loadQueue() {
  const raw = await AsyncStorage.getItem(QUEUE_KEY);
  return raw ? JSON.parse(raw) : [];
}

async function _saveQueue(queue) {
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

/**
 * Enqueue an operation for offline sync.
 * @param {string} entityType - e.g. "quotation", "sales_order"
 * @param {number|null} entityId - existing entity or null for create
 * @param {string} operation - "create" or "update"
 * @param {object} payload - the data to sync
 */
export async function enqueue(entityType, entityId, operation, payload) {
  const queue = await _loadQueue();
  queue.push({
    entity_type: entityType,
    entity_id: entityId,
    operation,
    payload,
    device_timestamp: new Date().toISOString(),
    retries: 0,
  });
  await _saveQueue(queue);
}

/**
 * Get the current offline queue size.
 */
export async function getQueueSize() {
  const queue = await _loadQueue();
  return queue.length;
}

/**
 * Flush the offline queue — batch-send to server.
 * Returns { synced, conflicts, errors, results }.
 */
export async function flush() {
  const state = await NetInfo.fetch();
  if (!state.isConnected) {
    return { synced: 0, conflicts: 0, errors: 0, results: [], offline: true };
  }

  const queue = await _loadQueue();
  if (queue.length === 0) {
    return { synced: 0, conflicts: 0, errors: 0, results: [] };
  }

  const deviceId = await getDeviceId();
  const items = queue.map(({ entity_type, entity_id, operation, payload, device_timestamp }) => ({
    entity_type,
    entity_id,
    operation,
    payload,
    device_timestamp,
  }));

  try {
    const result = await mobileAPI.batchSync(deviceId, items);

    // Remove successfully synced items from queue, keep errors for retry
    const remaining = [];
    for (let i = 0; i < queue.length; i++) {
      const r = result.results.find((x) => x.index === i);
      if (!r || r.status === 'error') {
        const entry = queue[i];
        entry.retries = (entry.retries || 0) + 1;
        if (entry.retries < 5) {
          remaining.push(entry);
        }
      }
      // 'synced' and 'conflict' items are removed from local queue
      // (conflicts are tracked server-side in sync_queue)
    }
    await _saveQueue(remaining);

    return result;
  } catch (err) {
    return { synced: 0, conflicts: 0, errors: queue.length, results: [], error: err.message };
  }
}

// ── Auto-sync on reconnection ─────────────────────────────────────────────────

let _unsubscribe = null;

export function startAutoSync() {
  if (_unsubscribe) return;
  _unsubscribe = NetInfo.addEventListener(async (state) => {
    if (state.isConnected) {
      const size = await getQueueSize();
      if (size > 0) {
        await flush();
      }
    }
  });
}

export function stopAutoSync() {
  if (_unsubscribe) {
    _unsubscribe();
    _unsubscribe = null;
  }
}
