import api from './apiClient'

export const contractsAPI = {
    listContracts: (params) => api.get('/contracts', { params }),
    getContract: (id) => api.get(`/contracts/${id}`),
    createContract: (data) => api.post('/contracts', data),
    updateContract: (id, data) => api.put(`/contracts/${id}`, data),
    renewContract: (id) => api.post(`/contracts/${id}/renew`),
    cancelContract: (id) => api.post(`/contracts/${id}/cancel`),
    generateInvoice: (id) => api.post(`/contracts/${id}/generate-invoice`),
    getExpiringContracts: (days = 30) => api.get('/contracts/alerts/expiring', { params: { days } }),
    getContractStats: () => api.get('/contracts/stats/summary')
}
