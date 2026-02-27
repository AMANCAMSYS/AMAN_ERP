import api from './apiClient'

export const securityAPI = {
    // 2FA
    setup2FA: () => api.post('/security/2fa/setup'),
    verify2FA: (data) => api.post('/security/2fa/verify', data),
    disable2FA: (data) => api.post('/security/2fa/disable', data),
    get2FAStatus: () => api.get('/security/2fa/status'),

    // Password
    changePassword: (data) => api.post('/security/change-password', data),
    getPasswordPolicy: () => api.get('/security/password-policy'),
    updatePasswordPolicy: (data) => api.put('/security/password-policy', data),
    checkPasswordExpiry: () => api.get('/security/password-expiry'),

    // Sessions
    listSessions: () => api.get('/security/sessions'),
    terminateSession: (id) => api.delete(`/security/sessions/${id}`),
    terminateAllSessions: () => api.delete('/security/sessions'),
}
