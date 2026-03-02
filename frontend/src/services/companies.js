import api from './apiClient'

export const companiesAPI = {
    register: (data) => api.post('/companies/register', data),
    getTemplates: () => api.get('/companies/public/templates'),
    list: (params) => api.get('/companies/list', { params }),
    get: (id) => api.get(`/companies/${id}`),
    getCurrentCompany: (companyId) => api.get(`/companies/${companyId}`),
    update: (id, data) => api.put(`/companies/update/${id}`, data),
    uploadLogo: (id, formData) => api.post(`/companies/upload-logo/${id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),

    // Module Management (B2)
    getEnabledModules: () => api.get('/companies/modules'),
    updateEnabledModules: (modules) => api.put('/companies/modules', modules),
}
