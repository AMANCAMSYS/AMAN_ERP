import api from './apiClient'

export const partiesAPI = {
    getCustomers: (params) => api.get('/parties/customers', { params }),
    getSuppliers: (params) => api.get('/parties/suppliers', { params }),
}
