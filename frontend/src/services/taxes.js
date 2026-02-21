import api from './apiClient'

export const taxesAPI = {
    getVATReport: (params) => api.get('/taxes/vat-report', { params }),
    getTaxAudit: (params) => api.get('/taxes/audit-report', { params }),
    getSummary: () => api.get('/taxes/summary'),
    // Tax Rates
    listRates: (params) => api.get('/taxes/rates', { params }),
    getRate: (id) => api.get(`/taxes/rates/${id}`),
    createRate: (data) => api.post('/taxes/rates', data),
    updateRate: (id, data) => api.put(`/taxes/rates/${id}`, data),
    deleteRate: (id) => api.delete(`/taxes/rates/${id}`),
    // Tax Groups
    listGroups: () => api.get('/taxes/groups'),
    createGroup: (data) => api.post('/taxes/groups', data),
    // Tax Returns
    listReturns: (params) => api.get('/taxes/returns', { params }),
    getReturn: (id) => api.get(`/taxes/returns/${id}`),
    createReturn: (data) => api.post('/taxes/returns', data),
    fileReturn: (id, data) => api.put(`/taxes/returns/${id}/file`, data),
    cancelReturn: (id) => api.put(`/taxes/returns/${id}/cancel`),
    // Tax Payments
    listPayments: (params) => api.get('/taxes/payments', { params }),
    createPayment: (data) => api.post('/taxes/payments', data),
    // Settlement
    settle: (data) => api.post('/taxes/settle', data)
}
