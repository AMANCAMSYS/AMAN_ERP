/**
 * Conflict detection and resolution — compares local vs server timestamps,
 * presents both versions for manual resolution.
 */
import { mobileAPI } from './api';
import { getDeviceId } from './syncService';

/**
 * Fetch all unresolved conflicts for the current device.
 * @returns {Promise<Array>} list of conflict items from sync_queue
 */
export async function getConflicts() {
  const deviceId = await getDeviceId();
  const status = await mobileAPI.syncStatus(deviceId);
  return status;
}

/**
 * Resolve a single conflict.
 * @param {number} syncQueueId - ID of the sync_queue row
 * @param {'keep_server'|'keep_device'|'merge'} resolution
 * @param {object|null} mergedPayload - only required when resolution is 'merge'
 */
export async function resolveConflict(syncQueueId, resolution, mergedPayload = null) {
  return mobileAPI.resolveConflict(syncQueueId, resolution, mergedPayload);
}

/**
 * Compare two versions of an entity and return diff fields.
 * @param {object} serverVersion - the server state
 * @param {object} deviceVersion - the device (offline) state
 * @returns {Array<{field, serverValue, deviceValue}>}
 */
export function diffVersions(serverVersion, deviceVersion) {
  const allKeys = new Set([
    ...Object.keys(serverVersion || {}),
    ...Object.keys(deviceVersion || {}),
  ]);

  const diffs = [];
  for (const key of allKeys) {
    // Skip metadata fields
    if (['id', 'created_at', 'updated_at', 'created_by', 'updated_by'].includes(key)) continue;

    const sv = serverVersion?.[key];
    const dv = deviceVersion?.[key];
    if (String(sv) !== String(dv)) {
      diffs.push({ field: key, serverValue: sv, deviceValue: dv });
    }
  }
  return diffs;
}

/**
 * Auto-resolve trivial conflicts (e.g., only updated_at differs).
 * Returns 'keep_server' if no meaningful differences.
 */
export function suggestResolution(serverVersion, deviceVersion) {
  const diffs = diffVersions(serverVersion, deviceVersion);
  if (diffs.length === 0) return 'keep_server';
  return null; // Needs manual resolution
}
