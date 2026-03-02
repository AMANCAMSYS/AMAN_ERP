import api from './apiClient'

// Backup & Restore
export const backupAPI = {
    create: () => api.post('/admin/backup'),
    list: () => api.get('/admin/backups'),
    download: (id) => api.get(`/admin/backups/${id}/download`, { responseType: 'blob' }),
}

// Print Templates
export const printTemplatesAPI = {
    list: () => api.get('/settings/print-templates'),
    get: (id) => api.get(`/settings/print-templates/${id}`),
    create: (data) => api.post('/settings/print-templates', data),
    update: (id, data) => api.put(`/settings/print-templates/${id}`, data),
}

// Duplicate Detection
export const duplicateDetectionAPI = {
    checkParties: (data) => api.post('/parties/check-duplicates', data),
    checkProducts: (data) => api.post('/inventory/check-duplicates', data),
}

// Forgot Password
export const passwordResetAPI = {
    forgotPassword: (data) => api.post('/auth/forgot-password', data),
    resetPassword: (data) => api.post('/auth/reset-password', data),
}

// Manufacturing Costing (extends manufacturing)
export const manufacturingCostingAPI = {
    calculateCost: (orderId) => api.post(`/manufacturing/orders/${orderId}/calculate-cost`),
    getCostVarianceReport: (params) => api.get('/manufacturing/cost-variance-report', { params }),
}

