import api from './apiClient'

export const projectsAPI = {
    list: (params) => api.get('/projects/', { params }),
    summary: () => api.get('/projects/summary'),
    get: (id) => api.get(`/projects/${id}`),
    create: (data) => api.post('/projects/', data),
    update: (id, data) => api.put(`/projects/${id}`, data),
    delete: (id) => api.delete(`/projects/${id}`),
    getTasks: (id) => api.get(`/projects/${id}/tasks`),
    createTask: (id, data) => api.post(`/projects/${id}/tasks`, data),
    updateTask: (id, tid, data) => api.put(`/projects/${id}/tasks/${tid}`, data),
    deleteTask: (id, tid) => api.delete(`/projects/${id}/tasks/${tid}`),
    getExpenses: (id) => api.get(`/projects/${id}/expenses`),
    createExpense: (id, data) => api.post(`/projects/${id}/expenses`, data),
    getRevenues: (id) => api.get(`/projects/${id}/revenues`),
    createRevenue: (id, data) => api.post(`/projects/${id}/revenues`, data),
    getFinancials: (id) => api.get(`/projects/${id}/financials`),
    listTimesheets: (id) => api.get(`/projects/${id}/timesheets`),
    createTimesheet: (id, data) => api.post(`/projects/${id}/timesheets`, data),
    updateTimesheet: (id, data) => api.put(`/projects/timesheets/${id}`, data),
    deleteTimesheet: (id) => api.delete(`/projects/timesheets/${id}`),
    approveTimesheets: (id, data) => api.post(`/projects/${id}/timesheets/approve`, data),
    getResourceAllocation: (params) => api.get('/projects/resources/allocation', { params }),
    getProfitabilityReport: (params) => api.get('/projects/reports/profitability', { params }),
    getResourceUtilization: (params) => api.get('/projects/reports/resource-utilization', { params }),

    // Documents
    uploadDocument: (id, formData) => api.post(`/projects/${id}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    getDocuments: (id) => api.get(`/projects/${id}/documents`),
    deleteDocument: (id, docId) => api.delete(`/projects/${id}/documents/${docId}`),

    // Invoicing
    createInvoice: (id, data) => api.post(`/projects/${id}/create-invoice`, data),

    // Alerts
    getAlertsDashboard: () => api.get('/projects/alerts/dashboard'),
    getOverBudgetAlerts: () => api.get('/projects/alerts/over-budget'),
    getOverdueTaskAlerts: () => api.get('/projects/alerts/overdue-tasks'),

    // Change Orders
    getChangeOrders: (projectId) => api.get(`/projects/${projectId}/change-orders`),
    createChangeOrder: (projectId, data) => api.post(`/projects/${projectId}/change-orders`, data),
    updateChangeOrder: (coId, data) => api.put(`/projects/change-orders/${coId}`, data),
    approveChangeOrder: (coId) => api.post(`/projects/change-orders/${coId}/approve`),

    // EVM & Analysis
    getEVM: (projectId) => api.get(`/projects/${projectId}/evm`),
    closeProject: (projectId) => api.post(`/projects/${projectId}/close`),
    getVarianceReport: (params) => api.get('/projects/reports/variance', { params }),

    // Retainer
    setupRetainer: (projectId, data) => api.put(`/projects/${projectId}/retainer-setup`, data),
    generateRetainerInvoices: (data) => api.post('/projects/retainer/generate-invoices', data),
}
