import api from './apiClient'

export const notificationsAPI = {
    getAll: () => api.get('/notifications', { skipAbort: true }),
    getUnreadCount: () => api.get('/notifications/unread-count', { skipAbort: true }),
    markRead: (id) => api.put(`/notifications/${id}/read`),
    markAllRead: () => api.post('/notifications/mark-all-read'),

    // Send notification
    send: (data) => api.post('/notifications/send', data),

    // Settings
    getSettings: () => api.get('/notifications/settings'),
    updateSettings: (data) => api.put('/notifications/settings', data),

    // Test
    testEmail: (data) => api.post('/notifications/test-email', data),

    // Notification Preferences
    getPreferences: () => api.get('/notifications/preferences'),
    updatePreference: (data) => api.put('/notifications/preferences', data),
}
