/**
 * Push notification handler — registers device with FCM,
 * receives and displays push notifications.
 */
import { Platform } from 'react-native';
import { mobileAPI } from './api';
import { getDeviceId } from './syncService';

let _messaging = null;

/**
 * Lazy-load Firebase messaging (avoids crash if Firebase not configured).
 */
function getMessaging() {
  if (!_messaging) {
    try {
      _messaging = require('@react-native-firebase/messaging').default();
    } catch {
      console.warn('Firebase messaging not available');
    }
  }
  return _messaging;
}

/**
 * Request notification permission and register the device with the backend.
 */
export async function registerForPushNotifications() {
  const messaging = getMessaging();
  if (!messaging) return null;

  // Request permission (iOS)
  const authStatus = await messaging.requestPermission();
  const enabled =
    authStatus === 1 /* AUTHORIZED */ || authStatus === 2; /* PROVISIONAL */

  if (!enabled) {
    console.log('Push notification permission denied');
    return null;
  }

  // Get FCM token
  const fcmToken = await messaging.getToken();
  if (!fcmToken) return null;

  // Register with backend
  const deviceId = await getDeviceId();
  const platform = Platform.OS === 'ios' ? 'ios' : 'android';

  try {
    await mobileAPI.registerDevice(deviceId, platform, fcmToken);
    console.log('Device registered for push notifications');
  } catch (err) {
    console.warn('Failed to register device:', err.message);
  }

  return fcmToken;
}

/**
 * Listen for incoming foreground messages.
 * @param {function} onMessage - callback receiving { title, body, data }
 * @returns {function} unsubscribe
 */
export function onForegroundMessage(onMessage) {
  const messaging = getMessaging();
  if (!messaging) return () => {};

  return messaging.onMessage(async (remoteMessage) => {
    const { notification, data } = remoteMessage;
    onMessage({
      title: notification?.title || 'إشعار',
      body: notification?.body || '',
      data: data || {},
    });
  });
}

/**
 * Handle background/quit-state messages (call once in app entry).
 */
export function setupBackgroundHandler() {
  const messaging = getMessaging();
  if (!messaging) return;

  messaging.setBackgroundMessageHandler(async (remoteMessage) => {
    // Background messages are handled by the OS notification tray
    console.log('Background message:', remoteMessage.messageId);
  });
}

/**
 * Handle notification tap that opened the app.
 * @param {function} onOpen - callback receiving notification data
 * @returns {function} unsubscribe
 */
export function onNotificationOpenedApp(onOpen) {
  const messaging = getMessaging();
  if (!messaging) return () => {};

  return messaging.onNotificationOpenedApp((remoteMessage) => {
    onOpen(remoteMessage.data || {});
  });
}
