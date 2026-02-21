import api from './apiClient'

export const companiesAPI = {
    register: (data) => api.post('/companies/register', data),
    list: (params) => api.get('/companies/list', { params }),
    get: (id) => api.get(`/companies/${id}`),
    getCurrentCompany: (companyId) => api.get(`/companies/${companyId}`)
}
