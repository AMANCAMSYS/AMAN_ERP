import api from './apiClient'

export const settingsAPI = {
    get: () => api.get('/settings/'),
    updateBulk: (settings) => api.post('/settings/bulk', { settings }),
    generateCSID: (data) => api.post('/settings/generate-csid', data),
    testEmail: (data) => api.post('/settings/test-email', data),
}

export const rolesAPI = {
    list: () => api.get('/roles/'),
    get: (id) => api.get(`/roles/${id}`),
    create: (data) => api.post('/roles/', data),
    update: (id, data) => api.put(`/roles/${id}`, data),
    delete: (id) => api.delete(`/roles/${id}`),
    listPermissions: () => api.get('/roles/permissions'),
    initDefaults: () => api.post('/roles/init-defaults'),
    getPermissionSections: () => api.get('/roles/permissions/sections'),
}

export const branchesAPI = {
    list: () => api.get('/branches'),
    create: (data) => api.post('/branches', data),
    update: (id, data) => api.put(`/branches/${id}`, data),
    delete: (id) => api.delete(`/branches/${id}`)
}
