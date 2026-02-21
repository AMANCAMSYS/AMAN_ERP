import api from './apiClient'
import { cleanParams } from './apiClient'

export const expensesAPI = {
    list: (params) => api.get('/expenses/', { params: cleanParams(params) }),
    summary: (params) => api.get('/expenses/summary', { params: cleanParams(params) }),
    get: (id) => api.get(`/expenses/${id}`),
    create: (data) => api.post('/expenses/', data),
    update: (id, data) => api.put(`/expenses/${id}`, data),
    approve: (id, data) => api.post(`/expenses/${id}/approve`, data),
    delete: (id) => api.delete(`/expenses/${id}`),
    getReportByType: (params) => api.get('/expenses/reports/by-type', { params: cleanParams(params) }),
    getReportByCostCenter: (params) => api.get('/expenses/reports/by-cost-center', { params: cleanParams(params) }),
    getReportMonthly: (params) => api.get('/expenses/reports/monthly', { params: cleanParams(params) }),
}
