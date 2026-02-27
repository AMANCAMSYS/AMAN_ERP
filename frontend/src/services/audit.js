import api from './apiClient'

export const auditAPI = {
    // Audit Logs
    getLogs: (params) => api.get('/audit/logs', { params }),
    getAvailableActions: (params) => api.get('/audit/logs/actions', { params }),
    getStats: (params) => api.get('/audit/logs/stats', { params }),
}
