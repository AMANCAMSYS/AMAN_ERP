import api from './apiClient'

export const notificationsAPI = {
    getAll: () => api.get('/notifications', { skipAbort: true }),
    getUnreadCount: () => api.get('/notifications/unread-count', { skipAbort: true }),
    markRead: (id) => api.put(`/notifications/${id}/read`),
    markAllRead: () => api.post('/notifications/read-all'),
}
