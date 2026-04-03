import api from './apiClient'
import { cleanParams } from './apiClient'

export const cashflowAPI = {
    generate: (data) => api.post('/finance/cashflow/generate', data),
    list: (params) => api.get('/finance/cashflow', { params: cleanParams(params) }),
    get: (id) => api.get(`/finance/cashflow/${id}`),
    delete: (id) => api.delete(`/finance/cashflow/${id}`),
}
