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

    // Documents
    uploadDocument: (id, formData) => api.post(`/projects/${id}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    getDocuments: (id) => api.get(`/projects/${id}/documents`),
    deleteDocument: (id, docId) => api.delete(`/projects/${id}/documents/${docId}`),

    // Invoicing
    createInvoice: (id, data) => api.post(`/projects/${id}/create-invoice`, data),
}
