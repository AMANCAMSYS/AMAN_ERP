import api from './apiClient'

export const checksAPI = {
    // Checks Receivable
    listReceivable: (params) => api.get('/checks/receivable', { params }),
    getReceivable: (id) => api.get(`/checks/receivable/${id}`),
    createReceivable: (data) => api.post('/checks/receivable', data),
    collectReceivable: (id, data) => api.post(`/checks/receivable/${id}/collect`, data),
    bounceReceivable: (id, data) => api.post(`/checks/receivable/${id}/bounce`, data),
    receivableStats: (params) => api.get('/checks/receivable/summary/stats', { params }),
    // Checks Payable
    listPayable: (params) => api.get('/checks/payable', { params }),
    getPayable: (id) => api.get(`/checks/payable/${id}`),
    createPayable: (data) => api.post('/checks/payable', data),
    clearPayable: (id, data) => api.post(`/checks/payable/${id}/clear`, data),
    bouncePayable: (id, data) => api.post(`/checks/payable/${id}/bounce`, data),
    payableStats: (params) => api.get('/checks/payable/summary/stats', { params }),
    // Alerts
    getDueAlerts: (params) => api.get('/checks/due-alerts', { params }),
}

export const notesAPI = {
    // Notes Receivable
    listReceivable: (params) => api.get('/notes/receivable', { params }),
    getReceivable: (id) => api.get(`/notes/receivable/${id}`),
    createReceivable: (data) => api.post('/notes/receivable', data),
    collectReceivable: (id, data) => api.post(`/notes/receivable/${id}/collect`, data),
    protestReceivable: (id, data) => api.post(`/notes/receivable/${id}/protest`, data),
    receivableStats: (params) => api.get('/notes/receivable/summary/stats', { params }),
    // Notes Payable
    listPayable: (params) => api.get('/notes/payable', { params }),
    getPayable: (id) => api.get(`/notes/payable/${id}`),
    createPayable: (data) => api.post('/notes/payable', data),
    payPayable: (id, data) => api.post(`/notes/payable/${id}/pay`, data),
    protestPayable: (id, data) => api.post(`/notes/payable/${id}/protest`, data),
    payableStats: (params) => api.get('/notes/payable/summary/stats', { params }),
    // Alerts
    getDueAlerts: (params) => api.get('/notes/due-alerts', { params }),
}
